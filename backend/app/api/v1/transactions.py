"""
Transaction endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import math

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionListResponse,
    CSVUploadResponse,
)
from app.services.transaction_service import TransactionService
from app.services.csv_parser import CSVParser, CSVValidationError
from app.services.ai_categorizer import AICategorizer  # ✨ NEW


router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/upload", response_model=CSVUploadResponse)
async def upload_csv(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload bank CSV file and import transactions with AI categorization

    Supports multiple bank formats including Bank of America
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported"
        )

    # Read file content
    try:
        content = await file.read()
        csv_content = content.decode('utf-8')
    except UnicodeDecodeError:
        # Try different encoding
        try:
            csv_content = content.decode('latin-1')
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to read CSV file. Please ensure it's properly encoded."
            )

    # Validate file size (10 MB max)
    parser = CSVParser()
    if not parser.validate_csv_size(len(content)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 10 MB limit"
        )

    # Parse CSV
    try:
        transactions_data = parser.parse(csv_content)
    except CSVValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )

    # ✨ AI Categorization
    try:
        categorizer = AICategorizer()
        transactions_data = categorizer.categorize_batch(transactions_data)
    except Exception as e:
        # If AI categorization fails, continue without it
        print(f"⚠️  AI categorization failed: {e}")

    # Save transactions to database
    try:
        db_transactions = TransactionService.create_transactions_bulk(
            db=db,
            user_id=user.id,
            transactions_data=transactions_data
        )

        # Count categorized transactions
        categorized = sum(1 for t in db_transactions if t.category)

        return CSVUploadResponse(
            total_uploaded=len(db_transactions),
            total_categorized=categorized,
            status="success",
            message=f"Successfully imported {len(db_transactions)} transactions. "
                   f"{categorized} automatically categorized by AI."
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save transactions: {str(e)}"
        )


@router.get("", response_model=TransactionListResponse)
def get_transactions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    start_date: Optional[date] = Query(None, description="Filter from date"),
    end_date: Optional[date] = Query(None, description="Filter to date"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's transactions with pagination and filters
    """
    skip = (page - 1) * page_size

    transactions, total = TransactionService.get_transactions(
        db=db,
        user_id=user.id,
        skip=skip,
        limit=page_size,
        category=category,
        start_date=start_date,
        end_date=end_date
    )

    total_pages = math.ceil(total / page_size)

    return TransactionListResponse(
        items=transactions,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a single transaction by ID"""
    transaction = TransactionService.get_transaction(
        db=db,
        transaction_id=transaction_id,
        user_id=user.id
    )

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    return transaction


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: str,
    update_data: TransactionUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a transaction (e.g., change category manually)"""
    transaction = TransactionService.update_transaction(
        db=db,
        transaction_id=transaction_id,
        user_id=user.id,
        update_data=update_data
    )

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a transaction"""
    success = TransactionService.delete_transaction(
        db=db,
        transaction_id=transaction_id,
        user_id=user.id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    return None
