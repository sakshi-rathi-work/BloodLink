"""
BloodLink Shortage Prediction Package (Standalone ML Engine).
Must not import from backend/app/ to ensure independence.
"""

from ml.pipeline import run_prediction, RunResult

__all__ = ["run_prediction", "RunResult"]
