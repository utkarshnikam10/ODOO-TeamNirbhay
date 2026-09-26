from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
from app.models.location import Location
from app.schemas.location import LocationCreate, LocationUpdate
from app.repositories.base import BaseRepository

class LocationRepository(BaseRepository[Location, LocationCreate, LocationUpdate]):
    def get_by_warehouse_and_code(self, db: Session, *, warehouse_id: int, code: str) -> Optional[Location]:
        return db.execute(
            select(Location).filter(Location.warehouse_id == warehouse_id, Location.code == code)
        ).scalar_one_or_none()

location_repository = LocationRepository(Location)
