import pytest
from fastapi.testclient import TestClient
import uuid

def get_unique_suffix():
    return str(uuid.uuid4())[:8]

def test_create_category(client: TestClient, admin_token_headers: dict):
    suffix = get_unique_suffix()
    response = client.post(
        "/api/v1/categories",
        headers=admin_token_headers,
        json={"name": f"Test Category {suffix}", "code": f"CAT-{suffix}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == f"Test Category {suffix}"
    assert data["code"] == f"CAT-{suffix}"

def test_get_categories(client: TestClient, normal_user_token_headers: dict):
    response = client.get("/api/v1/categories", headers=normal_user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data

def test_create_product(client: TestClient, admin_token_headers: dict):
    suffix = get_unique_suffix()
    
    # create category first
    cat_response = client.post(
        "/api/v1/categories",
        headers=admin_token_headers,
        json={"name": f"Prod Cat {suffix}", "code": f"PC-{suffix}"},
    )
    cat_id = cat_response.json()["id"]

    response = client.post(
        "/api/v1/products",
        headers=admin_token_headers,
        json={
            "name": f"Test Product {suffix}",
            "sku": f"SKU-{suffix}",
            "category_id": cat_id,
            "cost_price": "10.00",
            "selling_price": "20.00",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["sku"] == f"SKU-{suffix}"

def test_search_products(client: TestClient, admin_token_headers: dict, normal_user_token_headers: dict):
    suffix = get_unique_suffix()
    client.post(
        "/api/v1/products",
        headers=admin_token_headers,
        json={"name": f"Searchable {suffix}", "sku": f"SEARCH-{suffix}", "cost_price": "0", "selling_price": "0"},
    )
    
    response = client.get(f"/api/v1/products?query={suffix}", headers=normal_user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(p["sku"] == f"SEARCH-{suffix}" for p in data["items"])

def test_create_warehouse(client: TestClient, admin_token_headers: dict):
    suffix = get_unique_suffix()
    response = client.post(
        "/api/v1/warehouses",
        headers=admin_token_headers,
        json={"name": f"Warehouse {suffix}", "code": f"WH-{suffix}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == f"Warehouse {suffix}"

def test_create_location(client: TestClient, admin_token_headers: dict):
    suffix = get_unique_suffix()
    wh_response = client.post(
        "/api/v1/warehouses",
        headers=admin_token_headers,
        json={"name": f"Loc WH {suffix}", "code": f"LWH-{suffix}"},
    )
    wh_id = wh_response.json()["id"]

    response = client.post(
        "/api/v1/locations",
        headers=admin_token_headers,
        json={"warehouse_id": wh_id, "code": f"LOC-{suffix}", "name": f"Location {suffix}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == f"LOC-{suffix}"
