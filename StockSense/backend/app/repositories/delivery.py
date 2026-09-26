from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
from app.models.delivery import Delivery
from app.repositories.base import BaseRepository
from app.schemas.delivery import DeliveryCreate

class DeliveryRepository(BaseRepository[Delivery, DeliveryCreate, DeliveryCreate]):
    def get_with_items(self, db: Session, id: int) -> Optional[Delivery]:
        return db.execute(select(Delivery).filter(Delivery.id == id)).scalar_one_or_none()

    def get_by_delivery_number(self, db: Session, delivery_number: str) -> Optional[Delivery]:
        return db.execute(select(Delivery).filter(Delivery.delivery_number == delivery_number)).scalar_one_or_none()
        
delivery_repository = DeliveryRepository(Delivery)
