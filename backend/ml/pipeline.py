import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from ml.config import (
    BLOOD_GROUPS,
    DEFAULT_HORIZON_DAYS,
    HOLDOUT_DAYS,
    MIN_HISTORY_DAYS,
    get_default_safe_minimums,
)
from ml.data import prepare_stock_series
from ml.evaluation import evaluate_and_select_models
from ml.persistence import persist_predictions


@dataclass
class RunResult:
    run_id: str
    generated_at: str
    horizon_days: int
    groups_predicted: int
    groups_skipped: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "generated_at": self.generated_at,
            "horizon_days": self.horizon_days,
            "groups_predicted": self.groups_predicted,
            "groups_skipped": self.groups_skipped,
        }


def run_prediction(
    engine_or_conn: Any,
    safe_minimums: Optional[Dict[str, int]] = None,
    horizon_days: int = DEFAULT_HORIZON_DAYS,
    today: Optional[date] = None,
    min_history_days: int = MIN_HISTORY_DAYS,
    holdout_days: int = HOLDOUT_DAYS,
) -> RunResult:
    """
    Execute full shortage prediction pipeline:
    1. Data preparation from v_transactions
    2. Candidate evaluation & model selection
    3. Horizon forecasting & threshold checking
    4. Database persistence
    5. Artifact saving & summary generation
    """
    if today is None:
        today = date.today()

    if safe_minimums is None:
        safe_minimums = get_default_safe_minimums()

    run_id = str(uuid.uuid4())
    generated_at_dt = datetime.now(timezone.utc)
    generated_at_str = generated_at_dt.isoformat()

    # 1. Prepare data
    group_data = prepare_stock_series(
        engine_or_conn=engine_or_conn,
        today=today,
        min_history_days=min_history_days,
    )

    # 2. Evaluate and select models
    eval_dict, fitted_models = evaluate_and_select_models(
        group_data=group_data,
        holdout_days=holdout_days,
        run_id=run_id,
        generated_at=generated_at_dt,
    )

    # Forecast dates run from history_end + 1 (which is today) through today + horizon_days - 1
    forecast_dates = [today + timedelta(days=i) for i in range(horizon_days)]

    rows_to_persist: List[Dict[str, Any]] = []
    groups_predicted = 0
    groups_skipped: List[str] = []

    for bg in BLOOD_GROUPS:
        if bg not in fitted_models:
            groups_skipped.append(bg)
            continue

        model = fitted_models[bg]
        model_name = getattr(model, "name", "unknown")
        safe_min = safe_minimums.get(bg, 10)

        try:
            preds = model.forecast(horizon_days)
            for f_date, pred_val in zip(forecast_dates, preds):
                stock_val = round(float(pred_val), 2)
                stock_val = max(0.0, stock_val)
                is_below = stock_val < safe_min

                rows_to_persist.append({
                    "run_id": run_id,
                    "generated_at": generated_at_dt,
                    "blood_group": bg,
                    "forecast_date": f_date,
                    "predicted_stock": stock_val,
                    "safe_minimum": safe_min,
                    "is_below_minimum": is_below,
                    "model_name": model_name,
                })
            groups_predicted += 1
        except Exception:
            groups_skipped.append(bg)

    # 3. Persist rows
    persist_predictions(engine_or_conn, rows_to_persist)

    return RunResult(
        run_id=run_id,
        generated_at=generated_at_str,
        horizon_days=horizon_days,
        groups_predicted=groups_predicted,
        groups_skipped=groups_skipped,
    )
