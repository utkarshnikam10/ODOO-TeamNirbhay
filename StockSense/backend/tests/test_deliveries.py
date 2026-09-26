import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid
from app.services.stock import StockService

def get_unique_suffix():
    return str(uuid.uuid4())[:8]

def test_create_and_validate_delivery(client: TestClient, admin_token_headers: dict, db: Session):
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

    # manually inject stock to satisfy validation
    StockService.receive_stock(db, prod_id, loc_id, Decimal("100.000"))
    
    delivery_data = {
        "delivery_number": f"DEL-{suffix}",
        "customer_name": "Customer Inc",
        "items": [
            {
                "product_id": prod_id,
                "location_id": loc_id,
                "quantity_ordered": "20.000",
                "unit_price": "20.00"
            }
        ]
    }
    
    # Create delivery
    res = client.post("/api/v1/deliveries", headers=admin_token_headers, json=delivery_data)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "draft"
    delivery_id = data["id"]
    
    # Stock should still be 100 before validation
    assert StockService.get_available_stock(db, prod_id, loc_id) == Decimal("100.000")

    # Validate delivery
    val_res = client.post(f"/api/v1/deliveries/{delivery_id}/validate", headers=admin_token_headers)
    assert val_res.status_code == 200
    assert val_res.json()["status"] == "done"
    
    # Verify stock reduced
    assert StockService.get_available_stock(db, prod_id, loc_id) == Decimal("80.000")
    
    # Validate again should fail
    val_res2 = client.post(f"/api/v1/deliveries/{delivery_id}/validate", headers=admin_token_headers)
    assert val_res2.status_code == 400

def test_validate_delivery_insufficient_stock(client: TestClient, admin_token_headers: dict, db: Session):
    suffix = get_unique_suffix()
    
    cat_res = client.post("/api/v1/categories", headers=admin_token_headers, json={"name": f"Cat {suffix}", "code": f"C-{suffix}"})
    prod_res = client.post("/api/v1/products", headers=admin_token_headers, json={"name": f"P {suffix}", "sku": f"S-{suffix}", "category_id": cat_res.json()["id"]})
    wh_res = client.post("/api/v1/warehouses", headers=admin_token_headers, json={"name": f"W {suffix}", "code": f"W-{suffix}"})
    loc_res = client.post("/api/v1/locations", headers=admin_token_headers, json={"warehouse_id": wh_res.json()["id"], "code": f"L-{suffix}", "name": "Loc"})

    prod_id = prod_res.json()["id"]
    loc_id = loc_res.json()["id"]
    
    # receive only 10 stock
    StockService.receive_stock(db, prod_id, loc_id, Decimal("10.000"))

    delivery_data = {
        "delivery_number": f"DEL-{suffix}",
        "items": [
            {"product_id": prod_id, "location_id": loc_id, "quantity_ordered": "20.000"}
        ]
    }
    res = client.post("/api/v1/deliveries", headers=admin_token_headers, json=delivery_data)
    delivery_id = res.json()["id"]

    # Validate should fail
    val_res = client.post(f"/api/v1/deliveries/{delivery_id}/validate", headers=admin_token_headers)
    assert val_res.status_code == 400
    assert "Insufficient stock" in val_res.json()["detail"]

def test_cancel_delivery(client: TestClient, admin_token_headers: dict):
    suffix = get_unique_suffix()
    cat_res = client.post("/api/v1/categories", headers=admin_token_headers, json={"name": f"Cat {suffix}", "code": f"C-{suffix}"})
    prod_res = client.post("/api/v1/products", headers=admin_token_headers, json={"name": f"P {suffix}", "sku": f"S-{suffix}", "category_id": cat_res.json()["id"]})
    wh_res = client.post("/api/v1/warehouses", headers=admin_token_headers, json={"name": f"W {suffix}", "code": f"W-{suffix}"})
    loc_res = client.post("/api/v1/locations", headers=admin_token_headers, json={"warehouse_id": wh_res.json()["id"], "code": f"L-{suffix}", "name": "Loc"})

    delivery_data = {
        "delivery_number": f"DEL-{suffix}",
        "items": [
            {"product_id": prod_res.json()["id"], "location_id": loc_res.json()["id"], "quantity_ordered": "5.000"}
        ]
    }
    res = client.post("/api/v1/deliveries", headers=admin_token_headers, json=delivery_data)
    delivery_id = res.json()["id"]

    # Cancel
    can_res = client.post(f"/api/v1/deliveries/{delivery_id}/cancel", headers=admin_token_headers)
    assert can_res.status_code == 200
    assert can_res.json()["status"] == "canceled"

    # Validate canceled should fail
    val_res = client.post(f"/api/v1/deliveries/{delivery_id}/validate", headers=admin_token_headers)
    assert val_res.status_code == 400
    assert "canceled" in val_res.json()["detail"].lower()
