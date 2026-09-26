from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import math

from app.models.reorder_rule import ReorderRule
from app.schemas.reorder_rule import ReorderRuleCreate, ReorderRuleUpdate
from app.schemas.pagination import PaginatedResponse
from app.repositories.reorder_rule import reorder_rule_repository
from app.repositories.product import product_repository
from app.repositories.warehouse import warehouse_repository

class ReorderRuleService:
    @staticmethod
    def create_rule(db: Session, rule_in: ReorderRuleCreate) -> ReorderRule:
        if not product_repository.get(db, id=rule_in.product_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid product_id")
            
        if rule_in.warehouse_id and not warehouse_repository.get(db, id=rule_in.warehouse_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid warehouse_id")
            
        if rule_in.max_quantity < rule_in.min_quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Max quantity cannot be less than min quantity")
            
        existing = reorder_rule_repository.get_by_product_and_warehouse(db, rule_in.product_id, rule_in.warehouse_id)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reorder rule already exists for this product and warehouse")
            
        return reorder_rule_repository.create(db, obj_in=rule_in)

    @staticmethod
    def get_rule(db: Session, rule_id: int) -> ReorderRule:
        rule = reorder_rule_repository.get(db, id=rule_id)
        if not rule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reorder rule not found")
        return rule

    @staticmethod
    def get_rules(db: Session, page: int = 1, size: int = 50) -> PaginatedResponse:
        skip = (page - 1) * size
        items, total = reorder_rule_repository.get_multi(db, skip=skip, limit=size)
        pages = math.ceil(total / size) if total > 0 else 0
        return PaginatedResponse(items=items, total=total, page=page, size=size, pages=pages)

    @staticmethod
    def update_rule(db: Session, rule_id: int, rule_in: ReorderRuleUpdate) -> ReorderRule:
        rule = ReorderRuleService.get_rule(db, rule_id)
        return reorder_rule_repository.update(db, db_obj=rule, obj_in=rule_in)

    @staticmethod
    def delete_rule(db: Session, rule_id: int):
        rule = ReorderRuleService.get_rule(db, rule_id)
        reorder_rule_repository.remove(db, id=rule_id)
