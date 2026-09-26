from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field

class DeliveryStatus(str, Enum):
    DRAFT = "draft"
    WAITING = "waiting"
    READY = "ready"
    DONE = "done"
    CANCELED = "canceled"

class DeliveryItemBase(BaseModel):
    product_id: int
    location_id: int
    quantity_ordered: Decimal = Field(..., gt=0, max_digits=12, decimal_places=3)
    unit_price: Optional[Decimal] = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)

class DeliveryItemCreate(DeliveryItemBase):
    pass

class DeliveryItemResponse(DeliveryItemBase):
    id: int
    delivery_id: int
    quantity_delivered: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DeliveryBase(BaseModel):
    delivery_number: str = Field(..., max_length=100)
    customer_name: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    status: DeliveryStatus = DeliveryStatus.DRAFT

class DeliveryCreate(DeliveryBase):
    items: List[DeliveryItemCreate] = Field(..., min_length=1)

class DeliveryResponse(DeliveryBase):
    id: int
    created_by_id: Optional[int]
    shipped_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    delivery_items: List[DeliveryItemResponse]

    model_config = ConfigDict(from_attributes=True)
