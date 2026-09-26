from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User, Role
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.schemas.pagination import PaginatedResponse
from app.services.category import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER))
):
    """Create a new category. Requires Admin or Manager role."""
    return CategoryService.create_category(db, category_in)

@router.get("", response_model=PaginatedResponse[CategoryResponse])
def get_categories(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all categories with pagination."""
    return CategoryService.get_categories(db, page=page, size=size)

@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve a specific category by ID."""
    return CategoryService.get_category(db, category_id)

@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER))
):
    """Update a category. Requires Admin or Manager role."""
    return CategoryService.update_category(db, category_id, category_in)

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER))
):
    """Delete a category. Requires Admin or Manager role."""
    CategoryService.delete_category(db, category_id)
