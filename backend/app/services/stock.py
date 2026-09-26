from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.stock import Stock
from app.models.stock_ledger import StockLedger

class StockService:
    @staticmethod
    def _get_or_create_stock(db: Session, product_id: int, location_id: int) -> Stock:
        # Lock the row if it exists
        stmt = select(Stock).filter(
            Stock.product_id == product_id,
            Stock.location_id == location_id
        ).with_for_update()
        stock = db.execute(stmt).scalar_one_or_none()

        if not stock:
            stock = Stock(
                product_id=product_id,
                location_id=location_id,
                quantity=Decimal("0.000"),
                reserved_quantity=Decimal("0.000")
            )
            db.add(stock)
            db.flush()
        return stock

    @staticmethod
    def _create_ledger_entry(
        db: Session,
        product_id: int,
        location_id: int,
        operation_type: str,
        quantity_change: Decimal,
        balance_after: Decimal,
        reference_id: Optional[int] = None,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None
    ) -> StockLedger:
        ledger = StockLedger(
            product_id=product_id,
            location_id=location_id,
            operation_type=operation_type,
            quantity_change=quantity_change,
            balance_after=balance_after,
            reference_id=reference_id,
            reference_number=reference_number,
            notes=notes
        )
        db.add(ledger)
        db.flush()
        return ledger

    @staticmethod
    def get_available_stock(db: Session, product_id: int, location_id: int) -> Decimal:
        stock = db.execute(
            select(Stock).filter(
                Stock.product_id == product_id,
                Stock.location_id == location_id
            )
        ).scalar_one_or_none()
        if not stock:
            return Decimal("0.000")
        return stock.quantity - stock.reserved_quantity

    @staticmethod
    def receive_stock(
        db: Session,
        product_id: int,
        location_id: int,
        quantity: Decimal,
        reference_id: Optional[int] = None,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Stock:
        if quantity <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Receive quantity must be positive")
            
        stock = StockService._get_or_create_stock(db, product_id, location_id)
        stock.quantity += quantity
        
        StockService._create_ledger_entry(
            db=db,
            product_id=product_id,
            location_id=location_id,
            operation_type="RECEIPT",
            quantity_change=quantity,
            balance_after=stock.quantity,
            reference_id=reference_id,
            reference_number=reference_number,
            notes=notes
        )
        return stock

    @staticmethod
    def issue_stock(
        db: Session,
        product_id: int,
        location_id: int,
        quantity: Decimal,
        reference_id: Optional[int] = None,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Stock:
        if quantity <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Issue quantity must be positive")
            
        stock = StockService._get_or_create_stock(db, product_id, location_id)
        if stock.quantity < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Insufficient stock. Available: {stock.quantity}, Requested: {quantity}"
            )
            
        stock.quantity -= quantity
        
        StockService._create_ledger_entry(
            db=db,
            product_id=product_id,
            location_id=location_id,
            operation_type="DELIVERY",
            quantity_change=-quantity,
            balance_after=stock.quantity,
            reference_id=reference_id,
            reference_number=reference_number,
            notes=notes
        )
        return stock

    @staticmethod
    def transfer_stock(
        db: Session,
        product_id: int,
        source_location_id: int,
        destination_location_id: int,
        quantity: Decimal,
        reference_id: Optional[int] = None,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None
    ) -> tuple[Stock, Stock]:
        if source_location_id == destination_location_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source and destination locations must be different")
        if quantity <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transfer quantity must be positive")
            
        # To avoid deadlocks, always lock the location with the smaller ID first
        loc1, loc2 = sorted([source_location_id, destination_location_id])
        stock1 = StockService._get_or_create_stock(db, product_id, loc1)
        stock2 = StockService._get_or_create_stock(db, product_id, loc2)
        
        # Identify source and destination stocks
        if stock1.location_id == source_location_id:
            source_stock, dest_stock = stock1, stock2
        else:
            source_stock, dest_stock = stock2, stock1

        if source_stock.quantity < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Insufficient stock at source location. Available: {source_stock.quantity}, Requested: {quantity}"
            )
            
        # Deduct from source
        source_stock.quantity -= quantity
        StockService._create_ledger_entry(
            db=db,
            product_id=product_id,
            location_id=source_location_id,
            operation_type="TRANSFER_OUT",
            quantity_change=-quantity,
            balance_after=source_stock.quantity,
            reference_id=reference_id,
            reference_number=reference_number,
            notes=notes
        )
        
        # Add to destination
        dest_stock.quantity += quantity
        StockService._create_ledger_entry(
            db=db,
            product_id=product_id,
            location_id=destination_location_id,
            operation_type="TRANSFER_IN",
            quantity_change=quantity,
            balance_after=dest_stock.quantity,
            reference_id=reference_id,
            reference_number=reference_number,
            notes=notes
        )
        
        return source_stock, dest_stock

    @staticmethod
    def adjust_stock(
        db: Session,
        product_id: int,
        location_id: int,
        quantity_change: Decimal,
        reference_id: Optional[int] = None,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Stock:
        if quantity_change == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Adjustment quantity cannot be zero")
            
        stock = StockService._get_or_create_stock(db, product_id, location_id)
        
        new_quantity = stock.quantity + quantity_change
        if new_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Adjustment would result in negative stock. Current: {stock.quantity}, Adjustment: {quantity_change}"
            )
            
        stock.quantity = new_quantity
        
        StockService._create_ledger_entry(
            db=db,
            product_id=product_id,
            location_id=location_id,
            operation_type="ADJUSTMENT",
            quantity_change=quantity_change,
            balance_after=stock.quantity,
            reference_id=reference_id,
            reference_number=reference_number,
            notes=notes
        )
        return stock
