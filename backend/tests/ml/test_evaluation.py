import numpy as np
import pandas as pd
import pytest
from ml.evaluation import evaluate_and_select_models, load_evaluation_artifact


def test_evaluate_and_select_models():
    dates = pd.date_range("2026-01-01", periods=100, freq="D")
    t = np.arange(100)
    series_a = pd.Series(10.0 + 0.1 * t, index=dates)

    group_data = {
        "A+": {
            "status": "ok",
            "series": series_a,
            "history_days": 100,
        },
        "AB-": {
            "status": "insufficient_data",
            "series": None,
            "history_days": 20,
        },
    }

    eval_dict, fitted_models = evaluate_and_select_models(
        group_data=group_data,
        holdout_days=30,
    )

    assert "run_id" in eval_dict
    assert eval_dict["holdout_days"] == 30
    assert eval_dict["groups"]["A+"]["status"] == "ok"
    assert "selected_model" in eval_dict["groups"]["A+"]
    assert "metrics" in eval_dict["groups"]["A+"]
    assert eval_dict["groups"]["AB-"]["status"] == "insufficient_data"

    assert "A+" in fitted_models
    assert "AB-" not in fitted_models

    # Verify loading artifact
    loaded = load_evaluation_artifact()
    assert loaded["run_id"] == eval_dict["run_id"]
