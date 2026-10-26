# BloodLink — Blood Bank Management & Availability Prediction System

> **Mini Project** · Domain: Healthcare Informatics · AI/ML
> Core areas: Database Management Systems · Python for Data Science · Software Engineering
> Team: **Sakshi** (Phases 1–2) · **Saee** (Phases 3–4) · **Esha** (Phases 5–6) — work is divided by phase

---

## 0. How to Use This Document (READ FIRST — especially for AI coding agents)

This file is the **single source of truth** for building BloodLink. It is designed so that an AI coding agent (or a human) can build the entire project from it.

**Rules for the builder:**

1. **Build in phase order** (Section 15). Phases are strictly sequential: do not start a phase until the previous phase's exit criteria are met. Each phase is owned end-to-end (database, backend, frontend, tests) by one team member (Section 14).
2. **Follow the contracts exactly**: table/column names (Section 7), endpoint paths, request/response shapes, status codes and error codes (Section 8), config names (Section 12). Other team members code against these contracts in parallel — a silent deviation breaks their work.
3. **Do not invent features.** Anything not described here is out of scope (see Section 1.4). If something is genuinely ambiguous, use the documented default in Section 2 or ask the team — do not guess.
4. **Business rules live in the backend.** The frontend may mirror validations for UX, but the backend is the authority.
5. **All tunable numbers are configuration**, never hard-coded (Section 12).
6. **Dates:** the backend must obtain "today" from one helper function (`app/core/clock.py → today()`), never by calling `date.today()` all over the code, so that tests can freeze time.
7. **Every state-changing endpoint writes an activity-log entry** (Section 6.9) in the same DB transaction as the change.
8. **Language/stack constraints:** backend is Python (FastAPI); frontend is **JavaScript (not TypeScript)** with React.

---

## 1. Project Overview

### 1.1 Vision

BloodLink is a blood bank management platform that goes beyond record-keeping. It digitizes the day-to-day operations of a blood bank — donor management, inventory, requests, and issuing — and adds a predictive layer that estimates upcoming shortages of specific blood groups **before** they happen.

The mini project first builds a complete, working operational system (one a real blood bank could use to manage donors, stock, and requests). On top of it, a lightweight, explainable prediction module uses historical donation and usage data to flag blood groups likely to run low in the near future, giving staff time to act (organize a donation camp, contact regular donors) instead of reacting after stock has run out.

### 1.2 Problem Statement

Many blood banks, especially smaller ones, rely on registers or disconnected spreadsheets. This causes:

- No real-time visibility into which blood groups are running low.
- Manual matching of donor/stock blood group to patient requirement — slow during emergencies.
- Blood units expiring unused (shelf life roughly 35–42 days) because expiry is not tracked proactively.
- No way to anticipate shortages — staff only discover unavailability when a request cannot be fulfilled.
- Donor eligibility (90-day gap between donations, age/weight limits) tracked manually or not at all.

BloodLink addresses these with a properly structured database plus a simple, explainable prediction model — turning blood bank management from reactive to proactive.

### 1.3 In Scope

- Single blood bank operation (one physical location).
- Donor registration, eligibility tracking, and donation history.
- Blood stock inventory with expiry tracking.
- Blood request handling and issuing workflow.
- Compatibility-based matching between requested blood group and available stock.
- Shortage prediction model based on historical donation and usage trends.
- Reporting dashboard with key statistics, exportable reports (PDF/CSV).
- Role-based access: Admin, Blood Bank Staff, Hospital/Requester.

### 1.4 Out of Scope (reserved for future extension — do NOT build)

- Multiple blood banks / inter-bank transfer network.
- Real-time SMS/email donor alerts (in-app alerts only).
- Deep learning or image-based models.
- Routing / maps.
- Any blood component other than whole-blood/red-cell compatibility (no plasma/platelet rules).

### 1.5 Final Deliverables

At the end of the project BloodLink must be a complete, working system capable of:

- Managing donor records and enforcing eligibility rules
- Tracking blood inventory with expiry-aware stock management
- Handling requests end-to-end, from submission to issue
- Automatically matching compatible stock to requests
- Predicting upcoming shortages by blood group using historical data
- Presenting all of the above through a staff dashboard with exportable reports

---

## 2. Decision Log

Everything the original project document left open, plus everything this plan adds. **Nothing here is hidden — change a default by changing config, and update this table.**

### 2.1 Confirmed by the team

| # | Decision |
|---|----------|
| 1 | Backend framework: **FastAPI** |
| 2 | Database: **PostgreSQL** |
| 3 | PDF reports: **ReportLab** |
| 4 | Prediction approach: **regression baseline + statsmodels time-series models (Holt-Winters, ARIMA)**, compared on held-out data; **configurable safe-minimum threshold per blood group** |
| 5 | Eligibility: age **18–65**, weight **≥ 50 kg**, gap **90 days**; fixed blood shelf life **42 days**; all configurable |
| 6 | A **synthetic data generator** seeds realistic history for training and demo |
| 7 | Hospital/Requester users **self-register and log in** to submit requests themselves |
| 8 | Extra tables allowed: `users`, `activity_logs`, `shortage_predictions` |
| 9 | Auth: **JWT**. Frontend: **React + Vite + Tailwind CSS in plain JavaScript (no TypeScript)**. **Docker Compose for the database only** |
| 10 | **6 phases**, no fixed dates/deadlines |
| 11 | Work is divided **by phase**, not by layer: Sakshi owns Phases 1–2, Saee Phases 3–4, Esha Phases 5–6; each owner builds backend + frontend + tests for their phases |

### 2.2 Deviations from the original document's schema (and why)

| Original | This plan | Reason |
|----------|-----------|--------|
| `Staff(role, username, password_hash)` | Moved to new `users` table; `staff` keeps `staff_id`, `user_id`, `name` | Requesters must also log in (decision 7). One login table avoids duplicated credential columns (3NF). |
| `Requester` had no credentials | Added `user_id` FK to `users` | Same reason. |
| `DonationCamp.date` | Column named `camp_date` | `date` is a SQL type name; avoids quoting problems. |
| No transaction table | Read-only SQL **view** `v_transactions` | Workflow step 8 ("Transaction logged: donation / issue / wastage") is satisfied by deriving transactions from `blood_units` and `issue_records`, avoiding duplicated data. |
| `request_date`, `issue_date` unspecified type | Both `DATE` | Keeps day-level aggregation timezone-free. Same-day ordering uses `request_id` (monotonic). |
| Donation entity not listed | **A donation = one `blood_units` row** | Document states "donation recorded → blood unit added to inventory" and "a donor can contribute many blood units". Donation history = a donor's units. |

### 2.3 Defaults chosen by the planner (not stated in the original document)

All are configurable or trivially changeable. Items marked ⚙ are in `.env`.

| Item | Default |
|------|---------|
| Age bounds | Inclusive: 18 ≤ age ≤ 65 ⚙ |
| Donation gap | Eligible when `today − last_donation_date ≥ 90` days ⚙ |
| Unit expiry | `expiry_date = collection_date + 42 days` ⚙. A unit is **usable** while `expiry_date ≥ today`; it is **expired** when `expiry_date < today` |
| "Regular donor" | A donor with ≥ **3** donations ⚙ |
| Safe minimum stock | **10 units** per blood group ⚙ (overridable per group). Also used for "low stock" highlighting on the dashboard |
| "Nearing expiry" window | **7 days** ⚙ |
| Prediction minimum history | **90 days** of history per group, otherwise group is skipped ⚙ |
| Prediction hold-out | Last **30 days** ⚙ |
| Prediction horizon | Default **30 days**, allowed **7–30** |
| JWT lifetime | **60 minutes** ⚙, no refresh tokens |
| Password minimum length | **8** characters |
| Gender values | `male`, `female`, `other` |
| Urgency values | `emergency`, `routine` (from the original "emergency vs. routine") |
| Request quantity | Integer ≥ 1 (no upper bound) |
| Stock reservation | **None.** Approval does not reserve units; units are allocated at issue time |
| Issuing | **All-or-nothing**: a request is issued only if all `quantity` compatible units are available; otherwise nothing changes (HTTP 409) |
| Who creates requests | Only users with role `requester` |
| Pagination | `page_size` default 20, max 100 |
| Python / Node / PostgreSQL | Python 3.11+, current Node LTS, PostgreSQL 16 (docker image `postgres:16`) |
| Charts library | Recharts |
| Scheduler | APScheduler (daily expiry job) |
| Prediction run | Synchronous request (small data); switch to background task only if it proves slow |
| Evaluation storage | JSON file `backend/ml/artifacts/latest_evaluation.json` (not a DB table) |

---

## 3. Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React (Vite) + **JavaScript** + Tailwind CSS; React Router; Axios; Recharts |
| Backend | **FastAPI** (Python 3.11+), Uvicorn, Pydantic v2 + pydantic-settings |
| ORM / Migrations | SQLAlchemy 2.x + Alembic; PostgreSQL driver `psycopg` (v3, `psycopg[binary]`) |
| Database | **PostgreSQL 16** (via Docker Compose) |
| Auth | JWT (PyJWT), password hashing with `bcrypt` (use the `bcrypt` package directly) |
| Scheduling | APScheduler (`BackgroundScheduler`) for the daily expiry job |
| Analytics / Prediction | Python: pandas, numpy, scikit-learn, statsmodels |
| Reporting | PDF via **ReportLab**; CSV via Python `csv` |
| Testing | pytest + httpx (FastAPI TestClient); frontend manual/E2E checklist |
| Version control | Git + GitHub, shared repository |
| Containers | Docker Compose — **PostgreSQL only** (backend/frontend run locally) |

Dependency policy: do not pin versions in this document. On first successful install, freeze exact versions into `requirements.txt` / `package.json`.

`backend/requirements.txt` (unpinned list): `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `alembic`, `psycopg[binary]`, `pydantic`, `pydantic-settings`, `PyJWT`, `bcrypt`, `APScheduler`, `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `reportlab`.
`backend/requirements-dev.txt`: `pytest`, `httpx`.

