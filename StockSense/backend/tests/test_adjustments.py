import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid
from app.services.stock import StockService

def get_unique_suffix():
    return str(uuid.uuid4())[:8]

def test_create_and_validate_adjustment(client: TestClient, admin_token_headers: dict, db: Session):
    suffix = get_unique_suffix()
    
    # setup master data
    cat_res = client.post("/api/v1/categories", headers=admin_token_headers, json={"name": f"Cat {suffix}", "code": f"C-{suffix}"})
    cat_id = cat_res.json()["id"]

    prod_res = client.post("/api/v1/products", headers=admin_token_headers, json={
        "name": f"Prod {suffix}", "sku": f"SKU-{suffix}", "category_id": cat_id, "cost_price": "10", "selling_price": "20"
    })
    prod_id = prod_res.json()["id"]

    wh_res = client.post("/api/v1/warehouses", headers=admin_token_headers, json={"name": f"WH {suffix}", "code": f"W-{suffix}"})
    wh_id = wh_res.json()["id"]
    loc_res = client.post("/api/v1/locations", headers=admin_token_headers, json={"warehouse_id": wh_id, "code": f"L-{suffix}", "name": "Loc"})
    loc_id = loc_res.json()["id"]

    # System stock = 100
    StockService.receive_stock(db, prod_id, loc_id, Decimal("100.000"))
    
    # Physical = 97
    adj_data = {
        "adjustment_number": f"ADJ-{suffix}",
        "reason": "Damage",
        "items": [
            {
                "product_id": prod_id,
                "location_id": loc_id,
                "quantity_counted": "97.000"
            }
        ]
    }
    
    # Create adjustment
    res = client.post("/api/v1/adjustments", headers=admin_token_headers, json=adj_data)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "draft"
    assert data["reason"] == "Damage"
    
    item = data["adjustment_items"][0]
    assert Decimal(item["quantity_before"]) == Decimal("100.000")
    assert Decimal(item["difference"]) == Decimal("-3.000")
    adj_id = data["id"]
    
    # Stock should still be 100 before validation
    assert StockService.get_available_stock(db, prod_id, loc_id) == Decimal("100.000")

    # Validate adjustment
    val_res = client.post(f"/api/v1/adjustments/{adj_id}/validate", headers=admin_token_headers)
    assert val_res.status_code == 200
    assert val_res.json()["status"] == "done"
    
    # Verify stock updated correctly
    assert StockService.get_available_stock(db, prod_id, loc_id) == Decimal("97.000")
    
    # Validate again should fail
    val_res2 = client.post(f"/api/v1/adjustments/{adj_id}/validate", headers=admin_token_headers)
    assert val_res2.status_code == 400

def test_positive_adjustment(client: TestClient, admin_token_headers: dict, db: Session):
    suffix = get_unique_suffix()
    
    cat_res = client.post("/api/v1/categories", headers=admin_token_headers, json={"name": f"Cat {suffix}", "code": f"C-{suffix}"})
    prod_res = client.post("/api/v1/products", headers=admin_token_headers, json={"name": f"P {suffix}", "sku": f"S-{suffix}", "category_id": cat_res.json()["id"]})
    wh_res = client.post("/api/v1/warehouses", headers=admin_token_headers, json={"name": f"W {suffix}", "code": f"W-{suffix}"})
    loc_res = client.post("/api/v1/locations", headers=admin_token_headers, json={"warehouse_id": wh_res.json()["id"], "code": f"L-{suffix}", "name": "Loc"})

    prod_id = prod_res.json()["id"]
    loc_id = loc_res.json()["id"]
    
    # Empty stock
    assert StockService.get_available_stock(db, prod_id, loc_id) == Decimal("0.000")

    # Found 5 items
    adj_data = {
        "adjustment_number": f"ADJ-{suffix}",
        "reason": "Found in warehouse",
        "items": [
            {"product_id": prod_id, "location_id": loc_id, "quantity_counted": "5.000"}
        ]
    }
    res = client.post("/api/v1/adjustments", headers=admin_token_headers, json=adj_data)
    adj_id = res.json()["id"]

    # Validate
    val_res = client.post(f"/api/v1/adjustments/{adj_id}/validate", headers=admin_token_headers)
    assert val_res.status_code == 200
    assert val_res.json()["status"] == "done"
    
    assert StockService.get_available_stock(db, prod_id, loc_id) == Decimal("5.000")
