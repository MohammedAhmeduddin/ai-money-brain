"""
Insight model
"""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.db.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class SeverityEnum(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Insight(Base):
    __tablename__ = "insights"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    severity = Column(Enum(SeverityEnum), default=SeverityEnum.LOW)
    insight_type = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="insights")

    def __repr__(self):
        return f"<Insight {self.title} ({self.severity})>"
