import numpy as np
import pandas as pd
import pytest
from ml.models.arima import ARIMAModel
from ml.models.holt_winters import HoltWintersModel
from ml.models.linear_regression import LinearRegressionModel


@pytest.fixture
def sample_stock_series():
    # 120 days of daily stock data with weekly pattern and slight trend
    dates = pd.date_range("2026-01-01", periods=120, freq="D")
    t = np.arange(120)
    # stock around 15-25 with weekly variation
    values = 15.0 + 0.05 * t + 3.0 * np.sin(2 * np.pi * t / 7) + np.random.normal(0, 0.5, 120)
    values = np.clip(values, a_min=1.0, a_max=None)
    return pd.Series(values, index=dates)


def test_linear_regression_fit_and_forecast(sample_stock_series):
    model = LinearRegressionModel()
    assert model.name == "linear_regression"

    model.fit(sample_stock_series)
    preds = model.forecast(steps=30)

    assert isinstance(preds, np.ndarray)
    assert len(preds) == 30
    assert np.all(preds >= 0.0)


def test_holt_winters_fit_and_forecast(sample_stock_series):
    model = HoltWintersModel()
    assert model.name == "holt_winters"

    model.fit(sample_stock_series)
    preds = model.forecast(steps=30)

    assert isinstance(preds, np.ndarray)
    assert len(preds) == 30
    assert np.all(preds >= 0.0)


def test_arima_fit_and_forecast(sample_stock_series):
    model = ARIMAModel()
    assert model.name == "arima"

    model.fit(sample_stock_series)
    preds = model.forecast(steps=30)

    assert isinstance(preds, np.ndarray)
    assert len(preds) == 30
    assert np.all(preds >= 0.0)
    assert model.best_order is not None
