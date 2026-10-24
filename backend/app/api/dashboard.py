from datetime import date, timedelta
from typing import Literal, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core import clock
from app.core.deps import get_db, require_roles
from app.models.user import User
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    DashboardTrendsResponse,
    DashboardWastageResponse,
)
from app.services import dashboard as dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse, summary="Get dashboard summary metrics")
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    """Staff & Admin: Retrieve headline operational KPI metrics and blood stock levels."""
    return dashboard_service.get_dashboard_summary(db)


@router.get("/trends", response_model=DashboardTrendsResponse, summary="Get donations vs issues trends")
def get_trends(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    granularity: Literal["day", "week", "month"] = Query("day"),
    blood_group: Optional[Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    """Staff & Admin: Retrieve zero-filled time series of donations vs issues by granularity."""
    today = clock.today()
    if end_date is None:
        end_date = today
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    return dashboard_service.get_dashboard_trends(
        db,
        start_date=start_date,
        end_date=end_date,
        granularity=granularity,
        blood_group=blood_group,
    )


@router.get("/wastage", response_model=DashboardWastageResponse, summary="Get unit wastage analytics")
def get_wastage(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    """Staff & Admin: Retrieve blood unit wastage (expired units) breakdown by group and month."""
    today = clock.today()
    if end_date is None:
        end_date = today
    if start_date is None:
        start_date = end_date - timedelta(days=365)

    return dashboard_service.get_dashboard_wastage(
        db,
        start_date=start_date,
        end_date=end_date,
    )
