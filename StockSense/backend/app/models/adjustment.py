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


class Adjustment(Base):
    """Inventory count correction or damage/loss adjustment header."""

    __tablename__ = "adjustments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    adjustment_number: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    created_by: Mapped[Optional["User"]] = relationship("User")
    adjustment_items: Mapped[List["AdjustmentItem"]] = relationship(
        "AdjustmentItem", back_populates="adjustment", cascade="all, delete-orphan"
    )


class AdjustmentItem(Base):
    """Line item in a stock adjustment."""

    __tablename__ = "adjustment_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    adjustment_id: Mapped[int] = mapped_column(
        ForeignKey("adjustments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity_before: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), default=Decimal("0.000"), nullable=False
    )
    quantity_counted: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), default=Decimal("0.000"), nullable=False
    )
    difference: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), default=Decimal("0.000"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    adjustment: Mapped["Adjustment"] = relationship("Adjustment", back_populates="adjustment_items")
    product: Mapped["Product"] = relationship("Product")
    location: Mapped["Location"] = relationship("Location")
