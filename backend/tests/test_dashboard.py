import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid
from app.services.stock import StockService

def get_unique_suffix():
    return str(uuid.uuid4())[:8]

def test_dashboard_apis(client: TestClient, admin_token_headers: dict, db: Session):
    suffix = get_unique_suffix()
    
    # Pre-setup data
    cat_res = client.post("/api/v1/categories", headers=admin_token_headers, json={"name": f"Cat {suffix}", "code": f"C-{suffix}"})
    prod_res = client.post("/api/v1/products", headers=admin_token_headers, json={"name": f"P {suffix}", "sku": f"S-{suffix}", "category_id": cat_res.json()["id"], "cost_price": "10.00"})
    wh_res = client.post("/api/v1/warehouses", headers=admin_token_headers, json={"name": f"W {suffix}", "code": f"W-{suffix}"})
    loc_res = client.post("/api/v1/locations", headers=admin_token_headers, json={"warehouse_id": wh_res.json()["id"], "code": f"L-{suffix}", "name": "Loc"})

    prod_id = prod_res.json()["id"]
    loc_id = loc_res.json()["id"]

    # 1 out of stock item (add 0 quantity explicitly to Stock via receive/issue logic)
    StockService.receive_stock(db, prod_id, loc_id, Decimal("5.000"))
    StockService.issue_stock(db, prod_id, loc_id, Decimal("5.000"))

    # Add pending receipt
    res_rec = client.post("/api/v1/receipts", headers=admin_token_headers, json={
        "receipt_number": f"REC-{suffix}", "supplier_name": "Sup",
        "items": [{"product_id": prod_id, "location_id": loc_id, "quantity_expected": "10"}]
    })
    assert res_rec.status_code == 201

    # Add pending delivery
    res_del = client.post("/api/v1/deliveries", headers=admin_token_headers, json={
        "delivery_number": f"DEL-{suffix}", "customer_name": "Cus",
        "items": [{"product_id": prod_id, "location_id": loc_id, "quantity_ordered": "5"}]
    })
    assert res_del.status_code == 201
    
    res = client.get("/api/v1/dashboard/summary", headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["out_of_stock_items"] >= 1
    assert data["pending_receipts"] >= 1
    assert data["pending_deliveries"] >= 1
    
    res_stock = client.get("/api/v1/dashboard/stock-summary", headers=admin_token_headers)
    assert res_stock.status_code == 200
    assert "total_stock_value" in res_stock.json()
    
    res_mov = client.get("/api/v1/dashboard/recent-movements?limit=5", headers=admin_token_headers)
    assert res_mov.status_code == 200
    assert len(res_mov.json()) >= 1