`frontend` dependencies: `react`, `react-dom`, `react-router-dom`, `axios`, `recharts`, `tailwindcss` (set up per Tailwind's current official Vite guide), dev: `vite`, `@vitejs/plugin-react`, ESLint (from the Vite template).

---

## 4. System Architecture

BloodLink is layered: a relational database at the core; a FastAPI application layer implementing business logic (eligibility, compatibility, allocation, inventory updates); a React frontend; and a Python analytics layer that reads from the database, generates predictions, and exposes them back through the API to the dashboard.

### 4.1 Architecture Diagram

```mermaid
flowchart TB
  subgraph Presentation["Presentation Layer - React + Tailwind (Vite)"]
    SD["Staff / Admin Dashboard"]
    RP["Requester Portal"]
  end

  subgraph Application["Application Layer - FastAPI (/api)"]
    API["REST API routers"]
    AUTH["Auth and RBAC - JWT"]
    BL["Business logic: Eligibility, Compatibility, Nearest-expiry allocation, Activity log"]
    RPT["Dashboard stats and Reports - ReportLab / CSV"]
    SCH["Scheduler: expire overdue units daily"]
  end

  subgraph Analytics["Analytics Layer - Python (pandas, scikit-learn, statsmodels)"]
    AGG["Aggregation: daily donations, issues, wastage, stock"]
    MOD["Candidate models: Linear Regression, Holt-Winters, ARIMA"]
    EVAL["Hold-out evaluation and model selection"]
  end

  subgraph Data["Data Layer - PostgreSQL"]
    DB[("Tables + v_transactions view")]
  end

  SD --> API
  RP --> API
  API --> AUTH
  API --> BL
  API --> RPT
  SCH --> BL
  BL --> DB
  RPT --> DB
  API -->|"POST /api/predictions/run"| AGG
  AGG -->|"reads v_transactions"| DB
  AGG --> MOD
  MOD --> EVAL
  EVAL -->|"writes shortage_predictions"| DB
  API -->|"GET /api/predictions/*"| DB
```

**Layer responsibilities**

- **Presentation Layer** — React SPA. Staff/Admin dashboard and management screens; a separate, simpler portal for requesters.
- **Application Layer** — FastAPI. Authentication, RBAC, all business rules, REST API, dashboard statistics, report export, daily expiry job.
- **Analytics Layer** — the `backend/ml/` Python package. Independent of the `app` package (it receives a SQLAlchemy `Engine` and a config dict as arguments). Invoked by the API or via CLI.
- **Data Layer** — PostgreSQL. Source of truth for everything, including stored predictions.

### 4.2 Operational Workflow

```mermaid
flowchart LR
  A["1. Donor registration / walk-in"] --> B["2. Eligibility check: age, weight, last donation"]
  B --> C["3. Donation recorded: blood unit added to inventory"]
  C --> D["4. Inventory management: stock levels, expiry tracking"]
  D --> E["5. Requester places a blood request"]
  E --> F["6. Compatibility matching engine"]
  F --> G["7. Stock allocation and issue: nearest-expiry-first"]
  G --> H["8. Transaction logged: donation / issue / wastage"]
  H --> I["9. Shortage prediction module - Python"]
  I --> J["10. Dashboard and reports"]
```

### 4.3 Request Status State Machine

```mermaid
stateDiagram-v2
  [*] --> pending: requester submits
  pending --> approved: staff approves
  pending --> rejected: staff rejects
  approved --> issued: staff issues units
  approved --> rejected: staff rejects
  issued --> [*]
  rejected --> [*]
```

`issued` and `rejected` are terminal. Any other transition returns HTTP 409 `INVALID_STATUS_TRANSITION`.

---

## 5. Modules & Features

### Module 1 — User Authentication & Role Management
**Purpose:** secure, role-based access. Blood banks handle sensitive donor and patient data; uncontrolled access can cause misuse or untraceable errors.
**Features**
- Login (JWT). Admin-controlled creation of Staff/Admin accounts. Requester self-registration.
- Password hashing (bcrypt).
- Roles: `admin`, `staff`, `requester`.
- Role-based permissions (e.g., only Admin can delete records).
- Basic activity logging — who added/edited what, and when.

### Module 2 — Donor Management
**Purpose:** complete, accurate donor records and enforced eligibility rules.
**Features**
- Donor registration with demographics and blood group.
- Eligibility checks: min/max age, min weight, 90-day gap since last donation.
- Donation history per donor.
- Search/filter donors by blood group, location, or last-donation date.
- Flag regular/repeat donors.

### Module 3 — Blood Inventory Management
**Purpose:** track every unit from collection to expiry or issue.
**Features**
- Units are added **only** by recording a donation (so eligibility is always enforced).
- Per-unit blood group, collection date, expiry date.
- Real-time stock levels by blood group.
- Expiry alerts for units nearing shelf-life limit (in-app).
- Nearest-expiry-first allocation to minimize wastage.
- Automatic marking of overdue units as `expired` (wastage).

### Module 4 — Blood Request & Issuing Workflow
**Purpose:** handle requests and manage issuing with a clear, auditable trail.
**Features**
- Request submission with blood group, quantity, urgency.
- Status tracking: `pending → approved → issued` or `rejected`.
- Issue log linking specific units to a specific request (`issue_records`).
- Urgency-based prioritization (emergency before routine).

### Module 5 — Compatibility Matching Engine
**Purpose:** determine which units are safe to issue; manual checking is error-prone under emergency pressure.
**Features**
- Compatibility rules encoded in logic (Section 6.3).
- For a requested group, list all compatible available units.
- Rank by expiry date (soonest first).

### Module 6 — Shortage Prediction Module (Python)
**Purpose:** forecast which blood groups are likely to fall short soon.
**Features**
- Aggregate historical donations, issues, and wastage by blood group and day.
- Reconstruct daily stock; forecast stock for the next 7–30 days with regression and time-series models.
- Threshold alerts: flag a group if predicted stock falls below its safe minimum.
- Models evaluated against held-out historical data; best model chosen per blood group.

### Module 7 — Dashboard & Reports
**Purpose:** at-a-glance view of operations.
**Features**
- Current stock by blood group with low-stock highlighting.
- Donations vs. issues over time (charts).
- Predicted shortage alerts from Module 6.
- Wastage statistics (units expired unused).
- Exportable reports (PDF/CSV).

---

## 6. Business Rules (authoritative)

### 6.1 Roles & Permissions

| Capability | admin | staff | requester |
|-----------|:----:|:----:|:----:|
| Log in; view own account (`/auth/me`) | ✅ | ✅ | ✅ |
| Self-register | — | — | ✅ (public endpoint) |
| Create/manage Staff & Admin accounts | ✅ | ❌ | ❌ |
| Donors: create, read, update, record donation | ✅ | ✅ | ❌ |
| Inventory: read, trigger expiry sweep | ✅ | ✅ | ❌ |
| Requests: create | ❌ | ❌ | ✅ |
| Requests: read | all | all | own only |
| Requests: approve, reject, issue, view matches | ✅ | ✅ | ❌ |
| Camps: create, read, update | ✅ | ✅ | ❌ |
| Dashboard, reports, predictions (read + run) | ✅ | ✅ | ❌ |
| Activity logs: read | ✅ | ❌ | ❌ |
| **Delete any record** (donor, unit, request, requester, camp, staff) | ✅ | ❌ | ❌ |

### 6.2 Donor Eligibility
Evaluated against `today()` using the donor's stored data:

- `age = full years between dob and today` → eligible if `MIN_DONOR_AGE ≤ age ≤ MAX_DONOR_AGE` (inclusive).
- `weight ≥ MIN_DONOR_WEIGHT_KG`.
- `last_donation_date` is null **or** `today − last_donation_date ≥ MIN_DONATION_GAP_DAYS` days.
- `next_eligible_date = last_donation_date + MIN_DONATION_GAP_DAYS` (null if never donated).

Failure reason codes: `AGE_BELOW_MIN`, `AGE_ABOVE_MAX`, `WEIGHT_BELOW_MIN`, `DONATION_GAP_NOT_MET`. Registration of a donor is always allowed; eligibility is enforced when **recording a donation**.

### 6.3 Blood Group Compatibility (whole blood / red cells)
Keys are the **requested (recipient)** group; values are the **donor groups that are safe to issue**:

| Requested (recipient) | Compatible stock groups |
|---|---|
| O- | O- |
| O+ | O+, O- |
| A- | A-, O- |
| A+ | A+, A-, O+, O- |
| B- | B-, O- |
| B+ | B+, B-, O+, O- |
| AB- | AB-, A-, B-, O- |
| AB+ | AB+, AB-, A+, A-, B+, B-, O+, O- |

Valid blood groups: `A+, A-, B+, B-, AB+, AB-, O+, O-`.
Implement as a single constant dict in `app/services/compatibility.py`; no duplicate copies anywhere (the synthetic generator imports it).

### 6.4 Recording a Donation (atomic)
`POST /api/donors/{donor_id}/donations`, in one DB transaction:
1. Load donor; run eligibility. If not eligible → 409 `ELIGIBILITY_FAILED` with reasons; nothing is written.
2. Create `blood_units` row: `blood_group = donor.blood_group`, `collection_date = today()`, `expiry_date = today() + BLOOD_SHELF_LIFE_DAYS`, `status = 'available'`.
3. Set `donor.last_donation_date = today()`.
4. Write activity log (`create` / `blood_unit`).

Collection date is always today (no back-dating through the API).

### 6.5 Expiry
- `expire_overdue_units()`: sets `status = 'expired'` for all units with `status = 'available'` AND `expiry_date < today()`.
- Runs: (a) at application startup, (b) daily via APScheduler, (c) at the start of every issue operation and every prediction run, (d) on demand via `POST /api/inventory/expire-overdue`.
- "Expiring soon" = available units with `today() ≤ expiry_date ≤ today() + EXPIRY_ALERT_DAYS`.
- **Available stock** = `status = 'available' AND expiry_date ≥ today()`.

### 6.6 Matching & Nearest-Expiry-First Allocation
```
compatible_groups = COMPATIBILITY[requested_group]
candidates = units WHERE status='available' AND expiry_date >= today()
                    AND blood_group IN compatible_groups
             ORDER BY expiry_date ASC, unit_id ASC
```
- `GET .../matches` returns **all** candidates in that order plus the first `quantity` as the allocation preview.
- Ranking is by expiry only (as specified); no preference for exact-group over universal-donor units.

### 6.7 Issuing (atomic, all-or-nothing)
`POST /api/requests/{request_id}/issue`, in one DB transaction:
1. Run `expire_overdue_units()`.
2. Request must be `approved`; else 409 `INVALID_STATUS_TRANSITION`.
3. Select the first `quantity` candidates (6.6) using row locks (`SELECT ... FOR UPDATE`) so two concurrent issues cannot take the same unit.
4. If fewer than `quantity` candidates → 409 `INSUFFICIENT_STOCK` (include `requested` and `available`); nothing changes.
5. For each unit: insert `issue_records(request_id, unit_id, issue_date=today(), issued_by=<current user's staff_id>)`; set unit `status='issued'`.
6. Set request `status='issued'`.
7. Write activity log (`issue` / `blood_request`, details include unit ids).

`issue_records.unit_id` is UNIQUE, so a unit can never be issued twice.

### 6.8 Request Prioritization
Staff request lists default to **priority order**: `urgency = 'emergency'` first, then `request_date ASC`, then `request_id ASC`. Requesters' lists default to newest first. Selected via `sort=priority|newest`.

### 6.9 Activity Logging
Every create / update / delete / approve / reject / issue writes one row to `activity_logs` (who, what, which entity, when, plus a small JSON `details`). Written by a single helper `activity_log.record(db, user_id, action, entity_type, entity_id, details)` called inside the same transaction as the change. Reads are admin-only. Logs are append-only (no update/delete endpoints).

`action` values: `create`, `update`, `delete`, `approve`, `reject`, `issue`.
`entity_type` values: `user`, `staff`, `requester`, `donor`, `blood_unit`, `blood_request`, `donation_camp`, `prediction_run`.

### 6.10 Referential Integrity & Deletion
All foreign keys are `ON DELETE RESTRICT`. Deleting a record that is referenced returns 409 `REFERENCED_RECORD`, preserving traceability (every issued unit traceable to both donor and request). Rules:
- Donor with any units cannot be deleted. A donor's `blood_group` cannot be changed once they have units (409 `DONOR_HAS_UNITS`).
- A unit with `status='issued'` cannot be deleted.
- A request with status `issued` cannot be deleted.
- Staff/requester deletion removes the profile row then the `users` row. Staff referenced by `issue_records` cannot be deleted (deactivate instead via `is_active=false`).
- An admin cannot deactivate, demote, or delete **their own** account (409 `SELF_MODIFICATION_FORBIDDEN`).

### 6.11 Other Rules
- "Regular donor": `donation_count ≥ REGULAR_DONOR_MIN_DONATIONS`, where `donation_count` = number of the donor's `blood_units`.
- "Low stock": `available_units < safe_minimum` for that group (same threshold as predictions).
- Usernames are unique. Passwords: minimum 8 characters; stored only as bcrypt hashes; never returned by any endpoint.
- Disabled users (`is_active=false`) cannot log in (403 `ACCOUNT_DISABLED`).

---

## 7. Database Schema (PostgreSQL)

### 7.1 ER Diagram

```mermaid
erDiagram
  USERS ||--o| STAFF : "has profile"
  USERS ||--o| REQUESTERS : "has profile"
  USERS ||--o{ ACTIVITY_LOGS : "performs"
  DONORS ||--o{ BLOOD_UNITS : "donates"
  REQUESTERS ||--o{ BLOOD_REQUESTS : "places"
  BLOOD_REQUESTS ||--o{ ISSUE_RECORDS : "fulfilled by"
  BLOOD_UNITS ||--o| ISSUE_RECORDS : "issued as"
  STAFF ||--o{ ISSUE_RECORDS : "issues"

  USERS {
    int user_id PK
    string username UK
    string password_hash
    string role
    boolean is_active
    timestamptz created_at
  }
  STAFF {
    int staff_id PK
    int user_id FK
    string name
  }
  REQUESTERS {
    int requester_id PK
    int user_id FK
    string name
    string type
    string phone
    string address
  }
  DONORS {
    int donor_id PK
    string name
    date dob
    string gender
    string blood_group
    string phone
    string address
    numeric weight
    date last_donation_date
  }
  BLOOD_UNITS {
    int unit_id PK
    int donor_id FK
    string blood_group
    date collection_date
    date expiry_date
    string status
  }
  BLOOD_REQUESTS {
    int request_id PK
    int requester_id FK
    string blood_group
    int quantity
    string urgency
    string status
    date request_date
  }
  ISSUE_RECORDS {
    int issue_id PK
    int request_id FK
    int unit_id FK
    date issue_date
    int issued_by FK
  }
  DONATION_CAMPS {
    int camp_id PK
    string location
    date camp_date
    int target_units
    int units_collected
  }
  ACTIVITY_LOGS {
    int log_id PK
    int user_id FK
    string action
    string entity_type
    int entity_id
    jsonb details
    timestamptz created_at
  }
  SHORTAGE_PREDICTIONS {
    int prediction_id PK
    uuid run_id
    timestamptz generated_at
    string blood_group
    date forecast_date
    numeric predicted_stock
    int safe_minimum
    boolean is_below_minimum
    string model_name
  }
```

`donation_camps` and `shortage_predictions` have no foreign keys (standalone). Schema is normalized to at least 3NF: donor details are stored once and referenced by ID; credentials live only in `users`.

### 7.2 DDL (reference — implement via SQLAlchemy models + Alembic migration)

```sql
CREATE TABLE users (
  user_id       SERIAL PRIMARY KEY,
  username      VARCHAR(50)  NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role          VARCHAR(10)  NOT NULL CHECK (role IN ('admin','staff','requester')),
  is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE staff (
  staff_id SERIAL PRIMARY KEY,
  user_id  INTEGER NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE RESTRICT,
  name     VARCHAR(100) NOT NULL
);

CREATE TABLE requesters (
  requester_id SERIAL PRIMARY KEY,
  user_id      INTEGER NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE RESTRICT,
  name         VARCHAR(100) NOT NULL,
  type         VARCHAR(10)  NOT NULL CHECK (type IN ('hospital','patient')),
  phone        VARCHAR(20)  NOT NULL,
  address      TEXT         NOT NULL
);

CREATE TABLE donors (
  donor_id           SERIAL PRIMARY KEY,
  name               VARCHAR(100)  NOT NULL,
  dob                DATE          NOT NULL,
  gender             VARCHAR(10)   NOT NULL CHECK (gender IN ('male','female','other')),
  blood_group        VARCHAR(3)    NOT NULL CHECK (blood_group IN ('A+','A-','B+','B-','AB+','AB-','O+','O-')),
  phone              VARCHAR(20)   NOT NULL,
  address            TEXT          NOT NULL,
  weight             NUMERIC(5,2)  NOT NULL CHECK (weight > 0),   -- kilograms
  last_donation_date DATE
);

CREATE TABLE blood_units (
  unit_id         SERIAL PRIMARY KEY,
  donor_id        INTEGER    NOT NULL REFERENCES donors(donor_id) ON DELETE RESTRICT,
  blood_group     VARCHAR(3) NOT NULL CHECK (blood_group IN ('A+','A-','B+','B-','AB+','AB-','O+','O-')),
  collection_date DATE       NOT NULL,
  expiry_date     DATE       NOT NULL,
  status          VARCHAR(10) NOT NULL DEFAULT 'available' CHECK (status IN ('available','issued','expired')),
  CHECK (expiry_date > collection_date)
);

CREATE TABLE blood_requests (
  request_id   SERIAL PRIMARY KEY,
  requester_id INTEGER    NOT NULL REFERENCES requesters(requester_id) ON DELETE RESTRICT,
  blood_group  VARCHAR(3) NOT NULL CHECK (blood_group IN ('A+','A-','B+','B-','AB+','AB-','O+','O-')),
  quantity     INTEGER    NOT NULL CHECK (quantity >= 1),
  urgency      VARCHAR(10) NOT NULL CHECK (urgency IN ('emergency','routine')),
  status       VARCHAR(10) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','issued','rejected')),
  request_date DATE       NOT NULL
);

CREATE TABLE issue_records (
  issue_id   SERIAL PRIMARY KEY,
  request_id INTEGER NOT NULL REFERENCES blood_requests(request_id) ON DELETE RESTRICT,
  unit_id    INTEGER NOT NULL UNIQUE REFERENCES blood_units(unit_id) ON DELETE RESTRICT,
  issue_date DATE    NOT NULL,
  issued_by  INTEGER NOT NULL REFERENCES staff(staff_id) ON DELETE RESTRICT
);

CREATE TABLE donation_camps (
  camp_id         SERIAL PRIMARY KEY,
  location        TEXT    NOT NULL,
  camp_date       DATE    NOT NULL,
  target_units    INTEGER NOT NULL CHECK (target_units > 0),
  units_collected INTEGER NOT NULL DEFAULT 0 CHECK (units_collected >= 0)
);

CREATE TABLE activity_logs (
  log_id      SERIAL PRIMARY KEY,
  user_id     INTEGER     NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
  action      VARCHAR(20) NOT NULL,
  entity_type VARCHAR(30) NOT NULL,
  entity_id   INTEGER,
  details     JSONB,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE shortage_predictions (
  prediction_id    SERIAL PRIMARY KEY,
  run_id           UUID         NOT NULL,
  generated_at     TIMESTAMPTZ  NOT NULL,
  blood_group      VARCHAR(3)   NOT NULL CHECK (blood_group IN ('A+','A-','B+','B-','AB+','AB-','O+','O-')),
  forecast_date    DATE         NOT NULL,
  predicted_stock  NUMERIC(8,2) NOT NULL CHECK (predicted_stock >= 0),
  safe_minimum     INTEGER      NOT NULL,
  is_below_minimum BOOLEAN      NOT NULL,
  model_name       VARCHAR(30)  NOT NULL,
  UNIQUE (run_id, blood_group, forecast_date)
);
```

### 7.3 Indexes

```sql
-- required by the document: fast lookups during matching
CREATE INDEX idx_blood_units_blood_group ON blood_units (blood_group);
CREATE INDEX idx_blood_units_expiry_date ON blood_units (expiry_date);
-- composite for the matching/allocation query
CREATE INDEX idx_blood_units_match ON blood_units (status, blood_group, expiry_date);
-- foreign keys / common filters
CREATE INDEX idx_blood_units_donor_id        ON blood_units (donor_id);
CREATE INDEX idx_blood_requests_requester_id ON blood_requests (requester_id);
CREATE INDEX idx_blood_requests_status       ON blood_requests (status, urgency, request_date);
CREATE INDEX idx_issue_records_request_id    ON issue_records (request_id);
CREATE INDEX idx_donors_blood_group          ON donors (blood_group);
CREATE INDEX idx_donors_last_donation_date   ON donors (last_donation_date);
CREATE INDEX idx_activity_logs_created_at    ON activity_logs (created_at);
CREATE INDEX idx_activity_logs_user_id       ON activity_logs (user_id);
CREATE INDEX idx_predictions_run_id          ON shortage_predictions (run_id);
CREATE INDEX idx_predictions_generated_at    ON shortage_predictions (generated_at);
```

### 7.4 Transaction View (workflow step 8)

```sql
CREATE VIEW v_transactions AS
SELECT 'donation'::text AS transaction_type,
       u.unit_id, u.blood_group, u.collection_date AS transaction_date,
       u.donor_id, NULL::integer AS request_id, NULL::integer AS staff_id
FROM blood_units u
UNION ALL
SELECT 'issue'::text, i.unit_id, u.blood_group, i.issue_date,
       u.donor_id, i.request_id, i.issued_by
FROM issue_records i
JOIN blood_units u ON u.unit_id = i.unit_id
UNION ALL
SELECT 'wastage'::text, u.unit_id, u.blood_group, u.expiry_date,
       u.donor_id, NULL::integer, NULL::integer
FROM blood_units u
WHERE u.status = 'expired';
```

- `donation` is dated by `collection_date`, `issue` by `issue_date`, `wastage` by `expiry_date`.
- Create it in the Alembic migration with `op.execute(...)`; drop it in `downgrade()`.
- The analytics layer and the dashboard/report queries use this view as their source for daily activity.

---

## 8. API Specification

### 8.1 Conventions

- Base path `/api`. JSON in/out. Field names `snake_case`. Dates `YYYY-MM-DD`; timestamps ISO-8601 with timezone.
- Auth: `Authorization: Bearer <access_token>`. JWT claims: `sub` (user_id), `role`, `exp`. Algorithm HS256.
- Pagination (list endpoints that say "paginated"): query `page` (default 1), `page_size` (default 20, max 100). Response: `{"items": [...], "total": 123, "page": 1, "page_size": 20}`.
- OpenAPI docs are auto-served at `/docs`. Every route needs a `summary`, `response_model`, and `tags`.
- Access legend: **A** = admin, **S** = staff, **R** = requester, **Public** = no token.

**Status codes**

| Code | Use |
|------|-----|
| 200 / 201 / 204 | OK / Created / No content (deletes) |
| 401 | Missing/invalid/expired token |
| 403 | Authenticated but role not allowed (or disabled account) |
| 404 | Resource not found (or a requester accessing someone else's request) |
| 409 | Business-rule violation (eligibility, stock, state transition, delete blocked, duplicates) |
| 422 | Request validation error (FastAPI/Pydantic default format) |

**Error format** (all errors except 422): 
```json
{ "detail": { "code": "ELIGIBILITY_FAILED", "message": "Donor is not eligible to donate.", "reasons": ["DONATION_GAP_NOT_MET"] } }
```
Extra keys (e.g. `reasons`, `requested`, `available`) may appear alongside `code` and `message`.

| Error code | HTTP | When |
|-----------|------|------|
| `NOT_AUTHENTICATED` | 401 | No/invalid/expired token |
| `INVALID_CREDENTIALS` | 401 | Wrong username/password |
| `ACCOUNT_DISABLED` | 403 | `is_active = false` |
| `FORBIDDEN` | 403 | Role not allowed |
| `NOT_FOUND` | 404 | Missing resource |
| `DUPLICATE` | 409 | Username already exists |
| `ELIGIBILITY_FAILED` | 409 | Donor ineligible (body has `reasons`) |
| `INSUFFICIENT_STOCK` | 409 | Not enough compatible units (body has `requested`, `available`) |
| `INVALID_STATUS_TRANSITION` | 409 | Illegal request status change |
| `REFERENCED_RECORD` | 409 | Delete blocked by foreign key |
| `DONOR_HAS_UNITS` | 409 | Blood-group change blocked |
| `UNIT_ALREADY_ISSUED` | 409 | Deleting an issued unit |
| `SELF_MODIFICATION_FORBIDDEN` | 409 | Admin modifying/deleting self |

### 8.2 Endpoints

#### Health
| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/api/health` | Public | Returns `{"status":"ok","database":"ok"}` after a trivial DB query |

#### Auth
| Method | Path | Access | Description |
|---|---|---|---|
| POST | `/api/auth/login` | Public | Body `{username, password}` → `{access_token, token_type:"bearer", user}` |
| POST | `/api/auth/register` | Public | Requester self-registration. Body `{username, password, name, type, phone, address}`. Creates `users` (role `requester`) + `requesters` row. 201 → same shape as login response (auto-login) |
| GET | `/api/auth/me` | A,S,R | Current user |

`user` object: `{ "user_id": 1, "username": "esha", "role": "staff", "name": "Esha", "profile_id": 3 }` (`profile_id` = `staff_id` or `requester_id`).

#### Staff & Admin accounts (admin only)
| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/api/staff` | A | List staff/admin accounts (paginated) |
| POST | `/api/staff` | A | Body `{username, password, name, role}` where `role ∈ {staff, admin}` → 201 |
| GET | `/api/staff/{staff_id}` | A | Detail |
| PATCH | `/api/staff/{staff_id}` | A | Any of `{name, role, is_active, password}` |
| DELETE | `/api/staff/{staff_id}` | A | 204, or 409 `REFERENCED_RECORD` / `SELF_MODIFICATION_FORBIDDEN` |

Staff object: `{staff_id, user_id, username, name, role, is_active}`.

#### Activity Logs
| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/api/activity-logs` | A | Paginated, newest first. Filters: `user_id`, `entity_type`, `action`, `start_date`, `end_date` |

Object: `{log_id, user_id, username, action, entity_type, entity_id, details, created_at}`.

#### Donors
| Method | Path | Access | Description |
|---|---|---|---|
| POST | `/api/donors` | A,S | Body `{name, dob, gender, blood_group, phone, address, weight}` → 201 |
| GET | `/api/donors` | A,S | Paginated. Filters: `blood_group`, `location` (case-insensitive substring of `address`), `last_donation_before`, `last_donation_after`, `is_regular` (bool), `q` (substring of name or phone), `sort` (`name`, `last_donation_date`; default `name`) |
| GET | `/api/donors/{donor_id}` | A,S | Donor + `donation_count`, `is_regular`, `eligibility` |
| PATCH | `/api/donors/{donor_id}` | A,S | Any of `{name, dob, gender, blood_group, phone, address, weight}` (`blood_group` blocked if donor has units) |
| DELETE | `/api/donors/{donor_id}` | A | 204 or 409 `REFERENCED_RECORD` |
| GET | `/api/donors/{donor_id}/eligibility` | A,S | Eligibility result (below) |
| POST | `/api/donors/{donor_id}/donations` | A,S | Records a donation (Section 6.4). No body. 201 → BloodUnit. 409 `ELIGIBILITY_FAILED` |
| GET | `/api/donors/{donor_id}/donations` | A,S | Donor's donation history (their units, newest first) |

Donor object:
```json
{ "donor_id": 12, "name": "Asha Rao", "dob": "1995-04-12", "gender": "female", "blood_group": "O+",
  "phone": "9876543210", "address": "Andheri, Mumbai", "weight": 58.5,
  "last_donation_date": "2026-07-01", "donation_count": 4, "is_regular": true }
```
(`GET /donors/{id}` adds `"eligibility": {…}`.)

Eligibility object:
```json
{ "eligible": false, "reasons": ["DONATION_GAP_NOT_MET"], "age": 31, "weight": 58.5,
  "last_donation_date": "2026-07-01", "next_eligible_date": "2026-09-29" }
```

#### Inventory
| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/api/inventory/stock` | A,S | Available stock per blood group (all 8 groups, zero-filled) |
| GET | `/api/inventory/units` | A,S | Paginated units. Filters: `blood_group`, `status`, `donor_id`, `expiring_within_days` |
| GET | `/api/inventory/units/{unit_id}` | A,S | Unit detail |
| GET | `/api/inventory/expiring` | A,S | Available units expiring within `days` (default `EXPIRY_ALERT_DAYS`), soonest first |
| POST | `/api/inventory/expire-overdue` | A,S | Runs the expiry sweep → `{"expired_count": 3}` |
| DELETE | `/api/inventory/units/{unit_id}` | A | 204, or 409 `UNIT_ALREADY_ISSUED` / `REFERENCED_RECORD` |

Stock response:
```json
{ "as_of": "2026-10-21",
  "stock": [ {"blood_group":"A+","available_units":14}, {"blood_group":"A-","available_units":3} ],
  "total_available_units": 17 }
```
BloodUnit object: `{unit_id, donor_id, blood_group, collection_date, expiry_date, status, days_to_expiry}` where `days_to_expiry = expiry_date − today` (negative when past).

#### Requesters
| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/api/requesters` | A,S | Paginated; filters `type`, `q` |
| GET | `/api/requesters/me` | R | Own profile |
| PATCH | `/api/requesters/me` | R | Any of `{name, type, phone, address}` |
| GET | `/api/requesters/{requester_id}` | A,S | Detail |
| DELETE | `/api/requesters/{requester_id}` | A | 204 or 409 `REFERENCED_RECORD` |

Requester object: `{requester_id, user_id, username, name, type, phone, address}`.
(`/me` routes must be declared before `/{requester_id}`.)

#### Blood Requests
| Method | Path | Access | Description |
|---|---|---|---|
| POST | `/api/requests` | R | Body `{blood_group, quantity, urgency}` → 201, status `pending`, `request_date = today()` |
| GET | `/api/requests` | R (own), A,S (all) | Paginated. Filters: `status`, `urgency`, `blood_group`, `requester_id` (A,S only), `sort` (`priority`\|`newest`; default `priority`) |
| GET | `/api/requests/{request_id}` | R (own), A,S | Detail incl. `issued_units` |
| GET | `/api/requests/{request_id}/matches` | A,S | Compatible available units, ranked (Section 6.6) |
| POST | `/api/requests/{request_id}/approve` | A,S | `pending → approved` |
| POST | `/api/requests/{request_id}/reject` | A,S | `pending/approved → rejected` |
| POST | `/api/requests/{request_id}/issue` | A,S | `approved → issued` (Section 6.7) |
| DELETE | `/api/requests/{request_id}` | A | 204 or 409 `REFERENCED_RECORD` |

Request object:
```json
{ "request_id": 41, "requester_id": 5, "requester_name": "City Hospital", "blood_group": "A+",
  "quantity": 2, "urgency": "emergency", "status": "approved", "request_date": "2026-10-21",
  "issued_count": 0 }
```
Detail adds `"issued_units": [{"issue_id": 90, "unit_id": 311, "blood_group": "O+", "issue_date": "2026-10-21", "issued_by": 2, "issued_by_name": "Sakshi"}]`.

Matches response:
```json
{ "request_id": 41, "requested_group": "A+", "quantity": 2,
  "compatible_groups": ["A+","A-","O+","O-"],
  "available_compatible_count": 9, "sufficient": true,
  "allocation_preview_unit_ids": [311, 305],
  "units": [ {"unit_id":311,"blood_group":"O+","collection_date":"2026-09-12","expiry_date":"2026-10-24","days_to_expiry":3} ] }
```

#### Matching (stand-alone lookups)
| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/api/matching/compatibility` | A,S,R | The full compatibility matrix (Section 6.3) as `{"A+": ["A+","A-","O+","O-"], …}` |
| GET | `/api/matching/units` | A,S | Query `blood_group` (required), `limit` (optional) → compatible available units ranked by expiry |

#### Donation Camps
| Method | Path | Access | Description |
|---|---|---|---|
| POST | `/api/camps` | A,S | Body `{location, camp_date, target_units, units_collected?}` → 201 |
| GET | `/api/camps` | A,S | Paginated; filters `start_date`, `end_date`; sorted by `camp_date` desc |
| GET | `/api/camps/{camp_id}` | A,S | Detail |
| PATCH | `/api/camps/{camp_id}` | A,S | Any field |
| DELETE | `/api/camps/{camp_id}` | A | 204 |

Camp object: `{camp_id, location, camp_date, target_units, units_collected}`. `units_collected` is entered manually (camps are not linked to units in the schema).

#### Dashboard
| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/api/dashboard/summary` | A,S | Headline numbers (below) |
| GET | `/api/dashboard/trends` | A,S | Query `start_date`, `end_date` (default: last 30 days), `granularity` (`day`\|`week`\|`month`, default `day`), `blood_group` (optional) |
| GET | `/api/dashboard/wastage` | A,S | Query `start_date`, `end_date` (default: last 365 days) |

Summary:
```json
{ "as_of": "2026-10-21",
  "stock_by_group": [ {"blood_group":"A+","available_units":14,"safe_minimum":10,"is_low":false} ],
  "total_available_units": 96,
  "expiring_soon": {"days": 7, "count": 8},
  "pending_requests": 4,
  "pending_emergency_requests": 1,
  "approved_requests_awaiting_issue": 2,
  "predicted_shortage_alert_count": 2 }
```
(`predicted_shortage_alert_count` is `null` if no prediction run exists.)

Trends: `{"granularity":"week","series":[{"period_start":"2026-10-12","donations":31,"issues":27}]}` — zero-filled for empty periods; weeks start Monday; `donations` counts by `collection_date`, `issues` by `issue_date`.

Wastage: `{"start_date":…,"end_date":…,"total_expired":17,"by_blood_group":[{"blood_group":"O-","expired_units":4}],"by_month":[{"period_start":"2026-09-01","expired_units":5}]}` — counts units with `status='expired'` whose `expiry_date` falls in range.

#### Predictions
| Method | Path | Access | Description |
|---|---|---|---|
| POST | `/api/predictions/run` | A,S | Body `{"horizon_days": 30}` (7–30, default 30). Expires overdue units, runs the pipeline synchronously, stores results, writes activity log (`create`/`prediction_run`). Returns run summary |
| GET | `/api/predictions/latest` | A,S | Latest run's forecasts, grouped by blood group |
| GET | `/api/predictions/alerts` | A,S | Shortage alerts from the latest run. Query `within_days` (7–30, default 30) |
| GET | `/api/predictions/evaluation` | A,S | Contents of `latest_evaluation.json` |

Run summary: `{"run_id":"…","generated_at":"…","horizon_days":30,"groups_predicted":7,"groups_skipped":["AB-"]}`

Latest:
```json
{ "run_id": "6f1c…", "generated_at": "2026-10-21T09:30:00+05:30", "horizon_days": 30,
  "predictions": [
    { "blood_group": "O-", "model_name": "holt_winters", "safe_minimum": 10,
      "forecast": [ {"date":"2026-10-21","predicted_stock":12.4,"is_below_minimum":false} ] } ],
  "skipped_groups": [ {"blood_group":"AB-","reason":"insufficient_data"} ] }
```
When no run exists: `{"run_id":null,"generated_at":null,"horizon_days":null,"predictions":[],"skipped_groups":[]}` with HTTP 200.

Alerts: 
```json
[ { "blood_group": "O-", "current_stock": 11, "safe_minimum": 10,
    "first_shortage_date": "2026-10-27", "days_until_shortage": 6, "min_predicted_stock": 4.2 } ]
```
A group is alerted if any forecast day within `within_days` of the run's first forecast date has `is_below_minimum = true`. `current_stock` = available stock now. Sorted by `days_until_shortage` ascending.

Evaluation:
```json
{ "run_id": "6f1c…", "generated_at": "…", "holdout_days": 30,
  "groups": {
    "O-": { "status": "ok", "selected_model": "holt_winters", "train_days": 335, "history_days": 365,
            "metrics": { "linear_regression": {"mae": 2.1, "rmse": 2.7},
                         "holt_winters": {"mae": 1.4, "rmse": 1.9},
                         "arima": {"mae": 1.6, "rmse": 2.2} } },
    "AB-": { "status": "insufficient_data", "history_days": 40 } } }
```
If the file does not exist: `{"run_id":null,"generated_at":null,"holdout_days":null,"groups":{}}`.

#### Reports
| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/api/reports/{report_type}` | A,S | Query `format` (`csv`\|`pdf`, required), `start_date`, `end_date` (where applicable). Returns a file download |

`report_type` and columns (unknown type → 404):

| Type | Columns | Date filter applies to |
|---|---|---|
| `stock` | blood_group, available_units, safe_minimum, status (`LOW`/`OK`) | — |
| `donations` | unit_id, donor_id, donor_name, blood_group, collection_date, expiry_date, status | `collection_date` |
| `issues` | issue_id, request_id, requester_name, unit_id, blood_group, issue_date, issued_by_name | `issue_date` |
| `wastage` | unit_id, blood_group, collection_date, expiry_date | `expiry_date` |
| `donors` | donor_id, name, blood_group, phone, address, last_donation_date, donation_count, is_regular | — |
| `requests` | request_id, requester_name, blood_group, quantity, urgency, status, request_date | `request_date` |
| `predictions` | blood_group, model_name, forecast_date, predicted_stock, safe_minimum, is_below_minimum | — (latest run) |

- CSV: UTF-8, header row. PDF: ReportLab, title + generated-at timestamp + table with repeated header row; landscape for wide tables; paginated.
- Headers: `Content-Disposition: attachment; filename="bloodlink_<type>_<YYYYMMDD>.<ext>"`, correct `Content-Type`.

---

## 9. Shortage Prediction Module (Analytics Layer)

Lives in `backend/ml/`. **Must not import from `backend/app/`** — it receives a SQLAlchemy `Engine` and a `safe_minimums` dict (blood group → int) as arguments, so it can run standalone.

### 9.1 Data Preparation (`ml/data.py`)
1. Read daily activity from the `v_transactions` view, grouped by `blood_group` and `transaction_date`, counting `donation`, `issue`, `wastage`.
2. `first_date` = earliest `transaction_date` across all groups; `history_end = today − 1 day` (only completed days).
3. For each of the 8 blood groups build a continuous daily index `first_date … history_end`, filling missing days with 0, with columns `donations`, `issues`, `wastage`.
4. **Stock series (the forecasting target):** `stock(d) = cumsum(donations) − cumsum(issues) − cumsum(wastage)` up to and including day `d`. (Valid because the system starts empty at `first_date`; the seeder honours this.)
5. A group has `history_days = len(index)`. If `history_days < MIN_HISTORY_DAYS` (default 90) it is **skipped** with status `insufficient_data`.

### 9.2 Candidate Models (`ml/models/`)
Each implements the interface in `models/base.py`: `fit(series: pd.Series)` and `forecast(steps: int) -> np.ndarray`; plus a class attribute `name`.

| `name` | Library | Suggested configuration (tunable, but keep the interface) |
|---|---|---|
| `linear_regression` | scikit-learn `LinearRegression` | Features: time index `t` + day-of-week dummies (trend + weekly seasonality). Direct multi-step (no recursion) |
| `holt_winters` | statsmodels `ExponentialSmoothing` | Additive trend (damped), additive seasonality, `seasonal_periods=7` |
| `arima` | statsmodels `ARIMA` | `d=1`; choose `p, q ∈ {0,1,2}` by lowest AIC |

If a model raises or fails to converge for a group, exclude it for that group and record `error` text in the evaluation; if all fail the group status is `error` and it is skipped.

### 9.3 Evaluation & Selection (`ml/evaluation.py`)
Per group, chronological split (never shuffle):
- `train` = all but the last `HOLDOUT_DAYS` (default 30); `test` = last `HOLDOUT_DAYS`.
- Fit each candidate on `train`, forecast `HOLDOUT_DAYS` steps, clip at ≥ 0, compute **MAE** and **RMSE** vs `test`.
- Select the model with the lowest **RMSE** (ties broken by the table order above).
- Refit the selected model on the **full** history.
- Write all metrics to `backend/ml/artifacts/latest_evaluation.json` (gitignored; create the directory if missing).

### 9.4 Forecasting & Alerts (`ml/pipeline.py`)
`run_prediction(engine, safe_minimums, horizon_days=30, today=None) -> RunResult`:
1. Build data (9.1) → evaluate/select (9.3).
2. Forecast `horizon_days` steps. Forecast dates run from `history_end + 1 day` (i.e., today) through `today + horizon_days − 1`. Clip at ≥ 0; round to 2 decimals.
3. `is_below_minimum = predicted_stock < safe_minimums[group]`.
4. Generate one `run_id` (UUID4) and `generated_at`; append rows to `shortage_predictions` (one per group × day) — never overwrite old runs.
5. Return a summary (run_id, groups predicted/skipped).

Persistence (`ml/persistence.py`) uses plain SQL / `DataFrame.to_sql(..., if_exists="append")`. Alert derivation (`first_shortage_date`, etc.) is computed at read time by the API from stored rows.

### 9.5 CLI (`ml/cli.py`)
```
python -m ml.cli evaluate                  # builds data, evaluates, writes evaluation JSON, no DB writes
python -m ml.cli run --horizon 30          # full run: evaluate + forecast + store
```
Reads `DATABASE_URL` and safe-minimum config from the same settings as the app.

### 9.6 Synthetic Data Generator (`backend/scripts/seed_synthetic_data.py`)
Purpose: produce realistic history so the predictor and dashboard have something to work with. Built in Phase 4. Usage:
```
python -m scripts.seed_synthetic_data --days 365 --seed 42 --reset
```
- `--reset` truncates all domain tables and recreates demo accounts. `--seed` makes runs reproducible. Defaults: 365 days ending **yesterday**.
- Simulate **day by day**, in order, honouring every business rule:
  1. Expire units whose `expiry_date < day` (status `expired`).
  2. **Donations:** sample a daily count (Poisson, with a weekly pattern and occasional camp-day spikes); pick donors who are **eligible on that day** (reuse `app.services.eligibility`) from a donor pool; create units with `collection_date = day`, `expiry_date = day + shelf life`; update `last_donation_date`.
  3. **Requests:** sample per-group demand (weekly pattern; emergency share configurable); allocate with the **same** compatibility dict and nearest-expiry-first rule; if enough stock → request `issued` with `issue_records`; otherwise → `rejected`.
  4. Create past `donation_camps` consistent with the spikes.
- Leave the final 1–2 days' requests as `pending`/`approved` so the UI has live items.
- Seed: ~ a pool of donors (size chosen so the simulated donation volume is feasible under the 90-day gap), requesters (mix of hospitals/patients), staff accounts.
- Blood-group mix uses illustrative weights (not sourced from any dataset), configurable: A+ 0.22, A- 0.02, B+ 0.30, B- 0.02, AB+ 0.07, AB- 0.01, O+ 0.34, O- 0.02.
- **Calibration requirement (Phase 4 owner):** tune volumes, weights, and/or per-group safe minimums so that (a) stock is never negative, (b) every group has ≥ 180 days of history, (c) stock is in a range where the safe minimum is meaningful — some groups dip below it occasionally, some never do. Document the final parameters in the script's docstring.
- Demo accounts (development only — document in README): `admin / admin12345`, `staff / staff12345`, `hospital / hospital12345`.

---

## 10. Frontend Specification (React + Vite + Tailwind, JavaScript)

### 10.1 General
- Routing with React Router. Two layouts after login: **StaffLayout** (sidebar; for `admin` & `staff`) and **RequesterLayout** (simple top nav; for `requester`). Public: login and register pages.
- Auth: `AuthContext` stores `{token, user}`; token persisted in `localStorage`. Axios instance (`src/api/client.js`) attaches the Bearer header from `VITE_API_BASE_URL`, and on **401** clears auth and redirects to `/login`.
- Route protection: `ProtectedRoute` with `allowedRoles`. After login redirect by role: `admin/staff → /dashboard`, `requester → /my/requests`. Hide UI actions the role cannot perform (the backend still enforces).
- Every data screen has loading, error, and empty states. Mutations show success/error toasts. Destructive actions (delete) use a confirm dialog (admin only).
- Forms validate client-side (required fields, ranges) and display backend errors using `detail.code` / `detail.message` (a helper in `utils/errors.js` normalizes both the domain-error shape and the 422 list shape).
- Responsive layout (desktop-first, usable on tablet).
- Shared constants in `utils/constants.js`: blood groups, urgencies, statuses, genders.
- Report downloads: call the API with `responseType: 'blob'` (token needed), then trigger a browser download using the filename from `Content-Disposition`.

### 10.2 Pages & Routes

| Route | Page | Access | Content |
|---|---|---|---|
| `/login` | LoginPage | Public | Username/password form |
| `/register` | RegisterPage | Public | Requester self-registration (name, type, phone, address, username, password) |
| `/dashboard` | DashboardPage | A,S | Stat cards (total stock, pending, emergency pending, expiring soon, predicted alerts); **stock-by-group bar chart** with safe-minimum marker and low-stock highlighting; **donations vs issues line chart** (granularity + date range controls); **wastage chart + table**; expiring-soon list; predicted shortage alert list |
| `/donors` | DonorListPage | A,S | Paginated table; filters: blood group, location, last-donation date range, regular-only, search; "Regular" badge; "Add donor" button |
| `/donors/new`, `/donors/:id/edit` | DonorFormPage | A,S | Create/edit form |
| `/donors/:id` | DonorDetailPage | A,S | Profile, eligibility card (reasons, next eligible date), **Record donation** button (disabled with explanation if ineligible), donation history table, delete (admin) |
| `/inventory` | InventoryPage | A,S | Stock-by-group cards (low highlighted); tabs: **All units** (filters: group, status), **Expiring soon** (days selector); "Run expiry sweep" button; delete unit (admin) |
| `/requests` | RequestQueuePage | A,S | Priority-ordered table; filters: status, urgency, blood group; urgency/status badges |
| `/requests/:id` | RequestDetailPage | A,S | Request info; **matches panel** (ranked units, sufficiency indicator, allocation preview); Approve / Reject / Issue buttons enabled per status; issued units list |
| `/requesters` | RequestersPage | A,S | Paginated requester list |
| `/predictions` | PredictionsPage | A,S | Blood-group tabs; **forecast line chart** with safe-minimum reference line; alert cards; **evaluation table** (MAE/RMSE per model, selected model highlighted); horizon input (7–30) + **Run prediction** button with spinner; shows run time and skipped groups |
| `/camps` | CampsPage | A,S | List + create/edit modal; target vs collected progress; delete (admin) |
| `/reports` | ReportsPage | A,S | Report type, date range, format (CSV/PDF), download button |
| `/admin/staff` | StaffPage | A | Staff list, create, edit (name/role/active), reset password, delete |
| `/admin/activity-log` | ActivityLogPage | A | Paginated log with filters |
| `/my/requests` | MyRequestsPage | R | Own requests with status badges |
| `/my/requests/new` | NewRequestPage | R | Form: blood group, quantity, urgency |
| `/my/requests/:id` | MyRequestDetailPage | R | Status + issued units |
| `/my/profile` | MyProfilePage | R | View/edit own profile |
| `*` | NotFoundPage | all | 404 |

### 10.3 Visual conventions
- Tailwind utility classes only; consistent spacing/typography; a red accent color for primary actions is suggested (blood-bank theme).
- Badges: urgency (`emergency` red, `routine` gray); status (`pending` amber, `approved` blue, `issued` green, `rejected` gray/red); unit status (`available` green, `issued` blue, `expired` red).
- Low stock = red highlight; expiring soon = amber highlight.

---

## 11. Project Structure

```
bloodlink/
├── PROJECT.md
├── README.md
├── .gitignore
├── docker-compose.yml                  # PostgreSQL only
├── docker/
│   └── initdb/
│       └── 01-create-test-db.sql       # CREATE DATABASE bloodlink_test;
│
├── docs/
│   ├── ml_evaluation.md                # Phase 4
│   ├── qa_checklist.md                 # Phase 6
│   └── demo_script.md                  # Phase 6
│
├── backend/
│   ├── .env.example
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/                   # initial migration: tables, indexes, v_transactions
│   ├── app/
│   │   ├── main.py                     # app factory, CORS, routers, error handlers, lifespan (startup expiry + scheduler)
│   │   ├── core/
│   │   │   ├── config.py               # pydantic-settings (Section 12)
│   │   │   ├── clock.py                # today()
│   │   │   ├── security.py             # bcrypt hash/verify, JWT encode/decode
│   │   │   ├── deps.py                 # get_db, get_current_user, require_roles(...)
│   │   │   ├── errors.py               # AppError + handlers producing {detail:{code,message}}
│   │   │   └── constants.py            # BLOOD_GROUPS, URGENCIES, statuses
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   └── session.py
│   │   ├── models/                     # user, staff, requester, donor, blood_unit, blood_request,
│   │   │   └── ...                     # issue_record, donation_camp, activity_log, shortage_prediction
│   │   ├── schemas/                    # Pydantic request/response models per resource
│   │   ├── api/
│   │   │   ├── router.py               # mounts all routers under /api
│   │   │   ├── health.py
│   │   │   ├── auth.py
│   │   │   ├── staff.py
│   │   │   ├── activity_logs.py
│   │   │   ├── donors.py
│   │   │   ├── inventory.py
│   │   │   ├── requesters.py
│   │   │   ├── requests.py
│   │   │   ├── matching.py
│   │   │   ├── camps.py
│   │   │   ├── dashboard.py
│   │   │   ├── predictions.py
│   │   │   └── reports.py
│   │   ├── services/
│   │   │   ├── activity_log.py
│   │   │   ├── eligibility.py
│   │   │   ├── compatibility.py        # the single COMPATIBILITY dict + helpers
│   │   │   ├── donors.py               # donation recording
│   │   │   ├── inventory.py            # stock, expiring, expire_overdue_units
│   │   │   ├── matching.py             # ranked compatible-unit query (Section 6.6)
│   │   │   ├── issuing.py              # approve / reject / issue workflow (Section 6.7)
│   │   │   ├── dashboard.py            # summary, trends, wastage
│   │   │   └── reports/                # csv_writer.py, pdf_writer.py, definitions.py
│   │   └── jobs/
│   │       └── scheduler.py            # APScheduler daily expiry job
│   ├── ml/                             # ANALYTICS LAYER (independent of app/)
│   │   ├── __init__.py
│   │   ├── config.py                   # MIN_HISTORY_DAYS, HOLDOUT_DAYS, paths
│   │   ├── data.py                     # aggregation + stock reconstruction
│   │   ├── models/
│   │   │   ├── base.py
│   │   │   ├── linear_regression.py
│   │   │   ├── holt_winters.py
│   │   │   └── arima.py
│   │   ├── evaluation.py
│   │   ├── pipeline.py
│   │   ├── persistence.py
│   │   ├── cli.py
│   │   └── artifacts/                  # latest_evaluation.json (gitignored)
│   ├── scripts/
│   │   ├── create_admin.py             # bootstrap first admin
│   │   └── seed_synthetic_data.py
│   └── tests/
│       ├── conftest.py                 # test DB, Alembic upgrade, client, auth fixtures
│       ├── unit/                       # eligibility, compatibility, allocation, ml models
│       ├── api/                        # per-router API tests
│       └── ml/
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    ├── .env.example                    # VITE_API_BASE_URL=http://localhost:8000/api
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── index.css                   # Tailwind entry
        ├── api/                        # client.js + one module per resource
        ├── context/                    # AuthContext.jsx, ToastContext.jsx
        ├── hooks/                      # useFetch.js, usePagination.js
        ├── routes/                     # AppRoutes.jsx, ProtectedRoute.jsx
        ├── layouts/                    # AuthLayout, StaffLayout, RequesterLayout
        ├── components/
        │   ├── ui/                     # Button, Input, Select, Modal, ConfirmDialog, Badge, Table,
        │   │                           # Pagination, StatCard, Spinner, EmptyState, ErrorBanner
        │   └── charts/                 # StockBarChart, TrendsLineChart, ForecastChart, WastageBarChart
        ├── pages/
        │   ├── auth/                   # LoginPage, RegisterPage
        │   ├── dashboard/              # DashboardPage
        │   ├── donors/                 # DonorListPage, DonorFormPage, DonorDetailPage
        │   ├── inventory/              # InventoryPage
        │   ├── requests/               # RequestQueuePage, RequestDetailPage
        │   ├── requesters/             # RequestersPage
        │   ├── requester/              # MyRequestsPage, NewRequestPage, MyRequestDetailPage, MyProfilePage
        │   ├── predictions/            # PredictionsPage
        │   ├── camps/                  # CampsPage
        │   ├── reports/                # ReportsPage
        │   ├── admin/                  # StaffPage, ActivityLogPage
        │   └── NotFoundPage.jsx
        └── utils/                      # constants.js, format.js, errors.js
```

---

## 12. Configuration

`backend/.env.example` (copy to `backend/.env`):

```
DATABASE_URL=postgresql+psycopg://bloodlink:bloodlink@localhost:5432/bloodlink
TEST_DATABASE_URL=postgresql+psycopg://bloodlink:bloodlink@localhost:5432/bloodlink_test

JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=http://localhost:5173

# Business rules
MIN_DONOR_AGE=18
MAX_DONOR_AGE=65
MIN_DONOR_WEIGHT_KG=50
MIN_DONATION_GAP_DAYS=90
BLOOD_SHELF_LIFE_DAYS=42
REGULAR_DONOR_MIN_DONATIONS=3
EXPIRY_ALERT_DAYS=7

# Prediction
SAFE_MINIMUM_UNITS_DEFAULT=10
SAFE_MINIMUM_BY_GROUP={}              # JSON, e.g. {"O-": 15, "AB-": 5}
PREDICTION_MIN_HISTORY_DAYS=90
PREDICTION_HOLDOUT_DAYS=30
```

`frontend/.env.example`: `VITE_API_BASE_URL=http://localhost:8000/api`

`docker-compose.yml` (PostgreSQL only): service `db` using image `postgres:16`, env `POSTGRES_USER=bloodlink`, `POSTGRES_PASSWORD=bloodlink`, `POSTGRES_DB=bloodlink`, port `5432:5432`, a named volume for data, and `./docker/initdb` mounted at `/docker-entrypoint-initdb.d` (creates `bloodlink_test`). These are **development-only** credentials.

Safe minimum for group `g` = `SAFE_MINIMUM_BY_GROUP.get(g, SAFE_MINIMUM_UNITS_DEFAULT)`; resolved once in `app/core/config.py` and passed to the dashboard, reports, and `ml.pipeline`.

---

## 13. Setup & Run

```bash
# 1. Database
docker compose up -d

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
python -m scripts.create_admin --username admin --password <choose-a-password>   # real bootstrap
# OR load demo data (available from Phase 4 onward; creates demo accounts and ~1 year of history):
python -m scripts.seed_synthetic_data --days 365 --seed 42 --reset
uvicorn app.main:app --reload                             # http://localhost:8000  (docs at /docs)

# 3. Frontend
cd frontend
npm install
cp .env.example .env
npm run dev                                               # http://localhost:5173

# 4. Tests
cd backend && pytest

# 5. Prediction from the CLI (optional; available from Phase 4 onward)
cd backend && python -m ml.cli run --horizon 30
```

---

## 14. Team & Phase Ownership

Work is divided **by phase**, not by technology layer. Each member owns **two consecutive phases** and builds everything those phases need — database changes, backend, analytics, frontend, and tests — as complete vertical slices.

| Member | Phases | Modules covered | What the member delivers |
|---|---|---|---|
| **Sakshi** | **1 and 2** | Module 1 (authentication & roles), Module 2 (donors), Module 3 (inventory), Module 5 (compatibility rules & stock matching lookups) | Repository, Docker database, schema & migrations, backend scaffold, auth/RBAC, staff accounts, activity logging, frontend shell + shared UI kit + login/register; donors, donations, inventory, expiry handling, compatibility engine, and their screens |
| **Saee** | **3 and 4** | Module 4 (requests & issuing), Module 5 (request-level matches), Module 6 (shortage prediction) | Requesters, requests, approve/reject/issue workflow and their screens; synthetic data generator, the entire `backend/ml/` analytics package, prediction API, predictions screen, model evaluation write-up |
| **Esha** | **5 and 6** | Module 7 (dashboard & reports), donation camps, admin screens, system hardening | Dashboard, reports, camps, staff & activity-log screens; then RBAC/activity-log audits, integration tests, security/performance review, UI polish, QA, documentation, demo |

**Ownership rules**

1. Phases are **strictly sequential**. A phase starts only after the previous phase's exit criteria are met and its hand-off is complete. While waiting, the next owner should read this document and review the previous phase's pull requests.
2. The owner of a phase builds **both** the backend and the frontend for that phase (plus tests) and reuses the conventions established earlier: error format (Section 8.1), UI kit and API client, test fixtures, activity-log helper.
3. The API contract (Sections 7 and 8) is fixed. Changing it requires telling the other two members and updating this file in the same pull request.

**Hand-off checklist (end of every phase)**

- [ ] All of the phase's tasks and exit criteria are done; the full test suite passes.
- [ ] Work is merged to `main` through reviewed pull requests.
- [ ] `README.md` has any new setup/run notes; this file is updated if anything in it changed.
- [ ] The outgoing owner gives the next owner a short walkthrough of what exists and what to reuse.

**What each owner hands over**

| Hand-off | The incoming owner receives |
|---|---|
| Phase 2 → Phase 3 (Sakshi → Saee) | Running repo and database; full schema + migration; auth, RBAC dependencies (`require_roles`), activity-log helper, error handling; test fixtures; frontend shell, UI kit, API client, layouts and route protection; donors, donations, inventory, `expire_overdue_units()`; `eligibility.py`, `compatibility.py`, `matching.py` (ranked compatible-unit query) |
| Phase 4 → Phase 5 (Saee → Esha) | Requests/issuing workflow; seeded demo data via `seed_synthetic_data`; `ml` package; prediction endpoints and the reusable alert-derivation function; `ForecastChart` and Recharts usage patterns; `docs/ml_evaluation.md` |

(Phase 1 → 2 and Phase 3 → 4 stay with the same owner, so they are checkpoints, not hand-offs, but the checklist above still applies.)

---

## 15. Implementation Phases

Six phases, no fixed dates. A phase is **done** only when every exit criterion is met. Tasks are numbered `<phase>.<n>` (e.g., Task 2.3).

**Phase ownership:** Phases 1–2 → **Sakshi** · Phases 3–4 → **Saee** · Phases 5–6 → **Esha**.

| Phase | Owner | Theme | Modules |
|---|---|---|---|
| 1 | Sakshi | Foundation & Setup | 1 |
| 2 | Sakshi | Donors, Inventory & Compatibility | 2, 3, 5 (rules + lookups) |
| 3 | Saee | Requests & Issuing | 4, 5 (request-level matches) |
| 4 | Saee | Shortage Prediction | 6 |
| 5 | Esha | Dashboard, Reports, Camps & Admin Screens | 7 |
| 6 | Esha | Hardening, QA, Documentation & Demo | — |

---

### Phase 1 — Foundation & Setup · Owner: Sakshi

**Goal:** a running full-stack skeleton: repository, database, schema, authentication, activity logging, and a frontend shell with login.

**Tasks**

- **1.1 Repository & infrastructure (do first):** create the GitHub repo with the structure in Section 11; `.gitignore` (Python, Node, `.env`, `backend/ml/artifacts/`); root `README.md` skeleton (project name, stack, setup steps from Section 13); `docker-compose.yml` and `docker/initdb/01-create-test-db.sql`. Push to `main` and invite the teammates.
- **1.2 Backend scaffold:** `main.py`, `core/config.py` (all Section 12 settings), `core/clock.py`, `core/errors.py` (handlers producing the Section 8.1 error format), `core/constants.py`, CORS, router mounting under `/api`, `requirements.txt` and `requirements-dev.txt` (all libraries in Section 3, including the ML libraries, so later phases need no environment changes).
- **1.3 Models:** SQLAlchemy 2.x models for all 10 tables exactly as in Section 7.2.
- **1.4 Migration:** Alembic setup and the initial migration: tables, CHECK constraints, UNIQUEs, FKs (`ON DELETE RESTRICT`), all indexes (7.3), and the `v_transactions` view (7.4); working `downgrade()`.
- **1.5 Security & dependencies:** `core/security.py` (bcrypt hash/verify, JWT create/verify) and `core/deps.py` (`get_db`, `get_current_user`, `require_roles(*roles)`; disabled users rejected on every request).
- **1.6 Endpoints:** `GET /api/health`; `POST /api/auth/login`, `POST /api/auth/register`, `GET /api/auth/me`; Staff endpoints (`/api/staff`) including the self-modification guard (Section 6.10).
- **1.7 Activity log:** `services/activity_log.py` (the `record(...)` helper) and `GET /api/activity-logs` (admin); log auth-registration and staff writes.
- **1.8 Admin bootstrap:** `scripts/create_admin.py` (creates `users` + `staff` rows with role `admin`).
- **1.9 Backend tests:** pytest infrastructure — `conftest.py` (test DB from `TEST_DATABASE_URL`, Alembic `upgrade head` once per session, per-test cleanup, authenticated client fixtures for each role, frozen-clock fixture). Tests for auth, RBAC, staff CRUD, activity log, and the migration (tables/indexes/view exist).
- **1.10 Frontend scaffold:** `frontend/` with Vite + React (JavaScript) + Tailwind (per its current Vite guide); install `react-router-dom`, `axios`, `recharts`; `.env.example`.
- **1.11 Frontend core:** `api/client.js` (Axios, base URL from env, Bearer interceptor, 401 handler), `context/AuthContext.jsx`, `context/ToastContext.jsx`, `utils/constants.js`, `utils/errors.js`, `utils/format.js`, `hooks/useFetch.js`, `hooks/usePagination.js`.
- **1.12 Shared UI kit** (`components/ui/*`): Button, Input, Select, Modal, ConfirmDialog, Badge, Table, Pagination, StatCard, Spinner, EmptyState, ErrorBanner.
- **1.13 Layouts & routing:** `AuthLayout`, `StaffLayout` (sidebar), `RequesterLayout`, `AppRoutes.jsx`, `ProtectedRoute.jsx` with `allowedRoles` and role-based post-login redirect (Section 10.1).
- **1.14 Auth pages:** `LoginPage` and `RegisterPage` wired to the real API; placeholder pages for every other route in Section 10.2.

**Exit criteria**

- `docker compose up -d` brings up PostgreSQL with both `bloodlink` and `bloodlink_test` databases.
- `alembic upgrade head` creates all tables, indexes and the view on a clean DB; `alembic downgrade base` works.
- Login, register, `me`, staff CRUD and activity-log endpoints work and are role-protected; `pytest` passes.
- The frontend runs; a user can register (requester) and log in (admin/staff via `create_admin`); role-based redirects and route protection work.

---

### Phase 2 — Donors, Inventory & Compatibility (Modules 2, 3, 5) · Owner: Sakshi

**Goal:** donors can be registered and can donate; units appear in inventory with expiry tracking; the compatibility engine and ranked stock lookup exist.

**Tasks**

- **2.1 Eligibility service:** `services/eligibility.py` (Section 6.2) — a pure function taking donor data, `today` and config. Unit tests for the edge cases: age 17/18/65/66, weight 49.9/50, gap 89/90 days, never donated, multiple failure reasons.
- **2.2 Compatibility & matching services:** `services/compatibility.py` (the single Section 6.3 dict + helpers) and `services/matching.py` (the Section 6.6 ranked compatible-unit query: available, not expired, compatible group, ordered by `expiry_date`, `unit_id`). Unit tests for all 8 requested groups and ordering.
- **2.3 Donor endpoints:** create; list with all filters, sort and pagination; detail (with `donation_count`, `is_regular`, `eligibility`); patch (blood-group guard); delete (admin); `/eligibility`.
- **2.4 Donation endpoints:** `POST /api/donors/{id}/donations` (atomic, Section 6.4) and `GET /api/donors/{id}/donations`.
- **2.5 Inventory:** `services/inventory.py` including `expire_overdue_units()` (Section 6.5); endpoints `/inventory/stock`, `/inventory/units` (filters), `/inventory/units/{id}`, `/inventory/expiring`, `POST /inventory/expire-overdue`, `DELETE /inventory/units/{id}`.
- **2.6 Scheduler:** `jobs/scheduler.py` (APScheduler daily expiry job) and the startup expiry sweep in the `main.py` lifespan.
- **2.7 Matching endpoints:** `GET /api/matching/compatibility` and `GET /api/matching/units`.
- **2.8 Activity logging & backend tests:** log every donor/inventory write. Tests: donor filters, donation atomicity (nothing written on ineligibility), expiry sweep, delete guards (`REFERENCED_RECORD`, `DONOR_HAS_UNITS`, `UNIT_ALREADY_ISSUED`), matching endpoints, RBAC (requester → 403).
- **2.9 Frontend API modules:** `api/donors.js`, `api/inventory.js`, `api/matching.js`.
- **2.10 Donor screens:** `DonorListPage` (all filters, pagination, regular badge) and `DonorFormPage` (create/edit with validation).
- **2.11 Donor detail:** `DonorDetailPage` — profile, eligibility card, Record-donation flow (success toast showing unit id and expiry; ineligibility shows reasons), donation history table, admin delete with confirm.
- **2.12 Inventory screen:** `InventoryPage` — stock cards with low-stock highlighting, units table with filters, expiring-soon tab, expiry-sweep button, admin delete.

**Exit criteria**

- A staff user can register a donor, see eligibility, record a donation, and see the new unit in inventory with `expiry_date = collection_date + 42 days`.
- An ineligible donor is refused with the correct reasons (API and UI).
- The expiry sweep marks overdue units `expired`; the scheduler and startup sweep run without errors.
- `GET /api/matching/units` returns compatible units ranked soonest-expiry first for every blood group.
- All tests pass.

---

### Phase 3 — Requests & Issuing (Modules 4, 5) · Owner: Saee

**Goal:** the full request-to-issue workflow works end-to-end for requesters and staff.

**Tasks**

- **3.1 Requester endpoints:** `GET /requesters`, `GET/PATCH /requesters/me`, `GET /requesters/{id}`, `DELETE /requesters/{id}` — declare the `/me` routes before `/{requester_id}`.
- **3.2 Request endpoints:** `POST /requests` (requester only, `status='pending'`, `request_date = today()`), `GET /requests` (own vs. all, filters, `sort=priority|newest`), `GET /requests/{id}` (with `issued_units`), `DELETE /requests/{id}` (admin).
- **3.3 Request matches:** `GET /api/requests/{id}/matches` using `services/matching.py` (Section 8.2 response shape: compatible groups, count, `sufficient`, `allocation_preview_unit_ids`, ranked units).
- **3.4 Workflow:** `services/issuing.py` and the endpoints `approve`, `reject`, `issue` with the Section 4.3 state machine and the atomic, row-locked, all-or-nothing issue logic (Section 6.7), including `expire_overdue_units()` at the start. Activity logging for each.
- **3.5 Backend tests:** all valid and invalid state transitions; requester isolation (a requester reading another's request → 404); priority ordering; nearest-expiry-first allocation; `INSUFFICIENT_STOCK` leaves the DB unchanged; a **concurrency test** (two simultaneous issues never share a unit); `issue_records` traceability (unit ↔ donor ↔ request ↔ staff); RBAC.
- **3.6 Frontend API modules:** `api/requests.js`, `api/requesters.js`.
- **3.7 Requester portal:** `MyRequestsPage`, `NewRequestPage`, `MyRequestDetailPage`, `MyProfilePage`.
- **3.8 Staff request screens:** `RequestQueuePage` (priority order, filters, badges) and `RequestDetailPage` — request info, **matches panel** (ranked units, sufficiency indicator, allocation preview), Approve/Reject/Issue buttons enabled per status with confirmations, issued-units list, friendly handling of `INSUFFICIENT_STOCK` (shows requested vs. available).
- **3.9 Requesters screen:** `RequestersPage` (paginated list for admin/staff).

**Exit criteria**

- Requester registers → submits a request → staff approves → matches are shown nearest-expiry-first → issue succeeds → stock decreases, request shows `issued`, and issue records link unit ↔ donor ↔ request ↔ staff.
- Insufficient stock is reported with no side effects; rejection works; invalid transitions return 409; emergency requests sort before routine ones.
- All tests pass, including the concurrency test.

---

### Phase 4 — Shortage Prediction (Module 6) · Owner: Saee

**Goal:** a working, evaluated shortage-prediction pipeline exposed through the API and shown in the UI, with realistic seeded data to run it on.

**Tasks**

- **4.1 Synthetic data generator:** `scripts/seed_synthetic_data.py` per Section 9.6, reusing `services/eligibility.py` and `services/compatibility.py` from Phase 2 and the same nearest-expiry-first rule. Includes `--reset`, `--days`, `--seed`, demo accounts, donors, requesters, staff, camps, units, requests and issue records. **Calibrate** it to meet the Section 9.6 calibration requirement and record the final parameters in the script's docstring.
- **4.2 ML package skeleton & data prep:** `ml/` per Section 11 (`config.py`); `ml/data.py` — aggregation from `v_transactions`, stock reconstruction, `insufficient_data` handling (Section 9.1).
- **4.3 Models:** `ml/models/base.py` and the three models `linear_regression`, `holt_winters`, `arima` per Section 9.2, with graceful failure handling.
- **4.4 Evaluation:** `ml/evaluation.py` — chronological split, MAE/RMSE, selection by lowest RMSE, writing `latest_evaluation.json` (Section 9.3).
- **4.5 Pipeline & persistence:** `ml/pipeline.py` (`run_prediction`, Section 9.4) and `ml/persistence.py` (append rows to `shortage_predictions`; never overwrite earlier runs).
- **4.6 CLI:** `ml/cli.py` with `evaluate` and `run --horizon` (Section 9.5).
- **4.7 Prediction API:** `api/predictions.py` — `POST /predictions/run` (expire overdue → pipeline → activity log `prediction_run` with `run_id` in `details` and null `entity_id`), `GET /predictions/latest`, `GET /predictions/alerts` (`within_days`), `GET /predictions/evaluation`. Implement alert derivation (first shortage date, days until shortage, min predicted stock, current stock, sort order) as a **reusable service function** so Phase 5's dashboard can call it.
- **4.8 Tests:** generator invariants (no negative stock, every issued unit is compatible and nearest-expiry-first, no donor donates inside the 90-day gap, correct unit expiry dates, `issue_records.unit_id` unique, reproducible with `--seed`); data-prep correctness; model wrappers on hand-made series with known trend/seasonality (forecast length, values ≥ 0); evaluation (lowest-RMSE selection, failing model excluded, short series handled); pipeline on a small seeded DB (rows written = groups × horizon, skipped group handled, rerun appends a new `run_id`, `is_below_minimum` correct against custom safe minimums); API tests (run → latest → alerts → evaluation consistency, `horizon_days` 7–30 validation, empty-state responses, requester → 403).
- **4.9 Frontend:** `api/predictions.js`, `components/charts/ForecastChart.jsx`, and `PredictionsPage` — group tabs, forecast line chart with safe-minimum reference line, alert cards, evaluation table with the selected model highlighted, horizon input (7–30) + **Run prediction** button with spinner and error handling, skipped-groups note, empty state when no run exists.
- **4.10 Documentation:** `docs/ml_evaluation.md` — per blood group: selected model, MAE/RMSE, observations, and limitations (e.g., synthetic data); add the ML/analytics section to `README.md` (pipeline, models, evaluation method, how to re-run).

**Exit criteria**

- `seed_synthetic_data --reset` produces ≥ 365 days of consistent history meeting the calibration requirement; the same `--seed` reproduces identical data.
- `python -m ml.cli run` completes on seeded data, persists predictions, and writes `latest_evaluation.json` in the Section 8.2 shape.
- From the UI, staff run a prediction and see forecasts, alerts, and evaluation metrics for all predicted groups; requesters get 403 on every prediction route.
- All tests pass.

---

### Phase 5 — Dashboard, Reports, Camps & Admin Screens (Module 7) · Owner: Esha

**Goal:** the staff dashboard, exportable reports, donation camps, and admin screens are complete.

**Tasks**

- **5.1 Dashboard backend:** `services/dashboard.py` + `api/dashboard.py` — `/dashboard/summary`, `/dashboard/trends`, `/dashboard/wastage` exactly per Section 8.2 (zero-filled periods, Monday-start weeks, safe-minimum resolution per Section 12, `predicted_shortage_alert_count` from Phase 4's alert function, `null` when no run exists).
- **5.2 Reports backend:** `services/reports/` (`definitions.py` with the column set per report type, `csv_writer.py`, `pdf_writer.py` using ReportLab — title, generated-at, repeated header row, landscape for wide tables, pagination) and `api/reports.py` (`/reports/{report_type}`; correct headers and filenames; 404 for unknown type; 422 for a bad `format`).
- **5.3 Camps backend:** `api/camps.py` — create, list (filters, sorted by `camp_date` desc), detail, patch, delete (admin) per Section 8.2, with activity logging.
- **5.4 Backend tests:** dashboard numbers against known fixtures; trends granularity and zero-fill; wastage totals; every report type in both formats returns a valid non-empty file (CSV parses; PDF begins with `%PDF`); camps CRUD and RBAC; requester → 403 on dashboard/reports.
- **5.5 Frontend API modules:** `api/dashboard.js`, `api/reports.js`, `api/camps.js`, `api/staff.js`, `api/activityLogs.js`.
- **5.6 Dashboard screen:** `DashboardPage` (Section 10.2) with `StockBarChart` (safe-minimum marker, low-stock highlighting), `TrendsLineChart` (granularity + date-range controls), `WastageBarChart` + table, expiring-soon list, predicted-alert list linking to `/predictions`.
- **5.7 Reports screen:** `ReportsPage` with blob download handling (filename from `Content-Disposition`), loading and error states.
- **5.8 Camps screen:** `CampsPage` — list, create/edit modal, target-vs-collected progress, admin delete.
- **5.9 Admin screens:** `StaffPage` (create, edit name/role/active, reset password, delete with confirm) and `ActivityLogPage` (filters + pagination). Admin-only routes and links are hidden from staff.

**Exit criteria**

- The dashboard shows correct live numbers and charts; low stock is highlighted; predicted alerts are visible.
- Every report type downloads as a valid CSV and PDF from the UI.
- Camps can be managed end-to-end; an admin can manage staff and read the activity log; staff cannot see the admin screens.
- All tests pass; no console errors during a full click-through of the dashboard, reports, camps and admin screens.

---

### Phase 6 — Hardening, QA, Documentation & Demo · Owner: Esha

**Goal:** a stable, secure, documented, demo-ready system.

**Tasks**

- **6.1 RBAC audit:** a test that walks every registered route and asserts the Section 6.1 matrix, including 401 without a token and 403 for disallowed roles.
- **6.2 Activity-log audit:** confirm every write endpoint writes a log row (Section 6.9) and fix any gaps.
- **6.3 Full-flow integration tests:** register donor → donate → requester registers → requests → staff approves → issues → verify stock, `v_transactions`, and activity logs; plus a prediction run and a report export on the resulting data.
- **6.4 Validation & security review:** consistent pagination and error format across all routers; every route has an OpenAPI `summary`, tags and `response_model`; input validation (lengths, enums, `dob` not in the future, valid dates, positive numbers); no `password_hash` in any response; token expiry enforced; disabled users rejected on every request; CORS limited to configured origins.
- **6.5 Performance review:** on seeded data confirm list endpoints and the matching/allocation query stay responsive; `EXPLAIN` the allocation query to confirm index use; add any missing indexes via a new Alembic migration.
- **6.6 Fresh-environment verification:** `docker compose down -v` → `up -d` → `alembic upgrade head` → `create_admin`; `alembic downgrade base` then `upgrade head`; seeder reproducibility (`--seed 42` twice gives identical data); `python -m ml.cli run` on a fresh seeded DB.
- **6.7 UI polish:** consistent badges, spacing, empty/loading/error states, form validation messages, keyboard focus, responsive checks across all pages and both layouts.
- **6.8 Frontend quality gate:** `npm run lint` and `npm run build` pass with no errors or warnings.
- **6.9 End-to-end QA:** write and execute `docs/qa_checklist.md` covering all three roles and every workflow (donor → donation → stock → request → approve → issue → dashboard → prediction → report); record results.
- **6.10 Demo script:** `docs/demo_script.md` — the exact click-path and seeded accounts that show every module in order.
- **6.11 Final documentation:** complete the root `README.md` (overview, tech stack, setup/run, demo accounts, folder structure, how to run tests, screenshots) and make sure this PROJECT.md matches the implementation (update it if any contract changed, with team agreement).
- **6.12 Bug fixing & review:** fix everything found above; every pull request reviewed by another member; no failing tests; no known blockers.

**Exit criteria (project complete)**

- A fresh clone, following the README, gives a working system with seeded data.
- All backend and ML tests pass; frontend lint and build pass; the QA checklist is fully executed.
- Every item in Section 17 is checked.

---

## 16. Testing Strategy

- **Backend (pytest):** run against the dedicated `bloodlink_test` database with the real Alembic migration (so the view and constraints are exercised). Unit tests for pure logic; API tests with the FastAPI TestClient; integration tests for full flows; an RBAC test that walks all routes. Freeze time through `core/clock.today()` for date-dependent logic.
- **ML (pytest):** model wrappers and evaluation on synthetic in-memory series; pipeline against a small seeded DB.
- **Frontend:** `npm run lint`, `npm run build`, and the manual E2E checklist (`docs/qa_checklist.md`).
- Each member writes tests for what they build and does not merge a failing suite.

---

## 17. Final Acceptance Checklist

- [x] Donor registration with demographics and blood group; search/filter by blood group, location, last-donation date; regular donors flagged
- [x] Eligibility enforced (age, weight, 90-day gap) when recording a donation
- [x] Each donation creates a unit with a 42-day expiry; stock levels by group are accurate
- [x] Expiring units are surfaced in-app; overdue units are auto-marked expired (wastage)
- [x] Requesters can self-register, log in, submit requests, and see only their own
- [x] Requests progress `pending → approved → issued` or `rejected`; emergency requests are prioritized
- [x] Matching lists all compatible units ranked nearest-expiry-first; issuing is atomic and traceable (unit ↔ donor ↔ request ↔ staff)
- [x] Prediction run produces 7–30 day forecasts per group, stores them, selects the best of three models via held-out evaluation, and raises safe-minimum alerts
- [x] Dashboard shows stock (low highlighted), donations vs. issues, wastage, predicted alerts
- [x] PDF and CSV reports download correctly for all report types
- [x] Roles enforced exactly per Section 6.1; only admin can delete; activity log records every write
- [x] Passwords are bcrypt-hashed and never returned
- [x] Fresh-clone setup works from the README; all tests pass

---

## 18. Git Workflow (suggested)

- `main` is always runnable. Work on short-lived branches: `feature/<area>-<short-desc>` (e.g., `feature/backend-donors`, `feature/ml-pipeline`, `feature/frontend-dashboard`).
- Open a Pull Request into `main`; at least one other member reviews and the test suite must pass before merge.
- Commit messages: short imperative summary (e.g., `Add eligibility service and tests`).
- Never commit `.env`, virtualenvs, `node_modules`, or `backend/ml/artifacts/`.
- Changing anything in Sections 7 or 8 (schema/API contract) requires telling the other two members and updating this file in the same PR.

---

## 19. Future Extensions (explicitly out of scope now)

Multi-bank network with inter-bank transfers; routing; real-time SMS/email donor alerts and automated donor outreach; deep-learning forecasting; separate handling of blood components (plasma, platelets); linking donation camps to collected units.
