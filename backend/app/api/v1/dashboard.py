# backend/app/api/v1/dashboard.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.dashboard import (
    SpendingSummary,
    CategoryBreakdownResponse,
    MonthlyTrendResponse,
    TopMerchantsResponse,
    InsightsResponse,
)
from app.services.analytics_service import (
    get_spending_summary,
    get_category_breakdown,
    get_monthly_trend,
    get_top_merchants,
)
from app.services.insight_service import generate_insights

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Analytics"])


# ─── 1. Spending Summary ─────────────────────────────────────────────────────

@router.get(
    "/summary",
    response_model=SpendingSummary,
    summary="Get spending summary",
    description="Returns total spent, income, net, transaction count, and averages for a given period.",
)
def spending_summary(
    start_date: Optional[date] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    end_date:   Optional[date] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    db:         Session        = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    return get_spending_summary(
        db=db,
        user_id=str(current_user.id),
        start_date=start_date,
        end_date=end_date,
    )


# ─── 2. Category Breakdown ───────────────────────────────────────────────────

@router.get(
    "/by-category",
    response_model=CategoryBreakdownResponse,
    summary="Spending by category",
    description="Returns spending totals grouped by category, sorted by highest spend.",
)
def category_breakdown(
    start_date: Optional[date] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    end_date:   Optional[date] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    db:         Session        = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    return get_category_breakdown(
        db=db,
        user_id=str(current_user.id),
        start_date=start_date,
        end_date=end_date,
    )


# ─── 3. Monthly Trend ────────────────────────────────────────────────────────

@router.get(
    "/by-month",
    response_model=MonthlyTrendResponse,
    summary="Monthly spending trend",
    description="Returns spending and income aggregated by month for the last N months.",
)
def monthly_trend(
    months: int     = Query(6, ge=1, le=24, description="Number of months to return (1-24)"),
    db: Session     = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_monthly_trend(
        db=db,
        user_id=str(current_user.id),
        months=months,
    )


# ─── 4. Top Merchants ────────────────────────────────────────────────────────

@router.get(
    "/top-merchants",
    response_model=TopMerchantsResponse,
    summary="Top merchants by spend",
    description="Returns the top N merchants ranked by total spending.",
)
def top_merchants(
    limit:      int            = Query(10, ge=1, le=50, description="Number of merchants to return"),
    start_date: Optional[date] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    end_date:   Optional[date] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    db:         Session        = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    return get_top_merchants(
        db=db,
        user_id=str(current_user.id),
        limit=limit,
        start_date=start_date,
        end_date=end_date,
    )


# ─── 5. Insights ─────────────────────────────────────────────────────────────

@router.get(
    "/insights",
    response_model=InsightsResponse,
    summary="AI-powered spending insights",
    description="Analyzes your transactions and returns actionable spending insights.",
)
def spending_insights(
    start_date: Optional[date] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    end_date:   Optional[date] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    db:         Session        = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    return generate_insights(
        db=db,
        user_id=str(current_user.id),
        start_date=start_date,
        end_date=end_date,
    )
