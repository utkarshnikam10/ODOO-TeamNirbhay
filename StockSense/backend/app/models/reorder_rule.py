from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.warehouse import Warehouse


class ReorderRule(Base):
    """Automated or threshold-based replenishment rules."""

    __tablename__ = "reorder_rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    warehouse_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=True, index=True
    )
    min_quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), default=Decimal("0.000"), nullable=False
    )
    max_quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), default=Decimal("0.000"), nullable=False
    )
    reorder_quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), default=Decimal("0.000"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="reorder_rules")
    warehouse: Mapped[Optional["Warehouse"]] = relationship("Warehouse", back_populates="reorder_rules")
