from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class ReorderRuleBase(BaseModel):
    product_id: int
    warehouse_id: Optional[int] = None
    min_quantity: Decimal = Field(..., ge=0, max_digits=12, decimal_places=3)
    max_quantity: Decimal = Field(..., ge=0, max_digits=12, decimal_places=3)
    reorder_quantity: Decimal = Field(..., ge=0, max_digits=12, decimal_places=3)

class ReorderRuleCreate(ReorderRuleBase):
    pass

class ReorderRuleUpdate(BaseModel):
    min_quantity: Optional[Decimal] = Field(None, ge=0, max_digits=12, decimal_places=3)
    max_quantity: Optional[Decimal] = Field(None, ge=0, max_digits=12, decimal_places=3)
    reorder_quantity: Optional[Decimal] = Field(None, ge=0, max_digits=12, decimal_places=3)

class ReorderRuleResponse(ReorderRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
