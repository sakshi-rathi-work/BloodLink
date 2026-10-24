from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class PredictionRunRequest(BaseModel):
    horizon_days: int = Field(default=30, ge=7, le=30, description="Forecast horizon in days (7-30)")


class PredictionRunSummary(BaseModel):
    run_id: str
    generated_at: str
    horizon_days: int
    groups_predicted: int
    groups_skipped: List[str]


class ForecastItem(BaseModel):
    date: str
    predicted_stock: float
    is_below_minimum: bool


class GroupPrediction(BaseModel):
    blood_group: str
    model_name: str
    safe_minimum: int
    forecast: List[ForecastItem]


class SkippedGroup(BaseModel):
    blood_group: str
    reason: str


class LatestPredictionsResponse(BaseModel):
    run_id: Optional[str] = None
    generated_at: Optional[str] = None
    horizon_days: Optional[int] = None
    predictions: List[GroupPrediction] = []
    skipped_groups: List[SkippedGroup] = []


class ShortageAlertResponse(BaseModel):
    blood_group: str
    current_stock: int
    safe_minimum: int
    first_shortage_date: str
    days_until_shortage: int
    min_predicted_stock: float


class EvaluationResponse(BaseModel):
    run_id: Optional[str] = None
    generated_at: Optional[str] = None
    holdout_days: Optional[int] = None
    groups: Dict[str, Any] = {}
