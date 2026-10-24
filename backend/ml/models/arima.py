import warnings
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from ml.models.base import BaseTimeSeriesModel


class ARIMAModel(BaseTimeSeriesModel):
    name: str = "arima"

    def __init__(self):
        self.fitted_model = None
        self.best_order = None

    def fit(self, series: pd.Series) -> "ARIMAModel":
        s = series.copy()
        s.index = pd.to_datetime(s.index)
        if s.index.freq is None:
            s = s.asfreq("D")

        best_aic = float("inf")
        best_fit = None
        best_order = None

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Grid search p, q in {0, 1, 2} with d=1
            for p in [0, 1, 2]:
                for q in [0, 1, 2]:
                    try:
                        model = ARIMA(s, order=(p, 1, q))
                        fit_res = model.fit()
                        if fit_res.aic < best_aic:
                            best_aic = fit_res.aic
                            best_fit = fit_res
                            best_order = (p, 1, q)
                    except Exception:
                        continue

            if best_fit is None:
                # Ultimate fallback: ARIMA(0, 1, 0) random walk
                model = ARIMA(s, order=(0, 1, 0))
                best_fit = model.fit()
                best_order = (0, 1, 0)

        self.fitted_model = best_fit
        self.best_order = best_order
        return self

    def forecast(self, steps: int) -> np.ndarray:
        if self.fitted_model is None:
            raise RuntimeError("Model must be fitted before forecasting.")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            preds = self.fitted_model.forecast(steps)

        preds_array = np.asarray(preds, dtype=float)
        return np.clip(preds_array, a_min=0.0, a_max=None)
