from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import math

from app.schemas.location import LocationCreate, LocationUpdate
from app.schemas.pagination import PaginatedResponse
from app.repositories.location import location_repository
from app.repositories.warehouse import warehouse_repository
from app.models.location import Location

class LocationService:
    @staticmethod
    def create_location(db: Session, location_in: LocationCreate) -> Location:
        warehouse = warehouse_repository.get(db, id=location_in.warehouse_id)
        if not warehouse:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid warehouse_id")

        if location_repository.get_by_warehouse_and_code(db, warehouse_id=location_in.warehouse_id, code=location_in.code):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Location with this code already exists in the warehouse")
                
        return location_repository.create(db, obj_in=location_in)

    @staticmethod
    def get_location(db: Session, location_id: int) -> Location:
        location = location_repository.get(db, id=location_id)
        if not location:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
        return location

    @staticmethod
    def get_locations(db: Session, page: int = 1, size: int = 50) -> PaginatedResponse:
        skip = (page - 1) * size
        items, total = location_repository.get_multi(db, skip=skip, limit=size)
        pages = math.ceil(total / size) if total > 0 else 0
        
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    @staticmethod
    def update_location(db: Session, location_id: int, location_in: LocationUpdate) -> Location:
        location = LocationService.get_location(db, location_id)
        
        new_warehouse_id = location_in.warehouse_id if location_in.warehouse_id is not None else location.warehouse_id
        new_code = location_in.code if location_in.code is not None else location.code
        
        if location_in.warehouse_id is not None and location_in.warehouse_id != location.warehouse_id:
            warehouse = warehouse_repository.get(db, id=location_in.warehouse_id)
            if not warehouse:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid warehouse_id")
                
        if (location_in.warehouse_id is not None or location_in.code is not None) and (new_warehouse_id != location.warehouse_id or new_code != location.code):
            if location_repository.get_by_warehouse_and_code(db, warehouse_id=new_warehouse_id, code=new_code):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Location with this code already exists in the warehouse")

        return location_repository.update(db, db_obj=location, obj_in=location_in)

    @staticmethod
    def delete_location(db: Session, location_id: int) -> None:
        location = LocationService.get_location(db, location_id)
        if location.stock_items:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete location with active stock items")
        location_repository.remove(db, id=location_id)
