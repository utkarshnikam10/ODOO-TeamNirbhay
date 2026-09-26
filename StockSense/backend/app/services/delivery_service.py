"""
StockSense – Delivery Service
===============================
Business logic for validating outgoing goods deliveries.

Delivery validation flow
------------------------
1. Verify delivery exists.
2. Verify delivery status is 'draft'.
3. Validate each line item: positive quantity, product exists, location exists.
4. Check available stock >= requested quantity (REJECT if not).
5. Decrease stock for each line item.
6. Write a StockLedger entry for each line item.
7. Mark delivery as 'validated'.
8. Commit atomically.

KEY RULE: If ANY line item has insufficient stock, the ENTIRE delivery is
rejected. No partial deliveries are processed.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.delivery import Delivery
from app.services.stock_service import StockService
from app.services.ledger_service import LedgerService
from app.utils.exceptions import (
    DeliveryNotFoundError,
    InsufficientStockError,
    InvalidQuantityError,
)
from app.utils.validators import validate_is_draft, validate_positive_quantity


class DeliveryService:
    """Handles the full lifecycle of a Delivery transaction."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._stock = StockService(db)
        self._ledger = LedgerService(db)

    # ── Public API ─────────────────────────────────────────────────────────────

    def validate_delivery(
        self,
        delivery_id: int,
        validated_by_user_id: Optional[int] = None,
    ) -> Delivery:
        """Validate a delivery: check stock, decrease it, and write ledger.

        Args:
            delivery_id: PK of the Delivery to validate.
            validated_by_user_id: User performing the validation (for audit).

        Returns:
            The updated :class:`Delivery` object (status='validated').

        Raises:
            DeliveryNotFoundError: Delivery does not exist.
            DuplicateValidationError: Delivery is already validated.
            InvalidTransactionStateError: Delivery is cancelled.
            InvalidQuantityError: A line item has an invalid quantity.
            InsufficientStockError: Not enough stock for any line item.
            ProductNotFoundError: A line item references a non-existent product.
            LocationNotFoundError: Delivery references a non-existent location.
        """
        # ── Step 1: Fetch delivery ─────────────────────────────────────────────
        delivery = self._db.query(Delivery).filter(Delivery.id == delivery_id).first()
        if delivery is None:
            raise DeliveryNotFoundError(delivery_id)

        # ── Step 2: Validate state ─────────────────────────────────────────────
        validate_is_draft(delivery.status, "Delivery", delivery_id)

        # ── Step 3: Validate items exist ───────────────────────────────────────
        items = getattr(delivery, "delivery_items", None) or getattr(delivery, "items", None)
        if not items:
            raise InvalidQuantityError(
                f"Delivery id={delivery_id} has no line items. Cannot validate an empty delivery."
            )

        # ── Step 4: PRE-CHECK all stock before touching anything ───────────────
        for item in items:
            raw_qty = getattr(item, "quantity_ordered", None)
            if raw_qty is None:
                raw_qty = getattr(item, "quantity", None)
            if raw_qty is None:
                raw_qty = getattr(item, "quantity_demanded", Decimal("0"))

            qty = validate_positive_quantity(raw_qty, f"item id={item.id} quantity")
            available = self._stock.get_available_quantity(item.product_id, item.location_id)
            if available < qty:
                raise InsufficientStockError(
                    product_id=item.product_id,
                    location_id=item.location_id,
                    available=float(available),
                    requested=float(qty),
                )

        # ── Step 5 & 6: Decrease stock + ledger (all-or-nothing at this point) ─
        for item in items:
            raw_qty = getattr(item, "quantity_ordered", None)
            if raw_qty is None:
                raw_qty = getattr(item, "quantity", None)
            if raw_qty is None:
                raw_qty = getattr(item, "quantity_demanded", Decimal("0"))

            qty = validate_positive_quantity(raw_qty, f"item id={item.id} quantity")
            qty_before = self._stock.get_available_quantity(item.product_id, item.location_id)

            self._stock.decrease_stock(item.product_id, item.location_id, qty)

            if hasattr(item, "quantity_delivered"):
                item.quantity_delivered = qty

            self._ledger.record_delivery(
                product_id=item.product_id,
                location_id=item.location_id,
                quantity=qty,
                qty_before=qty_before,
                delivery_id=delivery_id,
                user_id=validated_by_user_id,
            )

        # ── Step 7: Mark validated ─────────────────────────────────────────────
        delivery.status = "validated"
        self._db.commit()
        self._db.refresh(delivery)
        return delivery

    def cancel_delivery(
        self,
        delivery_id: int,
        cancelled_by_user_id: Optional[int] = None,
    ) -> Delivery:
        """Cancel a draft delivery."""
        from app.utils.exceptions import InvalidTransactionStateError

        delivery = self._db.query(Delivery).filter(Delivery.id == delivery_id).first()
        if delivery is None:
            raise DeliveryNotFoundError(delivery_id)
        if delivery.status != "draft":
            raise InvalidTransactionStateError(
                f"Delivery id={delivery_id} cannot be cancelled (status='{delivery.status}'). "
                "Only draft deliveries can be cancelled."
            )
        delivery.status = "cancelled"
        self._db.commit()
        self._db.refresh(delivery)
        return delivery
