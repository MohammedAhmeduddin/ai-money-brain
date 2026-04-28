"""
Basic API tests
"""
from fastapi.testclient import TestClient


def test_read_root():
    """Test root endpoint"""
    from app.main import app
    client = TestClient(app)
    
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert "status" in data
    assert data["status"] == "running"


def test_openapi_docs():
    """Test that API docs are accessible"""
    from app.main import app
    client = TestClient(app)
    
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_json():
    """Test that OpenAPI schema is available"""
    from app.main import app
    client = TestClient(app)
    
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "info" in data
    assert "paths" in data
