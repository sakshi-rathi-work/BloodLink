from abc import ABC, abstractmethod
import numpy as np
import pandas as pd


class BaseTimeSeriesModel(ABC):
    name: str = "base_model"

    @abstractmethod
    def fit(self, series: pd.Series) -> "BaseTimeSeriesModel":
        """Fit model on the given time series."""
        pass

    @abstractmethod
    def forecast(self, steps: int) -> np.ndarray:
        """Forecast the next `steps` values. Return 1D ndarray clipped >= 0."""
        pass
