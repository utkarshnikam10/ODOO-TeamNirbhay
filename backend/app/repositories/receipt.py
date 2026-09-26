from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import Optional, List, Tuple
from app.models.receipt import Receipt, ReceiptItem
from app.repositories.base import BaseRepository
from app.schemas.receipt import ReceiptCreate

class ReceiptRepository(BaseRepository[Receipt, ReceiptCreate, ReceiptCreate]):
    def get_with_items(self, db: Session, id: int) -> Optional[Receipt]:
        # Utilizing lazy loading or joined loading in standard usage.
        # It's usually fine since relationships are accessed.
        return db.execute(select(Receipt).filter(Receipt.id == id)).scalar_one_or_none()

    def get_by_receipt_number(self, db: Session, receipt_number: str) -> Optional[Receipt]:
        return db.execute(select(Receipt).filter(Receipt.receipt_number == receipt_number)).scalar_one_or_none()
        
receipt_repository = ReceiptRepository(Receipt)
