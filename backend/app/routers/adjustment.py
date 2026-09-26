from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User, Role
from app.schemas.adjustment import AdjustmentCreate, AdjustmentResponse
from app.schemas.pagination import PaginatedResponse
from app.services.adjustment import AdjustmentService

router = APIRouter(prefix="/adjustments", tags=["Adjustments"])

@router.post("", response_model=AdjustmentResponse, status_code=status.HTTP_201_CREATED)
def create_adjustment(
    adjustment_in: AdjustmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER))
):
    """Create a new inventory adjustment. Requires Admin or Manager role."""
    return AdjustmentService.create_adjustment(db, adjustment_in, user_id=current_user.id)

@router.get("", response_model=PaginatedResponse[AdjustmentResponse])
def get_adjustments(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all adjustments with pagination."""
    return AdjustmentService.get_adjustments(db, page=page, size=size)

@router.get("/{adjustment_id}", response_model=AdjustmentResponse)
def get_adjustment(
    adjustment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve a specific adjustment by ID."""
    return AdjustmentService.get_adjustment(db, adjustment_id)

@router.post("/{adjustment_id}/validate", response_model=AdjustmentResponse)
def validate_adjustment(
    adjustment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER))
):
    """Validate an adjustment to mutate stock levels. Requires Admin or Manager role."""
    return AdjustmentService.validate_adjustment(db, adjustment_id)
