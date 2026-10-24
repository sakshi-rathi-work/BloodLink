from ml.models.base import BaseTimeSeriesModel
from ml.models.linear_regression import LinearRegressionModel
from ml.models.holt_winters import HoltWintersModel
from ml.models.arima import ARIMAModel

CANDIDATE_MODELS = [
    LinearRegressionModel,
    HoltWintersModel,
    ARIMAModel,
]

__all__ = [
    "BaseTimeSeriesModel",
    "LinearRegressionModel",
    "HoltWintersModel",
    "ARIMAModel",
    "CANDIDATE_MODELS",
]
