# Forewise — Forest & Project Operations Management

A full-stack web application for managing field operations in forests and nature reserves.
Handles the complete lifecycle from project creation through work orders, supplier coordination,
equipment tracking, time reporting, and invoicing.

---

## Project Structure

```
forewise/
├── app_backend/          # FastAPI backend (Python)
│   ├── alembic/          # Alembic DB migrations
│   ├── app/              # Application code
│   │   ├── core/         # Config, DB, auth, middleware
│   │   ├── models/       # SQLAlchemy models
│   │   ├── routers/      # API endpoints
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   ├── tasks/        # Background tasks
│   │   └── utils/        # Helpers and utilities
│   ├── migrations/       # Raw SQL migrations
│   ├── scripts/          # Utility and maintenance scripts
│   ├── tests/            # Pytest test suite
│   ├── run.py            # Development server entry point
│   ├── wsgi.py           # Production WSGI entry point
│   └── start_production.sh
│
├── app_frontend/         # React 18 + TypeScript + Vite frontend
│   ├── cypress/          # Cypress E2E tests
│   ├── electron/         # Electron desktop wrapper
│   ├── mock-server/      # Development mock API server
│   ├── src/              # Application source
│   ├── tests/            # Playwright E2E tests
│   └── vite.config.ts
│
├── docs/                 # Project documentation
│   ├── assets/           # Brand assets
│   ├── audits/           # Historical audit reports
│   ├── diagrams/         # Architecture diagrams
│   ├── geodata/          # GeoJSON boundary files
│   └── screenshots/      # UI screenshots
│
├── scripts/              # Top-level utility scripts
└── .github/workflows/    # CI/CD pipelines
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Backend | FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL |
| Auth | JWT, 2FA, OTP, WebAuthn |
| Maps | Leaflet, Google Maps |
| Tests | Playwright, Cypress, Pytest |
| Deploy | Docker, Gunicorn, GitHub Actions |

---

## Quick Start

### Backend

```bash
cd app_backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in DB credentials
alembic upgrade head
python run.py
```

### Frontend

```bash
cd app_frontend
npm install
npm run dev
```

### Demo Users

| Username | Role | Password |
|---|---|---|
| admin | Admin | !Forewise2026 |
| work.manager | Work Manager | !Forewise2026 |
| order.coordinator | Order Coordinator | !Forewise2026 |
| accountant.north | Accountant | !Forewise2026 |
| region.north | Region Manager | !Forewise2026 |
| area.upper | Area Manager | !Forewise2026 |

---

## User Roles

| Role | Responsibilities |
|---|---|
| **Admin** | Full system access, users, settings |
| **Region Manager** | Regional overview, budgets, reports |
| **Area Manager** | Area operations, budget approvals |
| **Work Manager** | Create work orders, report hours |
| **Order Coordinator** | Coordinate orders with suppliers |
| **Accountant** | Approve worklogs, manage invoices |

---

## Key Flows

1. **Work Order** → Work Manager creates → Coordinator sends to supplier → Supplier accepts → Equipment linked → Work begins
2. **Worklog** → Work Manager reports hours → Accountant approves → Budget updated
3. **Invoice** → Created from approved worklogs → Approved → Sent → Paid
