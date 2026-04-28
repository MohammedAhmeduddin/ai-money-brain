"""
Authentication service
"""
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional

from app.models.user import User
from app.schemas.user import UserCreate, Token
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
)
from app.core.config import settings


class AuthService:
    """Handle authentication logic"""

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """Create a new user"""
        # Hash the password
        hashed_password = get_password_hash(user_data.password)

        # Create user instance
        db_user = User(
            email=user_data.email,
            name=user_data.name,
            hashed_password=hashed_password
        )

        # Save to database
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return db_user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = AuthService.get_user_by_email(db, email)

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user

    @staticmethod
    def create_token_for_user(user: User) -> Token:
        """Create JWT token for user"""
        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

        access_token = create_access_token(
            data={"sub": user.id, "email": user.email},
            expires_delta=access_token_expires
        )

        return Token(access_token=access_token)
