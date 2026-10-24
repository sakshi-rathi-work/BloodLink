# BloodLink — Living Handoff & Phase Progress Document

## 1. Project Identity & Ownership
- **Project Name:** BloodLink — Blood Bank Management & Availability Prediction System
- **Completed Phases & Owners:**
  - **Sakshi:** Phase 1 (Foundation & Setup) & Phase 2 (Donors, Inventory & Compatibility) — `COMPLETE`.
  - **Saee:** Phase 3 (Requests & Issuing) & Phase 4 (Shortage Prediction) — `COMPLETE`.
- **Upcoming Phases & Owner:**
  - **Esha:** Phase 5 (Dashboard, Reports, Camps & Admin Screens) & Phase 6 (QA & Hardening) — `READY_TO_START`.

---

## 2. Current Phase, Task & Subtask
- **Current Phase:** Phase 5 — Dashboard, Reports, Camps & Admin Screens (Assigned to Esha)
- **Current Status:** Phases 1–4 are 100% COMPLETE. 83/83 pytest tests passing on PostgreSQL in Docker; frontend lint clean (0 errors, 0 warnings); production build clean (0 errors, built in ~12.8s). Ready for Esha to begin Phase 5.

---

## 3. Status Table per Task

| Task | Description | Status | Evidence |
|---|---|---|---|
| **Orientation (Part C)** | Repository mapping, environment discovery, baseline execution | **VERIFIED** | Baseline pytest 47/47 passed on real PostgreSQL (`bloodlink_test`); npm run lint 0 errors; npm run build 0 errors. |
| **Task 3.1** | Requesters schemas & endpoints (`/api/requesters`, `/me`) | **VERIFIED** | Implemented in `app/api/requesters.py` & `schemas/requester.py`. Tested in `tests/api/test_requesters.py`. |
| **Task 3.2** | Requests CRUD & list (`/api/requests`, priority/newest sort) | **VERIFIED** | Implemented in `app/api/requests.py` & `schemas/request.py`. Tested in `tests/api/test_requests.py`. |
| **Task 3.3** | Request matches endpoint (`/api/requests/{id}/matches`) | **VERIFIED** | Implemented using `services/matching.py`. Returns `compatible_groups`, `available_compatible_count`, `sufficient`, `preview`. |
| **Task 3.4** | Workflow state machine & atomic issuing (`services/issuing.py`) | **VERIFIED** | Implemented in `app/services/issuing.py`. Single-transaction row locking with `FOR UPDATE` on requests and candidate units. Tested in `tests/unit/test_issuing.py`. |
| **Task 3.5** | Phase 3 backend tests (unit, state transitions, API, concurrency) | **VERIFIED** | 21 Phase 3 tests passed. Total backend tests reached 68/68. |
| **Task 3.6** | Frontend API client for requests & requesters | **VERIFIED** | Implemented in `frontend/src/api/requests.js` & `requesters.js`. |
| **Task 3.7** | Requester portal pages (`MyRequestsPage`, `NewRequestPage`, `MyRequestDetailPage`, `MyProfilePage`) | **VERIFIED** | Fully functional UI pages with forms, status badges, and detail views. |
| **Task 3.8** | Staff request screens (`RequestQueuePage`, `RequestDetailPage`) | **VERIFIED** | Queue with priority/status filters; detail page with matches inspection, approve, reject, and atomic issue modals. |
| **Task 3.9** | Requesters list screen (`RequestersPage`) | **VERIFIED** | Paginated table with search by name/phone and type filter. |
| **Task 4.1** | Synthetic Data Generator (`scripts/seed_synthetic_data.py`) | **VERIFIED** | Day-by-day 365-day simulation with safety guards (loopback, PostgreSQL dialect, database allowlist), 180 donors, calibrated stock. |
| **Task 4.2** | ML Data Layer (`backend/ml/data.py`) | **VERIFIED** | Daily stock aggregation from `v_transactions` view, continuous date index, tested in `tests/ml/test_data.py`. |
| **Task 4.3** | Candidate Models (`backend/ml/models/`) | **VERIFIED** | `LinearRegressionModel`, `HoltWintersModel` (period=7), `ARIMAModel` (grid search p,q in {0,1,2}, d=1). Tested in `tests/ml/test_models.py`. |
| **Task 4.4** | Holdout Evaluation & Model Selection (`backend/ml/evaluation.py`) | **VERIFIED** | Chronological holdout, RMSE selection, fallback to linear regression, artifact written to `latest_evaluation.json`. Tested in `tests/ml/test_evaluation.py`. |
| **Task 4.5** | Prediction Pipeline & Persistence (`backend/ml/pipeline.py`, `persistence.py`) | **VERIFIED** | Appends forecasts to `shortage_predictions` table. Never overwrites historical runs. Tested in `tests/ml/test_pipeline.py`. |
| **Task 4.6** | ML CLI (`backend/ml/cli.py`) | **VERIFIED** | `python -m ml.cli run --horizon 30` and `python -m ml.cli evaluate` execute successfully. |
| **Task 4.7** | Prediction API & Alerts Service (`app/api/predictions.py`, `services/prediction_alerts.py`) | **VERIFIED** | `POST /api/predictions/run`, `GET /api/predictions/latest`, `GET /api/predictions/alerts`, `GET /api/predictions/evaluation`. RBAC tested in `tests/api/test_predictions.py`. |
| **Task 4.8** | Phase 4 Tests | **VERIFIED** | 15 Phase 4 tests passed (data, models, evaluation, pipeline, seeder, API). Total suite: 83/83 passed. |
| **Task 4.9** | Frontend Predictions Page & Chart | **VERIFIED** | `ForecastChart.jsx` (Recharts with safe-minimum reference line) and `PredictionsPage.jsx` (blood group tabs, alert cards, evaluation comparison table, run trigger). |
| **Task 4.10** | Evaluation Report Documentation | **VERIFIED** | Written in `docs/ml_evaluation.md`. |

