from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.core import clock
from app.core.config import settings
from app.models.shortage_prediction import ShortagePrediction
from app.models.user import User
from app.schemas.prediction import (
    EvaluationResponse,
    ForecastItem,
    GroupPrediction,
    LatestPredictionsResponse,
    PredictionRunRequest,
    PredictionRunSummary,
    ShortageAlertResponse,
    SkippedGroup,
)
from app.services import activity_log
from app.services.inventory import expire_overdue_units
from app.services.prediction_alerts import get_shortage_alerts
from ml.config import BLOOD_GROUPS
from ml.evaluation import load_evaluation_artifact
from ml.pipeline import run_prediction

router = APIRouter(prefix="/predictions", tags=["predictions"])

_staff_or_admin = require_roles("admin", "staff")


@router.post(
    "/run",
    response_model=PredictionRunSummary,
    status_code=status.HTTP_200_OK,
)
def trigger_prediction_run(
    payload: PredictionRunRequest = PredictionRunRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(_staff_or_admin),
) -> PredictionRunSummary:
    """
    Synchronously run shortage prediction pipeline (Admin/Staff only).
    Sweeps overdue units, evaluates models on held-out data, forecasts next horizon days,
    persists predictions to database, and writes an activity log.
    """
    # 1. Sweep expired units without committing yet
    expire_overdue_units(db, commit=False)

    # 2. Run prediction pipeline using the active DB connection
    conn = db.connection()
    result = run_prediction(
        engine_or_conn=conn,
        safe_minimums=settings.safe_minimums_dict,
        horizon_days=payload.horizon_days,
        today=clock.today(),
        min_history_days=settings.PREDICTION_MIN_HISTORY_DAYS,
        holdout_days=settings.PREDICTION_HOLDOUT_DAYS,
    )

    # 3. Record activity log
    activity_log.record(
        db,
        user_id=current_user.user_id,
        action="create",
        entity_type="prediction_run",
        entity_id=None,
        details={
            "run_id": result.run_id,
            "horizon_days": result.horizon_days,
            "groups_predicted": result.groups_predicted,
            "groups_skipped": result.groups_skipped,
        },
    )

    db.commit()

    return PredictionRunSummary(
        run_id=result.run_id,
        generated_at=result.generated_at,
        horizon_days=result.horizon_days,
        groups_predicted=result.groups_predicted,
        groups_skipped=result.groups_skipped,
    )


@router.get(
    "/latest",
    response_model=LatestPredictionsResponse,
)
def get_latest_predictions(
    db: Session = Depends(get_db),
    current_user: User = Depends(_staff_or_admin),
) -> LatestPredictionsResponse:
    """
    Retrieve latest prediction run's forecasts by blood group (Admin/Staff only).
    Returns 200 with empty fields if no runs exist.
    """
    latest_run = (
        db.query(ShortagePrediction.run_id, ShortagePrediction.generated_at)
        .order_by(ShortagePrediction.generated_at.desc())
        .first()
    )

    if not latest_run:
        return LatestPredictionsResponse(
            run_id=None,
            generated_at=None,
            horizon_days=None,
            predictions=[],
            skipped_groups=[],
        )

    run_id, generated_at = latest_run

    rows = (
        db.query(ShortagePrediction)
        .filter(ShortagePrediction.run_id == run_id)
        .order_by(ShortagePrediction.blood_group.asc(), ShortagePrediction.forecast_date.asc())
        .all()
    )

    # Group by blood group
    groups_map: Dict[str, List[ShortagePrediction]] = {}
    for r in rows:
        groups_map.setdefault(r.blood_group, []).append(r)

    predictions_list: List[GroupPrediction] = []
    horizon_days = 0

    for bg, bg_rows in groups_map.items():
        if not bg_rows:
            continue
        horizon_days = max(horizon_days, len(bg_rows))
        model_name = bg_rows[0].model_name
        safe_min = bg_rows[0].safe_minimum
        forecast_items = [
            ForecastItem(
                date=item.forecast_date.isoformat(),
                predicted_stock=float(item.predicted_stock),
                is_below_minimum=item.is_below_minimum,
            )
            for item in bg_rows
        ]
        predictions_list.append(
            GroupPrediction(
                blood_group=bg,
                model_name=model_name,
                safe_minimum=safe_min,
                forecast=forecast_items,
            )
        )

    # Check for skipped groups
    eval_artifact = load_evaluation_artifact()
    artifact_groups = eval_artifact.get("groups", {})

    skipped_list: List[SkippedGroup] = []
    for bg in BLOOD_GROUPS:
        if bg not in groups_map:
            bg_info = artifact_groups.get(bg, {})
            reason = bg_info.get("status", "insufficient_data")
            skipped_list.append(SkippedGroup(blood_group=bg, reason=reason))

    return LatestPredictionsResponse(
        run_id=str(run_id),
        generated_at=generated_at.isoformat(),
        horizon_days=horizon_days,
        predictions=predictions_list,
        skipped_groups=skipped_list,
    )


@router.get(
    "/alerts",
    response_model=List[ShortageAlertResponse],
)
def get_prediction_alerts(
    within_days: int = Query(30, ge=7, le=30, description="Shortage detection window in days (7-30)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(_staff_or_admin),
) -> List[ShortageAlertResponse]:
    """
    Retrieve blood shortage alerts from the latest prediction run (Admin/Staff only).
    """
    alerts = get_shortage_alerts(
        db=db,
        within_days=within_days,
        current_date=clock.today(),
    )
    return [ShortageAlertResponse(**a) for a in alerts]


@router.get(
    "/evaluation",
    response_model=EvaluationResponse,
)
def get_prediction_evaluation(
    current_user: User = Depends(_staff_or_admin),
) -> EvaluationResponse:
    """
    Retrieve model evaluation metrics from latest_evaluation.json (Admin/Staff only).
    """
    eval_dict = load_evaluation_artifact()
    return EvaluationResponse(
        run_id=eval_dict.get("run_id"),
        generated_at=eval_dict.get("generated_at"),
        holdout_days=eval_dict.get("holdout_days"),
        groups=eval_dict.get("groups", {}),
    )
