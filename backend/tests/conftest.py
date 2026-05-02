"""
Shared pytest fixtures for all tests.
"""
import os
import sys
from pathlib import Path

# Set test environment BEFORE importing app
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
os.environ["OPENAI_API_KEY"] = "sk-test-fake-key"
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "False"

# Add backend/ to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base
from app.api.deps import get_db


# ─── In-memory SQLite for fast, isolated tests ────────────────────────────
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ─── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def db_session():
    """Fresh in-memory database for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Test client with overridden DB dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Sample user registration data."""
    return {
        "email": "test@example.com",
        "name": "Test User",
        "password": "testpassword123",
    }


@pytest.fixture
def registered_user(client, test_user_data):
    """Register a user and return the response data."""
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code in (200, 201), f"Registration failed: {response.text}"
    return response.json()


@pytest.fixture
def auth_token(client, test_user_data, registered_user):
    """Get JWT token for an authenticated user."""
    response = client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"],
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Authorization header dict."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def fixtures_dir():
    """Path to test fixtures (sample CSVs, etc)."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_chase_csv():
    """Inline Chase CSV for upload tests."""
    return """Transaction Date,Post Date,Description,Category,Type,Amount,Memo
01/15/2024,01/16/2024,STARBUCKS STORE 12345,Food & Drink,Sale,-5.67,
01/20/2024,01/21/2024,WHOLE FOODS MKT,Groceries,Sale,-67.89,
01/22/2024,01/23/2024,UBER TRIP,Transportation,Sale,-18.50,
01/28/2024,01/29/2024,DIRECT DEPOSIT,Income,ACH,2500.00,Payroll
02/01/2024,02/02/2024,RENT PAYMENT,Bills,ACH,-1200.00,
02/05/2024,02/06/2024,SHELL OIL,Gas,Sale,-45.00,
02/12/2024,02/13/2024,GYM MEMBERSHIP,Health,Sale,-40.00,
"""
