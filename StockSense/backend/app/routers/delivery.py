from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User, Role
from app.schemas.delivery import DeliveryCreate, DeliveryResponse
from app.schemas.pagination import PaginatedResponse
from app.services.delivery import DeliveryService

router = APIRouter(prefix="/deliveries", tags=["Deliveries"])

@router.post("", response_model=DeliveryResponse, status_code=status.HTTP_201_CREATED)
def create_delivery(
    delivery_in: DeliveryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER))
):
    """Create a new outgoing delivery. Requires Admin or Manager role."""
    return DeliveryService.create_delivery(db, delivery_in, user_id=current_user.id)

@router.get("", response_model=PaginatedResponse[DeliveryResponse])
def get_deliveries(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all deliveries with pagination."""
    return DeliveryService.get_deliveries(db, page=page, size=size)

@router.get("/{delivery_id}", response_model=DeliveryResponse)
def get_delivery(
    delivery_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve a specific delivery by ID."""
    return DeliveryService.get_delivery(db, delivery_id)

@router.post("/{delivery_id}/validate", response_model=DeliveryResponse)
def validate_delivery(
    delivery_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER))
):
    """Validate a delivery to reduce stock levels. Requires Admin or Manager role."""
    return DeliveryService.validate_delivery(db, delivery_id)

@router.post("/{delivery_id}/cancel", response_model=DeliveryResponse)
def cancel_delivery(
    delivery_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER))
):
    """Cancel a delivery. Requires Admin or Manager role."""
    return DeliveryService.cancel_delivery(db, delivery_id)
