from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
from app.models.transfer import Transfer
from app.repositories.base import BaseRepository
from app.schemas.transfer import TransferCreate

class TransferRepository(BaseRepository[Transfer, TransferCreate, TransferCreate]):
    def get_with_items(self, db: Session, id: int) -> Optional[Transfer]:
        return db.execute(select(Transfer).filter(Transfer.id == id)).scalar_one_or_none()

    def get_by_transfer_number(self, db: Session, transfer_number: str) -> Optional[Transfer]:
        return db.execute(select(Transfer).filter(Transfer.transfer_number == transfer_number)).scalar_one_or_none()
        
transfer_repository = TransferRepository(Transfer)
