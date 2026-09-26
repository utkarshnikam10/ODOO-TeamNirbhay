from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User, Role
from app.schemas.reorder_rule import ReorderRuleCreate, ReorderRuleUpdate, ReorderRuleResponse
from app.schemas.pagination import PaginatedResponse
from app.services.reorder_rule import ReorderRuleService

router = APIRouter(prefix="/reorder-rules", tags=["Reorder Rules"])

@router.post("", response_model=ReorderRuleResponse, status_code=status.HTTP_201_CREATED)
def create_reorder_rule(
    rule_in: ReorderRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER))
):
    return ReorderRuleService.create_rule(db, rule_in)

@router.get("", response_model=PaginatedResponse[ReorderRuleResponse])
def get_reorder_rules(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ReorderRuleService.get_rules(db, page=page, size=size)

@router.put("/{rule_id}", response_model=ReorderRuleResponse)
def update_reorder_rule(
    rule_id: int,
    rule_in: ReorderRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER))
):
    return ReorderRuleService.update_rule(db, rule_id, rule_in)

@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reorder_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER))
):
    ReorderRuleService.delete_rule(db, rule_id)
