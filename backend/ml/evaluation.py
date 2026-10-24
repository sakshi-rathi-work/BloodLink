import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from ml.config import ARTIFACTS_DIR, EVALUATION_FILE, HOLDOUT_DAYS
from ml.models import CANDIDATE_MODELS, BaseTimeSeriesModel


def evaluate_and_select_models(
    group_data: Dict[str, Dict[str, Any]],
    holdout_days: int = HOLDOUT_DAYS,
    run_id: Optional[str] = None,
    generated_at: Optional[datetime] = None,
) -> Tuple[Dict[str, Any], Dict[str, BaseTimeSeriesModel]]:
    """
    Chronological hold-out evaluation on the last `holdout_days`.
    Returns:
      (evaluation_dict, selected_fitted_models)
    """
    if run_id is None:
        run_id = str(uuid.uuid4())
    if generated_at is None:
        generated_at = datetime.now(timezone.utc)

    iso_timestamp = generated_at.isoformat()

    eval_result: Dict[str, Any] = {
        "run_id": str(run_id),
        "generated_at": iso_timestamp,
        "holdout_days": holdout_days,
        "groups": {},
    }

    selected_models: Dict[str, BaseTimeSeriesModel] = {}

    for blood_group, info in group_data.items():
        status = info.get("status")
        history_days = info.get("history_days", 0)
        series: Optional[pd.Series] = info.get("series")

        if status != "ok" or series is None or len(series) <= holdout_days:
            eval_result["groups"][blood_group] = {
                "status": "insufficient_data",
                "history_days": history_days,
            }
            continue

        n_total = len(series)
        train_days = n_total - holdout_days
        train_series = series.iloc[:train_days]
        test_series = series.iloc[train_days:]
        y_test = test_series.values.astype(float)

        metrics: Dict[str, Any] = {}
        candidate_scores: List[Tuple[float, str, type]] = []

        for ModelCls in CANDIDATE_MODELS:
            model_instance = ModelCls()
            model_name = model_instance.name
            try:
                model_instance.fit(train_series)
                preds = model_instance.forecast(holdout_days)
                preds = np.clip(preds, a_min=0.0, a_max=None)

                # Compute MAE & RMSE
                errors = y_test - preds
                mae = float(np.mean(np.abs(errors)))
                rmse = float(np.sqrt(np.mean(errors ** 2)))

                metrics[model_name] = {
                    "mae": round(mae, 2),
                    "rmse": round(rmse, 2),
                }
                candidate_scores.append((rmse, model_name, ModelCls))
            except Exception as e:
                metrics[model_name] = {
                    "error": str(e),
                }

        if not candidate_scores:
            eval_result["groups"][blood_group] = {
                "status": "error",
                "history_days": history_days,
                "train_days": train_days,
                "metrics": metrics,
            }
            continue

        # Select candidate with lowest RMSE. Tie-break by candidate order
        candidate_scores.sort(key=lambda x: x[0])
        best_rmse, best_name, BestCls = candidate_scores[0]

        # Refit selected model on full history
        full_model = BestCls()
        try:
            full_model.fit(series)
            selected_models[blood_group] = full_model
        except Exception as e:
            eval_result["groups"][blood_group] = {
                "status": "error",
                "history_days": history_days,
                "train_days": train_days,
                "metrics": metrics,
            }
            continue

        eval_result["groups"][blood_group] = {
            "status": "ok",
            "selected_model": best_name,
            "train_days": train_days,
            "history_days": history_days,
            "metrics": metrics,
        }

    # Write evaluation artifact
    save_evaluation_artifact(eval_result)

    return eval_result, selected_models


def save_evaluation_artifact(eval_dict: Dict[str, Any]) -> None:
    """Save evaluation dictionary to latest_evaluation.json."""
    try:
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(EVALUATION_FILE, "w", encoding="utf-8") as f:
            json.dump(eval_dict, f, indent=2)
    except Exception as e:
        print(f"Warning: Failed to save evaluation artifact: {e}")


def load_evaluation_artifact() -> Dict[str, Any]:
    """Load latest_evaluation.json or return default empty evaluation dict."""
    if not EVALUATION_FILE.exists():
        return {
            "run_id": None,
            "generated_at": None,
            "holdout_days": None,
            "groups": {},
        }
    try:
        with open(EVALUATION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "run_id": None,
            "generated_at": None,
            "holdout_days": None,
            "groups": {},
        }
