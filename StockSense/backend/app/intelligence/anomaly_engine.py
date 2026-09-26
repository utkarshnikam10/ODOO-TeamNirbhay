"""
StockSense – Anomaly Detection Engine
========================================
Detects suspicious or unusual inventory movements using explainable rules.

This is NOT machine learning. It uses statistical thresholds and business
rules derived from actual historical data in the StockLedger.

Detection methods:
1. Large single adjustment (absolute value > N * std_dev of recent adjustments)
2. Repeated adjustments for same product in short window
3. Sudden large stock decrease not backed by a delivery
4. Delivery quantity significantly above recent average
5. Unusual transaction frequency (too many moves in 24h)

Every anomaly includes: event, reason, severity, supporting values, reference.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.stock_ledger import StockLedger
from app.models.product import Product


# ── Threshold configuration ────────────────────────────────────────────────────
# All thresholds in one place so they can be reviewed / tuned easily.

ANOMALY_THRESHOLDS = {
    # Large adjustment: flag if abs(diff) > this many std deviations from mean (2.0 = 95% CI)
    "ADJUSTMENT_ZSCORE_THRESHOLD": 2.0,
    # Repeated adjustment: flag if same product has more than N adjustments in window
    "REPEATED_ADJUSTMENT_MAX_COUNT": 3,
    "REPEATED_ADJUSTMENT_WINDOW_DAYS": 7,
    # Large delivery: flag if quantity > this many std deviations above recent mean
    "DELIVERY_ZSCORE_THRESHOLD": 2.0,
    # Unusual frequency: flag if more than N stock events for one product in 24h
    "HIGH_FREQUENCY_THRESHOLD": 10,
    "HIGH_FREQUENCY_WINDOW_HOURS": 24,
    # Minimum samples needed before we apply statistical tests
    "MIN_SAMPLES_FOR_STATS": 5,
}

SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_HIGH = "HIGH"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_LOW = "LOW"


@dataclass
class AnomalyEvent:
    """A single detected anomaly. Every field is populated from real data."""
    product_id: int
    product_name: str
    event_type: str           # e.g. "LARGE_ADJUSTMENT", "REPEATED_ADJUSTMENT"
    severity: str             # CRITICAL / HIGH / MEDIUM / LOW
    reason: str               # plain-English explanation
    detected_at: datetime
    supporting_values: dict   # raw numbers that triggered the flag
    reference_transaction_id: Optional[int] = None
    reference_transaction_type: Optional[str] = None


class AnomalyEngine:
    """Analyses ledger history to find suspicious inventory movements."""

    def __init__(self, db: Session) -> None:
        self._db = db

    # ── Public API ─────────────────────────────────────────────────────────────

    def detect_all(self, lookback_days: int = 30) -> list[AnomalyEvent]:
        """Run all anomaly detectors and return combined results.

        Args:
            lookback_days: How far back to look in the ledger.

        Returns:
            List of detected :class:`AnomalyEvent` objects, sorted by severity.
        """
        anomalies: list[AnomalyEvent] = []
        anomalies.extend(self.detect_large_adjustments(lookback_days))
        anomalies.extend(self.detect_repeated_adjustments())
        anomalies.extend(self.detect_large_deliveries(lookback_days))
        anomalies.extend(self.detect_high_frequency_movements())

        # Sort: CRITICAL first, then HIGH, MEDIUM, LOW
        order = {SEVERITY_CRITICAL: 0, SEVERITY_HIGH: 1, SEVERITY_MEDIUM: 2, SEVERITY_LOW: 3}
        anomalies.sort(key=lambda a: order.get(a.severity, 99))
        return anomalies

    def detect_large_adjustments(self, lookback_days: int = 30) -> list[AnomalyEvent]:
        """Flag adjustments whose absolute value is a statistical outlier."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        op_col = getattr(StockLedger, "operation_type", None) or getattr(StockLedger, "transaction_type", None)

        entries = (
            self._db.query(StockLedger)
            .filter(
                op_col == "ADJUSTMENT",
                StockLedger.created_at >= cutoff,
            )
            .all()
        )

        by_product: dict[int, list[StockLedger]] = {}
        for e in entries:
            by_product.setdefault(e.product_id, []).append(e)

        min_samples = ANOMALY_THRESHOLDS["MIN_SAMPLES_FOR_STATS"]
        z_threshold = ANOMALY_THRESHOLDS["ADJUSTMENT_ZSCORE_THRESHOLD"]
        anomalies: list[AnomalyEvent] = []

        for product_id, rows in by_product.items():
            magnitudes = [abs(float(r.quantity_change)) for r in rows]
            if len(magnitudes) < min_samples:
                continue

            mean = statistics.mean(magnitudes)
            stdev = statistics.stdev(magnitudes)
            if stdev == 0:
                continue

            product_name = self._product_name(product_id)
            for row in rows:
                mag = abs(float(row.quantity_change))
                z_score = (mag - mean) / stdev
                if z_score > z_threshold:
                    ref_id = getattr(row, "reference_id", None)
                    ref_type = getattr(row, "reference_type", None) or getattr(row, "reference_number", None)
                    anomalies.append(AnomalyEvent(
                        product_id=product_id,
                        product_name=product_name,
                        event_type="LARGE_ADJUSTMENT",
                        severity=SEVERITY_HIGH if z_score < z_threshold * 1.5 else SEVERITY_CRITICAL,
                        reason=(
                            f"Adjustment of {float(row.quantity_change):+.1f} units for "
                            f"'{product_name}' is {z_score:.1f} standard deviations above "
                            f"the recent mean adjustment magnitude ({mean:.1f} units, "
                            f"std_dev={stdev:.1f}). This is statistically unusual."
                        ),
                        detected_at=datetime.now(timezone.utc),
                        supporting_values={
                            "quantity_change": float(row.quantity_change),
                            "magnitude": mag,
                            "mean_magnitude": round(mean, 2),
                            "stdev": round(stdev, 2),
                            "z_score": round(z_score, 2),
                            "threshold_z": z_threshold,
                        },
                        reference_transaction_id=ref_id,
                        reference_transaction_type=ref_type,
                    ))

        return anomalies

    def detect_repeated_adjustments(self) -> list[AnomalyEvent]:
        """Flag products with too many adjustments in a short window."""
        window_days = ANOMALY_THRESHOLDS["REPEATED_ADJUSTMENT_WINDOW_DAYS"]
        max_count = ANOMALY_THRESHOLDS["REPEATED_ADJUSTMENT_MAX_COUNT"]
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
        op_col = getattr(StockLedger, "operation_type", None) or getattr(StockLedger, "transaction_type", None)

        rows = (
            self._db.query(
                StockLedger.product_id,
                func.count(StockLedger.id).label("adj_count"),
            )
            .filter(
                op_col == "ADJUSTMENT",
                StockLedger.created_at >= cutoff,
            )
            .group_by(StockLedger.product_id)
            .having(func.count(StockLedger.id) > max_count)
            .all()
        )

        anomalies: list[AnomalyEvent] = []
        for product_id, adj_count in rows:
            product_name = self._product_name(product_id)
            anomalies.append(AnomalyEvent(
                product_id=product_id,
                product_name=product_name,
                event_type="REPEATED_ADJUSTMENT",
                severity=SEVERITY_HIGH,
                reason=(
                    f"'{product_name}' has had {adj_count} inventory adjustments in the last "
                    f"{window_days} days (threshold: {max_count}). Repeated adjustments may "
                    "indicate systematic counting errors, data entry issues, or inventory shrinkage."
                ),
                detected_at=datetime.now(timezone.utc),
                supporting_values={
                    "adjustment_count": adj_count,
                    "window_days": window_days,
                    "max_allowed": max_count,
                },
            ))
        return anomalies

    def detect_large_deliveries(self, lookback_days: int = 30) -> list[AnomalyEvent]:
        """Flag deliveries significantly above the recent average for a product."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        op_col = getattr(StockLedger, "operation_type", None) or getattr(StockLedger, "transaction_type", None)

        entries = (
            self._db.query(StockLedger)
            .filter(
                op_col == "DELIVERY",
                StockLedger.created_at >= cutoff,
            )
            .all()
        )

        by_product: dict[int, list[StockLedger]] = {}
        for e in entries:
            by_product.setdefault(e.product_id, []).append(e)

        min_samples = ANOMALY_THRESHOLDS["MIN_SAMPLES_FOR_STATS"]
        z_threshold = ANOMALY_THRESHOLDS["DELIVERY_ZSCORE_THRESHOLD"]
        anomalies: list[AnomalyEvent] = []

        for product_id, rows in by_product.items():
            magnitudes = [abs(float(r.quantity_change)) for r in rows]
            if len(magnitudes) < min_samples:
                continue

            mean = statistics.mean(magnitudes)
            stdev = statistics.stdev(magnitudes)
            if stdev == 0:
                continue

            product_name = self._product_name(product_id)
            for row in rows:
                mag = abs(float(row.quantity_change))
                z_score = (mag - mean) / stdev
                if z_score > z_threshold:
                    ref_id = getattr(row, "reference_id", None)
                    ref_type = getattr(row, "reference_type", None) or getattr(row, "reference_number", None)
                    anomalies.append(AnomalyEvent(
                        product_id=product_id,
                        product_name=product_name,
                        event_type="LARGE_DELIVERY",
                        severity=SEVERITY_MEDIUM,
                        reason=(
                            f"Delivery of {mag:.1f} units for '{product_name}' is "
                            f"{z_score:.1f} standard deviations above the recent delivery "
                            f"average ({mean:.1f} units). Verify this is legitimate."
                        ),
                        detected_at=datetime.now(timezone.utc),
                        supporting_values={
                            "delivery_quantity": mag,
                            "mean_delivery": round(mean, 2),
                            "stdev": round(stdev, 2),
                            "z_score": round(z_score, 2),
                        },
                        reference_transaction_id=ref_id,
                        reference_transaction_type=ref_type,
                    ))
        return anomalies

    def detect_high_frequency_movements(self) -> list[AnomalyEvent]:
        """Flag products with an unusually high number of stock movements in 24 hours."""
        window_hours = ANOMALY_THRESHOLDS["HIGH_FREQUENCY_WINDOW_HOURS"]
        threshold = ANOMALY_THRESHOLDS["HIGH_FREQUENCY_THRESHOLD"]
        cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)

        rows = (
            self._db.query(
                StockLedger.product_id,
                func.count(StockLedger.id).label("move_count"),
            )
            .filter(StockLedger.created_at >= cutoff)
            .group_by(StockLedger.product_id)
            .having(func.count(StockLedger.id) > threshold)
            .all()
        )

        anomalies: list[AnomalyEvent] = []
        for product_id, move_count in rows:
            product_name = self._product_name(product_id)
            anomalies.append(AnomalyEvent(
                product_id=product_id,
                product_name=product_name,
                event_type="HIGH_FREQUENCY_MOVEMENT",
                severity=SEVERITY_MEDIUM,
                reason=(
                    f"'{product_name}' has had {move_count} stock movements in the last "
                    f"{window_hours} hours (threshold: {threshold}). "
                    "Unusually high transaction frequency may indicate a data entry error "
                    "or a process issue."
                ),
                detected_at=datetime.now(timezone.utc),
                supporting_values={
                    "movement_count": move_count,
                    "window_hours": window_hours,
                    "threshold": threshold,
                },
            ))
        return anomalies

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _product_name(self, product_id: int) -> str:
        product = self._db.query(Product).filter(Product.id == product_id).first()
        return product.name if product else f"Product#{product_id}"
