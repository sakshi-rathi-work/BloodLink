from datetime import date
from typing import List, Optional
from pydantic import BaseModel


class BloodGroupStock(BaseModel):
    blood_group: str
    available_units: int
    safe_minimum: int
    is_low: bool


class ExpiringSoonSummary(BaseModel):
    days: int
    count: int


class DashboardSummaryResponse(BaseModel):
    as_of: date
    stock_by_group: List[BloodGroupStock]
    total_available_units: int
    expiring_soon: ExpiringSoonSummary
    pending_requests: int
    pending_emergency_requests: int
    approved_requests_awaiting_issue: int
    predicted_shortage_alert_count: Optional[int] = None


class TrendPoint(BaseModel):
    period_start: str
    donations: int
    issues: int


class DashboardTrendsResponse(BaseModel):
    granularity: str
    series: List[TrendPoint]


class WastageByBloodGroup(BaseModel):
    blood_group: str
    expired_units: int


class WastageByMonth(BaseModel):
    period_start: str
    expired_units: int


class DashboardWastageResponse(BaseModel):
    start_date: date
    end_date: date
    total_expired: int
    by_blood_group: List[WastageByBloodGroup]
    by_month: List[WastageByMonth]
