"""
Alert model
"""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.db.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class AlertStatusEnum(str, enum.Enum):
    UNREAD = "unread"
    READ = "read"
    DISMISSED = "dismissed"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rule_id = Column(String, ForeignKey("rules.id", ondelete="CASCADE"))
    message = Column(Text, nullable=False)
    status = Column(Enum(AlertStatusEnum), default=AlertStatusEnum.UNREAD)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="alerts")
    rule = relationship("Rule", back_populates="alerts")

    # Index for faster queries
    __table_args__ = (
        Index('idx_user_status', 'user_id', 'status'),
    )

    def __repr__(self):
        return f"<Alert {self.status} - {self.message[:30]}...>"
