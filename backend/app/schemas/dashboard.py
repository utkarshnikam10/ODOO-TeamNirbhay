from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from app.schemas.ledger import LedgerResponse

class DashboardSummaryResponse(BaseModel):
    total_products_in_stock: int
    low_stock_items: int
    out_of_stock_items: int
    pending_receipts: int
    pending_deliveries: int
    scheduled_transfers: int

    model_config = ConfigDict(from_attributes=True)

class StockSummaryResponse(BaseModel):
    total_stock_value: str
    total_items_quantity: str

    model_config = ConfigDict(from_attributes=True)
