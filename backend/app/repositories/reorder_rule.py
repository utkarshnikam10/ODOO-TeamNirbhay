from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
from app.models.reorder_rule import ReorderRule
from app.repositories.base import BaseRepository
from app.schemas.reorder_rule import ReorderRuleCreate, ReorderRuleUpdate

class ReorderRuleRepository(BaseRepository[ReorderRule, ReorderRuleCreate, ReorderRuleUpdate]):
    def get_by_product_and_warehouse(self, db: Session, product_id: int, warehouse_id: Optional[int] = None) -> Optional[ReorderRule]:
        stmt = select(ReorderRule).filter(ReorderRule.product_id == product_id)
        if warehouse_id:
            stmt = stmt.filter(ReorderRule.warehouse_id == warehouse_id)
        else:
            stmt = stmt.filter(ReorderRule.warehouse_id.is_(None))
        return db.execute(stmt).scalar_one_or_none()
        
reorder_rule_repository = ReorderRuleRepository(ReorderRule)
