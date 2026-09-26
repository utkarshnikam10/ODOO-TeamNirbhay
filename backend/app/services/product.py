from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.pagination import PaginatedResponse
from app.repositories.product import product_repository
from app.repositories.category import category_repository
from app.models.product import Product

class ProductService:
    @staticmethod
    def create_product(db: Session, product_in: ProductCreate) -> Product:
        if product_repository.get_by_sku(db, sku=product_in.sku):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product with this SKU already exists")
            
        if product_in.barcode and product_repository.get_by_barcode(db, barcode=product_in.barcode):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product with this barcode already exists")
            
        if product_in.category_id:
            category = category_repository.get(db, id=product_in.category_id)
            if not category:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category_id")
                
        return product_repository.create(db, obj_in=product_in)

    @staticmethod
    def get_product(db: Session, product_id: int) -> Product:
        product = product_repository.get(db, id=product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return product

    @staticmethod
    def get_products(db: Session, page: int = 1, size: int = 50, query: Optional[str] = None, category_id: Optional[int] = None) -> PaginatedResponse:
        skip = (page - 1) * size
        items, total = product_repository.search_products(db, skip=skip, limit=size, query=query, category_id=category_id)
        pages = math.ceil(total / size) if total > 0 else 0
        
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    @staticmethod
    def update_product(db: Session, product_id: int, product_in: ProductUpdate) -> Product:
        product = ProductService.get_product(db, product_id)
        
        if product_in.sku and product_in.sku != product.sku:
            if product_repository.get_by_sku(db, sku=product_in.sku):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product with this SKU already exists")
                
        if product_in.barcode and product_in.barcode != product.barcode:
            if product_repository.get_by_barcode(db, barcode=product_in.barcode):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product with this barcode already exists")

        if product_in.category_id is not None and product_in.category_id != product.category_id:
            category = category_repository.get(db, id=product_in.category_id)
            if not category:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category_id")

        return product_repository.update(db, db_obj=product, obj_in=product_in)

    @staticmethod
    def delete_product(db: Session, product_id: int) -> None:
        product = ProductService.get_product(db, product_id)
        if product.stock_items:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete product with active stock items")
        product_repository.remove(db, id=product_id)
