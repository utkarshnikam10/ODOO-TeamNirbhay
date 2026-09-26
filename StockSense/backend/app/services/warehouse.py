from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import math

from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate
from app.schemas.pagination import PaginatedResponse
from app.repositories.warehouse import warehouse_repository
from app.models.warehouse import Warehouse

class WarehouseService:
    @staticmethod
    def create_warehouse(db: Session, warehouse_in: WarehouseCreate) -> Warehouse:
        if warehouse_repository.get_by_name(db, name=warehouse_in.name):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Warehouse name already exists")
            
        if warehouse_repository.get_by_code(db, code=warehouse_in.code):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Warehouse code already exists")
                
        return warehouse_repository.create(db, obj_in=warehouse_in)

    @staticmethod
    def get_warehouse(db: Session, warehouse_id: int) -> Warehouse:
        warehouse = warehouse_repository.get(db, id=warehouse_id)
        if not warehouse:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")
        return warehouse

    @staticmethod
    def get_warehouses(db: Session, page: int = 1, size: int = 50) -> PaginatedResponse:
        skip = (page - 1) * size
        items, total = warehouse_repository.get_multi(db, skip=skip, limit=size)
        pages = math.ceil(total / size) if total > 0 else 0
        
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    @staticmethod
    def update_warehouse(db: Session, warehouse_id: int, warehouse_in: WarehouseUpdate) -> Warehouse:
        warehouse = WarehouseService.get_warehouse(db, warehouse_id)
        
        if warehouse_in.name and warehouse_in.name != warehouse.name:
            if warehouse_repository.get_by_name(db, name=warehouse_in.name):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Warehouse name already exists")
                
        if warehouse_in.code and warehouse_in.code != warehouse.code:
            if warehouse_repository.get_by_code(db, code=warehouse_in.code):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Warehouse code already exists")

        return warehouse_repository.update(db, db_obj=warehouse, obj_in=warehouse_in)
