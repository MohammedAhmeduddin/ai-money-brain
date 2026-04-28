"""
Rule model for automated alerts
"""
from sqlalchemy import Column, String, DateTime, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Rule(Base):
    __tablename__ = "rules"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    condition_type = Column(String, nullable=False)  # e.g., "category_budget", "anomaly"
    category = Column(String)
    threshold_amount = Column(Numeric(10, 2))
    action_type = Column(String)  # e.g., "send_alert", "notify"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="rules")
    alerts = relationship("Alert", back_populates="rule", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Rule {self.name} ({'active' if self.is_active else 'inactive'})>"
