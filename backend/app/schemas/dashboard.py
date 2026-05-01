# backend/app/schemas/dashboard.py

from pydantic import BaseModel
from typing import Optional
from datetime import date


# ─── Summary ────────────────────────────────────────────────────────────────

class SpendingSummary(BaseModel):
    total_spent: float
    total_income: float
    net: float
    transaction_count: int
    avg_transaction: float
    largest_expense: float
    period_start: Optional[date] = None
    period_end: Optional[date] = None


# ─── Category Breakdown ──────────────────────────────────────────────────────

class CategorySpend(BaseModel):
    category: str
    total: float
    count: int
    percentage: float


class CategoryBreakdownResponse(BaseModel):
    categories: list[CategorySpend]
    total_spent: float


# ─── Monthly Trend ───────────────────────────────────────────────────────────

class MonthlySpend(BaseModel):
    year: int
    month: int
    month_name: str
    total_spent: float
    total_income: float
    transaction_count: int


class MonthlyTrendResponse(BaseModel):
    months: list[MonthlySpend]
    avg_monthly_spend: float
    highest_month: Optional[str] = None
    lowest_month: Optional[str] = None


# ─── Top Merchants ───────────────────────────────────────────────────────────

class MerchantSpend(BaseModel):
    merchant: str
    total: float
    count: int
    avg_transaction: float


class TopMerchantsResponse(BaseModel):
    merchants: list[MerchantSpend]


# ─── Insights ────────────────────────────────────────────────────────────────

class InsightItem(BaseModel):
    type: str          # "spike", "top_category", "unusual", "trend"
    title: str
    description: str
    severity: str      # "info", "warning", "positive"
    value: Optional[float] = None


class InsightsResponse(BaseModel):
    insights: list[InsightItem]
    generated_at: str
    transaction_count_analyzed: int
