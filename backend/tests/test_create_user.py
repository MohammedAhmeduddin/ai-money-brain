"""
Test creating a user in the database
"""
import sys
from pathlib import Path

# Add backend to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

# Create database session
db = SessionLocal()

try:
    # Check if test user already exists
    existing_user = db.query(User).filter(User.email == "test@example.com").first()

    if existing_user:
        print(f"⚠️  User already exists: {existing_user.email}")
        print(f"   Deleting old user...")
        db.delete(existing_user)
        db.commit()

    # Create new test user
    test_user = User(
        email="test@example.com",
        name="Test User",
        hashed_password=get_password_hash("password123")
    )

    db.add(test_user)
    db.commit()
    db.refresh(test_user)

    print(f"\n✅ User created successfully!")
    print(f"   ID: {test_user.id}")
    print(f"   Email: {test_user.email}")
    print(f"   Name: {test_user.name}")
    print(f"   Created at: {test_user.created_at}")

    # Query it back to verify
    found_user = db.query(User).filter(User.email == "test@example.com").first()
    print(f"\n✅ User retrieved from database!")
    print(f"   Found: {found_user.name} ({found_user.email})")

    # Count total users
    total_users = db.query(User).count()
    print(f"\n📊 Total users in database: {total_users}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    db.rollback()
finally:
    db.close()
