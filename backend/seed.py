import os
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, Role
from app.models.category import Category
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.models.location import Location
from app.services.stock import StockService

def seed_database():
    print("Starting database seed process...")
    db = SessionLocal()
    try:
        # Seed Admin User
        admin_email = os.getenv("SEED_ADMIN_EMAIL", "seed_admin@stocksense.local")
        admin_password = os.getenv("SEED_ADMIN_PASSWORD", "changeme123")
        
        admin_user = db.execute(select(User).filter(User.email == admin_email)).scalar_one_or_none()
        if not admin_user:
            admin_user = User(
                email=admin_email,
                username="seed_admin",
                full_name="System Administrator",
                hashed_password=get_password_hash(admin_password),
                role=Role.ADMIN.value,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print(f"Created admin user: {admin_email}")
        else:
            print("Admin user already exists, skipping.")

        # Seed Categories
        category = db.execute(select(Category).filter(Category.code == "SEED-ELEC-01")).scalar_one_or_none()
        if not category:
            category = Category(name="Seed Electronics", code="SEED-ELEC-01", description="Consumer Electronics")
            db.add(category)
            db.commit()
            db.refresh(category)
            print("Created 'Seed Electronics' category.")
        else:
            print("Category already exists, skipping.")

        # Seed Warehouse
        warehouse = db.execute(select(Warehouse).filter(Warehouse.code == "SEED-WH-MAIN")).scalar_one_or_none()
        if not warehouse:
            warehouse = Warehouse(name="Seed Main Distribution", code="SEED-WH-MAIN", address="123 Logistics Way")
            db.add(warehouse)
            db.commit()
            db.refresh(warehouse)
            print("Created Main Warehouse.")
        else:
            print("Warehouse already exists, skipping.")

        # Seed Locations
        loc1 = db.execute(select(Location).filter(Location.code == "SEED-LOC-A1", Location.warehouse_id == warehouse.id)).scalar_one_or_none()
        if not loc1:
            loc1 = Location(warehouse_id=warehouse.id, code="SEED-LOC-A1", name="Seed Aisle A, Rack 1")
            db.add(loc1)
            db.commit()
            db.refresh(loc1)
            print("Created Location SEED-LOC-A1.")

        loc2 = db.execute(select(Location).filter(Location.code == "SEED-LOC-B2", Location.warehouse_id == warehouse.id)).scalar_one_or_none()
        if not loc2:
            loc2 = Location(warehouse_id=warehouse.id, code="SEED-LOC-B2", name="Seed Aisle B, Rack 2")
            db.add(loc2)
            db.commit()
            db.refresh(loc2)
            print("Created Location SEED-LOC-B2.")

        # Seed Products
        product1 = db.execute(select(Product).filter(Product.sku == "SEED-LAPTOP-X1")).scalar_one_or_none()
        if not product1:
            product1 = Product(
                name="Seed ThinkPad X1 Carbon", 
                sku="SEED-LAPTOP-X1", 
                category_id=category.id,
                unit_of_measure="pcs",
                cost_price=Decimal("1200.00"),
                selling_price=Decimal("1500.00")
            )
            db.add(product1)
            db.commit()
            db.refresh(product1)
            print("Created Product ThinkPad X1 Carbon.")

        product2 = db.execute(select(Product).filter(Product.sku == "SEED-MOUSE-G1")).scalar_one_or_none()
        if not product2:
            product2 = Product(
                name="Seed Logitech MX Master 3", 
                sku="SEED-MOUSE-G1", 
                category_id=category.id,
                unit_of_measure="pcs",
                cost_price=Decimal("80.00"),
                selling_price=Decimal("99.99")
            )
            db.add(product2)
            db.commit()
            db.refresh(product2)
            print("Created Product Logitech MX Master 3.")

        # Seed Stock
        # We need to make sure we don't repeatedly add stock if script is run multiple times
        available_stock_p1 = StockService.get_available_stock(db, product1.id, loc1.id)
        if available_stock_p1 == Decimal("0.000"):
            StockService.receive_stock(
                db=db,
                product_id=product1.id,
                location_id=loc1.id,
                quantity=Decimal("50.000"),
                notes="Initial Seed Data"
            )
            db.commit()
            print("Added 50 units of Laptop to LOC-A1.")
        
        available_stock_p2 = StockService.get_available_stock(db, product2.id, loc2.id)
        if available_stock_p2 == Decimal("0.000"):
            StockService.receive_stock(
                db=db,
                product_id=product2.id,
                location_id=loc2.id,
                quantity=Decimal("120.000"),
                notes="Initial Seed Data"
            )
            db.commit()
            print("Added 120 units of Mouse to LOC-B2.")

        print("Database seed process completed successfully!")
    
    except Exception as e:
        print(f"Error during seed process: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
