from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.location import Location
    from app.models.product import Product
    from app.models.user import User
    from app.models.warehouse import Warehouse


class Transfer(Base):
    """Internal stock transfer between warehouses."""

    __tablename__ = "transfers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    transfer_number: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    source_warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    destination_warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    source_warehouse: Mapped["Warehouse"] = relationship(
        "Warehouse", foreign_keys=[source_warehouse_id]
    )
    destination_warehouse: Mapped["Warehouse"] = relationship(
        "Warehouse", foreign_keys=[destination_warehouse_id]
    )
    created_by: Mapped[Optional["User"]] = relationship("User")
    transfer_items: Mapped[List["TransferItem"]] = relationship(
        "TransferItem", back_populates="transfer", cascade="all, delete-orphan"
    )


class TransferItem(Base):
    """Line item in a stock transfer."""

    __tablename__ = "transfer_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    transfer_id: Mapped[int] = mapped_column(
        ForeignKey("transfers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    source_location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    destination_location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), default=Decimal("0.000"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    transfer: Mapped["Transfer"] = relationship("Transfer", back_populates="transfer_items")
    product: Mapped["Product"] = relationship("Product")
    source_location: Mapped["Location"] = relationship(
        "Location", foreign_keys=[source_location_id]
    )
    destination_location: Mapped["Location"] = relationship(
        "Location", foreign_keys=[destination_location_id]
    )
