from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, case, func
from decimal import Decimal
from typing import List
import math

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.stock import Stock
from app.models.product import Product
from app.models.location import Location
from app.models.reorder_rule import ReorderRule
from app.schemas.stock import StockAlertResponse, StockResponse
from app.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/stock", tags=["Stock Alerts"])

@router.get("/low-stock", response_model=List[StockAlertResponse])
def get_low_stock(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Calculate low stock: stock.quantity <= reorder_rule.min_quantity AND stock.quantity > 0
    # Match reorder rules by product and either specific warehouse or global (warehouse_id is null)
    stmt = (
        select(
            Stock.product_id,
            Product.name.label("product_name"),
            Stock.location_id,
            Location.name.label("location_name"),
            Location.warehouse_id,
            Stock.quantity,
            ReorderRule.min_quantity.label("reorder_level")
        )
        .join(Product, Stock.product_id == Product.id)
        .join(Location, Stock.location_id == Location.id)
        .join(
            ReorderRule,
            and_(
                ReorderRule.product_id == Stock.product_id,
                or_(
                    ReorderRule.warehouse_id == Location.warehouse_id,
                    ReorderRule.warehouse_id.is_(None)
                )
            )
        )
        .where(
            and_(
                Stock.quantity <= ReorderRule.min_quantity,
                Stock.quantity > 0
            )
        )
    )
    
    results = db.execute(stmt).all()
    
    return [
        StockAlertResponse(
            product_id=row.product_id,
            product_name=row.product_name,
            location_id=row.location_id,
            location_name=row.location_name,
            warehouse_id=row.warehouse_id,
            quantity=row.quantity,
            reorder_level=row.reorder_level,
            status="LOW_STOCK"
        )
        for row in results
    ]

@router.get("/out-of-stock", response_model=List[StockAlertResponse])
def get_out_of_stock(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Calculate out of stock: stock.quantity == 0
    # Also fetch reorder level if rule exists
    stmt = (
        select(
            Stock.product_id,
            Product.name.label("product_name"),
            Stock.location_id,
            Location.name.label("location_name"),
            Location.warehouse_id,
            Stock.quantity,
            ReorderRule.min_quantity.label("reorder_level")
        )
        .join(Product, Stock.product_id == Product.id)
        .join(Location, Stock.location_id == Location.id)
        .outerjoin(
            ReorderRule,
            and_(
                ReorderRule.product_id == Stock.product_id,
                or_(
                    ReorderRule.warehouse_id == Location.warehouse_id,
                    ReorderRule.warehouse_id.is_(None)
                )
            )
        )
        .where(Stock.quantity == 0)
    )
    
    results = db.execute(stmt).all()
    
    return [
        StockAlertResponse(
            product_id=row.product_id,
            product_name=row.product_name,
            location_id=row.location_id,
            location_name=row.location_name,
            warehouse_id=row.warehouse_id,
            quantity=row.quantity,
            reorder_level=row.reorder_level,
            status="OUT_OF_STOCK"
        )
        for row in results
    ]

@router.get("", response_model=PaginatedResponse[StockResponse])
def get_all_stock(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    skip = (page - 1) * size
    total = db.query(Stock).count()
    items = db.query(Stock).offset(skip).limit(size).all()
    pages = math.ceil(total / size) if total > 0 else 0
    return PaginatedResponse(items=items, total=total, page=page, size=size, pages=pages)

@router.get("/{id}", response_model=StockResponse)
def get_stock_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stock = db.query(Stock).filter(Stock.id == id).first()
    if not stock:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock record not found")
    return stock

@router.get("/product/{product_id}", response_model=PaginatedResponse[StockResponse])
def get_stock_by_product(
    product_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    skip = (page - 1) * size
    query = db.query(Stock).filter(Stock.product_id == product_id)
    total = query.count()
    items = query.offset(skip).limit(size).all()
    pages = math.ceil(total / size) if total > 0 else 0
    return PaginatedResponse(items=items, total=total, page=page, size=size, pages=pages)

@router.get("/location/{location_id}", response_model=PaginatedResponse[StockResponse])
def get_stock_by_location(
    location_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    skip = (page - 1) * size
    query = db.query(Stock).filter(Stock.location_id == location_id)
    total = query.count()
    items = query.offset(skip).limit(size).all()
    pages = math.ceil(total / size) if total > 0 else 0
    return PaginatedResponse(items=items, total=total, page=page, size=size, pages=pages)
