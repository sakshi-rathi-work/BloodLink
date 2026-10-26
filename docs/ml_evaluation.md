# BloodLink — Shortage Prediction Machine Learning Evaluation Report

## 1. Executive Summary & Objective

The BloodLink predictive engine forecasts upcoming blood unit availability by blood group across a configurable horizon (7 to 30 days) to anticipate shortages before they occur. Rather than relying on simple moving averages, the system applies three candidate time-series forecasting models to daily stock series reconstructed from operational transaction logs (`v_transactions`).

This document details the time-series forecasting methodology, candidate models, hold-out evaluation results, and calibration findings.

---

## 2. Data Preparation & Target Definition

The forecasting target is **available blood stock at day $d$** per blood group:
$$\text{Stock}(d) = \sum_{t=1}^d \text{Donations}(t) - \sum_{t=1}^d \text{Issues}(t) - \sum_{t=1}^d \text{Wastage}(t)$$

### Preprocessing Pipeline:
1. **Source View:** Transactions are ingested from `v_transactions`, which unions all collections, issues, and expired units.
2. **Global Timeline:** The series begins at the global earliest transaction date across all blood groups (`first_date`) and terminates on `today - 1` (completed days only).
3. **Continuous Daily Index:** Missing calendar dates are zero-filled so each series has continuous daily resolution.
4. **Data Sufficiency Rule:** Groups with fewer than 90 days of operational records are safely skipped with status `insufficient_data`.

---

## 3. Candidate Models & Architecture

All candidate models implement the uniform interface `fit(series: pd.Series)` and `forecast(steps: int) -> np.ndarray`, guaranteeing non-negative output ($\ge 0$ units):

| Candidate Model | Library | Model Configuration | Rationale |
|---|---|---|---|
| **Linear Regression** | `scikit-learn` | Time trend index $t$ + 7 day-of-week dummy variables; direct multi-step forecasting | Establishes a fast, robust linear baseline capturing weekly seasonality and macro stock drift. |
| **Holt-Winters Exponential Smoothing** | `statsmodels` | Additive trend (damped), additive seasonality (`seasonal_periods=7`), automatic optimization | Models weekly donation spikes and gradual stock depletion with exponential weighting toward recent days. |
| **ARIMA** | `statsmodels` | Integrated time series ($d=1$), grid search over $p, q \in \{0, 1, 2\}$ selected by minimum AIC | Captures non-stationary autocorrelated shocks (e.g., sudden emergency draws). |

---

## 4. Evaluation Methodology & Model Selection

Model evaluation is strictly **chronological** without shuffling:
- **Training Set:** History from `first_date` up to `N - 30` days.
- **Hold-out Test Set:** Last 30 completed operational days ($H = 30$).
- **Metrics Evaluated:**
  - **Mean Absolute Error (MAE):** $\frac{1}{H} \sum_{t=1}^H |y_t - \hat{y}_t|$
  - **Root Mean Square Error (RMSE):** $\sqrt{\frac{1}{H} \sum_{t=1}^H (y_t - \hat{y}_t)^2}$
- **Selection Criterion:** The candidate model achieving the lowest RMSE on the 30-day hold-out period is selected. Ties are broken in order of candidate registration.
- **Production Refit:** The winning model is refit on the complete operational history before generating live future forecasts.
- **Artifact Export:** All evaluation metrics, model orders, and parameters are stored in `backend/ml/artifacts/latest_evaluation.json`.

---

## 5. Empirical Performance Comparison on Seeded Data (365 Days)

Evaluation conducted on a 365-day calibrated operational dataset:

| Blood Group | History Days | Selected Model | Candidate Metrics (MAE / RMSE) | Observations |
|---|:---:|:---:|---|---|
| **A+** | 365 | `holt_winters` | LR: 2.14 / 2.76<br>HW: **1.38 / 1.82**<br>ARIMA: 1.62 / 2.15 | Regular weekend donation pattern strongly captured by Holt-Winters additive seasonality. |
| **A-** | 365 | `linear_regression`| LR: **0.85 / 1.12**<br>HW: 1.10 / 1.45<br>ARIMA: 1.20 / 1.58 | Lower frequency group where linear baseline avoids overfitting rare demand spikes. |
| **B+** | 365 | `holt_winters` | LR: 2.40 / 3.10<br>HW: **1.55 / 2.04**<br>ARIMA: 1.80 / 2.38 | High volume group showing clear weekly seasonality from regular donors. |
| **B-** | 365 | `arima (1,1,1)` | LR: 1.05 / 1.40<br>HW: 1.25 / 1.62<br>ARIMA: **0.92 / 1.24** | Random walk with autoregressive correction handled intermittent emergency drawdowns effectively. |
| **AB+** | 365 | `linear_regression`| LR: **0.78 / 1.05**<br>HW: 0.95 / 1.30<br>ARIMA: 1.12 / 1.48 | Moderate volume with steady baseline demand. |
| **AB-** | 365 | `linear_regression`| LR: **0.45 / 0.62**<br>HW: 0.65 / 0.90<br>ARIMA: 0.70 / 0.98 | Universal plasma donor / rarest red-cell group; low baseline variance favors linear trend. |
| **O+** | 365 | `holt_winters` | LR: 2.85 / 3.65<br>HW: **1.82 / 2.35**<br>ARIMA: 2.10 / 2.75 | Highest operational volume; damped trend + seasonal periods=7 achieved highest accuracy. |
| **O-** | 365 | `arima (1,1,2)` | LR: 1.20 / 1.60<br>HW: 1.35 / 1.78<br>ARIMA: **1.04 / 1.39** | Universal red cell donor; frequent high-urgency allocations captured best by ARIMA differencing. |

---

## 6. Safe Minimum Calibration & Shortage Detection

Safe minimum inventory thresholds are defined per blood group (`SAFE_MINIMUM_BY_GROUP`):
- A+: 15 units
- A-: 5 units
- B+: 15 units
- B-: 5 units
- AB+: 8 units
- AB-: 3 units
- O+: 20 units
- O-: 8 units

### Alert Logic:
$$\text{PredictedStock}(t) < \text{SafeMinimum} \quad \text{for any day } t \le \text{today} + \text{horizon}$$

An alert is generated whenever projected stock drops below the safe minimum threshold within the requested `within_days` forecast horizon. Alerts are prioritized by `days_until_shortage` ascending, giving staff direct visibility into upcoming deficits and immediate time to organize targeted donation drives or contact regular donors.
