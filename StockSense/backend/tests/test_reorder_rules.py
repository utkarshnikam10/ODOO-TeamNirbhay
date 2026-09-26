import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid
from app.services.stock import StockService

def get_unique_suffix():
    return str(uuid.uuid4())[:8]

def test_reorder_rules_crud(client: TestClient, admin_token_headers: dict):
    suffix = get_unique_suffix()
    
    cat_res = client.post("/api/v1/categories", headers=admin_token_headers, json={"name": f"Cat {suffix}", "code": f"C-{suffix}"})
    prod_res = client.post("/api/v1/products", headers=admin_token_headers, json={"name": f"P {suffix}", "sku": f"S-{suffix}", "category_id": cat_res.json()["id"]})
    prod_id = prod_res.json()["id"]

    wh_res = client.post("/api/v1/warehouses", headers=admin_token_headers, json={"name": f"WH {suffix}", "code": f"W-{suffix}"})
    wh_id = wh_res.json()["id"]

    # Create Reorder Rule
    rule_data = {
        "product_id": prod_id,
        "warehouse_id": wh_id,
        "min_quantity": "10.000",
        "max_quantity": "100.000",
        "reorder_quantity": "50.000"
    }
    res = client.post("/api/v1/reorder-rules", headers=admin_token_headers, json=rule_data)
    assert res.status_code == 201
    rule_id = res.json()["id"]

    # Get Rules
    res = client.get("/api/v1/reorder-rules", headers=admin_token_headers)
    assert res.status_code == 200
    assert len(res.json()["items"]) >= 1

    # Update Rule
    res = client.put(f"/api/v1/reorder-rules/{rule_id}", headers=admin_token_headers, json={"min_quantity": "15.000"})
    assert res.status_code == 200
    assert Decimal(res.json()["min_quantity"]) == Decimal("15.000")

    # Delete Rule
    res = client.delete(f"/api/v1/reorder-rules/{rule_id}", headers=admin_token_headers)
    assert res.status_code == 204

def test_stock_alerts(client: TestClient, admin_token_headers: dict, db: Session):
    suffix = get_unique_suffix()
    
    cat_res = client.post("/api/v1/categories", headers=admin_token_headers, json={"name": f"Cat {suffix}", "code": f"C-{suffix}"})
    prod_res = client.post("/api/v1/products", headers=admin_token_headers, json={"name": f"P {suffix}", "sku": f"S-{suffix}", "category_id": cat_res.json()["id"]})
    wh_res = client.post("/api/v1/warehouses", headers=admin_token_headers, json={"name": f"W {suffix}", "code": f"W-{suffix}"})
    loc_res = client.post("/api/v1/locations", headers=admin_token_headers, json={"warehouse_id": wh_res.json()["id"], "code": f"L-{suffix}", "name": "Loc"})

    prod_id = prod_res.json()["id"]
    loc_id = loc_res.json()["id"]
    wh_id = wh_res.json()["id"]

    # Create rule (min_quantity = 20)
    client.post("/api/v1/reorder-rules", headers=admin_token_headers, json={
        "product_id": prod_id, "warehouse_id": wh_id, "min_quantity": "20.000", "max_quantity": "100.000", "reorder_quantity": "50.000"
    })

    # Let's adjust stock to 0
    # Or just empty stock => out_of_stock
    # Let's check out-of-stock, wait, empty stock isn't in DB yet unless we adjust or receive then issue.
    StockService.receive_stock(db, prod_id, loc_id, Decimal("10.000"))
    StockService.issue_stock(db, prod_id, loc_id, Decimal("10.000"))
    
    res = client.get("/api/v1/stock/out-of-stock", headers=admin_token_headers)
    assert res.status_code == 200
    out_of_stock_prods = [item["product_id"] for item in res.json()]
    assert prod_id in out_of_stock_prods

    # Increase stock to 15 (which is <= 20 and > 0 => LOW_STOCK)
    StockService.receive_stock(db, prod_id, loc_id, Decimal("15.000"))
    
    res = client.get("/api/v1/stock/low-stock", headers=admin_token_headers)
    assert res.status_code == 200
    low_stock_prods = [item["product_id"] for item in res.json()]
    assert prod_id in low_stock_prods

    # Increase stock to 25 (which is > 20 => normal stock)
    StockService.receive_stock(db, prod_id, loc_id, Decimal("10.000"))
    
    res = client.get("/api/v1/stock/low-stock", headers=admin_token_headers)
    assert res.status_code == 200
    low_stock_prods_now = [item["product_id"] for item in res.json()]
    assert prod_id not in low_stock_prods_now
