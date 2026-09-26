from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
from app.models.adjustment import Adjustment
from app.repositories.base import BaseRepository
from app.schemas.adjustment import AdjustmentCreate

class AdjustmentRepository(BaseRepository[Adjustment, AdjustmentCreate, AdjustmentCreate]):
    def get_with_items(self, db: Session, id: int) -> Optional[Adjustment]:
        return db.execute(select(Adjustment).filter(Adjustment.id == id)).scalar_one_or_none()

    def get_by_adjustment_number(self, db: Session, adjustment_number: str) -> Optional[Adjustment]:
        return db.execute(select(Adjustment).filter(Adjustment.adjustment_number == adjustment_number)).scalar_one_or_none()
        
adjustment_repository = AdjustmentRepository(Adjustment)
