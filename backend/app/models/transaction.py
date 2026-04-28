"""
Transaction model
"""
from sqlalchemy import Column, String, DateTime, Numeric, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    merchant = Column(String)
    description = Column(String)
    amount = Column(Numeric(10, 2), nullable=False)
    category = Column(String, index=True)
    payment_type = Column(String)
    is_recurring = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction {self.merchant} ${self.amount}>"
