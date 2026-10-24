# BloodLink — Blood Bank Management & Availability Prediction System

> **Mini Project** · Healthcare Informatics · AI/ML  
> Core areas: Database Management Systems · Python for Data Science · Software Engineering  
> Team: **Sakshi** (Phases 1–2) · **Saee** (Phases 3–4) · **Esha** (Phases 5–6)

---

## Overview

BloodLink is a centralized blood bank management platform that digitizes donor records, inventory tracking, and request issuing while providing explainable time-series shortage prediction (Holt-Winters, ARIMA, Linear Regression) to proactively alert staff before blood group shortages occur.

---

## Tech Stack

- **Backend**: FastAPI (Python 3.11+), Uvicorn, SQLAlchemy 2.x, Alembic, psycopg v3, Pydantic v2, PyJWT, bcrypt, APScheduler.
- **Analytics & Prediction**: pandas, numpy, scikit-learn, statsmodels.
- **Reporting**: ReportLab (PDF), standard CSV.
- **Database**: PostgreSQL 16 (via Docker Compose).
- **Frontend**: React (Vite, plain JavaScript, no TypeScript), Tailwind CSS, React Router, Axios, Recharts.
- **Testing**: pytest, httpx (TestClient).

---

## Quickstart Setup & Run

### 1. Database (PostgreSQL 16)

```bash
docker compose up -d
```
This spins up PostgreSQL on port 5432 and initializes both `bloodlink` and `bloodlink_test` databases.

### 2. Backend

```bash
cd backend
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
alembic upgrade head

# Bootstrap first admin user:
python -m scripts.create_admin --username admin --password adminpassword123 --name "Admin User"

# Start the dev server:
uvicorn app.main:app --reload
```
API Documentation is available at: `http://localhost:8000/docs`

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
Access the application at: `http://localhost:5173`

### 4. Running Tests

```bash
cd backend
pytest
```

---

## Documentation

- [PROJECT.md](PROJECT.md): Definitive architecture and system specifications.
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md): Living handoff plan and implementation tracking.
- [HANDOFF.md](HANDOFF.md): Living handoff log and phase progress tracking.

