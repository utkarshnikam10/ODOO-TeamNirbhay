from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field

class ReceiptStatus(str, Enum):
    DRAFT = "draft"
    WAITING = "waiting"
    READY = "ready"
    DONE = "done"
    CANCELED = "canceled"

class ReceiptItemBase(BaseModel):
    product_id: int
    location_id: int
    quantity_expected: Decimal = Field(..., gt=0, max_digits=12, decimal_places=3)
    unit_cost: Optional[Decimal] = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)

class ReceiptItemCreate(ReceiptItemBase):
    pass

class ReceiptItemResponse(ReceiptItemBase):
    id: int
    receipt_id: int
    quantity_received: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ReceiptBase(BaseModel):
    receipt_number: str = Field(..., max_length=100)
    supplier_name: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    status: ReceiptStatus = ReceiptStatus.DRAFT

class ReceiptCreate(ReceiptBase):
    items: List[ReceiptItemCreate] = Field(..., min_length=1)

class ReceiptResponse(ReceiptBase):
    id: int
    created_by_id: Optional[int]
    received_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    receipt_items: List[ReceiptItemResponse]

    model_config = ConfigDict(from_attributes=True)
