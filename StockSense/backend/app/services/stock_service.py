"""
StockSense – Stock Service
===========================
Core stock calculation engine.

Responsibilities:
- Read current stock (quantity on-hand per product + location)
- Increase stock (after receipt or transfer-in)
- Decrease stock (after delivery or transfer-out)
- Move stock between locations atomically
- Prevent negative stock
- Upsert Stock rows (insert on first touch, update thereafter)

Architecture note
-----------------
This service is NOT aware of receipts, deliveries, or transfers.
It only knows about Stock rows and StockLedger rows.
The higher-level services (ReceiptService, DeliveryService, etc.)
call this service for the actual stock mutation.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.stock import Stock
from app.models.product import Product
from app.models.location import Location
from app.utils.exceptions import (
    InsufficientStockError,
    ProductNotFoundError,
    LocationNotFoundError,
)
from app.utils.validators import validate_positive_quantity


class StockService:
    """Encapsulates all stock quantity operations."""

    def __init__(self, db: Session) -> None:
        self._db = db

    # ── Lookups ────────────────────────────────────────────────────────────────

    def get_stock(self, product_id: int, location_id: int) -> Optional[Stock]:
        """Return the Stock row for *product_id* at *location_id*, or None."""
        return (
            self._db.query(Stock)
            .filter(Stock.product_id == product_id, Stock.location_id == location_id)
            .first()
        )

    def get_available_quantity(self, product_id: int, location_id: int) -> Decimal:
        """Return how many units are on-hand.  Returns Decimal('0') if no row exists."""
        stock = self.get_stock(product_id, location_id)
        if stock is None:
            return Decimal("0")
        return Decimal(str(stock.quantity))

    def get_total_stock_for_product(self, product_id: int) -> Decimal:
        """Sum stock across all locations for a single product.

        Useful for: transfer validation (total company stock should not change).
        """
        rows = self._db.query(Stock).filter(Stock.product_id == product_id).all()
        return sum((Decimal(str(r.quantity)) for r in rows), Decimal("0"))

    # ── Write helpers ──────────────────────────────────────────────────────────

    def _validate_entities_exist(self, product_id: int, location_id: int) -> None:
        """Raise typed errors if the product or location do not exist."""
        if not self._db.query(Product).filter(Product.id == product_id).first():
            raise ProductNotFoundError(product_id)
        if not self._db.query(Location).filter(Location.id == location_id).first():
            raise LocationNotFoundError(location_id)

    def _get_or_create_stock(self, product_id: int, location_id: int) -> Stock:
        """Return existing Stock row or create a new one with quantity=0."""
        stock = self.get_stock(product_id, location_id)
        if stock is None:
            stock = Stock(
                product_id=product_id,
                location_id=location_id,
                quantity=Decimal("0"),
            )
            self._db.add(stock)
            self._db.flush()  # get an id without committing
        return stock

    # ── Public mutation API ────────────────────────────────────────────────────

    def increase_stock(
        self,
        product_id: int,
        location_id: int,
        quantity: Decimal,
    ) -> Stock:
        """Add *quantity* units to the stock at *location_id*.

        Args:
            product_id: Product being received.
            location_id: Location receiving the stock.
            quantity: Positive quantity to add.

        Returns:
            Updated :class:`Stock` row (not yet committed).

        Raises:
            InvalidQuantityError: quantity <= 0.
            ProductNotFoundError: product does not exist.
            LocationNotFoundError: location does not exist.
        """
        quantity = validate_positive_quantity(quantity, "quantity")
        self._validate_entities_exist(product_id, location_id)
        stock = self._get_or_create_stock(product_id, location_id)

        before = Decimal(str(stock.quantity))
        stock.quantity = before + quantity
        self._db.flush()
        return stock

    def decrease_stock(
        self,
        product_id: int,
        location_id: int,
        quantity: Decimal,
    ) -> Stock:
        """Remove *quantity* units from stock at *location_id*.

        Args:
            product_id: Product being consumed.
            location_id: Location supplying the stock.
            quantity: Positive quantity to remove.

        Returns:
            Updated :class:`Stock` row (not yet committed).

        Raises:
            InvalidQuantityError: quantity <= 0.
            InsufficientStockError: not enough stock available.
            ProductNotFoundError / LocationNotFoundError: entity missing.
        """
        quantity = validate_positive_quantity(quantity, "quantity")
        self._validate_entities_exist(product_id, location_id)

        available = self.get_available_quantity(product_id, location_id)
        if available < quantity:
            raise InsufficientStockError(
                product_id=product_id,
                location_id=location_id,
                available=float(available),
                requested=float(quantity),
            )

        stock = self._get_or_create_stock(product_id, location_id)
        stock.quantity = Decimal(str(stock.quantity)) - quantity
        self._db.flush()
        return stock

    def move_stock(
        self,
        product_id: int,
        source_location_id: int,
        dest_location_id: int,
        quantity: Decimal,
    ) -> tuple[Stock, Stock]:
        """Move *quantity* from source to destination atomically (within the same DB session).

        This is used by TransferService.  Both the decrease and increase happen
        in the same flush so there is no window where total company stock changes.

        Returns:
            (source_stock, dest_stock) both updated but not yet committed.
        """
        src_stock = self.decrease_stock(product_id, source_location_id, quantity)
        dst_stock = self.increase_stock(product_id, dest_location_id, quantity)
        return src_stock, dst_stock

    def apply_adjustment(
        self,
        product_id: int,
        location_id: int,
        physical_qty: Decimal,
    ) -> tuple[Decimal, Decimal, Decimal, Stock]:
        """Reconcile recorded stock to a physical count.

        Args:
            product_id: The product being counted.
            location_id: The location being adjusted.
            physical_qty: Actual physical quantity observed.

        Returns:
            (qty_before, physical_qty, difference, updated_stock)
            difference = physical_qty - qty_before  (positive = gain, negative = loss)

        Raises:
            InvalidQuantityError: physical_qty < 0.
        """
        from app.utils.validators import validate_non_negative_quantity
        physical_qty = validate_non_negative_quantity(physical_qty, "physical_qty")
        self._validate_entities_exist(product_id, location_id)

        stock = self._get_or_create_stock(product_id, location_id)
        qty_before = Decimal(str(stock.quantity))
        difference = physical_qty - qty_before
        stock.quantity = physical_qty
        self._db.flush()
        return qty_before, physical_qty, difference, stock
