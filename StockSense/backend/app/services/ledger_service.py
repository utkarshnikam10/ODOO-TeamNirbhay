"""
StockSense – Stock Ledger Service
===================================
Every stock-changing operation creates an immutable ledger entry here.

The ledger is APPEND-ONLY. We never update or delete ledger rows.
It is the canonical audit trail of every quantity change in the system.

Transaction / Operation types:
  RECEIPT       – incoming goods from a supplier
  DELIVERY      – outgoing goods to a customer
  TRANSFER_OUT  – stock leaving a source location (internal move)
  TRANSFER_IN   – stock arriving at a destination location (internal move)
  ADJUSTMENT    – physical count correction
  OPENING_STOCK – initial stock loaded into the system
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.stock_ledger import StockLedger
from app.utils.exceptions import ProductNotFoundError, LocationNotFoundError
from app.models.product import Product
from app.models.location import Location


# ── Valid transaction type strings ─────────────────────────────────────────────
TRANSACTION_TYPE_RECEIPT: str = "RECEIPT"
TRANSACTION_TYPE_DELIVERY: str = "DELIVERY"
TRANSACTION_TYPE_TRANSFER_OUT: str = "TRANSFER_OUT"
TRANSACTION_TYPE_TRANSFER_IN: str = "TRANSFER_IN"
TRANSACTION_TYPE_ADJUSTMENT: str = "ADJUSTMENT"
TRANSACTION_TYPE_OPENING_STOCK: str = "OPENING_STOCK"


class LedgerService:
    """Creates and queries stock ledger entries."""

    def __init__(self, db: Session) -> None:
        self._db = db

    # ── Write ──────────────────────────────────────────────────────────────────

    def create_entry(
        self,
        product_id: int,
        location_id: int,
        transaction_type: str,
        quantity_change: Decimal,
        quantity_before: Decimal,
        quantity_after: Decimal,
        reference_id: Optional[int] = None,
        reference_type: Optional[str] = None,
        performed_by_user_id: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> StockLedger:
        """Append one immutable ledger row.

        Args:
            product_id:            FK to products.id
            location_id:           FK to locations.id
            transaction_type:      One of the TRANSACTION_TYPE_* constants above.
            quantity_change:       How much stock changed (negative for decreases).
            quantity_before:       Stock level BEFORE this change.
            quantity_after:        Stock level AFTER this change.
            reference_id:          PK of the source transaction (receipt/delivery/etc.).
            reference_type:        Human-readable type of the source ('Receipt', etc.).
            performed_by_user_id:  FK to users.id (optional, None for system actions).
            notes:                 Free-text reason or reference number.

        Returns:
            The newly created :class:`StockLedger` row (flushed, not committed).
        """
        # Determine attributes supported by StockLedger dynamically
        # to ensure 100% compatibility with Nayan's model and any custom models
        ledger_kwargs = {
            "product_id": product_id,
            "location_id": location_id,
            "quantity_change": quantity_change,
            "notes": notes,
        }

        if hasattr(StockLedger, "operation_type"):
            ledger_kwargs["operation_type"] = transaction_type
        if hasattr(StockLedger, "transaction_type"):
            ledger_kwargs["transaction_type"] = transaction_type

        if hasattr(StockLedger, "balance_after"):
            ledger_kwargs["balance_after"] = quantity_after
        if hasattr(StockLedger, "quantity_after"):
            ledger_kwargs["quantity_after"] = quantity_after
        if hasattr(StockLedger, "quantity_before"):
            ledger_kwargs["quantity_before"] = quantity_before

        if hasattr(StockLedger, "reference_id"):
            ledger_kwargs["reference_id"] = reference_id
        if hasattr(StockLedger, "reference_number"):
            ledger_kwargs["reference_number"] = notes or reference_type
        if hasattr(StockLedger, "reference_type"):
            ledger_kwargs["reference_type"] = reference_type
        if hasattr(StockLedger, "performed_by_user_id"):
            ledger_kwargs["performed_by_user_id"] = performed_by_user_id

        entry = StockLedger(**ledger_kwargs)
        self._db.add(entry)
        self._db.flush()
        return entry

    # ── Convenience wrappers ───────────────────────────────────────────────────

    def record_receipt(
        self,
        product_id: int,
        location_id: int,
        quantity: Decimal,
        qty_before: Decimal,
        receipt_id: int,
        user_id: Optional[int] = None,
    ) -> StockLedger:
        """Ledger entry for incoming receipt: positive quantity change."""
        return self.create_entry(
            product_id=product_id,
            location_id=location_id,
            transaction_type=TRANSACTION_TYPE_RECEIPT,
            quantity_change=quantity,
            quantity_before=qty_before,
            quantity_after=qty_before + quantity,
            reference_id=receipt_id,
            reference_type="Receipt",
            performed_by_user_id=user_id,
            notes=f"Receipt id={receipt_id}",
        )

    def record_delivery(
        self,
        product_id: int,
        location_id: int,
        quantity: Decimal,
        qty_before: Decimal,
        delivery_id: int,
        user_id: Optional[int] = None,
    ) -> StockLedger:
        """Ledger entry for outgoing delivery: negative quantity change."""
        return self.create_entry(
            product_id=product_id,
            location_id=location_id,
            transaction_type=TRANSACTION_TYPE_DELIVERY,
            quantity_change=-quantity,
            quantity_before=qty_before,
            quantity_after=qty_before - quantity,
            reference_id=delivery_id,
            reference_type="Delivery",
            performed_by_user_id=user_id,
            notes=f"Delivery id={delivery_id}",
        )

    def record_transfer(
        self,
        product_id: int,
        source_location_id: int,
        dest_location_id: int,
        quantity: Decimal,
        src_qty_before: Decimal,
        dst_qty_before: Decimal,
        transfer_id: int,
        user_id: Optional[int] = None,
    ) -> tuple[StockLedger, StockLedger]:
        """Record paired ledger rows for a transfer: out from src, in to dst."""
        out_entry = self.create_entry(
            product_id=product_id,
            location_id=source_location_id,
            transaction_type=TRANSACTION_TYPE_TRANSFER_OUT,
            quantity_change=-quantity,
            quantity_before=src_qty_before,
            quantity_after=src_qty_before - quantity,
            reference_id=transfer_id,
            reference_type="Transfer",
            performed_by_user_id=user_id,
            notes=f"Transfer id={transfer_id} to location id={dest_location_id}",
        )
        in_entry = self.create_entry(
            product_id=product_id,
            location_id=dest_location_id,
            transaction_type=TRANSACTION_TYPE_TRANSFER_IN,
            quantity_change=quantity,
            quantity_before=dst_qty_before,
            quantity_after=dst_qty_before + quantity,
            reference_id=transfer_id,
            reference_type="Transfer",
            performed_by_user_id=user_id,
            notes=f"Transfer id={transfer_id} from location id={source_location_id}",
        )
        return out_entry, in_entry

    def record_adjustment(
        self,
        product_id: int,
        location_id: int,
        difference: Decimal,
        qty_before: Decimal,
        qty_after: Decimal,
        adjustment_id: int,
        reason: str,
        user_id: Optional[int] = None,
    ) -> StockLedger:
        """Ledger entry for physical count adjustment."""
        return self.create_entry(
            product_id=product_id,
            location_id=location_id,
            transaction_type=TRANSACTION_TYPE_ADJUSTMENT,
            quantity_change=difference,
            quantity_before=qty_before,
            quantity_after=qty_after,
            reference_id=adjustment_id,
            reference_type="Adjustment",
            performed_by_user_id=user_id,
            notes=f"Adjustment id={adjustment_id}: {reason}",
        )

    # ── Read / Audit ───────────────────────────────────────────────────────────

    def get_product_ledger(
        self,
        product_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[StockLedger]:
        """Return audit history for a product in reverse chronological order."""
        return (
            self._db.query(StockLedger)
            .filter(StockLedger.product_id == product_id)
            .order_by(StockLedger.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_location_ledger(
        self,
        location_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[StockLedger]:
        """Return audit history for a location in reverse chronological order."""
        return (
            self._db.query(StockLedger)
            .filter(StockLedger.location_id == location_id)
            .order_by(StockLedger.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
