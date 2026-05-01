# backend/app/services/insight_service.py

from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import Optional
import json

from app.services.analytics_service import (
    get_spending_summary,
    get_category_breakdown,
    get_monthly_trend,
    get_top_merchants,
)
from app.schemas.dashboard import InsightItem, InsightsResponse


# ─── Rule-Based Insights (no AI needed) ─────────────────────────────────────

def _detect_spending_spike(monthly_data) -> Optional[InsightItem]:
    """Flag if the latest month is 20%+ higher than the previous month."""
    months = monthly_data.months
    if len(months) < 2:
        return None

    latest   = months[-1]
    previous = months[-2]

    if previous.total_spent == 0:
        return None

    change_pct = ((latest.total_spent - previous.total_spent) / previous.total_spent) * 100

    if change_pct >= 20:
        return InsightItem(
            type="spike",
            title="📈 Spending Spike Detected",
            description=(
                f"Your spending in {latest.month_name} (${latest.total_spent:,.2f}) "
                f"is {change_pct:.1f}% higher than {previous.month_name} "
                f"(${previous.total_spent:,.2f})."
            ),
            severity="warning",
            value=round(change_pct, 1),
        )
    elif change_pct <= -20:
        return InsightItem(
            type="spike",
            title="📉 Spending Decreased",
            description=(
                f"Great job! Your spending dropped {abs(change_pct):.1f}% "
                f"from {previous.month_name} to {latest.month_name}."
            ),
            severity="positive",
            value=round(change_pct, 1),
        )
    return None


def _top_category_insight(category_data) -> Optional[InsightItem]:
    """Highlight the #1 spending category."""
    if not category_data.categories:
        return None

    top = category_data.categories[0]
    return InsightItem(
        type="top_category",
        title=f"🏆 Top Spending: {top.category}",
        description=(
            f"{top.category} is your biggest expense at "
            f"${top.total:,.2f} ({top.percentage}% of total spending) "
            f"across {top.count} transactions."
        ),
        severity="info",
        value=top.total,
    )


def _top_merchant_insight(merchant_data) -> Optional[InsightItem]:
    """Highlight the #1 merchant."""
    if not merchant_data.merchants:
        return None

    top = merchant_data.merchants[0]
    return InsightItem(
        type="top_merchant",
        title=f"🏪 Most Visited: {top.merchant}",
        description=(
            f"You've spent ${top.total:,.2f} at {top.merchant} "
            f"across {top.count} transactions "
            f"(avg ${top.avg_transaction:,.2f} each)."
        ),
        severity="info",
        value=top.total,
    )


def _savings_insight(summary) -> Optional[InsightItem]:
    """Positive or warning message based on net spend vs income."""
    if summary.total_income == 0:
        return None

    savings_rate = (summary.net / summary.total_income) * 100

    if savings_rate >= 20:
        return InsightItem(
            type="savings",
            title="💰 Great Savings Rate!",
            description=(
                f"You're saving {savings_rate:.1f}% of your income. "
                f"Net: ${summary.net:,.2f} this period."
            ),
            severity="positive",
            value=round(savings_rate, 1),
        )
    elif savings_rate < 0:
        return InsightItem(
            type="savings",
            title="⚠️ Spending Exceeds Income",
            description=(
                f"You spent ${abs(summary.net):,.2f} more than you earned "
                f"this period. Consider reviewing your budget."
            ),
            severity="warning",
            value=round(savings_rate, 1),
        )
    return None


def _high_frequency_insight(merchant_data) -> Optional[InsightItem]:
    """Flag merchants visited very frequently (possible subscription)."""
    if not merchant_data.merchants:
        return None

    # Find merchant with highest transaction count
    frequent = max(merchant_data.merchants, key=lambda m: m.count)

    if frequent.count >= 10:
        return InsightItem(
            type="unusual",
            title=f"🔄 Frequent Charges: {frequent.merchant}",
            description=(
                f"{frequent.merchant} appears {frequent.count} times "
                f"totalling ${frequent.total:,.2f}. "
                f"This may be a subscription or recurring charge."
            ),
            severity="info",
            value=float(frequent.count),
        )
    return None


# ─── Main Insights Generator ────────────────────────────────────────────────

def generate_insights(
    db: Session,
    user_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> InsightsResponse:
    """
    Generate all spending insights for a user.
    Runs rule-based checks — no extra AI cost.
    """

    # Gather all analytics data
    summary       = get_spending_summary(db, user_id, start_date, end_date)
    category_data = get_category_breakdown(db, user_id, start_date, end_date)
    monthly_data  = get_monthly_trend(db, user_id, months=6)
    merchant_data = get_top_merchants(db, user_id, limit=10, start_date=start_date, end_date=end_date)

    # Run all insight checks
    raw_insights = [
        _detect_spending_spike(monthly_data),
        _top_category_insight(category_data),
        _top_merchant_insight(merchant_data),
        _savings_insight(summary),
        _high_frequency_insight(merchant_data),
    ]

    # Filter out None results
    insights = [i for i in raw_insights if i is not None]

    # Always add a summary insight
    if summary.transaction_count > 0:
        insights.append(InsightItem(
            type="summary",
            title="📊 Period Overview",
            description=(
                f"Analyzed {summary.transaction_count} transactions. "
                f"Total spent: ${summary.total_spent:,.2f}. "
                f"Largest single expense: ${summary.largest_expense:,.2f}."
            ),
            severity="info",
            value=summary.total_spent,
        ))

    return InsightsResponse(
        insights=insights,
        generated_at=datetime.utcnow().isoformat(),
        transaction_count_analyzed=summary.transaction_count,
    )
