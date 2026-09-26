"""
StockSense – Transfer Service
================================
Business logic for internal stock transfers between locations/warehouses.

Transfer validation flow
------------------------
1. Verify transfer exists.
2. Verify transfer status is 'draft'.
3. Validate source != destination.
4. Validate items: positive quantity, product/location exist.
5. Check source has sufficient stock for every item.
6. Move stock (decrease source, increase destination) per item.
7. Write two ledger entries per item (TRANSFER_OUT + TRANSFER_IN).
8. Mark transfer as 'validated'.
9. Commit atomically.

INVARIANT: Total company stock for every product must be identical
before and after a transfer. Only the split between locations changes.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.transfer import Transfer
from app.services.stock_service import StockService
from app.services.ledger_service import LedgerService
from app.utils.exceptions import (
    TransferNotFoundError,
    InsufficientStockError,
    InvalidQuantityError,
    SameLocationTransferError,
)
from app.utils.validators import (
    validate_is_draft,
    validate_positive_quantity,
    validate_different_locations,
)


class TransferService:
    """Handles the full lifecycle of an internal Transfer."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._stock = StockService(db)
        self._ledger = LedgerService(db)

    # ── Public API ─────────────────────────────────────────────────────────────

    def validate_transfer(
        self,
        transfer_id: int,
        validated_by_user_id: Optional[int] = None,
    ) -> Transfer:
        """Validate an internal transfer.

        Args:
            transfer_id: PK of the Transfer to validate.
            validated_by_user_id: User performing the validation (for audit).

        Returns:
            Updated :class:`Transfer` object.

        Raises:
            TransferNotFoundError: Transfer does not exist.
            DuplicateValidationError: Transfer is already validated.
            SameLocationTransferError: Source and destination are the same.
            InsufficientStockError: Not enough stock at source.
            InvalidQuantityError: A line item has an invalid quantity.
        """
        # ── Step 1: Fetch transfer ─────────────────────────────────────────────
        transfer = self._db.query(Transfer).filter(Transfer.id == transfer_id).first()
        if transfer is None:
            raise TransferNotFoundError(transfer_id)

        # ── Step 2: Validate state ─────────────────────────────────────────────
        validate_is_draft(transfer.status, "Transfer", transfer_id)

        # ── Step 3: Validate items exist ───────────────────────────────────────
        items = getattr(transfer, "transfer_items", None) or getattr(transfer, "items", None)
        if not items:
            raise InvalidQuantityError(
                f"Transfer id={transfer_id} has no line items. Cannot validate an empty transfer."
            )

        # If header has locations/warehouses, validate them
        src_loc_header = getattr(transfer, "source_location_id", None)
        dst_loc_header = getattr(transfer, "dest_location_id", None) or getattr(transfer, "destination_location_id", None)
        if src_loc_header is not None and dst_loc_header is not None:
            validate_different_locations(src_loc_header, dst_loc_header)

        src_wh_header = getattr(transfer, "source_warehouse_id", None)
        dst_wh_header = getattr(transfer, "destination_warehouse_id", None)
        if src_wh_header is not None and dst_wh_header is not None and src_wh_header == dst_wh_header:
            # If same warehouse, ensure locations differ
            if src_loc_header is not None and dst_loc_header is not None:
                validate_different_locations(src_loc_header, dst_loc_header)

        # ── Step 4: Pre-check ALL items before mutating anything ───────────────
        for item in items:
            src_loc = getattr(item, "source_location_id", None) or src_loc_header
            dst_loc = getattr(item, "destination_location_id", None) or getattr(item, "dest_location_id", None) or dst_loc_header

            if src_loc is None or dst_loc is None:
                raise InvalidQuantityError(f"Transfer item id={item.id} missing source or destination location.")

            validate_different_locations(src_loc, dst_loc)

            qty = validate_positive_quantity(item.quantity, f"item id={item.id} quantity")
            available = self._stock.get_available_quantity(item.product_id, src_loc)
            if available < qty:
                raise InsufficientStockError(
                    product_id=item.product_id,
                    location_id=src_loc,
                    available=float(available),
                    requested=float(qty),
                )

        # ── Step 5 & 6: Execute moves + write paired ledger entries ─────────────
        for item in items:
            src_loc = getattr(item, "source_location_id", None) or src_loc_header
            dst_loc = getattr(item, "destination_location_id", None) or getattr(item, "dest_location_id", None) or dst_loc_header
            qty = validate_positive_quantity(item.quantity, f"item id={item.id} quantity")

            src_before = self._stock.get_available_quantity(item.product_id, src_loc)
            dst_before = self._stock.get_available_quantity(item.product_id, dst_loc)

            # Atomic move
            self._stock.move_stock(
                product_id=item.product_id,
                source_location_id=src_loc,
                dest_location_id=dst_loc,
                quantity=qty,
            )

            # Two ledger rows: one for OUT, one for IN
            self._ledger.record_transfer(
                product_id=item.product_id,
                source_location_id=src_loc,
                dest_location_id=dst_loc,
                quantity=qty,
                src_qty_before=src_before,
                dst_qty_before=dst_before,
                transfer_id=transfer_id,
                user_id=validated_by_user_id,
            )

        # ── Step 7: Mark validated ─────────────────────────────────────────────
        transfer.status = "validated"
        self._db.commit()
        self._db.refresh(transfer)
        return transfer

    def cancel_transfer(
        self,
        transfer_id: int,
        cancelled_by_user_id: Optional[int] = None,
    ) -> Transfer:
        """Cancel a draft transfer."""
        from app.utils.exceptions import InvalidTransactionStateError

        transfer = self._db.query(Transfer).filter(Transfer.id == transfer_id).first()
        if transfer is None:
            raise TransferNotFoundError(transfer_id)
        if transfer.status != "draft":
            raise InvalidTransactionStateError(
                f"Transfer id={transfer_id} cannot be cancelled (status='{transfer.status}'). "
                "Only draft transfers can be cancelled."
            )
        transfer.status = "cancelled"
        self._db.commit()
        self._db.refresh(transfer)
        return transfer
