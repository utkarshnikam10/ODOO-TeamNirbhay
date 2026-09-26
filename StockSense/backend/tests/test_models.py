from decimal import Decimal
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    Adjustment,
    AdjustmentItem,
    Category,
    Delivery,
    DeliveryItem,
    Location,
    Product,
    Receipt,
    ReceiptItem,
    ReorderRule,
    Stock,
    StockLedger,
    Transfer,
    TransferItem,
    User,
    Warehouse,
)


def test_user_creation(db: Session) -> None:
    """Test user model instantiation, defaults, and primary key."""
    user = User(
        email="admin@stocksense.io",
        username="admin",
        hashed_password="secure_hashed_password",
        full_name="System Administrator",
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    assert user.id is not None
    assert user.email == "admin@stocksense.io"
    assert user.is_active is True
    assert user.created_at is not None
    assert user.updated_at is not None


def test_category_and_product_relationship(db: Session) -> None:
    """Requirement 7: Product belongs to a category."""
    category = Category(
        name="Electronics",
        code="ELEC",
        description="Electronic components and devices",
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    product = Product(
        name="Wireless Barcode Scanner",
        sku="SCAN-W-001",
        barcode="123456789012",
        category_id=category.id,
        unit_of_measure="units",
        cost_price=Decimal("45.00"),
        selling_price=Decimal("79.99"),
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    assert product.id is not None
    assert product.category is not None
    assert product.category.name == "Electronics"
    assert product in category.products


def test_product_unique_sku_constraint(db: Session) -> None:
    """Requirement 3: Unique SKU constraint on products."""
    p1 = Product(name="Item A", sku="UNIQUE-SKU-1", cost_price=Decimal("10.00"))
    db.add(p1)
    db.commit()

    p2 = Product(name="Item B", sku="UNIQUE-SKU-1", cost_price=Decimal("20.00"))
    db.add(p2)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_warehouse_and_location_relationship(db: Session) -> None:
    """Requirement 8: Location belongs to a warehouse."""
    warehouse = Warehouse(
        name="Central Distribution Center",
        code="WH-CENTRAL",
        address="100 Logistics Way",
    )
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)

    location = Location(
        warehouse_id=warehouse.id,
        code="A-01-01",
        name="Aisle 1 Shelf 1 Bin 1",
        aisle="A",
        shelf="01",
        bin="01",
    )
    db.add(location)
    db.commit()
    db.refresh(location)

    assert location.id is not None
    assert location.warehouse.code == "WH-CENTRAL"
    assert location in warehouse.locations


def test_stock_tracking_by_product_and_location(db: Session) -> None:
    """Requirement 9: Stock is tracked by product + location."""
    warehouse = Warehouse(name="WH North", code="WH-N")
    category = Category(name="Tools", code="TOOL")
    db.add_all([warehouse, category])
    db.commit()

    location = Location(warehouse_id=warehouse.id, code="T-01", name="Tool Rack 1")
    product = Product(name="Hammer", sku="HAM-001", category_id=category.id)
    db.add_all([location, product])
    db.commit()

    stock = Stock(
        product_id=product.id,
        location_id=location.id,
        quantity=Decimal("50.000"),
        reserved_quantity=Decimal("5.000"),
    )
    db.add(stock)
    db.commit()
    db.refresh(stock)

    assert stock.id is not None
    assert stock.product.sku == "HAM-001"
    assert stock.location.code == "T-01"
    assert stock.quantity == Decimal("50.000")


def test_stock_duplicate_product_location_constraint(db: Session) -> None:
    """Requirement 15: Prevent duplicate product/location stock records."""
    wh = Warehouse(name="WH South", code="WH-S")
    db.add(wh)
    db.commit()

    loc = Location(warehouse_id=wh.id, code="S-01", name="Section 1")
    prod = Product(name="Wrench", sku="WRN-001")
    db.add_all([loc, prod])
    db.commit()

    s1 = Stock(product_id=prod.id, location_id=loc.id, quantity=Decimal("10.000"))
    db.add(s1)
    db.commit()

    s2 = Stock(product_id=prod.id, location_id=loc.id, quantity=Decimal("20.000"))
    db.add(s2)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_reorder_rule(db: Session) -> None:
    """Test reorder rules thresholds."""
    prod = Product(name="Bolts Pack", sku="BLT-100")
    wh = Warehouse(name="WH East", code="WH-E")
    db.add_all([prod, wh])
    db.commit()

    rule = ReorderRule(
        product_id=prod.id,
        warehouse_id=wh.id,
        min_quantity=Decimal("10.000"),
        max_quantity=Decimal("100.000"),
        reorder_quantity=Decimal("50.000"),
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    assert rule.id is not None
    assert rule.min_quantity == Decimal("10.000")
    assert rule.product.sku == "BLT-100"


def test_receipt_with_items_and_cascade(db: Session) -> None:
    """Requirement 10: Receipt has receipt_items."""
    wh = Warehouse(name="Main Hub", code="WH-HUB")
    prod = Product(name="Widget X", sku="WDG-X")
    db.add_all([wh, prod])
    db.commit()

    loc = Location(warehouse_id=wh.id, code="IN-01", name="Inbound Bay 1")
    db.add(loc)
    db.commit()

    receipt = Receipt(
        receipt_number="REC-2026-0001",
        supplier_name="Global Suppliers Inc.",
        status="confirmed",
    )
    item = ReceiptItem(
        product_id=prod.id,
        location_id=loc.id,
        quantity_expected=Decimal("100.000"),
        quantity_received=Decimal("100.000"),
        unit_cost=Decimal("12.50"),
    )
    receipt.receipt_items.append(item)
    db.add(receipt)
    db.commit()
    db.refresh(receipt)

    assert len(receipt.receipt_items) == 1
    assert receipt.receipt_items[0].product.sku == "WDG-X"

    # Test cascade deletion of items when receipt is removed
    receipt_id = receipt.id
    db.delete(receipt)
    db.commit()

    orphaned_items = db.query(ReceiptItem).filter_by(receipt_id=receipt_id).all()
    assert len(orphaned_items) == 0


def test_delivery_with_items(db: Session) -> None:
    """Requirement 11: Delivery has delivery_items."""
    wh = Warehouse(name="WH West", code="WH-W")
    prod = Product(name="Gear Y", sku="GR-Y")
    db.add_all([wh, prod])
    db.commit()

    loc = Location(warehouse_id=wh.id, code="OUT-01", name="Outbound Bay 1")
    db.add(loc)
    db.commit()

    delivery = Delivery(
        delivery_number="DEL-2026-0001",
        customer_name="Acme Corp",
        status="draft",
    )
    item = DeliveryItem(
        product_id=prod.id,
        location_id=loc.id,
        quantity_ordered=Decimal("25.000"),
        quantity_delivered=Decimal("0.000"),
        unit_price=Decimal("35.00"),
    )
    delivery.delivery_items.append(item)
    db.add(delivery)
    db.commit()
    db.refresh(delivery)

    assert len(delivery.delivery_items) == 1
    assert delivery.delivery_items[0].product.sku == "GR-Y"


def test_transfer_with_items(db: Session) -> None:
    """Requirement 12: Transfer has transfer_items."""
    wh1 = Warehouse(name="Warehouse Origin", code="WH-ORIG")
    wh2 = Warehouse(name="Warehouse Dest", code="WH-DEST")
    prod = Product(name="Component C", sku="COMP-C")
    db.add_all([wh1, wh2, prod])
    db.commit()

    loc1 = Location(warehouse_id=wh1.id, code="LOC-ORIG", name="Origin Shelf")
    loc2 = Location(warehouse_id=wh2.id, code="LOC-DEST", name="Dest Shelf")
    db.add_all([loc1, loc2])
    db.commit()

    transfer = Transfer(
        transfer_number="TRF-2026-0001",
        source_warehouse_id=wh1.id,
        destination_warehouse_id=wh2.id,
        status="draft",
    )
    item = TransferItem(
        product_id=prod.id,
        source_location_id=loc1.id,
        destination_location_id=loc2.id,
        quantity=Decimal("15.000"),
    )
    transfer.transfer_items.append(item)
    db.add(transfer)
    db.commit()
    db.refresh(transfer)

    assert len(transfer.transfer_items) == 1
    assert transfer.source_warehouse.code == "WH-ORIG"
    assert transfer.destination_warehouse.code == "WH-DEST"
    assert transfer.transfer_items[0].quantity == Decimal("15.000")


def test_adjustment_with_items(db: Session) -> None:
    """Requirement 13: Adjustment has adjustment_items."""
    wh = Warehouse(name="Warehouse Audit", code="WH-AUDIT")
    prod = Product(name="Item Audit", sku="AUD-01")
    db.add_all([wh, prod])
    db.commit()

    loc = Location(warehouse_id=wh.id, code="BIN-AUD", name="Audit Bin")
    db.add(loc)
    db.commit()

    adj = Adjustment(
        adjustment_number="ADJ-2026-0001",
        reason="Annual Physical Stock Count",
        status="applied",
    )
    item = AdjustmentItem(
        product_id=prod.id,
        location_id=loc.id,
        quantity_before=Decimal("20.000"),
        quantity_counted=Decimal("18.000"),
        difference=Decimal("-2.000"),
    )
    adj.adjustment_items.append(item)
    db.add(adj)
    db.commit()
    db.refresh(adj)

    assert len(adj.adjustment_items) == 1
    assert adj.adjustment_items[0].difference == Decimal("-2.000")


def test_stock_ledger_reference_operation(db: Session) -> None:
    """Requirement 14: Stock ledger references the relevant stock operation."""
    wh = Warehouse(name="WH Ledger", code="WH-LEDGER")
    prod = Product(name="Ledger Item", sku="LEDG-01")
    db.add_all([wh, prod])
    db.commit()

    loc = Location(warehouse_id=wh.id, code="LEDG-LOC", name="Ledger Bin")
    db.add(loc)
    db.commit()

    ledger_entry = StockLedger(
        product_id=prod.id,
        location_id=loc.id,
        operation_type="RECEIPT",
        reference_id=101,
        reference_number="REC-2026-0001",
        quantity_change=Decimal("50.000"),
        balance_after=Decimal("50.000"),
        notes="Initial stock received from vendor",
    )
    db.add(ledger_entry)
    db.commit()
    db.refresh(ledger_entry)

    assert ledger_entry.id is not None
    assert ledger_entry.operation_type == "RECEIPT"
    assert ledger_entry.reference_number == "REC-2026-0001"
    assert ledger_entry.quantity_change == Decimal("50.000")
    assert ledger_entry.created_at is not None
