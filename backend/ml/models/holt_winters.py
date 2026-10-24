import warnings
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from ml.models.base import BaseTimeSeriesModel


class HoltWintersModel(BaseTimeSeriesModel):
    name: str = "holt_winters"

    def __init__(self):
        self.fitted_model = None

    def fit(self, series: pd.Series) -> "HoltWintersModel":
        # Ensure daily frequency
        s = series.copy()
        s.index = pd.to_datetime(s.index)
        if s.index.freq is None:
            s = s.asfreq("D")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Try additive trend (damped) + additive seasonality with period 7
            try:
                model = ExponentialSmoothing(
                    s,
                    trend="add",
                    damped_trend=True,
                    seasonal="add",
                    seasonal_periods=7,
                    initialization_method="estimated",
                )
                self.fitted_model = model.fit(optimized=True)
            except Exception:
                # Fallback: trend without seasonality if seasonality fails
                model = ExponentialSmoothing(
                    s,
                    trend="add",
                    damped_trend=True,
                    seasonal=None,
                    initialization_method="estimated",
                )
                self.fitted_model = model.fit(optimized=True)

        return self

    def forecast(self, steps: int) -> np.ndarray:
        if self.fitted_model is None:
            raise RuntimeError("Model must be fitted before forecasting.")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            preds = self.fitted_model.forecast(steps)

        preds_array = np.asarray(preds, dtype=float)
        return np.clip(preds_array, a_min=0.0, a_max=None)
