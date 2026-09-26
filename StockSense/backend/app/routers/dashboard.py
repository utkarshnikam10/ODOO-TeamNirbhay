from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_, and_
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.product import Product
from app.models.stock import Stock
from app.models.receipt import Receipt
from app.models.delivery import Delivery
from app.models.transfer import Transfer
from app.models.stock_ledger import StockLedger
from app.models.reorder_rule import ReorderRule
from app.models.location import Location
from app.schemas.dashboard import DashboardSummaryResponse, StockSummaryResponse
from app.schemas.ledger import LedgerResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Total distinct products in stock (quantity > 0)
    total_products_in_stock = db.query(func.count(func.distinct(Stock.product_id))).filter(Stock.quantity > 0).scalar() or 0

    # Low stock items: quantity <= reorder min and quantity > 0
    low_stock_stmt = select(func.count(func.distinct(Stock.product_id))).select_from(Stock) \
        .join(Location, Stock.location_id == Location.id) \
        .join(ReorderRule, and_(ReorderRule.product_id == Stock.product_id, or_(ReorderRule.warehouse_id == Location.warehouse_id, ReorderRule.warehouse_id.is_(None)))) \
        .where(and_(Stock.quantity <= ReorderRule.min_quantity, Stock.quantity > 0))
    low_stock_items = db.execute(low_stock_stmt).scalar() or 0

    # Out of stock items: products that exist but have 0 stock across all locations, or just any stock record with 0?
    # Better definition: products that have a stock record with 0 quantity.
    out_of_stock_stmt = select(func.count(func.distinct(Stock.product_id))).select_from(Stock).where(Stock.quantity == 0)
    out_of_stock_items = db.execute(out_of_stock_stmt).scalar() or 0

    # Pending Receipts: Draft or Waiting
    pending_receipts = db.query(func.count(Receipt.id)).filter(Receipt.status.in_(["draft", "waiting"])).scalar() or 0

    # Pending Deliveries: Draft or Waiting
    pending_deliveries = db.query(func.count(Delivery.id)).filter(Delivery.status.in_(["draft", "waiting"])).scalar() or 0

    # Scheduled Transfers: Draft or Waiting
    scheduled_transfers = db.query(func.count(Transfer.id)).filter(Transfer.status.in_(["draft", "waiting"])).scalar() or 0

    return DashboardSummaryResponse(
        total_products_in_stock=total_products_in_stock,
        low_stock_items=low_stock_items,
        out_of_stock_items=out_of_stock_items,
        pending_receipts=pending_receipts,
        pending_deliveries=pending_deliveries,
        scheduled_transfers=scheduled_transfers
    )

@router.get("/stock-summary", response_model=StockSummaryResponse)
def get_stock_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Calculate total quantity and value
    # Value = stock.quantity * product.cost_price
    result = db.query(
        func.sum(Stock.quantity).label("total_quantity"),
        func.sum(Stock.quantity * Product.cost_price).label("total_value")
    ).join(Product, Stock.product_id == Product.id).first()

    total_quantity = result.total_quantity or 0
    total_value = result.total_value or 0

    return StockSummaryResponse(
        total_items_quantity=str(total_quantity),
        total_stock_value=str(total_value)
    )

@router.get("/recent-movements", response_model=List[LedgerResponse])
def get_recent_movements(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    movements = db.query(StockLedger).order_by(StockLedger.created_at.desc()).limit(limit).all()
    return movements
