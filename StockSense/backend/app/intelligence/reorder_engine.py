"""
StockSense – Reorder Recommendation Engine
============================================
Generates explainable reorder quantity recommendations.

This is NOT machine learning. It uses a transparent, documented formula
based on real inventory data from the database.

Formula (documented)
--------------------
Step 1 – Compute demand during lead time:
    demand_during_lead_time = average_daily_demand * supplier_lead_time_days

Step 2 – Required stock to be safe:
    required_stock = demand_during_lead_time + safety_stock

Step 3 – Account for stock already incoming:
    recommended_order = max(0, required_stock - current_stock - incoming_stock)

If recommended_order > 0, a reorder is recommended.
If recommended_order == 0, stock is sufficient.

All inputs come from real database records (ReorderRule + Stock + StockLedger).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.stock import Stock
from app.models.product import Product
from app.models.reorder_rule import ReorderRule
from app.models.stock_ledger import StockLedger


@dataclass
class ReorderRecommendation:
    """Structured recommendation result – every field is explainable."""
    product_id: int
    product_name: str
    recommended_order_qty: float
    reason: str
    current_stock: float
    average_daily_demand: float
    safety_stock: float
    incoming_stock: float
    supplier_lead_time_days: float
    demand_during_lead_time: float
    required_stock: float
    should_reorder: bool


class ReorderEngine:
    """Generates reorder recommendations from real database stock data."""

    def __init__(self, db: Session) -> None:
        self._db = db

    # ── Public API ─────────────────────────────────────────────────────────────

    def recommend_for_product(self, product_id: int) -> ReorderRecommendation:
        """Generate a reorder recommendation for one product.

        Args:
            product_id: The product to analyse.

        Returns:
            :class:`ReorderRecommendation` with full formula trace.
        """
        product = self._db.query(Product).filter(Product.id == product_id).first()
        product_name = product.name if product else f"Product#{product_id}"

        current_stock = self._get_current_stock(product_id)
        avg_daily_demand = self._compute_average_daily_demand(product_id, days=30)
        incoming_stock = self._get_incoming_stock(product_id)
        reorder_rule = self._get_reorder_rule(product_id)

        # Pull parameters from reorder rule if it exists, else use safe defaults
        safety_stock = 0.0
        lead_time = 0.0
        if reorder_rule:
            ss = getattr(reorder_rule, "safety_stock", None) or getattr(reorder_rule, "min_quantity", None)
            safety_stock = float(ss) if ss is not None else 0.0
            lt = getattr(reorder_rule, "lead_time_days", None) or getattr(reorder_rule, "lead_time", None)
            lead_time = float(lt) if lt is not None else 0.0

        # ── Apply the documented formula ───────────────────────────────────────
        demand_during_lead_time = avg_daily_demand * lead_time
        required_stock = demand_during_lead_time + safety_stock
        recommended_qty = max(0.0, required_stock - current_stock - incoming_stock)
        should_reorder = recommended_qty > 0.0

        # ── Build a human-readable explanation ────────────────────────────────
        reason = self._build_reason(
            product_name=product_name,
            current_stock=current_stock,
            avg_daily_demand=avg_daily_demand,
            lead_time=lead_time,
            safety_stock=safety_stock,
            incoming_stock=incoming_stock,
            demand_during_lead_time=demand_during_lead_time,
            required_stock=required_stock,
            recommended_qty=recommended_qty,
            should_reorder=should_reorder,
        )

        return ReorderRecommendation(
            product_id=product_id,
            product_name=product_name,
            recommended_order_qty=round(recommended_qty, 2),
            reason=reason,
            current_stock=round(current_stock, 2),
            average_daily_demand=round(avg_daily_demand, 2),
            safety_stock=round(safety_stock, 2),
            incoming_stock=round(incoming_stock, 2),
            supplier_lead_time_days=round(lead_time, 1),
            demand_during_lead_time=round(demand_during_lead_time, 2),
            required_stock=round(required_stock, 2),
            should_reorder=should_reorder,
        )

    def recommend_all(self) -> list[ReorderRecommendation]:
        """Generate recommendations for all products with stock records."""
        product_ids = [
            pid for (pid,) in self._db.query(Stock.product_id).distinct().all()
        ]
        return [self.recommend_for_product(pid) for pid in product_ids]

    def get_reorder_alerts(self) -> list[ReorderRecommendation]:
        """Return only products where a reorder is actually needed (qty > 0)."""
        return [r for r in self.recommend_all() if r.should_reorder]

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _get_current_stock(self, product_id: int) -> float:
        result = (
            self._db.query(func.coalesce(func.sum(Stock.quantity), 0))
            .filter(Stock.product_id == product_id)
            .scalar()
        )
        return float(result) if result else 0.0

    def _compute_average_daily_demand(self, product_id: int, days: int = 30) -> float:
        """Compute average daily demand from DELIVERY ledger entries."""
        from datetime import datetime, timedelta, timezone

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        op_col = getattr(StockLedger, "operation_type", None) or getattr(StockLedger, "transaction_type", None)

        total_delivered_neg = (
            self._db.query(func.coalesce(func.sum(StockLedger.quantity_change), 0))
            .filter(
                StockLedger.product_id == product_id,
                op_col == "DELIVERY",
                StockLedger.created_at >= cutoff,
            )
            .scalar()
        ) or 0
        total_delivered = abs(float(total_delivered_neg))
        return total_delivered / days if days > 0 else 0.0

    def _get_incoming_stock(self, product_id: int) -> float:
        """Sum stock quantities from DRAFT receipts (not yet delivered)."""
        from app.models.receipt import Receipt, ReceiptItem
        qty_col = getattr(ReceiptItem, "quantity_expected", None) or getattr(ReceiptItem, "quantity", None)
        if qty_col is None:
            return 0.0

        result = (
            self._db.query(func.coalesce(func.sum(qty_col), 0))
            .join(Receipt, Receipt.id == ReceiptItem.receipt_id)
            .filter(
                ReceiptItem.product_id == product_id,
                Receipt.status == "draft",
            )
            .scalar()
        )
        return float(result) if result else 0.0

    def _get_reorder_rule(self, product_id: int) -> Optional[ReorderRule]:
        return (
            self._db.query(ReorderRule)
            .filter(ReorderRule.product_id == product_id)
            .first()
        )

    @staticmethod
    def _build_reason(
        product_name: str,
        current_stock: float,
        avg_daily_demand: float,
        lead_time: float,
        safety_stock: float,
        incoming_stock: float,
        demand_during_lead_time: float,
        required_stock: float,
        recommended_qty: float,
        should_reorder: bool,
    ) -> str:
        if not should_reorder:
            return (
                f"'{product_name}' does not need reordering. "
                f"Current stock ({current_stock:.1f}) + incoming ({incoming_stock:.1f}) "
                f"= {current_stock + incoming_stock:.1f} units, which exceeds the required "
                f"stock of {required_stock:.1f} units "
                f"(demand during {lead_time:.0f}-day lead time={demand_during_lead_time:.1f} "
                f"+ safety stock={safety_stock:.1f})."
            )

        if avg_daily_demand == 0.0:
            return (
                f"'{product_name}': No recent demand data available. "
                f"Recommending {recommended_qty:.1f} units based on safety stock only."
            )

        return (
            f"'{product_name}' should be reordered. "
            f"Formula: demand_during_lead_time ({avg_daily_demand:.2f}/day x {lead_time:.0f} days "
            f"= {demand_during_lead_time:.1f}) + safety_stock ({safety_stock:.1f}) "
            f"= required_stock ({required_stock:.1f}). "
            f"Current stock ({current_stock:.1f}) + incoming ({incoming_stock:.1f}) "
            f"= {current_stock + incoming_stock:.1f}, which is short by {recommended_qty:.1f} units."
        )
