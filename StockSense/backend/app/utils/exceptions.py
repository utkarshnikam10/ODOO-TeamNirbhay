"""
StockSense – Custom Exception Hierarchy
========================================
All exceptions raised by the service / intelligence layer.
API routers catch these and translate them into appropriate HTTP responses.
Never let raw SQLAlchemy or database exceptions reach the frontend.
"""


class StockSenseError(Exception):
    """Base class for all StockSense domain errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return self.message


# ── Validation errors ──────────────────────────────────────────────────────────

class InvalidQuantityError(StockSenseError):
    """Raised when a quantity is zero, negative, or otherwise invalid."""


class InvalidTransactionStateError(StockSenseError):
    """Raised when trying to act on a transaction that is in the wrong state."""


class DuplicateValidationError(StockSenseError):
    """Raised when an attempt is made to validate an already-validated transaction."""


class InvalidDateError(StockSenseError):
    """Raised when a provided date is logically impossible."""


class SameLocationTransferError(StockSenseError):
    """Raised when a transfer source and destination location are identical."""


# ── Not-found errors ───────────────────────────────────────────────────────────

class ProductNotFoundError(StockSenseError):
    """Raised when a referenced product does not exist in the database."""
    def __init__(self, product_id: int) -> None:
        super().__init__(f"Product with id={product_id} not found.")
        self.product_id = product_id


class WarehouseNotFoundError(StockSenseError):
    """Raised when a referenced warehouse does not exist."""
    def __init__(self, warehouse_id: int) -> None:
        super().__init__(f"Warehouse with id={warehouse_id} not found.")
        self.warehouse_id = warehouse_id


class LocationNotFoundError(StockSenseError):
    """Raised when a referenced storage location does not exist."""
    def __init__(self, location_id: int) -> None:
        super().__init__(f"Location with id={location_id} not found.")
        self.location_id = location_id


class ReceiptNotFoundError(StockSenseError):
    """Raised when a receipt record cannot be found."""
    def __init__(self, receipt_id: int) -> None:
        super().__init__(f"Receipt with id={receipt_id} not found.")
        self.receipt_id = receipt_id


class DeliveryNotFoundError(StockSenseError):
    """Raised when a delivery record cannot be found."""
    def __init__(self, delivery_id: int) -> None:
        super().__init__(f"Delivery with id={delivery_id} not found.")
        self.delivery_id = delivery_id


class TransferNotFoundError(StockSenseError):
    """Raised when an internal transfer record cannot be found."""
    def __init__(self, transfer_id: int) -> None:
        super().__init__(f"Transfer with id={transfer_id} not found.")
        self.transfer_id = transfer_id


class AdjustmentNotFoundError(StockSenseError):
    """Raised when an adjustment record cannot be found."""
    def __init__(self, adjustment_id: int) -> None:
        super().__init__(f"Adjustment with id={adjustment_id} not found.")
        self.adjustment_id = adjustment_id


class ReorderRuleNotFoundError(StockSenseError):
    """Raised when no reorder rule exists for a product/warehouse pair."""


# ── Stock / inventory errors ───────────────────────────────────────────────────

class InsufficientStockError(StockSenseError):
    """Raised when a delivery or transfer requests more stock than is
    currently available at the source location.

    Example:
        Available = 20, Requested = 25  =>  InsufficientStockError
    """
    def __init__(self, product_id: int, location_id: int,
                 available: float, requested: float) -> None:
        super().__init__(
            f"Insufficient stock for product_id={product_id} at "
            f"location_id={location_id}. "
            f"Available={available}, Requested={requested}."
        )
        self.product_id = product_id
        self.location_id = location_id
        self.available = available
        self.requested = requested


class NegativeStockError(StockSenseError):
    """Raised when a stock operation would result in a negative quantity."""
