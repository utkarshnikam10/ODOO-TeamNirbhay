from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.location import Location
    from app.models.product import Product


class StockLedger(Base):
    """Immutable audit trail of all inventory quantity changes."""

    __tablename__ = "stock_ledger"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    operation_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # e.g., RECEIPT, DELIVERY, TRANSFER_IN, TRANSFER_OUT, ADJUSTMENT
    reference_id: Mapped[Optional[int]] = mapped_column(
        nullable=True, index=True
    )  # References id in receipts, deliveries, transfers, or adjustments
    reference_number: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )  # Human-readable reference number (e.g. REC-2026-001)
    quantity_change: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False
    )  # Positive for additions, negative for reductions
    balance_after: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False
    )  # Stock balance at the location after transaction
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    product: Mapped["Product"] = relationship("Product")
    location: Mapped["Location"] = relationship("Location")
