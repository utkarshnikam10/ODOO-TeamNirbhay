from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict

class StockAlertResponse(BaseModel):
    product_id: int
    product_name: str
    location_id: int
    location_name: str
    warehouse_id: int
    quantity: Decimal
    reorder_level: Optional[Decimal] = None
    status: str  # 'LOW_STOCK' or 'OUT_OF_STOCK'

    model_config = ConfigDict(from_attributes=True)

class StockResponse(BaseModel):
    id: int
    product_id: int
    location_id: int
    quantity: Decimal
    reserved_quantity: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
