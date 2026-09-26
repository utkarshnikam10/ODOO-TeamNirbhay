from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User, Role
from app.schemas.receipt import ReceiptCreate, ReceiptResponse
from app.schemas.pagination import PaginatedResponse
from app.services.receipt import ReceiptService

router = APIRouter(prefix="/receipts", tags=["Receipts"])

@router.post("", response_model=ReceiptResponse, status_code=status.HTTP_201_CREATED)
def create_receipt(
    receipt_in: ReceiptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER))
):
    """Create a new incoming receipt. Requires Admin or Manager role."""
    return ReceiptService.create_receipt(db, receipt_in, user_id=current_user.id)

@router.get("", response_model=PaginatedResponse[ReceiptResponse])
def get_receipts(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all receipts with pagination."""
    return ReceiptService.get_receipts(db, page=page, size=size)

@router.get("/{receipt_id}", response_model=ReceiptResponse)
def get_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve a specific receipt by ID."""
    return ReceiptService.get_receipt(db, receipt_id)

@router.post("/{receipt_id}/validate", response_model=ReceiptResponse)
def validate_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER))
):
    """Validate a receipt to update stock levels. Requires Admin or Manager role."""
    return ReceiptService.validate_receipt(db, receipt_id)

@router.post("/{receipt_id}/cancel", response_model=ReceiptResponse)
def cancel_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER))
):
    """Cancel a receipt. Requires Admin or Manager role."""
    return ReceiptService.cancel_receipt(db, receipt_id)
