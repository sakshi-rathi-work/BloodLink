import json
import os
from pathlib import Path
from typing import Dict

# 8 standard blood groups
BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

# Core thresholds
MIN_HISTORY_DAYS = int(os.getenv("PREDICTION_MIN_HISTORY_DAYS", "90"))
HOLDOUT_DAYS = int(os.getenv("PREDICTION_HOLDOUT_DAYS", "30"))
DEFAULT_HORIZON_DAYS = 30
SAFE_MINIMUM_UNITS_DEFAULT = int(os.getenv("SAFE_MINIMUM_UNITS_DEFAULT", "10"))

# Artifacts
ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
EVALUATION_FILE = ARTIFACTS_DIR / "latest_evaluation.json"


def get_default_safe_minimums() -> Dict[str, int]:
    """Parse SAFE_MINIMUM_BY_GROUP from env if present, else fallback to SAFE_MINIMUM_UNITS_DEFAULT."""
    raw = os.getenv("SAFE_MINIMUM_BY_GROUP", "{}")
    overrides = {}
    try:
        overrides = json.loads(raw)
    except Exception:
        overrides = {}

    return {
        bg: int(overrides.get(bg, SAFE_MINIMUM_UNITS_DEFAULT))
        for bg in BLOOD_GROUPS
    }
