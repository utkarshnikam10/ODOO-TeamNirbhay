import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid

def get_unique_suffix():
    return str(uuid.uuid4())[:8]

def test_product_search_and_filter(client: TestClient, admin_token_headers: dict, db: Session):
    suffix = get_unique_suffix()
    
    # Create categories
    cat1_res = client.post("/api/v1/categories", headers=admin_token_headers, json={"name": f"CatA {suffix}", "code": f"CA-{suffix}"})
    cat1_id = cat1_res.json()["id"]
    
    cat2_res = client.post("/api/v1/categories", headers=admin_token_headers, json={"name": f"CatB {suffix}", "code": f"CB-{suffix}"})
    cat2_id = cat2_res.json()["id"]

    # Create products
    p1 = client.post("/api/v1/products", headers=admin_token_headers, json={"name": f"Apple {suffix}", "sku": f"SKU-A-{suffix}", "category_id": cat1_id, "cost_price": "1"})
    p2 = client.post("/api/v1/products", headers=admin_token_headers, json={"name": f"Banana {suffix}", "sku": f"SKU-B-{suffix}", "category_id": cat2_id, "cost_price": "2"})
    p3 = client.post("/api/v1/products", headers=admin_token_headers, json={"name": f"Apricot {suffix}", "sku": f"SKU-C-{suffix}", "category_id": cat1_id, "cost_price": "3"})

    # Test Search by Name
    res = client.get(f"/api/v1/products?query=Apple", headers=admin_token_headers)
    assert res.status_code == 200
    assert any(p["name"] == f"Apple {suffix}" for p in res.json()["items"])
    assert not any(p["name"] == f"Banana {suffix}" for p in res.json()["items"])

    # Test Filter by Category
    res = client.get(f"/api/v1/products?category_id={cat1_id}", headers=admin_token_headers)
    assert res.status_code == 200
    names = [p["name"] for p in res.json()["items"]]
    assert f"Apple {suffix}" in names
    assert f"Apricot {suffix}" in names
    assert f"Banana {suffix}" not in names

    # Test Search + Filter
    res = client.get(f"/api/v1/products?query=Ap&category_id={cat1_id}", headers=admin_token_headers)
    assert res.status_code == 200
    names = [p["name"] for p in res.json()["items"]]
    assert f"Apple {suffix}" in names
    assert f"Apricot {suffix}" in names
    assert f"Banana {suffix}" not in names
