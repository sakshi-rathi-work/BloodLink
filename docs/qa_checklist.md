# BloodLink — Quality Assurance & End-to-End Verification Checklist

> **Document Status:** Comprehensive System Quality Gate  
> **Target Version:** 1.0.0 (Production Release)  
> **System Scope:** Modules 1–7 (Auth & Admin, Donors, Inventory, Requests & Issuing, Compatibility Matching, Predictions & Alerts, Dashboard & Reports)  
> **Personas Evaluated:** Administrator (`admin`), Blood Bank Staff (`staff`), Hospital / Clinic Requester (`requester`)  
> **Last Verified Date:** 2026-10-24  

---

## 1. Executive Summary & Verification Sign-off

| Evaluation Area | Scope | Verification Status | Verified By |
|---|---|:---:|---|
| **Role-Based Access Control (RBAC)** | Route protections, 401 unauthenticated, 403 role mismatch, disabled accounts | **PASSED** | Esha (Automated & Manual QA) |
| **Audit Trail & Immutability** | State transitions write activity log entries in same transaction | **PASSED** | Esha (Automated & Manual QA) |
| **Donor Management & Eligibility** | Demographics, 18–65 age, ≥50kg weight, 90-day gap, regular donor flag | **PASSED** | Esha (Automated & Manual QA) |
| **Inventory & Expiry Engine** | 42-day shelf life, startup sweep, scheduler job, safe-minimum alerts | **PASSED** | Esha (Automated & Manual QA) |
| **Request & Issuing Lifecycle** | Urgent/Routine sort, compatibility engine, atomic row-locked allocation | **PASSED** | Esha (Automated & Manual QA) |
| **Predictive Analytics & ML** | 7–30 day horizon, holdout evaluation, best RMSE selection, alert triggers | **PASSED** | Esha (Automated & Manual QA) |
| **Executive Dashboard & Reporting** | Real-time counters, zero-filled trends, ReportLab PDF and CSV generators | **PASSED** | Esha (Automated & Manual QA) |
| **Frontend UI/UX Quality** | Responsive design, keyboard navigation, toast UX, empty/loading states | **PASSED** | Esha (Automated & Manual QA) |

---

## 2. Test Environment Specification

- **Backend Runtime:** FastAPI, Python 3.12, SQLAlchemy 2.x, Alembic, Pydantic v2.
- **Database Engine:** PostgreSQL 16 (production/staging container) / SQLite compatibility layer for isolated unit tests.
- **Frontend Stack:** React 18, Vite, Tailwind CSS, React Router v6, Axios, Recharts, Lucide Icons.
- **Prediction Package:** `backend/ml/` (scikit-learn, statsmodels, pandas, numpy).
- **Report Engine:** ReportLab (landscape PDF table generator, running headers, pagination).

---

## 3. Persona-Specific End-to-End Verification Matrix

### 3.1 Persona 1: Hospital / Clinic Requester (`requester`)

| ID | Test Scenario | Expected Outcome | Actual Result | Status |
|:---:|---|---|---|:---:|
| **REQ-01** | **Self-Registration (`POST /api/auth/register`)** | User account created with `role='requester'`, profile saved in `requesters` table, JWT returned. | Requester registered and auto-redirected to `/my/requests`. | **PASSED** |
| **REQ-02** | **Portal Isolation & Unauthorized Routes** | Requester cannot access `/dashboard`, `/donors`, `/inventory`, `/predictions`, `/camps`, `/admin/*`. | Redirected / blocked with 403 Forbidden. | **PASSED** |
| **REQ-03** | **Submit Emergency Request (`POST /api/requests`)** | Form accepts blood group, quantity, emergency urgency, patient name, and hospital notes. Request saved with `status='pending'`. | Form validates input, dispatches request, shows success toast. | **PASSED** |
| **REQ-04** | **Submit Routine Request (`POST /api/requests`)** | Routine urgency selected. Form validation enforces positive quantity and required fields. | Request created and visible on `/my/requests`. | **PASSED** |
| **REQ-05** | **Data Isolation (Anti-Tampering)** | Requester only sees requests belonging to their own `requester_id`. Querying another requester's request returns 404. | Strict isolation enforced in API and UI. | **PASSED** |
| **REQ-06** | **Profile Management (`GET/PATCH /api/requesters/me`)** | Requester can update contact name, phone, and hospital address. | Updates persisted and confirmed via toast. | **PASSED** |

---

### 3.2 Persona 2: Blood Bank Staff Member (`staff`)

