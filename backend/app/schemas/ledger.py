from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict

class LedgerResponse(BaseModel):
    id: int
    product_id: int
    location_id: int
    operation_type: str
    reference_id: Optional[int]
    reference_number: Optional[str]
    quantity_change: Decimal
    balance_after: Decimal
    notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
