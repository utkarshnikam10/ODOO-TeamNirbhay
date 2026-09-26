from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    name: str = Field(..., max_length=255)
    sku: str = Field(..., max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    category_id: Optional[int] = None
    unit_of_measure: str = Field(default="units", max_length=50)
    cost_price: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)
    selling_price: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    sku: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    category_id: Optional[int] = None
    unit_of_measure: Optional[str] = Field(None, max_length=50)
    cost_price: Optional[Decimal] = Field(None, max_digits=12, decimal_places=2)
    selling_price: Optional[Decimal] = Field(None, max_digits=12, decimal_places=2)
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
