from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.repositories.base import BaseRepository

class CategoryRepository(BaseRepository[Category, CategoryCreate, CategoryUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Optional[Category]:
        return db.execute(select(Category).filter(Category.name == name)).scalar_one_or_none()

    def get_by_code(self, db: Session, *, code: str) -> Optional[Category]:
        return db.execute(select(Category).filter(Category.code == code)).scalar_one_or_none()

category_repository = CategoryRepository(Category)
