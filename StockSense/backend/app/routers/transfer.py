from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User, Role
from app.schemas.transfer import TransferCreate, TransferResponse
from app.schemas.pagination import PaginatedResponse
from app.services.transfer import TransferService

router = APIRouter(prefix="/transfers", tags=["Transfers"])

@router.post("", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
def create_transfer(
    transfer_in: TransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER))
):
    """Create a new internal transfer. Requires Admin or Manager role."""
    return TransferService.create_transfer(db, transfer_in, user_id=current_user.id)

@router.get("", response_model=PaginatedResponse[TransferResponse])
def get_transfers(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all transfers with pagination."""
    return TransferService.get_transfers(db, page=page, size=size)

@router.get("/{transfer_id}", response_model=TransferResponse)
def get_transfer(
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve a specific transfer by ID."""
    return TransferService.get_transfer(db, transfer_id)

@router.post("/{transfer_id}/validate", response_model=TransferResponse)
def validate_transfer(
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER))
):
    """Validate a transfer to move stock. Requires Admin or Manager role."""
    return TransferService.validate_transfer(db, transfer_id)

@router.post("/{transfer_id}/cancel", response_model=TransferResponse)
def cancel_transfer(
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER))
):
    """Cancel a transfer. Requires Admin or Manager role."""
    return TransferService.cancel_transfer(db, transfer_id)
