from datetime import date, timedelta
from typing import Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core import clock
from app.core.config import settings
from app.core.constants import BLOOD_GROUPS
from app.models.blood_request import BloodRequest
from app.models.blood_unit import BloodUnit
from app.models.issue_record import IssueRecord
from app.schemas.dashboard import (
    BloodGroupStock,
    DashboardSummaryResponse,
    DashboardTrendsResponse,
    DashboardWastageResponse,
    ExpiringSoonSummary,
    TrendPoint,
    WastageByBloodGroup,
    WastageByMonth,
)
from app.services.inventory import get_stock_by_blood_group
from app.services.prediction_alerts import get_predicted_alert_count


def get_dashboard_summary(
    db: Session, today_date: Optional[date] = None
) -> DashboardSummaryResponse:
    """
    Compute headline operational metrics for the executive dashboard:
    - Stock per blood group with safe-minimum threshold comparison and low-stock flag.
    - Expiring soon units within EXPIRY_ALERT_DAYS (7 days).
    - Pending and emergency request counts.
    - Approved requests awaiting unit issuance.
    - Active shortage alert count from the latest ML prediction run.
    """
    if today_date is None:
        today_date = clock.today()

    # 1. Stock per blood group
    stock_map = get_stock_by_blood_group(db, today_date)
    stock_by_group: List[BloodGroupStock] = []
    total_available = 0

    for group in BLOOD_GROUPS:
        avail = stock_map.get(group, 0)
        safe_min = settings.get_safe_minimum(group)
        is_low = avail < safe_min
        stock_by_group.append(
            BloodGroupStock(
                blood_group=group,
                available_units=avail,
                safe_minimum=safe_min,
                is_low=is_low,
            )
        )
        total_available += avail

    # 2. Units expiring within alert window
    alert_cutoff = today_date + timedelta(days=settings.EXPIRY_ALERT_DAYS)
    expiring_count = (
        db.query(func.count(BloodUnit.unit_id))
        .filter(
            BloodUnit.status == "available",
            BloodUnit.expiry_date >= today_date,
            BloodUnit.expiry_date <= alert_cutoff,
        )
        .scalar()
        or 0
    )

    # 3. Request counts
    pending_count = (
        db.query(func.count(BloodRequest.request_id))
        .filter(BloodRequest.status == "pending")
        .scalar()
        or 0
    )

    pending_emergency = (
        db.query(func.count(BloodRequest.request_id))
        .filter(
            BloodRequest.status == "pending",
            BloodRequest.urgency == "emergency",
        )
        .scalar()
        or 0
    )

    approved_awaiting = (
        db.query(func.count(BloodRequest.request_id))
        .filter(BloodRequest.status == "approved")
        .scalar()
        or 0
    )

    # 4. Shortage alert count from ML prediction service
    alert_count = get_predicted_alert_count(db)

    return DashboardSummaryResponse(
        as_of=today_date,
        stock_by_group=stock_by_group,
        total_available_units=total_available,
        expiring_soon=ExpiringSoonSummary(
            days=settings.EXPIRY_ALERT_DAYS,
            count=expiring_count,
        ),
        pending_requests=pending_count,
        pending_emergency_requests=pending_emergency,
        approved_requests_awaiting_issue=approved_awaiting,
        predicted_shortage_alert_count=alert_count,
    )


def _get_period_bucket(d: date, granularity: str) -> str:
    """Helper to map a calendar date to its zero-filled period start bucket string."""
    if granularity == "month":
        return date(d.year, d.month, 1).isoformat()
    elif granularity == "week":
        # ISO week starts Monday: weekday 0 is Monday
        monday = d - timedelta(days=d.weekday())
        return monday.isoformat()
    else:  # day
        return d.isoformat()


