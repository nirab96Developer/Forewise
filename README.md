# Forewise — Field Operations Management System

Forewise is a comprehensive platform for managing field operations: projects, suppliers, equipment, work orders, worklogs, budgets, invoices, and real-time monitoring.

---

## Architecture

```
app_frontend/   — React 18 + TypeScript + Vite (PWA, mobile-first)
app_backend/    — FastAPI + SQLAlchemy + PostgreSQL
```

---

## Key Modules

| Module | Frontend | Backend |
|--------|----------|---------|
| Auth | Login, OTP, Biometric | `/api/v1/auth` |
| Users & Roles | Settings → Admin | `/api/v1/users`, `/api/v1/roles` |
| Organization | Regions, Areas, Locations | `/api/v1/regions`, `/api/v1/areas` |
| Projects | Projects, Workspace | `/api/v1/projects` |
| Budgets | Settings → Budgets | `/api/v1/budgets` |
| Work Orders | Work Orders, Coordination | `/api/v1/work-orders` |
| Suppliers | Suppliers, QR Tools | `/api/v1/suppliers` |
| Equipment | Inventory, Scan | `/api/v1/equipment` |
| Work Logs | Field Reports, Approval | `/api/v1/worklogs` |
| Invoices | Invoices | `/api/v1/invoices` |
| Reports | Pricing, Excel Export | `/api/v1/reports` |
| Support | Tickets | `/api/v1/support-tickets` |

---

## Business Flow

```
Work Request → Budget Check → Work Order → Coordinator Queue
→ Supplier Dispatch (email + portal token)
→ Supplier Approve/Reject via Landing Page
→ Field Execution (QR Scan validation)
→ Worklog Submission
→ Accountant Approval
→ Invoice Generation → Payment
```

---

## Local Development

### Backend

```bash
cd app_backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill DB credentials
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd app_frontend
npm install
cp .env.example .env.local   # set VITE_API_URL and VITE_SENTRY_DSN
npm run dev
```

App: http://localhost:5173

---

## Environment Variables

### Backend (`app_backend/.env`)

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing key |
| `SENTRY_DSN` | Sentry error tracking DSN |
| `ENVIRONMENT` | `production` / `development` |

### Frontend (`app_frontend/.env.local`)

| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Backend API base URL |
| `VITE_SENTRY_DSN` | Sentry DSN (browser) |

---

## Production Deployment

The backend runs under systemd (`kkl-backend.service`). Restart after changes:

```bash
sudo systemctl restart kkl-backend
sudo journalctl -u kkl-backend -f
```

Frontend is built and served as static files:

```bash
cd app_frontend && npm run build
# dist/ → served by nginx
```

---

## Key Technical Decisions

- **QR Code validation**: Supplier equipment tools generate scannable QR codes (`GET /api/v1/suppliers/{id}/equipment/{eqId}/qr-code`) containing `supplier_id`, `equipment_id`, and `license_plate` for field validation.
- **Budget guard**: Work order creation checks remaining project budget and returns `422 BUDGET_INSUFFICIENT` if estimated cost exceeds available funds.
- **Offline sync**: PWA service worker + `/api/v1/sync` endpoint queue operations for later submission.
- **Fair rotation**: Supplier selection follows configurable fair-rotation rules (`/api/v1/supplier-rotations`).
- **Monitoring**: Sentry (frontend replay + backend FastAPI/SQLAlchemy integrations), slow-query alerting (> 500 ms), Loguru structured logs.
