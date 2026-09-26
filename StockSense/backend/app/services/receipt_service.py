"""
StockSense – Receipt Service
==============================
Business logic for validating incoming goods receipts.

Receipt validation flow
-----------------------
1. Verify receipt exists.
2. Verify receipt status is 'draft' (not already validated / cancelled).
3. Validate each line item: positive quantity, product exists, location exists.
4. Increase stock for each line item.
5. Write a StockLedger entry for each line item.
6. Mark receipt as 'validated'.
7. Commit atomically.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.receipt import Receipt
from app.services.stock_service import StockService
from app.services.ledger_service import LedgerService
from app.utils.exceptions import (
    ReceiptNotFoundError,
    InvalidQuantityError,
)
from app.utils.validators import validate_is_draft, validate_positive_quantity


class ReceiptService:
    """Handles the full lifecycle of a Receipt transaction."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._stock = StockService(db)
        self._ledger = LedgerService(db)

    # ── Public API ─────────────────────────────────────────────────────────────

    def validate_receipt(
        self,
        receipt_id: int,
        validated_by_user_id: Optional[int] = None,
    ) -> Receipt:
        """Validate a receipt: increase stock and write ledger entries.

        Args:
            receipt_id: PK of the Receipt to validate.
            validated_by_user_id: User performing the validation (for audit).

        Returns:
            The updated :class:`Receipt` object (status='validated' or 'done').

        Raises:
            ReceiptNotFoundError: Receipt does not exist.
            DuplicateValidationError: Receipt is already validated.
            InvalidTransactionStateError: Receipt is cancelled.
            InvalidQuantityError: A line item has an invalid quantity.
            ProductNotFoundError: A line item references a non-existent product.
            LocationNotFoundError: Receipt references a non-existent location.
        """
        # ── Step 1: Fetch receipt ──────────────────────────────────────────────
        receipt = self._db.query(Receipt).filter(Receipt.id == receipt_id).first()
        if receipt is None:
            raise ReceiptNotFoundError(receipt_id)

        # ── Step 2: Validate state ─────────────────────────────────────────────
        validate_is_draft(receipt.status, "Receipt", receipt_id)

        # ── Step 3-6: Process line items ───────────────────────────────────────
        items = getattr(receipt, "receipt_items", None) or getattr(receipt, "items", None)
        if not items:
            raise InvalidQuantityError(
                f"Receipt id={receipt_id} has no line items. Cannot validate an empty receipt."
            )

        for item in items:
            raw_qty = getattr(item, "quantity_expected", None)
            if raw_qty is None:
                raw_qty = getattr(item, "quantity", None)
            if raw_qty is None:
                raw_qty = getattr(item, "quantity_received", Decimal("0"))

            qty = validate_positive_quantity(raw_qty, f"item id={item.id} quantity")
            qty_before = self._stock.get_available_quantity(item.product_id, item.location_id)

            # Step 4 & 5: increase stock + validate entities
            self._stock.increase_stock(item.product_id, item.location_id, qty)

            # Update quantity_received if field exists on model
            if hasattr(item, "quantity_received"):
                item.quantity_received = qty

            # Step 6: write ledger
            self._ledger.record_receipt(
                product_id=item.product_id,
                location_id=item.location_id,
                quantity=qty,
                qty_before=qty_before,
                receipt_id=receipt_id,
                user_id=validated_by_user_id,
            )

        # ── Step 7: Mark validated ─────────────────────────────────────────────
        receipt.status = "validated"
        self._db.commit()
        self._db.refresh(receipt)
        return receipt

    def cancel_receipt(
        self,
        receipt_id: int,
        cancelled_by_user_id: Optional[int] = None,
    ) -> Receipt:
        """Cancel a draft receipt. Only draft receipts can be cancelled."""
        from app.utils.exceptions import InvalidTransactionStateError

        receipt = self._db.query(Receipt).filter(Receipt.id == receipt_id).first()
        if receipt is None:
            raise ReceiptNotFoundError(receipt_id)
        if receipt.status != "draft":
            raise InvalidTransactionStateError(
                f"Receipt id={receipt_id} cannot be cancelled (status='{receipt.status}'). "
                "Only draft receipts can be cancelled."
            )
        receipt.status = "cancelled"
        self._db.commit()
        self._db.refresh(receipt)
        return receipt
