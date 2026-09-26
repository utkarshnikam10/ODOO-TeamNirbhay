from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.schemas.category import CategoryCreate, CategoryUpdate
from app.schemas.pagination import PaginatedResponse
from app.repositories.category import category_repository
from app.models.category import Category

class CategoryService:
    @staticmethod
    def create_category(db: Session, category_in: CategoryCreate) -> Category:
        existing = category_repository.get_by_name(db, name=category_in.name)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category name already exists")
        
        if category_in.code:
            existing_code = category_repository.get_by_code(db, code=category_in.code)
            if existing_code:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category code already exists")
                
        return category_repository.create(db, obj_in=category_in)

    @staticmethod
    def get_category(db: Session, category_id: int) -> Category:
        category = category_repository.get(db, id=category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return category

    @staticmethod
    def get_categories(db: Session, page: int = 1, size: int = 50) -> PaginatedResponse:
        skip = (page - 1) * size
        items, total = category_repository.get_multi(db, skip=skip, limit=size)
        pages = math.ceil(total / size)
        
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    @staticmethod
    def update_category(db: Session, category_id: int, category_in: CategoryUpdate) -> Category:
        category = CategoryService.get_category(db, category_id)
        
        if category_in.name and category_in.name != category.name:
            existing = category_repository.get_by_name(db, name=category_in.name)
            if existing:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category name already exists")
                
        if category_in.code and category_in.code != category.code:
            existing_code = category_repository.get_by_code(db, code=category_in.code)
            if existing_code:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category code already exists")

        return category_repository.update(db, db_obj=category, obj_in=category_in)

    @staticmethod
    def delete_category(db: Session, category_id: int) -> None:
        category = CategoryService.get_category(db, category_id)
        # Check if category has products before deleting could be handled via DB constraint or explicit check here
        if category.products:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete category with assigned products")
        category_repository.remove(db, id=category_id)
