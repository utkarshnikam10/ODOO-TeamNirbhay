import pytest
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.services.stock import StockService
from app.models.product import Product
from app.models.location import Location
from app.models.warehouse import Warehouse
from app.models.stock_ledger import StockLedger
import uuid

def get_unique_suffix():
    return str(uuid.uuid4())[:8]

@pytest.fixture
def test_product(db: Session):
    suffix = get_unique_suffix()
    product = Product(name=f"Prod {suffix}", sku=f"SKU-{suffix}", cost_price=Decimal("10"), selling_price=Decimal("20"))
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@pytest.fixture
def test_location_1(db: Session):
    suffix = get_unique_suffix()
    warehouse = Warehouse(name=f"WH1 {suffix}", code=f"WH1-{suffix}")
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    location = Location(warehouse_id=warehouse.id, code=f"LOC1-{suffix}", name="Loc 1")
    db.add(location)
    db.commit()
    db.refresh(location)
    return location

@pytest.fixture
def test_location_2(db: Session):
    suffix = get_unique_suffix()
    warehouse = Warehouse(name=f"WH2 {suffix}", code=f"WH2-{suffix}")
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    location = Location(warehouse_id=warehouse.id, code=f"LOC2-{suffix}", name="Loc 2")
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


def test_receive_stock(db: Session, test_product, test_location_1):
    stock = StockService.receive_stock(db, test_product.id, test_location_1.id, Decimal("50.000"))
    assert stock.quantity == Decimal("50.000")
    
    # check ledger
    ledgers = db.query(StockLedger).filter_by(product_id=test_product.id).all()
    assert len(ledgers) == 1
    assert ledgers[0].operation_type == "RECEIPT"
    assert ledgers[0].quantity_change == Decimal("50.000")
    assert ledgers[0].balance_after == Decimal("50.000")

def test_receive_stock_negative(db: Session, test_product, test_location_1):
    with pytest.raises(HTTPException) as exc:
        StockService.receive_stock(db, test_product.id, test_location_1.id, Decimal("-10.000"))
    assert exc.value.status_code == 400

def test_issue_stock(db: Session, test_product, test_location_1):
    StockService.receive_stock(db, test_product.id, test_location_1.id, Decimal("100.000"))
    
    stock = StockService.issue_stock(db, test_product.id, test_location_1.id, Decimal("20.000"))
    assert stock.quantity == Decimal("80.000")
    
    # check ledger
    ledgers = db.query(StockLedger).filter_by(product_id=test_product.id).order_by(StockLedger.id).all()
    assert len(ledgers) == 2
    assert ledgers[1].operation_type == "DELIVERY"
    assert ledgers[1].quantity_change == Decimal("-20.000")
    assert ledgers[1].balance_after == Decimal("80.000")

def test_issue_stock_insufficient(db: Session, test_product, test_location_1):
    StockService.receive_stock(db, test_product.id, test_location_1.id, Decimal("10.000"))
    with pytest.raises(HTTPException) as exc:
        StockService.issue_stock(db, test_product.id, test_location_1.id, Decimal("20.000"))
    assert exc.value.status_code == 400
    assert "Insufficient stock" in exc.value.detail

def test_transfer_stock(db: Session, test_product, test_location_1, test_location_2):
    StockService.receive_stock(db, test_product.id, test_location_1.id, Decimal("100.000"))
    
    src, dst = StockService.transfer_stock(
        db, test_product.id, test_location_1.id, test_location_2.id, Decimal("30.000")
    )
    
    assert src.quantity == Decimal("70.000")
    assert dst.quantity == Decimal("30.000")
    
    ledgers = db.query(StockLedger).filter_by(product_id=test_product.id).order_by(StockLedger.id).all()
    # 1 receipt, 1 transfer_out, 1 transfer_in
    assert len(ledgers) == 3
    assert ledgers[1].operation_type == "TRANSFER_OUT"
    assert ledgers[1].location_id == test_location_1.id
    assert ledgers[1].quantity_change == Decimal("-30.000")
    assert ledgers[2].operation_type == "TRANSFER_IN"
    assert ledgers[2].location_id == test_location_2.id
    assert ledgers[2].quantity_change == Decimal("30.000")

def test_transfer_stock_insufficient(db: Session, test_product, test_location_1, test_location_2):
    StockService.receive_stock(db, test_product.id, test_location_1.id, Decimal("20.000"))
    with pytest.raises(HTTPException):
        StockService.transfer_stock(db, test_product.id, test_location_1.id, test_location_2.id, Decimal("30.000"))

def test_adjust_stock_positive(db: Session, test_product, test_location_1):
    stock = StockService.adjust_stock(db, test_product.id, test_location_1.id, Decimal("15.000"))
    assert stock.quantity == Decimal("15.000")
    
    ledgers = db.query(StockLedger).filter_by(product_id=test_product.id).all()
    assert len(ledgers) == 1
    assert ledgers[0].operation_type == "ADJUSTMENT"
    assert ledgers[0].quantity_change == Decimal("15.000")
    assert ledgers[0].balance_after == Decimal("15.000")

def test_adjust_stock_negative(db: Session, test_product, test_location_1):
    StockService.receive_stock(db, test_product.id, test_location_1.id, Decimal("50.000"))
    stock = StockService.adjust_stock(db, test_product.id, test_location_1.id, Decimal("-10.000"))
    assert stock.quantity == Decimal("40.000")
    
def test_adjust_stock_below_zero(db: Session, test_product, test_location_1):
    StockService.receive_stock(db, test_product.id, test_location_1.id, Decimal("10.000"))
    with pytest.raises(HTTPException):
        StockService.adjust_stock(db, test_product.id, test_location_1.id, Decimal("-15.000"))

def test_get_available_stock(db: Session, test_product, test_location_1):
    assert StockService.get_available_stock(db, test_product.id, test_location_1.id) == Decimal("0.000")
    
    StockService.receive_stock(db, test_product.id, test_location_1.id, Decimal("100.000"))
    assert StockService.get_available_stock(db, test_product.id, test_location_1.id) == Decimal("100.000")
