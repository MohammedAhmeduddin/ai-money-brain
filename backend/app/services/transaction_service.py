"""
Transaction Service - Business logic for transactions
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate


class TransactionService:
    """Handle transaction business logic"""

    @staticmethod
    def create_transaction(
        db: Session,
        user_id: str,
        transaction_data: TransactionCreate
    ) -> Transaction:
        """Create a new transaction"""
        db_transaction = Transaction(
            user_id=user_id,
            date=transaction_data.date,
            merchant=transaction_data.merchant,
            description=transaction_data.description,
            amount=transaction_data.amount,
            category=transaction_data.category,
            payment_type=transaction_data.payment_type,
            is_recurring=transaction_data.is_recurring
        )

        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)

        return db_transaction

    @staticmethod
    def create_transactions_bulk(
        db: Session,
        user_id: str,
        transactions_data: List[dict]
    ) -> List[Transaction]:
        """Create multiple transactions at once"""
        db_transactions = []

        for trans_data in transactions_data:
            db_transaction = Transaction(
                user_id=user_id,
                **trans_data
            )
            db_transactions.append(db_transaction)

        db.add_all(db_transactions)
        db.commit()

        # Refresh all
        for trans in db_transactions:
            db.refresh(trans)

        return db_transactions

    @staticmethod
    def get_transaction(
        db: Session,
        transaction_id: str,
        user_id: str
    ) -> Optional[Transaction]:
        """Get a single transaction by ID"""
        return db.query(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id
        ).first()

    @staticmethod
    def get_transactions(
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> tuple[List[Transaction], int]:
        """
        Get transactions with pagination and filters
        Returns (transactions, total_count)
        """
        query = db.query(Transaction).filter(Transaction.user_id == user_id)

        # Apply filters
        if category:
            query = query.filter(Transaction.category == category)

        if start_date:
            query = query.filter(Transaction.date >= start_date)

        if end_date:
            query = query.filter(Transaction.date <= end_date)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        transactions = query.order_by(
            Transaction.date.desc()
        ).offset(skip).limit(limit).all()

        return transactions, total

    @staticmethod
    def update_transaction(
        db: Session,
        transaction_id: str,
        user_id: str,
        update_data: TransactionUpdate
    ) -> Optional[Transaction]:
        """Update a transaction"""
        db_transaction = TransactionService.get_transaction(
            db, transaction_id, user_id
        )

        if not db_transaction:
            return None

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(db_transaction, field, value)

        db.commit()
        db.refresh(db_transaction)

        return db_transaction

    @staticmethod
    def delete_transaction(
        db: Session,
        transaction_id: str,
        user_id: str
    ) -> bool:
        """Delete a transaction"""
        db_transaction = TransactionService.get_transaction(
            db, transaction_id, user_id
        )

        if not db_transaction:
            return False

        db.delete(db_transaction)
        db.commit()

        return True
