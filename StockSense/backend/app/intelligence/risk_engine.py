"""
StockSense – Stock Risk Engine
================================
Calculates explainable stock risk levels for every product.

This is NOT machine learning and does NOT use an LLM.
It uses transparent, auditable business logic based on real inventory data.

Risk Formula
------------
days_of_cover = current_stock / average_daily_usage

    If average_daily_usage == 0 and current_stock > 0:
        days_of_cover = float('inf')  (stock will never run out)
    If average_daily_usage == 0 and current_stock == 0:
        days_of_cover = 0  (nothing on hand, nothing needed)

Risk Levels (configurable via RISK_THRESHOLDS)
----------------------------------------------
CRITICAL : days_of_cover < CRITICAL_DAYS
HIGH     : days_of_cover < HIGH_DAYS
MEDIUM   : days_of_cover < MEDIUM_DAYS
LOW      : days_of_cover >= MEDIUM_DAYS

All threshold values are centralized at the top of this module.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.stock import Stock
from app.models.product import Product
from app.models.reorder_rule import ReorderRule
from app.models.stock_ledger import StockLedger


# ── Centralized threshold configuration ───────────────────────────────────────
# Change these values to tune risk sensitivity for the business.

RISK_THRESHOLDS = {
    "CRITICAL_DAYS": 2,   # < 2 days cover  => CRITICAL
    "HIGH_DAYS": 7,        # < 7 days cover  => HIGH
    "MEDIUM_DAYS": 14,     # < 14 days cover => MEDIUM
    # >= 14 days cover     => LOW
}

RISK_LEVEL_CRITICAL = "CRITICAL"
RISK_LEVEL_HIGH = "HIGH"
RISK_LEVEL_MEDIUM = "MEDIUM"
RISK_LEVEL_LOW = "LOW"


@dataclass
class StockRiskResult:
    """Structured result for a single product risk calculation.

    Every field is populated with real data – no invented values.
    """
    product_id: int
    product_name: str
    risk_level: str
    reason: str
    days_of_cover: Optional[float]          # None if unknown
    current_stock: float
    average_daily_usage: float
    reorder_point: Optional[float]
    safety_stock: Optional[float]
    incoming_stock: float = 0.0
    extra_info: dict = field(default_factory=dict)


class RiskEngine:
    """Analyses real stock data and returns explainable risk assessments."""

    def __init__(self, db: Session) -> None:
        self._db = db

    # ── Public API ─────────────────────────────────────────────────────────────

    def assess_product_risk(
        self,
        product_id: int,
        location_id: Optional[int] = None,
    ) -> StockRiskResult:
        """Calculate the risk level for a single product.

        Args:
            product_id: Which product to assess.
            location_id: Restrict to a specific location. If None, use total stock.

        Returns:
            :class:`StockRiskResult` with full explanation.
        """
        product = self._db.query(Product).filter(Product.id == product_id).first()
        product_name = product.name if product else f"Product#{product_id}"

        current_stock = self._get_current_stock(product_id, location_id)
        avg_daily_usage = self._compute_average_daily_usage(product_id, location_id, days=30)
        reorder_rule = self._get_reorder_rule(product_id)

        reorder_point = None
        safety_stock = None
        if reorder_rule:
            rp = getattr(reorder_rule, "reorder_point", None) or getattr(reorder_rule, "min_quantity", None)
            reorder_point = float(rp) if rp is not None else None
            ss = getattr(reorder_rule, "safety_stock", None) or getattr(reorder_rule, "min_quantity", None)
            safety_stock = float(ss) if ss is not None else None

        days_of_cover = self._compute_days_of_cover(current_stock, avg_daily_usage)
        risk_level, reason = self._classify_risk(
            days_of_cover=days_of_cover,
            current_stock=current_stock,
            avg_daily_usage=avg_daily_usage,
            reorder_point=reorder_point,
            product_name=product_name,
        )

        return StockRiskResult(
            product_id=product_id,
            product_name=product_name,
            risk_level=risk_level,
            reason=reason,
            days_of_cover=days_of_cover,
            current_stock=current_stock,
            average_daily_usage=avg_daily_usage,
            reorder_point=reorder_point,
            safety_stock=safety_stock,
        )

    def assess_all_products(self) -> list[StockRiskResult]:
        """Assess risk for every product that has a stock record."""
        product_ids = [
            pid for (pid,) in self._db.query(Stock.product_id).distinct().all()
        ]
        return [self.assess_product_risk(pid) for pid in product_ids]

    def get_critical_and_high_risk(self) -> list[StockRiskResult]:
        """Return only CRITICAL and HIGH risk products (for dashboard alerts)."""
        all_results = self.assess_all_products()
        return [
            r for r in all_results
            if r.risk_level in (RISK_LEVEL_CRITICAL, RISK_LEVEL_HIGH)
        ]

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _get_current_stock(self, product_id: int, location_id: Optional[int]) -> float:
        """Query actual current stock quantity."""
        query = self._db.query(func.coalesce(func.sum(Stock.quantity), 0)).filter(
            Stock.product_id == product_id
        )
        if location_id is not None:
            query = query.filter(Stock.location_id == location_id)
        result = query.scalar()
        return float(result) if result else 0.0

    def _compute_average_daily_usage(
        self,
        product_id: int,
        location_id: Optional[int],
        days: int = 30,
    ) -> float:
        """Compute average daily usage from DELIVERY ledger entries in the last *days*."""
        from datetime import datetime, timedelta, timezone

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        op_col = getattr(StockLedger, "operation_type", None) or getattr(StockLedger, "transaction_type", None)

        query = (
            self._db.query(func.coalesce(func.sum(StockLedger.quantity_change), 0))
            .filter(
                StockLedger.product_id == product_id,
                op_col == "DELIVERY",
                StockLedger.created_at >= cutoff,
            )
        )
        if location_id is not None:
            query = query.filter(StockLedger.location_id == location_id)

        total_delivered_negative = query.scalar() or 0
        total_delivered = abs(float(total_delivered_negative))
        return total_delivered / days if days > 0 else 0.0

    def _get_reorder_rule(self, product_id: int) -> Optional[ReorderRule]:
        """Fetch the most relevant reorder rule for the product."""
        return (
            self._db.query(ReorderRule)
            .filter(ReorderRule.product_id == product_id)
            .first()
        )

    @staticmethod
    def _compute_days_of_cover(current_stock: float, avg_daily_usage: float) -> Optional[float]:
        """Safely compute days of cover without division-by-zero errors."""
        if avg_daily_usage <= 0:
            if current_stock > 0:
                return float("inf")
            return 0.0
        return current_stock / avg_daily_usage

    @classmethod
    def _classify_risk(
        cls,
        days_of_cover: Optional[float],
        current_stock: float,
        avg_daily_usage: float,
        reorder_point: Optional[float],
        product_name: str,
    ) -> tuple[str, str]:
        """Determine risk level and write a plain-English explanation."""
        if current_stock == 0:
            return (
                RISK_LEVEL_CRITICAL,
                f"'{product_name}' has ZERO stock on hand. Immediate stockout.",
            )

        if days_of_cover is None or math.isinf(days_of_cover):
            if reorder_point is not None and current_stock <= reorder_point:
                return (
                    RISK_LEVEL_HIGH,
                    f"'{product_name}' current stock ({current_stock:.1f}) is at or below the reorder point "
                    f"({reorder_point:.1f}), though no recent delivery usage is recorded.",
                )
            return (
                RISK_LEVEL_LOW,
                f"'{product_name}' has {current_stock:.1f} units in stock with no recent demand recorded. "
                "Risk is low (inactive or new product).",
            )

        doc = days_of_cover

        if doc < RISK_THRESHOLDS["CRITICAL_DAYS"]:
            return (
                RISK_LEVEL_CRITICAL,
                f"'{product_name}' has only {doc:.1f} days of cover "
                f"(current stock: {current_stock:.1f}, average usage: {avg_daily_usage:.1f}/day). "
                f"Critical threshold is {RISK_THRESHOLDS['CRITICAL_DAYS']} days.",
            )

        if doc < RISK_THRESHOLDS["HIGH_DAYS"]:
            return (
                RISK_LEVEL_HIGH,
                f"'{product_name}' has {doc:.1f} days of cover "
                f"(current stock: {current_stock:.1f}, average usage: {avg_daily_usage:.1f}/day). "
                f"High risk threshold is {RISK_THRESHOLDS['HIGH_DAYS']} days.",
            )

        if doc < RISK_THRESHOLDS["MEDIUM_DAYS"]:
            return (
                RISK_LEVEL_MEDIUM,
                f"'{product_name}' has {doc:.1f} days of cover "
                f"(current stock: {current_stock:.1f}, average usage: {avg_daily_usage:.1f}/day). "
                f"Medium risk threshold is {RISK_THRESHOLDS['MEDIUM_DAYS']} days.",
            )

        return (
            RISK_LEVEL_LOW,
            f"'{product_name}' stock is healthy: {doc:.1f} days of cover "
            f"(current stock: {current_stock:.1f}, average usage: {avg_daily_usage:.1f}/day).",
        )
