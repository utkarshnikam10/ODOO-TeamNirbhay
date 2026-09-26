from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User, Role
from app.schemas.location import LocationCreate, LocationUpdate, LocationResponse
from app.schemas.pagination import PaginatedResponse
from app.services.location import LocationService

router = APIRouter(prefix="/locations", tags=["Locations"])

@router.post("", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
def create_location(
    location_in: LocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER))
):
    """Create a new location. Requires Admin or Manager role."""
    return LocationService.create_location(db, location_in)

@router.get("", response_model=PaginatedResponse[LocationResponse])
def get_locations(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all locations with pagination."""
    return LocationService.get_locations(db, page=page, size=size)

@router.get("/{location_id}", response_model=LocationResponse)
def get_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve a specific location by ID."""
    return LocationService.get_location(db, location_id)

@router.put("/{location_id}", response_model=LocationResponse)
def update_location(
    location_id: int,
    location_in: LocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER))
):
    """Update a location. Requires Admin or Manager role."""
    return LocationService.update_location(db, location_id, location_in)

@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER))
):
    """Delete a location. Requires Admin or Manager role."""
    LocationService.delete_location(db, location_id)
