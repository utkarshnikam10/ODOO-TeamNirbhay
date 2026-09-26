from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from typing import Optional
from datetime import datetime
import math

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.stock_ledger import StockLedger
from app.models.location import Location
from app.schemas.ledger import LedgerResponse
from app.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/ledger", tags=["Ledger"])

@router.get("", response_model=PaginatedResponse[LedgerResponse])
def get_ledger(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    product_id: Optional[int] = None,
    warehouse_id: Optional[int] = None,
    location_id: Optional[int] = None,
    operation_type: Optional[str] = None,
    reference_type: Optional[str] = None, # same as operation_type practically in this model, but keeping if asked
    reference_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(StockLedger)

    if product_id:
        query = query.filter(StockLedger.product_id == product_id)
    if location_id:
        query = query.filter(StockLedger.location_id == location_id)
    if warehouse_id:
        query = query.join(Location, StockLedger.location_id == Location.id).filter(Location.warehouse_id == warehouse_id)
    if operation_type:
        query = query.filter(StockLedger.operation_type == operation_type)
    if reference_type:
        query = query.filter(StockLedger.operation_type == reference_type) # Assuming operation type maps to reference type
    if reference_id:
        query = query.filter(StockLedger.reference_id == reference_id)
    if start_date:
        query = query.filter(StockLedger.created_at >= start_date)
    if end_date:
        query = query.filter(StockLedger.created_at <= end_date)

    total = query.count()
    skip = (page - 1) * size
    items = query.order_by(StockLedger.created_at.desc()).offset(skip).limit(size).all()
    pages = math.ceil(total / size) if total > 0 else 0

    return PaginatedResponse(items=items, total=total, page=page, size=size, pages=pages)

@router.get("/{id}", response_model=LedgerResponse)
def get_ledger_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ledger = db.query(StockLedger).filter(StockLedger.id == id).first()
    if not ledger:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ledger record not found")
    return ledger