| ID | Test Scenario | Expected Outcome | Actual Result | Status |
|:---:|---|---|---|:---:|
| **STF-01** | **Staff Authentication & Dashboard Navigation** | Staff logs in with username/password. Navigates to `/dashboard`. | Login successful; JWT stored; redirects to executive dashboard. | **PASSED** |
| **STF-02** | **Donor Registration (`POST /api/donors`)** | Validates DOB (age 18–65), weight (≥50 kg), valid blood group. Regular donor badge inactive initially. | Donor created with initial demographics. | **PASSED** |
| **STF-03** | **Eligibility Engine Check (`GET /api/donors/{id}/eligibility`)** | Ineligible donor (e.g. donated 30 days ago) receives `eligible=false` with reason code `DONATION_GAP_NOT_MET`. | Correct reasons surfaced on UI card; Record Donation button blocked. | **PASSED** |
| **STF-04** | **Record Donation (`POST /api/donors/{id}/donations`)** | Creates unit in `blood_units` with collection date = `today()`, expiry date = `today() + 42 days`, status `available`. | Unit created; donor's `last_donation_date` updated; success toast displayed. | **PASSED** |
| **STF-05** | **Inventory Management & Expiry Tracking** | `/inventory` displays stock counts by blood group with low-stock warning (< 10 units). Expiring-soon tab highlights units expiring within 7 days. | Accurate stock counts displayed; expiring units filtered. | **PASSED** |
| **STF-06** | **Manual Expiry Sweep (`POST /api/inventory/expire-overdue`)** | Overdue available units are transitioned to `expired` status and logged as wastage in `v_transactions`. | Expired units decremented from available stock; status shows `expired`. | **PASSED** |
| **STF-07** | **Request Queue Prioritization (`GET /api/requests?sort=priority`)** | Emergency requests appear at the top of the queue, followed by oldest routine requests. | Emergency badge displayed; priority sort order confirmed. | **PASSED** |
| **STF-08** | **Compatibility Matching & Allocation Preview** | Staff clicks into request detail. System lists all compatible units ranked nearest-expiry-first. Sufficiency badge reflects stock. | Allocation preview matches Section 6.3 compatibility rules. | **PASSED** |
| **STF-09** | **Atomic Issuing (`POST /api/requests/{id}/issue`)** | Locks rows with `FOR UPDATE`. Sets unit status to `issued`, creates `issue_records`, transitions request to `issued`. Decrements inventory. | Atomic fulfillment succeeds; issue records link donor, unit, request, and staff. | **PASSED** |
| **STF-10** | **Insufficient Stock Handling** | Attempting to issue when insufficient units exist raises 409 `INSUFFICIENT_STOCK` without modifying inventory. | Error banner shows requested vs available units; zero state mutation. | **PASSED** |
| **STF-11** | **Donation Camps Management (`/camps`)** | Staff creates, updates, and tracks donation camps (location, date, target units, units collected). | Camp listed with interactive collection progress bar. | **PASSED** |
| **STF-12** | **Predictive Shortage Analytics (`/predictions`)** | Staff triggers prediction run. Horizon selector (7–30 days). Model evaluation comparison table displays MAE/RMSE and winning model. Forecast chart shows safe-minimum line. | Pipeline executes synchronously; forecasts and alerts render cleanly. | **PASSED** |
| **STF-13** | **Multi-Format Report Generation (`/reports`)** | Staff generates CSV and ReportLab PDF for all 7 domains (`stock`, `donations`, `issues`, `wastage`, `donors`, `requests`, `predictions`). | CSV parses cleanly; PDF streams valid `%PDF-` document with repeated headers and landscape pagination. | **PASSED** |
| **STF-14** | **Admin Route Guard Enforcement** | Staff attempts to navigate to `/admin/staff` or `/admin/activity-log`. | Route blocked by `ProtectedRoute`; sidebar hides admin section. | **PASSED** |

---

### 3.3 Persona 3: System Administrator (`admin`)

| ID | Test Scenario | Expected Outcome | Actual Result | Status |
|:---:|---|---|---|:---:|
| **ADM-01** | **Admin Access to Full Suite** | Admin possesses all staff permissions plus exclusive administration screens. | Admin layout displays both Operations and Administration sidebar menus. | **PASSED** |
| **ADM-02** | **Staff Account Provisioning (`POST /api/staff`)** | Admin creates new staff user with username, initial password, and staff profile. | Account created; credentials hashed with bcrypt; user can log in. | **PASSED** |
| **ADM-03** | **Staff Account Deactivation & Role Editing** | Admin deactivates staff account or changes role between `staff` and `admin`. | Deactivated user receives 403 `ACCOUNT_DISABLED` on subsequent requests. | **PASSED** |
| **ADM-04** | **Self-Modification & Deletion Guard** | Admin attempts to deactivate, demote, or delete their own active account. | Blocked with 409 `SELF_MODIFICATION_FORBIDDEN`. | **PASSED** |
| **ADM-05** | **Password Reset Utility (`POST /api/staff/{id}/reset-password`)** | Admin resets staff user password. Old password invalidated; new password active immediately. | Password updated with bcrypt; user logs in with new password. | **PASSED** |
| **ADM-06** | **Activity Log Audit Trail (`GET /api/activity-logs`)** | Paginated audit log table displaying user, action, entity type, timestamp, IP, and JSON details. | Complete immutable log visible; JSON viewer modal displays payload details. | **PASSED** |
| **ADM-07** | **Exclusive Deletion Rights** | Only Admin can delete records (donors, units, requests, camps, staff). Referential integrity enforced (`ON DELETE RESTRICT`). | Admin can delete unreferenced records; referenced records blocked with 409 `REFERENCED_RECORD`. | **PASSED** |

---

## 4. Non-Functional & Security Quality Gate

| Category | Requirement | Acceptance Criteria | Result |
|---|---|---|:---:|
| **Authentication** | JWT Bearer Token | 60-minute expiration, HS256 algorithm, sub=user_id. | **PASSED** |
| **Password Security** | Bcrypt direct hashing | Stored as bcrypt hash; `password_hash` never serialized in any API response. | **PASSED** |
| **Data Protection** | CORS policy | Restricted to configured frontend origins (`localhost:5173`, `localhost:3000`). | **PASSED** |
| **Error Standardization** | Uniform Error Envelope | `{detail: {code, message}}` across all endpoints. | **PASSED** |
| **Concurrency Safety** | All-or-nothing allocation | `SELECT ... FOR UPDATE` prevents race conditions during unit issuing. | **PASSED** |
| **Deterministic Time** | Clock centralized | `app.core.clock.today()` used universally; freeze time in test suites. | **PASSED** |
| **Frontend Code Quality** | Vanilla JavaScript + Vite | 0 ESLint errors/warnings; production build bundle generates cleanly. | **PASSED** |

---

## 5. Verification Sign-Off

- **Lead QA Engineer & Phase Owner:** Esha
- **Date:** 2026-10-24
- **Recommendation:** Production Release Ready. All Phase 1–6 requirements verified.
