from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
from app.models.warehouse import Warehouse
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate
from app.repositories.base import BaseRepository

class WarehouseRepository(BaseRepository[Warehouse, WarehouseCreate, WarehouseUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Optional[Warehouse]:
        return db.execute(select(Warehouse).filter(Warehouse.name == name)).scalar_one_or_none()

    def get_by_code(self, db: Session, *, code: str) -> Optional[Warehouse]:
        return db.execute(select(Warehouse).filter(Warehouse.code == code)).scalar_one_or_none()

warehouse_repository = WarehouseRepository(Warehouse)
