"""
StockSense – Comprehensive Unit Tests for Inventory Core & Intelligence
========================================================================
Author: Utkarsh (Team Nirbhay)
Role: Inventory Intelligence + Core Business Logic

Covers all 12 required test scenarios:
1. Receipt increases stock
2. Delivery decreases stock
3. Delivery greater than available stock is rejected
4. Transfer preserves total stock
5. Adjustment calculates correct difference
6. Duplicate transaction validation is rejected
7. Ledger entry is created
8. Zero/negative quantity is rejected
9. Risk calculation handles zero demand
10. Reorder calculation works
11. What-if simulation does not modify actual stock
12. Anomaly detection identifies obvious abnormal movement
"""

import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.database import Base
from app.models.product import Product
from app.models.location import Location
from app.models.warehouse import Warehouse
from app.models.stock import Stock
from app.models.stock_ledger import StockLedger
from app.models.receipt import Receipt, ReceiptItem
from app.models.delivery import Delivery, DeliveryItem
from app.models.transfer import Transfer, TransferItem
from app.models.adjustment import Adjustment, AdjustmentItem
from app.models.reorder_rule import ReorderRule

from app.services.stock_service import StockService
from app.services.receipt_service import ReceiptService
from app.services.delivery_service import DeliveryService
from app.services.transfer_service import TransferService
from app.services.adjustment_service import AdjustmentService
from app.services.ledger_service import LedgerService

from app.intelligence.risk_engine import (
    RiskEngine,
    RISK_LEVEL_CRITICAL,
    RISK_LEVEL_HIGH,
    RISK_LEVEL_MEDIUM,
    RISK_LEVEL_LOW,
)
from app.intelligence.reorder_engine import ReorderEngine
from app.intelligence.anomaly_engine import AnomalyEngine
from app.intelligence.what_if_engine import WhatIfEngine, WhatIfInput

from app.utils.exceptions import (
    InsufficientStockError,
    InvalidQuantityError,
    DuplicateValidationError,
    InvalidTransactionStateError,
    SameLocationTransferError,
)


