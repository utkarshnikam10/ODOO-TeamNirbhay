"""
StockSense – Input Validators
===============================
All validation logic for quantities, IDs, and transaction states.
Validators raise typed exceptions from utils.exceptions — never raw assertions.
This keeps routers thin; all business rules live here or in the service layer.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from app.utils.exceptions import (
    InvalidQuantityError,
    InvalidTransactionStateError,
    SameLocationTransferError,
)

if TYPE_CHECKING:
    pass

# ── Threshold constants ────────────────────────────────────────────────────────
# Keep all "magic numbers" centralised here so they can be changed in one place.

#: Maximum single-transaction quantity (sanity cap; adjust per business need)
MAX_SINGLE_QUANTITY: Decimal = Decimal("999_999")

#: Valid transaction states per model type
VALID_RECEIPT_STATES: frozenset[str] = frozenset({"draft", "validated", "cancelled"})
VALID_DELIVERY_STATES: frozenset[str] = frozenset({"draft", "validated", "cancelled"})
VALID_TRANSFER_STATES: frozenset[str] = frozenset({"draft", "validated", "cancelled"})
VALID_ADJUSTMENT_STATES: frozenset[str] = frozenset({"draft", "validated", "cancelled"})


# ── Quantity validators ────────────────────────────────────────────────────────

def validate_positive_quantity(quantity: Decimal | float | int, field_name: str = "quantity") -> Decimal:
    """Ensure *quantity* is a positive (> 0) Decimal.

    Args:
        quantity: The value to validate.
        field_name: Human-readable field name for the error message.

    Returns:
        The quantity as a :class:`Decimal`.

    Raises:
        InvalidQuantityError: If the quantity is <= 0 or exceeds MAX_SINGLE_QUANTITY.
    """
    qty = Decimal(str(quantity))
    if qty <= Decimal("0"):
        raise InvalidQuantityError(
            f"{field_name} must be greater than zero. Got: {qty}"
        )
    if qty > MAX_SINGLE_QUANTITY:
        raise InvalidQuantityError(
            f"{field_name} exceeds the maximum allowed value of {MAX_SINGLE_QUANTITY}. Got: {qty}"
        )
    return qty


def validate_non_negative_quantity(quantity: Decimal | float | int, field_name: str = "quantity") -> Decimal:
    """Ensure *quantity* is >= 0 (allows zero for adjustment differences)."""
    qty = Decimal(str(quantity))
    if qty < Decimal("0"):
        raise InvalidQuantityError(
            f"{field_name} cannot be negative. Got: {qty}"
        )
    return qty


# ── Transaction state validators ───────────────────────────────────────────────

def validate_is_draft(status: str, transaction_type: str, transaction_id: int) -> None:
    """Ensure a transaction is still in 'draft' state before allowing mutation.

    Args:
        status: Current status string of the transaction.
        transaction_type: Human-readable label ('Receipt', 'Delivery', etc.).
        transaction_id: The primary key, for the error message.

    Raises:
        InvalidTransactionStateError: If status is not 'draft'.
        DuplicateValidationError: If status is already 'validated'.
    """
    from app.utils.exceptions import DuplicateValidationError  # local import avoids circular

    if status == "validated":
        raise DuplicateValidationError(
            f"{transaction_type} id={transaction_id} is already validated. "
            "Duplicate validation is not allowed."
        )
    if status == "cancelled":
        raise InvalidTransactionStateError(
            f"{transaction_type} id={transaction_id} is cancelled and cannot be validated."
        )
    if status != "draft":
        raise InvalidTransactionStateError(
            f"{transaction_type} id={transaction_id} has unexpected status '{status}'. "
            "Only 'draft' transactions can be validated."
        )


# ── Location / transfer validators ────────────────────────────────────────────

def validate_different_locations(source_location_id: int, dest_location_id: int) -> None:
    """Ensure source and destination locations differ for a transfer.

    Raises:
        SameLocationTransferError: If both IDs are identical.
    """
    if source_location_id == dest_location_id:
        raise SameLocationTransferError(
            f"Transfer source and destination location cannot be the same "
            f"(location_id={source_location_id})."
        )


def validate_different_warehouses(source_warehouse_id: int, dest_warehouse_id: int) -> None:
    """Ensure source and destination warehouses differ for a transfer."""
    if source_warehouse_id == dest_warehouse_id:
        raise SameLocationTransferError(
            f"Transfer source and destination warehouse cannot be the same "
            f"(warehouse_id={source_warehouse_id})."
        )
