from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User, Role
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate, WarehouseResponse
from app.schemas.pagination import PaginatedResponse
from app.services.warehouse import WarehouseService

router = APIRouter(prefix="/warehouses", tags=["Warehouses"])

@router.post("", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
def create_warehouse(
    warehouse_in: WarehouseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER))
):
    """Create a new warehouse. Requires Admin or Manager role."""
    return WarehouseService.create_warehouse(db, warehouse_in)

@router.get("", response_model=PaginatedResponse[WarehouseResponse])
def get_warehouses(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all warehouses with pagination."""
    return WarehouseService.get_warehouses(db, page=page, size=size)

@router.get("/{warehouse_id}", response_model=WarehouseResponse)
def get_warehouse(
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve a specific warehouse by ID."""
    return WarehouseService.get_warehouse(db, warehouse_id)

@router.put("/{warehouse_id}", response_model=WarehouseResponse)
def update_warehouse(
    warehouse_id: int,
    warehouse_in: WarehouseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER))
):
    """Update a warehouse. Requires Admin or Manager role."""
    return WarehouseService.update_warehouse(db, warehouse_id, warehouse_in)