@pytest.fixture
def db_session() -> Session:
    """Creates a fresh, isolated SQLite in-memory database for each test."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def setup_inventory(db_session: Session):
    """Sets up a warehouse, locations, and products."""
    wh1 = Warehouse(name="Central Warehouse", code="WH-CENTRAL")
    wh2 = Warehouse(name="North Warehouse", code="WH-NORTH")
    db_session.add_all([wh1, wh2])
    db_session.flush()

    loc1 = Location(warehouse_id=wh1.id, name="Bin A1", code="LOC-A1")
    loc2 = Location(warehouse_id=wh1.id, name="Bin A2", code="LOC-A2")
    loc3 = Location(warehouse_id=wh2.id, name="Bin B1", code="LOC-B1")
    db_session.add_all([loc1, loc2, loc3])
    db_session.flush()

    prod1 = Product(name="Industrial Widget A", sku="WIDGET-A")
    prod2 = Product(name="Component Gear B", sku="GEAR-B")
    db_session.add_all([prod1, prod2])
    db_session.commit()

    return {
        "wh1": wh1,
        "wh2": wh2,
        "loc1": loc1,
        "loc2": loc2,
        "loc3": loc3,
        "prod1": prod1,
        "prod2": prod2,
    }


# ── TEST 1: Receipt increases stock ──────────────────────────────────────────
def test_01_receipt_increases_stock(db_session: Session, setup_inventory):
    loc = setup_inventory["loc1"]
    prod = setup_inventory["prod1"]

    stock_service = StockService(db_session)
    receipt_service = ReceiptService(db_session)

    # Initial stock is 0
    assert stock_service.get_available_quantity(prod.id, loc.id) == Decimal("0")

    # Create a draft receipt
    receipt = Receipt(receipt_number="REC-2026-001", status="draft")
    db_session.add(receipt)
    db_session.flush()

    item = ReceiptItem(
        receipt_id=receipt.id,
        product_id=prod.id,
        location_id=loc.id,
        quantity_expected=Decimal("50.000"),
    )
    db_session.add(item)
    db_session.commit()

    # Validate receipt
    validated_receipt = receipt_service.validate_receipt(receipt.id)
    assert validated_receipt.status == "validated"

    # Verify stock increased to 50
    qty = stock_service.get_available_quantity(prod.id, loc.id)
    assert qty == Decimal("50.000")


# ── TEST 2: Delivery decreases stock ─────────────────────────────────────────
def test_02_delivery_decreases_stock(db_session: Session, setup_inventory):
    loc = setup_inventory["loc1"]
    prod = setup_inventory["prod1"]

    stock_service = StockService(db_session)
    delivery_service = DeliveryService(db_session)

    # Pre-seed 100 units of stock
    stock_service.increase_stock(prod.id, loc.id, Decimal("100.000"))
    db_session.commit()
    assert stock_service.get_available_quantity(prod.id, loc.id) == Decimal("100.000")

    # Create draft delivery of 35 units
    delivery = Delivery(delivery_number="DEL-2026-001", status="draft")
    db_session.add(delivery)
    db_session.flush()

    item = DeliveryItem(
        delivery_id=delivery.id,
        product_id=prod.id,
        location_id=loc.id,
        quantity_ordered=Decimal("35.000"),
    )
    db_session.add(item)
    db_session.commit()

    # Validate delivery
    validated_delivery = delivery_service.validate_delivery(delivery.id)
    assert validated_delivery.status == "validated"

    # Check stock decreased to 65
    qty = stock_service.get_available_quantity(prod.id, loc.id)
    assert qty == Decimal("65.000")


# ── TEST 3: Delivery greater than available stock is rejected ────────────────
def test_03_delivery_greater_than_available_stock_rejected(db_session: Session, setup_inventory):
    loc = setup_inventory["loc1"]
    prod = setup_inventory["prod1"]

    stock_service = StockService(db_session)
    delivery_service = DeliveryService(db_session)

    # Initial available stock = 20 units
    stock_service.increase_stock(prod.id, loc.id, Decimal("20.000"))
    db_session.commit()

    # Attempt to deliver 25 units
    delivery = Delivery(delivery_number="DEL-2026-002", status="draft")
    db_session.add(delivery)
    db_session.flush()

    item = DeliveryItem(
        delivery_id=delivery.id,
        product_id=prod.id,
        location_id=loc.id,
        quantity_ordered=Decimal("25.000"),
    )
    db_session.add(item)
    db_session.commit()

    with pytest.raises(InsufficientStockError) as exc_info:
        delivery_service.validate_delivery(delivery.id)

    assert "Insufficient stock" in str(exc_info.value)
    assert exc_info.value.available == 20.0
    assert exc_info.value.requested == 25.0

    # Stock must remain unchanged at 20
    assert stock_service.get_available_quantity(prod.id, loc.id) == Decimal("20.000")


# ── TEST 4: Transfer preserves total stock ───────────────────────────────────
def test_04_transfer_preserves_total_stock(db_session: Session, setup_inventory):
    loc1 = setup_inventory["loc1"]
    loc2 = setup_inventory["loc2"]
    prod = setup_inventory["prod1"]
    wh1 = setup_inventory["wh1"]

    stock_service = StockService(db_session)
    transfer_service = TransferService(db_session)

    # Pre-seed loc1 with 20 units
    stock_service.increase_stock(prod.id, loc1.id, Decimal("20.000"))
    db_session.commit()

    total_before = stock_service.get_total_stock_for_product(prod.id)
    assert total_before == Decimal("20.000")

    # Transfer 7 units from loc1 to loc2
    transfer = Transfer(
        transfer_number="TRF-2026-001",
        source_warehouse_id=wh1.id,
        destination_warehouse_id=wh1.id,
        status="draft",
    )
    db_session.add(transfer)
    db_session.flush()

    item = TransferItem(
        transfer_id=transfer.id,
        product_id=prod.id,
        source_location_id=loc1.id,
        destination_location_id=loc2.id,
        quantity=Decimal("7.000"),
    )
    db_session.add(item)
    db_session.commit()

    transfer_service.validate_transfer(transfer.id)

    # Verify breakdown: loc1 = 13, loc2 = 7
    qty_loc1 = stock_service.get_available_quantity(prod.id, loc1.id)
    qty_loc2 = stock_service.get_available_quantity(prod.id, loc2.id)
    assert qty_loc1 == Decimal("13.000")
    assert qty_loc2 == Decimal("7.000")

    # Verify invariant: total company stock is strictly preserved
    total_after = stock_service.get_total_stock_for_product(prod.id)
    assert total_after == Decimal("20.000")
    assert total_before == total_after


# ── TEST 5: Adjustment calculates correct difference ─────────────────────────
def test_05_adjustment_calculates_correct_difference(db_session: Session, setup_inventory):
    loc = setup_inventory["loc1"]
    prod = setup_inventory["prod1"]

    stock_service = StockService(db_session)
    adjustment_service = AdjustmentService(db_session)

    # Seed 100 units
    stock_service.increase_stock(prod.id, loc.id, Decimal("100.000"))
    db_session.commit()

    # Scenario 1: Physical count is 94 (-6 difference)
    adj_down = Adjustment(adjustment_number="ADJ-2026-001", reason="Cycle count loss", status="draft")
    db_session.add(adj_down)
    db_session.flush()

    item_down = AdjustmentItem(
        adjustment_id=adj_down.id,
        product_id=prod.id,
        location_id=loc.id,
        quantity_counted=Decimal("94.000"),
    )
    db_session.add(item_down)
    db_session.commit()

    adjustment_service.validate_adjustment(adj_down.id)
    assert stock_service.get_available_quantity(prod.id, loc.id) == Decimal("94.000")
    assert item_down.difference == Decimal("-6.000")

    # Scenario 2: Physical count is 107 (+13 difference)
    adj_up = Adjustment(adjustment_number="ADJ-2026-002", reason="Found goods", status="draft")
    db_session.add(adj_up)
    db_session.flush()

    item_up = AdjustmentItem(
        adjustment_id=adj_up.id,
        product_id=prod.id,
        location_id=loc.id,
        quantity_counted=Decimal("107.000"),
    )
    db_session.add(item_up)
    db_session.commit()

    adjustment_service.validate_adjustment(adj_up.id)
    assert stock_service.get_available_quantity(prod.id, loc.id) == Decimal("107.000")
    assert item_up.difference == Decimal("13.000")


# ── TEST 6: Duplicate transaction validation is rejected ─────────────────────
def test_06_duplicate_validation_rejected(db_session: Session, setup_inventory):
    loc = setup_inventory["loc1"]
    prod = setup_inventory["prod1"]

    receipt_service = ReceiptService(db_session)

    receipt = Receipt(receipt_number="REC-2026-DUP", status="draft")
    db_session.add(receipt)
    db_session.flush()

    item = ReceiptItem(
        receipt_id=receipt.id,
        product_id=prod.id,
        location_id=loc.id,
        quantity_expected=Decimal("10.000"),
    )
    db_session.add(item)
    db_session.commit()

    # First validation succeeds
    receipt_service.validate_receipt(receipt.id)

    # Second validation must raise DuplicateValidationError
    with pytest.raises(DuplicateValidationError):
        receipt_service.validate_receipt(receipt.id)


# ── TEST 7: Ledger entry is created ──────────────────────────────────────────
def test_07_ledger_entry_created(db_session: Session, setup_inventory):
    loc = setup_inventory["loc1"]
    prod = setup_inventory["prod1"]

    receipt_service = ReceiptService(db_session)
    ledger_service = LedgerService(db_session)

    receipt = Receipt(receipt_number="REC-2026-LEDGER", status="draft")
    db_session.add(receipt)
    db_session.flush()

    item = ReceiptItem(
        receipt_id=receipt.id,
        product_id=prod.id,
        location_id=loc.id,
        quantity_expected=Decimal("40.000"),
    )
    db_session.add(item)
    db_session.commit()

    receipt_service.validate_receipt(receipt.id)

    # Audit ledger
    history = ledger_service.get_product_ledger(prod.id)
    assert len(history) == 1
    entry = history[0]

    op = getattr(entry, "operation_type", None) or getattr(entry, "transaction_type", None)
    assert op == "RECEIPT"
    assert entry.quantity_change == Decimal("40.000")
    bal = getattr(entry, "balance_after", None) or getattr(entry, "quantity_after", None)
    assert bal == Decimal("40.000")


# ── TEST 8: Zero/negative quantity is rejected ───────────────────────────────
def test_08_zero_or_negative_quantity_rejected(db_session: Session, setup_inventory):
    loc = setup_inventory["loc1"]
    prod = setup_inventory["prod1"]

    stock_service = StockService(db_session)

    # Zero quantity
    with pytest.raises(InvalidQuantityError) as exc_zero:
        stock_service.increase_stock(prod.id, loc.id, Decimal("0.000"))
    assert "greater than zero" in str(exc_zero.value)

    # Negative quantity
    with pytest.raises(InvalidQuantityError) as exc_neg:
        stock_service.increase_stock(prod.id, loc.id, Decimal("-15.000"))
    assert "greater than zero" in str(exc_neg.value)


# ── TEST 9: Risk calculation handles zero demand ─────────────────────────────
def test_09_risk_calculation_handles_zero_demand(db_session: Session, setup_inventory):
    loc = setup_inventory["loc1"]
    prod = setup_inventory["prod1"]

    stock_service = StockService(db_session)
    risk_engine = RiskEngine(db_session)

    # Case 9a: Zero stock + zero demand => CRITICAL (Stockout)
    res_zero = risk_engine.assess_product_risk(prod.id)
    assert res_zero.risk_level == RISK_LEVEL_CRITICAL
    assert res_zero.current_stock == 0.0
    assert res_zero.average_daily_usage == 0.0

    # Case 9b: Stock on hand + zero demand => LOW (safe, no division by zero error)
    stock_service.increase_stock(prod.id, loc.id, Decimal("50.000"))
    db_session.commit()

    res_positive = risk_engine.assess_product_risk(prod.id)
    assert res_positive.risk_level == RISK_LEVEL_LOW
    assert res_positive.current_stock == 50.0
    assert res_positive.average_daily_usage == 0.0
    assert res_positive.days_of_cover == float("inf")
    assert "Risk is low" in res_positive.reason


# ── TEST 10: Reorder calculation works ───────────────────────────────────────
def test_10_reorder_calculation_works(db_session: Session, setup_inventory):
    loc = setup_inventory["loc1"]
    prod = setup_inventory["prod1"]

    reorder_engine = ReorderEngine(db_session)
    stock_service = StockService(db_session)

    # Set up reorder rule: min_quantity=20 (safety stock)
    rule = ReorderRule(
        product_id=prod.id,
        min_quantity=Decimal("20.000"),
        max_quantity=Decimal("100.000"),
        reorder_quantity=Decimal("50.000"),
    )
    db_session.add(rule)

    # Current stock = 5 units
    stock_service.increase_stock(prod.id, loc.id, Decimal("5.000"))
    db_session.commit()

    rec = reorder_engine.recommend_for_product(prod.id)

    # Since demand is 0, required_stock = safety_stock (20.0)
    # recommended_qty = 20.0 - 5.0 = 15.0 units
    assert rec.should_reorder is True
    assert rec.recommended_order_qty == 15.0
    assert rec.current_stock == 5.0
    assert rec.safety_stock == 20.0
    assert "should be reordered" in rec.reason or "Recommending" in rec.reason


# ── TEST 11: What-if simulation does not modify actual stock ─────────────────
def test_11_what_if_simulation_does_not_modify_stock(db_session: Session, setup_inventory):
    loc = setup_inventory["loc1"]
    prod = setup_inventory["prod1"]

    stock_service = StockService(db_session)
    what_if = WhatIfEngine()

    stock_service.increase_stock(prod.id, loc.id, Decimal("100.000"))
    db_session.commit()

    stock_before = stock_service.get_available_quantity(prod.id, loc.id)
    assert stock_before == Decimal("100.000")

    # Run in-memory simulation with 50% demand surge
    inputs = WhatIfInput(
        product_id=prod.id,
        product_name=prod.name,
        current_stock=100.0,
        average_daily_demand=10.0,
        safety_stock=20.0,
        incoming_stock=0.0,
        supplier_lead_time_days=5.0,
    )

    res = what_if.simulate_demand_increase(inputs, demand_increase_pct=50.0)

    # Check projection outputs
    assert res.projected_days_of_cover == pytest.approx(100.0 / 15.0, 0.01)
    assert res.shortage_estimate == pytest.approx(0.0)

    # Test lead time increase
    res_lead = what_if.simulate_lead_time_increase(inputs, extra_lead_time_days=10.0)
    # required = 10 * 15 + 20 = 170 => shortage = 170 - 100 = 70
    assert res_lead.shortage_estimate == 70.0
    assert res_lead.projected_risk_level == RISK_LEVEL_MEDIUM

    # CRITICAL: Verify production DB stock was NEVER touched
    stock_after = stock_service.get_available_quantity(prod.id, loc.id)
    assert stock_after == stock_before == Decimal("100.000")


# ── TEST 12: Anomaly detection identifies obvious abnormal movement ──────────
def test_12_anomaly_detection_identifies_abnormal_movement(db_session: Session, setup_inventory):
    loc = setup_inventory["loc1"]
    prod = setup_inventory["prod1"]

    ledger_service = LedgerService(db_session)
    anomaly_engine = AnomalyEngine(db_session)

    # Insert 10 normal adjustments with small differences
    for i in range(10):
        diff = Decimal("1.500") if i % 2 == 0 else Decimal("2.500")
        ledger_service.record_adjustment(
            product_id=prod.id,
            location_id=loc.id,
            difference=diff,
            qty_before=Decimal("100.000"),
            qty_after=Decimal("100.000") + diff,
            adjustment_id=1,
            reason="Normal variance",
        )

    # Insert one massive anomalous adjustment of +150 units
    ledger_service.record_adjustment(
        product_id=prod.id,
        location_id=loc.id,
        difference=Decimal("150.000"),
        qty_before=Decimal("102.000"),
        qty_after=Decimal("252.000"),
        adjustment_id=2,
        reason="Suspicious giant adjustment",
    )
    db_session.commit()

    # Detect anomalies
    anomalies = anomaly_engine.detect_large_adjustments(lookback_days=7)
    assert len(anomalies) >= 1

    flagged = anomalies[0]
    assert flagged.product_id == prod.id
    assert flagged.event_type == "LARGE_ADJUSTMENT"
    assert flagged.severity in ["CRITICAL", "HIGH"]
    assert "statistically unusual" in flagged.reason
    assert flagged.supporting_values["quantity_change"] == 150.0
