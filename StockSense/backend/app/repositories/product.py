from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import Optional, List, Tuple
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.repositories.base import BaseRepository

class ProductRepository(BaseRepository[Product, ProductCreate, ProductUpdate]):
    def get_by_sku(self, db: Session, *, sku: str) -> Optional[Product]:
        return db.execute(select(Product).filter(Product.sku == sku)).scalar_one_or_none()

    def get_by_barcode(self, db: Session, *, barcode: str) -> Optional[Product]:
        return db.execute(select(Product).filter(Product.barcode == barcode)).scalar_one_or_none()

    def search_products(self, db: Session, *, skip: int = 0, limit: int = 100, query: Optional[str] = None, category_id: Optional[int] = None) -> Tuple[List[Product], int]:
        stmt = select(Product)
        count_stmt = select(func.count(Product.id))
        
        if query:
            filter_cond = (Product.name.ilike(f"%{query}%")) | (Product.sku.ilike(f"%{query}%"))
            stmt = stmt.filter(filter_cond)
            count_stmt = count_stmt.filter(filter_cond)
            
        if category_id:
            stmt = stmt.filter(Product.category_id == category_id)
            count_stmt = count_stmt.filter(Product.category_id == category_id)
            
        total = db.execute(count_stmt).scalar_one()
        items = db.execute(stmt.offset(skip).limit(limit)).scalars().all()
        return list(items), total

product_repository = ProductRepository(Product)
