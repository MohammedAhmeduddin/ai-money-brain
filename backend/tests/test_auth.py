"""
Test authentication endpoints (basic smoke tests).
For comprehensive auth tests, see tests/integration/test_auth_api.py
"""


def test_register_user(client, test_user_data):
    """Register a new user successfully."""
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert "id" in data
    assert "password" not in data
    assert "hashed_password" not in data


def test_register_duplicate_user(client, test_user_data, registered_user):
    """Registering the same email twice should fail."""
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 400


def test_login_invalid_credentials(client):
    """Login with non-existent user returns 401."""
    response = client.post("/api/v1/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


def test_login_valid_credentials(client, test_user_data, registered_user):
    """Login with correct credentials returns JWT token."""
    response = client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"],
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
