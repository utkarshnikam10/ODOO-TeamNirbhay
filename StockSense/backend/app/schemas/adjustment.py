from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field

class AdjustmentStatus(str, Enum):
    DRAFT = "draft"
    WAITING = "waiting"
    READY = "ready"
    DONE = "done"
    CANCELED = "canceled"

class AdjustmentItemBase(BaseModel):
    product_id: int
    location_id: int
    quantity_counted: Decimal = Field(..., ge=0, max_digits=12, decimal_places=3)

class AdjustmentItemCreate(AdjustmentItemBase):
    pass

class AdjustmentItemResponse(AdjustmentItemBase):
    id: int
    adjustment_id: int
    quantity_before: Decimal
    difference: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AdjustmentBase(BaseModel):
    adjustment_number: str = Field(..., max_length=100)
    reason: str = Field(..., max_length=255)
    notes: Optional[str] = None
    status: AdjustmentStatus = AdjustmentStatus.DRAFT

class AdjustmentCreate(AdjustmentBase):
    items: List[AdjustmentItemCreate] = Field(..., min_length=1)

class AdjustmentResponse(AdjustmentBase):
    id: int
    created_by_id: Optional[int]
    applied_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    adjustment_items: List[AdjustmentItemResponse]

    model_config = ConfigDict(from_attributes=True)
