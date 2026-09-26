from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field

class TransferStatus(str, Enum):
    DRAFT = "draft"
    WAITING = "waiting"
    READY = "ready"
    DONE = "done"
    CANCELED = "canceled"

class TransferItemBase(BaseModel):
    product_id: int
    source_location_id: int
    destination_location_id: int
    quantity: Decimal = Field(..., gt=0, max_digits=12, decimal_places=3)

class TransferItemCreate(TransferItemBase):
    pass

class TransferItemResponse(TransferItemBase):
    id: int
    transfer_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TransferBase(BaseModel):
    transfer_number: str = Field(..., max_length=100)
    source_warehouse_id: int
    destination_warehouse_id: int
    notes: Optional[str] = None
    status: TransferStatus = TransferStatus.DRAFT

class TransferCreate(TransferBase):
    items: List[TransferItemCreate] = Field(..., min_length=1)

class TransferResponse(TransferBase):
    id: int
    created_by_id: Optional[int]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    transfer_items: List[TransferItemResponse]

    model_config = ConfigDict(from_attributes=True)
