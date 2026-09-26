import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid
from app.services.stock import StockService

def get_unique_suffix():
    return str(uuid.uuid4())[:8]

def test_stock_and_ledger_history(client: TestClient, admin_token_headers: dict, db: Session):
    suffix = get_unique_suffix()
    
    cat_res = client.post("/api/v1/categories", headers=admin_token_headers, json={"name": f"Cat {suffix}", "code": f"C-{suffix}"})
    prod_res = client.post("/api/v1/products", headers=admin_token_headers, json={"name": f"P {suffix}", "sku": f"S-{suffix}", "category_id": cat_res.json()["id"]})
    wh_res = client.post("/api/v1/warehouses", headers=admin_token_headers, json={"name": f"W {suffix}", "code": f"W-{suffix}"})
    loc_res = client.post("/api/v1/locations", headers=admin_token_headers, json={"warehouse_id": wh_res.json()["id"], "code": f"L-{suffix}", "name": "Loc"})

    prod_id = prod_res.json()["id"]
    loc_id = loc_res.json()["id"]
    
    # Receive stock to generate ledger entries
    StockService.receive_stock(db, prod_id, loc_id, Decimal("100.000"), reference_number="REC-TEST-123")
    StockService.issue_stock(db, prod_id, loc_id, Decimal("20.000"), reference_number="DEL-TEST-123")
    
    # Test GET /stock
    res = client.get("/api/v1/stock", headers=admin_token_headers)
    assert res.status_code == 200
    assert "items" in res.json()
    
    # Test GET /stock/product/{id}
    res = client.get(f"/api/v1/stock/product/{prod_id}", headers=admin_token_headers)
    assert res.status_code == 200
    assert len(res.json()["items"]) >= 1
    
    # Test GET /stock/location/{id}
    res = client.get(f"/api/v1/stock/location/{loc_id}", headers=admin_token_headers)
    assert res.status_code == 200
    assert len(res.json()["items"]) >= 1
    stock_id = res.json()["items"][0]["id"]
    
    # Test GET /stock/{id}
    res = client.get(f"/api/v1/stock/{stock_id}", headers=admin_token_headers)
    assert res.status_code == 200
    
    # Test GET /ledger
    res = client.get(f"/api/v1/ledger?product_id={prod_id}", headers=admin_token_headers)
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) >= 2 # 1 receipt, 1 delivery
    ledger_id = items[0]["id"]
    
    # Test GET /ledger filters
    res = client.get(f"/api/v1/ledger?operation_type=RECEIPT&product_id={prod_id}", headers=admin_token_headers)
    assert res.status_code == 200
    assert all(item["operation_type"] == "RECEIPT" for item in res.json()["items"])
    
    # Test GET /ledger/{id}
    res = client.get(f"/api/v1/ledger/{ledger_id}", headers=admin_token_headers)
    assert res.status_code == 200
