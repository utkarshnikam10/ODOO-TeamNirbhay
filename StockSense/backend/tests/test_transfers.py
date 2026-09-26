import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid
from app.services.stock import StockService

def get_unique_suffix():
    return str(uuid.uuid4())[:8]

def test_create_and_validate_transfer(client: TestClient, admin_token_headers: dict, db: Session):
    suffix = get_unique_suffix()
    
    # setup master data
    cat_res = client.post("/api/v1/categories", headers=admin_token_headers, json={"name": f"Cat {suffix}", "code": f"C-{suffix}"})
    cat_id = cat_res.json()["id"]

    prod_res = client.post("/api/v1/products", headers=admin_token_headers, json={
        "name": f"Prod {suffix}", "sku": f"SKU-{suffix}", "category_id": cat_id, "cost_price": "10", "selling_price": "20"
    })
    prod_id = prod_res.json()["id"]

    wh1_res = client.post("/api/v1/warehouses", headers=admin_token_headers, json={"name": f"WH1 {suffix}", "code": f"W1-{suffix}"})
    wh1_id = wh1_res.json()["id"]
    loc1_res = client.post("/api/v1/locations", headers=admin_token_headers, json={"warehouse_id": wh1_id, "code": f"L1-{suffix}", "name": "Loc1"})
    loc1_id = loc1_res.json()["id"]

    wh2_res = client.post("/api/v1/warehouses", headers=admin_token_headers, json={"name": f"WH2 {suffix}", "code": f"W2-{suffix}"})
    wh2_id = wh2_res.json()["id"]
    loc2_res = client.post("/api/v1/locations", headers=admin_token_headers, json={"warehouse_id": wh2_id, "code": f"L2-{suffix}", "name": "Loc2"})
    loc2_id = loc2_res.json()["id"]

    # manually inject stock to source
    StockService.receive_stock(db, prod_id, loc1_id, Decimal("100.000"))
    
    transfer_data = {
        "transfer_number": f"TRF-{suffix}",
        "source_warehouse_id": wh1_id,
        "destination_warehouse_id": wh2_id,
        "items": [
            {
                "product_id": prod_id,
                "source_location_id": loc1_id,
                "destination_location_id": loc2_id,
                "quantity": "20.000"
            }
        ]
    }
    
    # Create transfer
    res = client.post("/api/v1/transfers", headers=admin_token_headers, json=transfer_data)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "draft"
    transfer_id = data["id"]
    
    # Stock should still be 100 before validation at loc1, 0 at loc2
    assert StockService.get_available_stock(db, prod_id, loc1_id) == Decimal("100.000")
    assert StockService.get_available_stock(db, prod_id, loc2_id) == Decimal("0.000")

    # Validate transfer
    val_res = client.post(f"/api/v1/transfers/{transfer_id}/validate", headers=admin_token_headers)
    assert val_res.status_code == 200
    assert val_res.json()["status"] == "done"
    
    # Verify stock updated correctly (Total unchanged, shifted)
    assert StockService.get_available_stock(db, prod_id, loc1_id) == Decimal("80.000")
    assert StockService.get_available_stock(db, prod_id, loc2_id) == Decimal("20.000")
    
    # Validate again should fail
    val_res2 = client.post(f"/api/v1/transfers/{transfer_id}/validate", headers=admin_token_headers)
    assert val_res2.status_code == 400

def test_validate_transfer_insufficient_stock(client: TestClient, admin_token_headers: dict, db: Session):
    suffix = get_unique_suffix()
    
    cat_res = client.post("/api/v1/categories", headers=admin_token_headers, json={"name": f"Cat {suffix}", "code": f"C-{suffix}"})
    prod_res = client.post("/api/v1/products", headers=admin_token_headers, json={"name": f"P {suffix}", "sku": f"S-{suffix}", "category_id": cat_res.json()["id"]})
    
    wh1_res = client.post("/api/v1/warehouses", headers=admin_token_headers, json={"name": f"W1 {suffix}", "code": f"W1-{suffix}"})
    loc1_res = client.post("/api/v1/locations", headers=admin_token_headers, json={"warehouse_id": wh1_res.json()["id"], "code": f"L1-{suffix}", "name": "Loc1"})
    
    wh2_res = client.post("/api/v1/warehouses", headers=admin_token_headers, json={"name": f"W2 {suffix}", "code": f"W2-{suffix}"})
    loc2_res = client.post("/api/v1/locations", headers=admin_token_headers, json={"warehouse_id": wh2_res.json()["id"], "code": f"L2-{suffix}", "name": "Loc2"})

    prod_id = prod_res.json()["id"]
    loc1_id = loc1_res.json()["id"]
    loc2_id = loc2_res.json()["id"]
    wh1_id = wh1_res.json()["id"]
    wh2_id = wh2_res.json()["id"]
    
    # Receive only 10 stock
    StockService.receive_stock(db, prod_id, loc1_id, Decimal("10.000"))

    transfer_data = {
        "transfer_number": f"TRF-{suffix}",
        "source_warehouse_id": wh1_id,
        "destination_warehouse_id": wh2_id,
        "items": [
            {"product_id": prod_id, "source_location_id": loc1_id, "destination_location_id": loc2_id, "quantity": "20.000"}
        ]
    }
    res = client.post("/api/v1/transfers", headers=admin_token_headers, json=transfer_data)
    transfer_id = res.json()["id"]

    # Validate should fail due to insufficient stock at source
    val_res = client.post(f"/api/v1/transfers/{transfer_id}/validate", headers=admin_token_headers)
    assert val_res.status_code == 400
    assert "Insufficient stock" in val_res.json()["detail"]

def test_transfer_same_location(client: TestClient, admin_token_headers: dict):
    suffix = get_unique_suffix()
    cat_res = client.post("/api/v1/categories", headers=admin_token_headers, json={"name": f"Cat {suffix}", "code": f"C-{suffix}"})
    prod_res = client.post("/api/v1/products", headers=admin_token_headers, json={"name": f"P {suffix}", "sku": f"S-{suffix}", "category_id": cat_res.json()["id"]})
    wh_res = client.post("/api/v1/warehouses", headers=admin_token_headers, json={"name": f"W {suffix}", "code": f"W-{suffix}"})
    loc_res = client.post("/api/v1/locations", headers=admin_token_headers, json={"warehouse_id": wh_res.json()["id"], "code": f"L-{suffix}", "name": "Loc"})

    transfer_data = {
        "transfer_number": f"TRF-{suffix}",
        "source_warehouse_id": wh_res.json()["id"],
        "destination_warehouse_id": wh_res.json()["id"],
        "items": [
            {"product_id": prod_res.json()["id"], "source_location_id": loc_res.json()["id"], "destination_location_id": loc_res.json()["id"], "quantity": "5.000"}
        ]
    }
    res = client.post("/api/v1/transfers", headers=admin_token_headers, json=transfer_data)
    assert res.status_code == 400
    assert "same" in res.json()["detail"].lower()
