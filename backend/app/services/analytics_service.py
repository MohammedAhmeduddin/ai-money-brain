# backend/app/services/analytics_service.py

from sqlalchemy.orm import Session
from sqlalchemy import func, extract, Numeric
from datetime import date
from calendar import month_name
from typing import Optional

from app.models.transaction import Transaction
from app.schemas.dashboard import (
    SpendingSummary,
    CategorySpend,
    CategoryBreakdownResponse,
    MonthlySpend,
    MonthlyTrendResponse,
    MerchantSpend,
    TopMerchantsResponse,
)


def _apply_date_filters(query, start_date: Optional[date], end_date: Optional[date]):
    """Helper to apply optional date range filters to any query."""
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    return query


# ─── Summary ────────────────────────────────────────────────────────────────

def get_spending_summary(
    db: Session,
    user_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> SpendingSummary:
    """Total spent, income, net, averages for a given period."""

    base_q = db.query(Transaction).filter(Transaction.user_id == user_id)
    base_q = _apply_date_filters(base_q, start_date, end_date)
    all_txns = base_q.all()

    if not all_txns:
        return SpendingSummary(
            total_spent=0,
            total_income=0,
            net=0,
            transaction_count=0,
            avg_transaction=0,
            largest_expense=0,
            period_start=start_date,
            period_end=end_date,
        )

    # ✅ All amounts stored as positive — treat all as expenses
    amounts      = [float(t.amount) for t in all_txns]
    total_spent  = sum(amounts)
    total_income = 0.0
    net          = total_income - total_spent
    count        = len(all_txns)
    avg          = total_spent / count if count else 0.0
    largest      = max(amounts)        if amounts else 0.0

    return SpendingSummary(
        total_spent=round(total_spent, 2),
        total_income=round(total_income, 2),
        net=round(net, 2),
        transaction_count=count,
        avg_transaction=round(avg, 2),
        largest_expense=round(largest, 2),
        period_start=start_date,
        period_end=end_date,
    )


# ─── Category Breakdown ──────────────────────────────────────────────────────

def get_category_breakdown(
    db: Session,
    user_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> CategoryBreakdownResponse:
    """Spending totals grouped by category."""

    query = (
        db.query(
            Transaction.category,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .filter(
            Transaction.user_id == user_id,
            # ✅ Removed amount < 0 — all amounts are positive
        )
    )
    query = _apply_date_filters(query, start_date, end_date)
    rows  = query.group_by(Transaction.category).all()

    total_spent = sum(float(r.total) for r in rows) or 1.0

    categories = [
        CategorySpend(
            category=r.category or "Uncategorized",
            total=round(float(r.total), 2),
            count=r.count,
            percentage=round((float(r.total) / total_spent) * 100, 1),
        )
        for r in sorted(rows, key=lambda x: float(x.total), reverse=True)
    ]

    return CategoryBreakdownResponse(
        categories=categories,
        total_spent=round(total_spent, 2),
    )


# ─── Monthly Trend ───────────────────────────────────────────────────────────

def get_monthly_trend(
    db: Session,
    user_id: str,
    months: int = 6,
) -> MonthlyTrendResponse:
    """Spending and income aggregated by month (last N months)."""

    rows = (
        db.query(
            extract("year",  Transaction.date).label("year"),
            extract("month", Transaction.date).label("month"),
            # ✅ All amounts are positive = all spending
            func.sum(Transaction.amount).label("spent"),
            func.count(Transaction.id).label("count"),
        )
        .filter(Transaction.user_id == user_id)
        .group_by("year", "month")
        .order_by("year", "month")
        .limit(months)
        .all()
    )

    monthly = [
        MonthlySpend(
            year=int(r.year),
            month=int(r.month),
            month_name=month_name[int(r.month)],
            total_spent=round(float(r.spent or 0), 2),
            total_income=0.0,
            transaction_count=r.count,
        )
        for r in rows
    ]

    spends = [m.total_spent for m in monthly] or [0]
    avg    = round(sum(spends) / len(spends), 2)

    highest = max(monthly, key=lambda m: m.total_spent, default=None)
    lowest  = min(monthly, key=lambda m: m.total_spent, default=None)

    return MonthlyTrendResponse(
        months=monthly,
        avg_monthly_spend=avg,
        highest_month=f"{highest.month_name} {highest.year}" if highest else None,
        lowest_month=f"{lowest.month_name} {lowest.year}"   if lowest  else None,
    )


# ─── Top Merchants ───────────────────────────────────────────────────────────

def get_top_merchants(
    db: Session,
    user_id: str,
    limit: int = 10,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> TopMerchantsResponse:
    """Top merchants by total spend."""

    query = (
        db.query(
            Transaction.merchant,                              # ✅ merchant not merchant_name
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .filter(
            Transaction.user_id == user_id,
            Transaction.merchant.isnot(None),
            # ✅ Removed amount < 0 — all amounts are positive
        )
    )
    query = _apply_date_filters(query, start_date, end_date)
    rows  = (
        query
        .group_by(Transaction.merchant)
        .order_by(func.sum(Transaction.amount).desc())        # ✅ desc = highest spender first
        .limit(limit)
        .all()
    )

    merchants = [
        MerchantSpend(
            merchant=r.merchant,                              # ✅ merchant not merchant_name
            total=round(float(r.total), 2),
            count=r.count,
            avg_transaction=round(float(r.total) / r.count, 2),
        )
        for r in rows
    ]

    return TopMerchantsResponse(merchants=merchants)
