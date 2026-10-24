import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from ml.models.base import BaseTimeSeriesModel


class LinearRegressionModel(BaseTimeSeriesModel):
    name: str = "linear_regression"

    def __init__(self):
        self.model = LinearRegression()
        self.last_date = None
        self.n_samples = 0

    def _build_features(self, dates: pd.DatetimeIndex, start_t: int) -> np.ndarray:
        n = len(dates)
        t = np.arange(start_t, start_t + n).reshape(-1, 1)

        # Day of week one-hot encoding (7 days)
        dow = dates.dayofweek.values
        dow_one_hot = np.zeros((n, 7))
        for i in range(7):
            dow_one_hot[:, i] = (dow == i).astype(float)

        return np.hstack([t, dow_one_hot])

    def fit(self, series: pd.Series) -> "LinearRegressionModel":
        self.n_samples = len(series)
        dates = pd.to_datetime(series.index)
        self.last_date = dates[-1]

        X = self._build_features(dates, start_t=0)
        y = series.values.astype(float)

        self.model.fit(X, y)
        return self

    def forecast(self, steps: int) -> np.ndarray:
        if self.last_date is None or self.n_samples == 0:
            raise RuntimeError("Model must be fitted before forecasting.")

        future_dates = pd.date_range(
            start=self.last_date + pd.Timedelta(days=1),
            periods=steps,
            freq="D",
        )
        X_future = self._build_features(future_dates, start_t=self.n_samples)
        preds = self.model.predict(X_future)
        return np.clip(preds, a_min=0.0, a_max=None)
