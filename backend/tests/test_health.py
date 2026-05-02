"""
Test app health and basic endpoints.
"""


def test_root_endpoint(client):
    """Root endpoint returns app status and metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "app" in data
    assert "version" in data
    assert "environment" in data
    assert data["docs"] == "/docs"


def test_health_endpoint(client):
    """Health endpoint returns system status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "database" in data
    assert "ai_service" in data
    assert "version" in data


def test_health_reports_version(client):
    """Health endpoint reports correct version."""
    response = client.get("/health")
    data = response.json()
    assert data["version"] == "0.3.0"


def test_openapi_docs(client):
    """Swagger UI is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower() or "openapi" in response.text.lower()


def test_openapi_redoc(client):
    """ReDoc UI is accessible."""
    response = client.get("/redoc")
    assert response.status_code == 200


def test_openapi_schema(client):
    """OpenAPI JSON schema is valid."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "info" in data
    assert "paths" in data
    assert data["info"]["version"] == "0.3.0"


def test_openapi_schema_has_auth_routes(client):
    """OpenAPI schema includes authentication endpoints."""
    response = client.get("/openapi.json")
    paths = response.json()["paths"]
    assert "/api/v1/auth/register" in paths
    assert "/api/v1/auth/login" in paths


def test_openapi_schema_has_dashboard_routes(client):
    """OpenAPI schema includes v0.3.0 dashboard endpoints."""
    response = client.get("/openapi.json")
    paths = response.json()["paths"]
    # At least one dashboard endpoint must exist
    dashboard_routes = [p for p in paths if "/dashboard" in p]
    assert len(dashboard_routes) > 0, "No dashboard routes found in OpenAPI schema"

def test_multi_bank_endpoint_with_no_fixtures(client, monkeypatch, tmp_path):
    """Trigger the 'fixtures not found' branch in main.py."""
    import os
    # Save original cwd
    original_cwd = os.getcwd()
    try:
        # Change to a directory without fixtures
        os.chdir(tmp_path)
        response = client.get("/test-multi-bank")
        # Should return either error or successful response
        assert response.status_code == 200
        data = response.json()
        # Either has results or error key
        assert "results" in data or "error" in data
    finally:
        os.chdir(original_cwd)


def test_health_endpoint_in_test_mode(client):
    """Verify health endpoint detects SQLite test mode."""
    response = client.get("/health")
    data = response.json()
    # In test mode, database should report 'skipped' or 'connected'
    assert "skipped" in data["database"] or "connected" in data["database"]


def test_health_ai_status(client):
    """Verify AI status reporting."""
    response = client.get("/health")
    data = response.json()
    assert data["ai_service"] in ("configured", "not configured")
