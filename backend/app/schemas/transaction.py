"""
Transaction schemas for API validation
"""
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from decimal import Decimal


class TransactionBase(BaseModel):
    """Base transaction schema"""
    date: date
    merchant: Optional[str] = None
    description: Optional[str] = None
    amount: Decimal = Field(..., decimal_places=2)
    category: Optional[str] = None
    payment_type: Optional[str] = None
    is_recurring: bool = False


class TransactionCreate(TransactionBase):
    """Schema for creating a transaction"""
    pass


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction"""
    date: Optional[date] = None
    merchant: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    category: Optional[str] = None
    payment_type: Optional[str] = None
    is_recurring: Optional[bool] = None


class TransactionResponse(TransactionBase):
    """Schema for transaction response"""
    id: str
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """Schema for paginated transaction list"""
    items: list[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CSVUploadResponse(BaseModel):
    """Schema for CSV upload response"""
    total_uploaded: int
    total_categorized: int
    status: str
    message: str
