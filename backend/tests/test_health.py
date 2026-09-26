from fastapi.testclient import TestClient


def test_health_check_endpoint(client: TestClient) -> None:
    """Test root-level GET /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "StockSense" in data["app_name"]
    assert "environment" in data
    assert data["version"] == "1.0.0"


def test_api_v1_health_check_endpoint(client: TestClient) -> None:
    """Test versioned GET /api/v1/health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_root_endpoint(client: TestClient) -> None:
    """Test root GET / entrypoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "StockSense" in data["message"]
    assert data["health"] == "/health"
