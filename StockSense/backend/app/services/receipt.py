from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import math
from typing import Optional

from app.models.receipt import Receipt, ReceiptItem
from app.schemas.receipt import ReceiptCreate, ReceiptStatus
from app.schemas.pagination import PaginatedResponse
from app.repositories.receipt import receipt_repository
from app.repositories.product import product_repository
from app.repositories.location import location_repository
from app.services.stock import StockService

class ReceiptService:
    @staticmethod
    def create_receipt(db: Session, receipt_in: ReceiptCreate, user_id: int) -> Receipt:
        # Check if receipt number exists
        if receipt_repository.get_by_receipt_number(db, receipt_number=receipt_in.receipt_number):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Receipt number already exists")
            
        # Verify products and locations
        for item in receipt_in.items:
            if not product_repository.get(db, id=item.product_id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid product_id: {item.product_id}")
            if not location_repository.get(db, id=item.location_id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid location_id: {item.location_id}")

        receipt = Receipt(
            receipt_number=receipt_in.receipt_number,
            supplier_name=receipt_in.supplier_name,
            notes=receipt_in.notes,
            status=receipt_in.status.value,
            created_by_id=user_id
        )
        db.add(receipt)
        db.flush()
        
        for item in receipt_in.items:
            db_item = ReceiptItem(
                receipt_id=receipt.id,
                product_id=item.product_id,
                location_id=item.location_id,
                quantity_expected=item.quantity_expected,
                unit_cost=item.unit_cost
            )
            db.add(db_item)
            
        db.flush()
        return receipt

    @staticmethod
    def get_receipt(db: Session, receipt_id: int) -> Receipt:
        receipt = receipt_repository.get_with_items(db, id=receipt_id)
        if not receipt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")
        return receipt

    @staticmethod
    def get_receipts(db: Session, page: int = 1, size: int = 50) -> PaginatedResponse:
        skip = (page - 1) * size
        items, total = receipt_repository.get_multi(db, skip=skip, limit=size)
        pages = math.ceil(total / size) if total > 0 else 0
        
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    @staticmethod
    def validate_receipt(db: Session, receipt_id: int) -> Receipt:
        receipt = ReceiptService.get_receipt(db, receipt_id)
        
        if receipt.status == ReceiptStatus.DONE.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Receipt is already completed")
            
        if receipt.status == ReceiptStatus.CANCELED.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot validate a canceled receipt")
            
        for item in receipt.receipt_items:
            if item.quantity_expected <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail=f"Invalid quantity {item.quantity_expected} for product {item.product_id}"
                )
            
            # Receive stock for each item using StockService
            # StockService will also create the ledger entry
            StockService.receive_stock(
                db=db,
                product_id=item.product_id,
                location_id=item.location_id,
                quantity=item.quantity_expected,
                reference_id=receipt.id,
                reference_number=receipt.receipt_number,
                notes=f"Receipt Validation: {receipt.receipt_number}"
            )
            item.quantity_received = item.quantity_expected
            
        receipt.status = ReceiptStatus.DONE.value
        import datetime
        receipt.received_at = datetime.datetime.now(datetime.timezone.utc)
        
        db.add(receipt)
        db.flush()
        
        return receipt

    @staticmethod
    def cancel_receipt(db: Session, receipt_id: int) -> Receipt:
        receipt = ReceiptService.get_receipt(db, receipt_id)
        
        if receipt.status == ReceiptStatus.DONE.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot cancel a completed receipt")
            
        receipt.status = ReceiptStatus.CANCELED.value
        db.add(receipt)
        db.flush()
        
        return receipt
