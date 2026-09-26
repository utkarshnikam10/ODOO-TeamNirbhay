import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid

def get_unique_suffix():
    return str(uuid.uuid4())[:8]

def test_create_receipt(client: TestClient, admin_token_headers: dict, db: Session):
    suffix = get_unique_suffix()
    
    # create category
    cat_res = client.post("/api/v1/categories", headers=admin_token_headers, json={"name": f"Cat {suffix}", "code": f"C-{suffix}"})
    cat_id = cat_res.json()["id"]

    # create product
    prod_res = client.post("/api/v1/products", headers=admin_token_headers, json={
        "name": f"Prod {suffix}", "sku": f"SKU-{suffix}", "category_id": cat_id, "cost_price": "10", "selling_price": "20"
    })
    prod_id = prod_res.json()["id"]

    # create warehouse & location
    wh_res = client.post("/api/v1/warehouses", headers=admin_token_headers, json={"name": f"WH {suffix}", "code": f"W-{suffix}"})
    wh_id = wh_res.json()["id"]
    loc_res = client.post("/api/v1/locations", headers=admin_token_headers, json={"warehouse_id": wh_id, "code": f"L-{suffix}", "name": "Loc"})
    loc_id = loc_res.json()["id"]

    receipt_data = {
        "receipt_number": f"REC-{suffix}",
        "supplier_name": "Supplier Inc",
        "items": [
            {
                "product_id": prod_id,
                "location_id": loc_id,
                "quantity_expected": "100.000",
                "unit_cost": "10.00"
            }
        ]
    }
    
    # Create receipt
    res = client.post("/api/v1/receipts", headers=admin_token_headers, json=receipt_data)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "draft"
    assert len(data["receipt_items"]) == 1
    receipt_id = data["id"]
    
    # Verify stock has not changed yet
    from app.services.stock import StockService
    assert StockService.get_available_stock(db, prod_id, loc_id) == Decimal("0.000")

    # Validate receipt
    val_res = client.post(f"/api/v1/receipts/{receipt_id}/validate", headers=admin_token_headers)
    assert val_res.status_code == 200
    assert val_res.json()["status"] == "done"
    
    # Verify stock increased
    assert StockService.get_available_stock(db, prod_id, loc_id) == Decimal("100.000")
    
    # Validate again should fail
    val_res2 = client.post(f"/api/v1/receipts/{receipt_id}/validate", headers=admin_token_headers)
    assert val_res2.status_code == 400
    assert "already completed" in val_res2.json()["detail"]

    # Cancel should fail since it's done
    can_res = client.post(f"/api/v1/receipts/{receipt_id}/cancel", headers=admin_token_headers)
    assert can_res.status_code == 400

def test_cancel_receipt(client: TestClient, admin_token_headers: dict):
    suffix = get_unique_suffix()
    cat_res = client.post("/api/v1/categories", headers=admin_token_headers, json={"name": f"Cat {suffix}", "code": f"C-{suffix}"})
    prod_res = client.post("/api/v1/products", headers=admin_token_headers, json={"name": f"P {suffix}", "sku": f"S-{suffix}", "category_id": cat_res.json()["id"]})
    wh_res = client.post("/api/v1/warehouses", headers=admin_token_headers, json={"name": f"W {suffix}", "code": f"W-{suffix}"})
    loc_res = client.post("/api/v1/locations", headers=admin_token_headers, json={"warehouse_id": wh_res.json()["id"], "code": f"L-{suffix}", "name": "Loc"})

    receipt_data = {
        "receipt_number": f"REC-{suffix}",
        "items": [
            {"product_id": prod_res.json()["id"], "location_id": loc_res.json()["id"], "quantity_expected": "50.000"}
        ]
    }
    res = client.post("/api/v1/receipts", headers=admin_token_headers, json=receipt_data)
    receipt_id = res.json()["id"]

    # Cancel
    can_res = client.post(f"/api/v1/receipts/{receipt_id}/cancel", headers=admin_token_headers)
    assert can_res.status_code == 200
    assert can_res.json()["status"] == "canceled"

    # Validate canceled should fail
    val_res = client.post(f"/api/v1/receipts/{receipt_id}/validate", headers=admin_token_headers)
    assert val_res.status_code == 400
    assert "canceled" in val_res.json()["detail"].lower()
