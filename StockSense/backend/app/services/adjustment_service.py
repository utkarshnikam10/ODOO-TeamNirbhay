"""
StockSense – Adjustment Service
==================================
Business logic for physical inventory count adjustments.

Adjustment flow
---------------
1. Verify adjustment exists and is in 'draft' state.
2. For each item: validate physical_qty >= 0, product/location exist.
3. Compute difference = physical_qty - recorded_qty.
4. Set stock.quantity = physical_qty (regardless of sign).
5. Write a StockLedger entry for each adjusted item.
6. Mark adjustment as 'validated'.
7. Commit atomically.

Every adjustment is fully traceable: we record the old quantity, new
quantity, difference, reason, user, and timestamp in the ledger.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.adjustment import Adjustment, AdjustmentItem
from app.services.stock_service import StockService
from app.services.ledger_service import LedgerService
from app.utils.exceptions import (
    AdjustmentNotFoundError,
    InvalidQuantityError,
)
from app.utils.validators import validate_is_draft, validate_non_negative_quantity


class AdjustmentService:
    """Handles the full lifecycle of inventory count adjustments."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._stock = StockService(db)
        self._ledger = LedgerService(db)

    # ── Public API ─────────────────────────────────────────────────────────────

    def validate_adjustment(
        self,
        adjustment_id: int,
        validated_by_user_id: Optional[int] = None,
    ) -> Adjustment:
        """Validate a physical inventory adjustment.

        Examples:
            Recorded stock = 100, Physical count = 94  => difference = -6
            Recorded stock = 100, Physical count = 107 => difference = +7

        Args:
            adjustment_id: PK of the Adjustment to validate.
            validated_by_user_id: User performing the validation (for audit).

        Returns:
            Updated :class:`Adjustment` object (status='validated').

        Raises:
            AdjustmentNotFoundError: Adjustment does not exist.
            DuplicateValidationError: Already validated.
            InvalidQuantityError: A line item has an invalid physical_qty.
            ProductNotFoundError / LocationNotFoundError: Entity missing.
        """
        # ── Step 1: Fetch adjustment ───────────────────────────────────────────
        adjustment = self._db.query(Adjustment).filter(Adjustment.id == adjustment_id).first()
        if adjustment is None:
            raise AdjustmentNotFoundError(adjustment_id)

        # ── Step 2: Validate state ─────────────────────────────────────────────
        validate_is_draft(adjustment.status, "Adjustment", adjustment_id)

        items = getattr(adjustment, "adjustment_items", None) or getattr(adjustment, "items", None)
        if not items:
            raise InvalidQuantityError(
                f"Adjustment id={adjustment_id} has no line items."
            )

        # ── Step 3-5: Process each item ────────────────────────────────────────
        for item in items:
            raw_qty = getattr(item, "quantity_counted", None)
            if raw_qty is None:
                raw_qty = getattr(item, "physical_qty", None)
            if raw_qty is None:
                raw_qty = getattr(item, "counted_quantity", Decimal("0"))

            physical_qty = validate_non_negative_quantity(
                raw_qty, f"item id={item.id} physical_qty"
            )

            qty_before, qty_after, difference, _ = self._stock.apply_adjustment(
                product_id=item.product_id,
                location_id=item.location_id,
                physical_qty=physical_qty,
            )

            # Persist calculated fields back onto the item for traceability
            if hasattr(item, "quantity_before"):
                item.quantity_before = qty_before
            if hasattr(item, "quantity_after"):
                item.quantity_after = qty_after
            if hasattr(item, "difference"):
                item.difference = difference
            if hasattr(item, "quantity_counted"):
                item.quantity_counted = physical_qty
            if hasattr(item, "physical_qty"):
                item.physical_qty = physical_qty

            self._ledger.record_adjustment(
                product_id=item.product_id,
                location_id=item.location_id,
                difference=difference,
                qty_before=qty_before,
                qty_after=qty_after,
                adjustment_id=adjustment_id,
                reason=getattr(adjustment, "reason", "Physical inventory count"),
                user_id=validated_by_user_id,
            )

        # ── Step 6: Mark validated ─────────────────────────────────────────────
        adjustment.status = "validated"
        self._db.commit()
        self._db.refresh(adjustment)
        return adjustment

    def cancel_adjustment(
        self,
        adjustment_id: int,
        cancelled_by_user_id: Optional[int] = None,
    ) -> Adjustment:
        """Cancel a draft adjustment."""
        from app.utils.exceptions import InvalidTransactionStateError

        adjustment = self._db.query(Adjustment).filter(Adjustment.id == adjustment_id).first()
        if adjustment is None:
            raise AdjustmentNotFoundError(adjustment_id)
        if adjustment.status != "draft":
            raise InvalidTransactionStateError(
                f"Adjustment id={adjustment_id} cannot be cancelled (status='{adjustment.status}'). "
                "Only draft adjustments can be cancelled."
            )
        adjustment.status = "cancelled"
        self._db.commit()
        self._db.refresh(adjustment)
        return adjustment