def get_dashboard_trends(
    db: Session,
    start_date: date,
    end_date: date,
    granularity: str = "day",
    blood_group: Optional[str] = None,
) -> DashboardTrendsResponse:
    """
    Generate time series of donations vs. issues grouped by day, week (Monday start), or month.
    The series is continuous and zero-filled for empty intervals.
    """
    # 1. Generate all expected period buckets in chronological order
    period_buckets: Dict[str, Dict[str, int]] = {}

    if granularity == "month":
        curr = date(start_date.year, start_date.month, 1)
        end_month = date(end_date.year, end_date.month, 1)
        while curr <= end_month:
            period_buckets[curr.isoformat()] = {"donations": 0, "issues": 0}
            # Advance to next month
            if curr.month == 12:
                curr = date(curr.year + 1, 1, 1)
            else:
                curr = date(curr.year, curr.month + 1, 1)
    elif granularity == "week":
        curr_monday = start_date - timedelta(days=start_date.weekday())
        end_monday = end_date - timedelta(days=end_date.weekday())
        while curr_monday <= end_monday:
            period_buckets[curr_monday.isoformat()] = {"donations": 0, "issues": 0}
            curr_monday += timedelta(days=7)
    else:  # day
        curr = start_date
        while curr <= end_date:
            period_buckets[curr.isoformat()] = {"donations": 0, "issues": 0}
            curr += timedelta(days=1)

    # 2. Query donations by collection_date
    d_query = db.query(BloodUnit.collection_date, func.count(BloodUnit.unit_id)).filter(
        BloodUnit.collection_date >= start_date,
        BloodUnit.collection_date <= end_date,
    )
    if blood_group:
        d_query = d_query.filter(BloodUnit.blood_group == blood_group)
    donations_rows = d_query.group_by(BloodUnit.collection_date).all()

    for col_date, count in donations_rows:
        bucket = _get_period_bucket(col_date, granularity)
        if bucket in period_buckets:
            period_buckets[bucket]["donations"] += count

    # 3. Query issues by issue_date
    i_query = (
        db.query(IssueRecord.issue_date, func.count(IssueRecord.issue_id))
        .join(BloodUnit, BloodUnit.unit_id == IssueRecord.unit_id)
        .filter(
            IssueRecord.issue_date >= start_date,
            IssueRecord.issue_date <= end_date,
        )
    )
    if blood_group:
        i_query = i_query.filter(BloodUnit.blood_group == blood_group)
    issues_rows = i_query.group_by(IssueRecord.issue_date).all()

    for iss_date, count in issues_rows:
        bucket = _get_period_bucket(iss_date, granularity)
        if bucket in period_buckets:
            period_buckets[bucket]["issues"] += count

    # 4. Assemble sorted series
    sorted_series = [
        TrendPoint(
            period_start=bucket_key,
            donations=vals["donations"],
            issues=vals["issues"],
        )
        for bucket_key, vals in sorted(period_buckets.items())
    ]

    return DashboardTrendsResponse(granularity=granularity, series=sorted_series)


def get_dashboard_wastage(
    db: Session, start_date: date, end_date: date
) -> DashboardWastageResponse:
    """
    Aggregate expired unit wastage across date range:
    - Total expired units.
    - Breakdown by blood group (zero-filled for all 8 groups).
    - Breakdown by month (zero-filled for all months in range).
    """
    # 1. Total and by blood group
    rows = (
        db.query(BloodUnit.blood_group, func.count(BloodUnit.unit_id))
        .filter(
            BloodUnit.status == "expired",
            BloodUnit.expiry_date >= start_date,
            BloodUnit.expiry_date <= end_date,
        )
        .group_by(BloodUnit.blood_group)
        .all()
    )

    group_counts = {group: 0 for group in BLOOD_GROUPS}
    total_expired = 0
    for bg, count in rows:
        if bg in group_counts:
            group_counts[bg] = count
        total_expired += count

    by_blood_group = [
        WastageByBloodGroup(blood_group=bg, expired_units=group_counts[bg])
        for bg in BLOOD_GROUPS
    ]

    # 2. Monthly breakdown (zero-filled)
    monthly_counts: Dict[str, int] = {}
    curr_m = date(start_date.year, start_date.month, 1)
    end_m = date(end_date.year, end_date.month, 1)
    while curr_m <= end_m:
        monthly_counts[curr_m.isoformat()] = 0
        if curr_m.month == 12:
            curr_m = date(curr_m.year + 1, 1, 1)
        else:
            curr_m = date(curr_m.year, curr_m.month + 1, 1)

    month_rows = (
        db.query(BloodUnit.expiry_date, func.count(BloodUnit.unit_id))
        .filter(
            BloodUnit.status == "expired",
            BloodUnit.expiry_date >= start_date,
            BloodUnit.expiry_date <= end_date,
        )
        .group_by(BloodUnit.expiry_date)
        .all()
    )

    for exp_date, count in month_rows:
        m_key = date(exp_date.year, exp_date.month, 1).isoformat()
        if m_key in monthly_counts:
            monthly_counts[m_key] += count

    by_month = [
        WastageByMonth(period_start=m_key, expired_units=count)
        for m_key, count in sorted(monthly_counts.items())
    ]

    return DashboardWastageResponse(
        start_date=start_date,
        end_date=end_date,
        total_expired=total_expired,
        by_blood_group=by_blood_group,
        by_month=by_month,
    )