---

## 4. Completed Work in this Iteration
- Created missing `backend/tests/ml/__init__.py` to ensure package discovery by pytest.
- Fixed `activity_log.record()` call in `backend/app/api/predictions.py` where `entity_id` was being passed as a UUID string to an `INTEGER` database column; updated to `entity_id=None` with `run_id` placed in `details` JSONB per architectural specification Section 15 / Decision D9.
- Updated `backend/tests/api/test_predictions.py` to handle both cold test database states and populated states, adding an explicit populated test `test_predictions_with_populated_predictions`.
- Executed the complete backend test suite: **83 passed in 61.80s** against PostgreSQL 16 on Docker (`bloodlink_test`).
- Executed frontend linting: `npm run lint` exited code 0 with **0 errors, 0 warnings**.
- Executed frontend production build: `npm run build` exited code 0 (**built dist cleanly in 12.84s**).
- Synchronized `IMPLEMENTATION_PLAN.md` to reflect Phase 3 and Phase 4 completion and assigned Phase 5 to Esha.

---

## 5. Files Created / Modified
- `backend/tests/ml/__init__.py`: Created package marker.
- `backend/app/api/predictions.py`: Modified (entity_id=None in activity log).
- `backend/tests/api/test_predictions.py`: Modified (added assertions and populated prediction test).
- `IMPLEMENTATION_PLAN.md`: Synchronized (Phases 1–4 COMPLETE, Phase 5 READY_TO_START).
- `HANDOFF.md`: Updated with full verification evidence and instructions for Esha.

---

## 6. Verification Summary
- **Backend Test Suite:**
  - Command: `.\.venv\Scripts\pytest.exe -rs -q` (executed in `backend/`)
  - Target: Real PostgreSQL 16 running via Docker (`bloodlink_test`)
  - Result: `83 passed, 1 warning in 61.80s` (100% pass)
- **Frontend Quality:**
  - `npm run lint`: `0 errors, 0 warnings`
  - `npm run build`: `built in 12.84s`, 0 errors.

---

## 7. Instructions for Incoming Developer (Esha — Phase 5 & 6)
1. **Scope:** Esha owns **Phase 5** (Dashboard, Reports, Camps & Admin Screens) and **Phase 6** (QA & Hardening).
2. **Reusable Components Available:**
   - `app/services/prediction_alerts.py`: Reusable function `compute_shortage_alerts(db, within_days)` ready to be embedded into Phase 5 executive dashboard widgets.
   - `scripts/seed_synthetic_data.py`: Run `python scripts/seed_synthetic_data.py --reset --yes` to seed realistic demo data whenever demonstrating dashboard charts, camps, and reports.
   - `frontend/src/components/charts/ForecastChart.jsx`: Reference for Recharts usage in dashboard analytics.
3. **Phase 5 Requirements:**
   - Executive Dashboard (`/api/dashboard`): KPI summary cards (total stock, units expiring in 7 days, pending requests, active camps, critical shortages), 30-day donation vs. issue trend, wastage by reason chart, and shortage alert cards.
   - Reports Engine (`/api/reports`): ReportLab PDF and CSV generation for 7 report types (Inventory Summary, Expiry Audit, Donor Activity, Issuance Log, Request Fulfillment, Wastage Analysis, Shortage Forecast).
   - Donation Camps (`/api/camps`): CRUD, status management (upcoming, active, completed, cancelled), and staff assignment.
   - Admin Views: Staff management CRUD, user role management, and activity log audit viewer.
