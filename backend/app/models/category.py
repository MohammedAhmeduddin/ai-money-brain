"""
Category model
"""
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Category(Base):
    __tablename__ = "categories"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    monthly_budget = Column(Numeric(10, 2), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="categories")

    # Unique constraint: user can't have duplicate category names
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='uq_user_category'),
    )

    def __repr__(self):
        return f"<Category {self.name}>"
