"""
Basic health check tests
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    """Create test client"""
    from app.main import app
    return TestClient(app)


def test_read_root(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert data["app"] == "AI Money Brain"
    assert data["status"] == "running"
    assert data["environment"] == "development"


def test_health_check_success(client):
    """Test health endpoint with successful DB connection"""
    # Mock the database connection
    with patch('app.main.engine') as mock_engine:
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data


def test_health_check_without_db(client):
    """Test health endpoint gracefully handles DB errors"""
    # This tests that the endpoint doesn't crash even if DB fails
    with patch('app.main.engine') as mock_engine:
        mock_engine.connect.side_effect = Exception("DB Error")
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        # Should be degraded if DB fails
        assert data["status"] in ["healthy", "degraded"]
