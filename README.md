Forewise
========

Forewise is an operational and finance workflow system for managing projects, work orders, suppliers, equipment, time/work logs, and invoicing, with geo layers (PostGIS) for regions/areas/projects.

This repository intentionally contains **no credentials** (no usernames/passwords/API keys). Configure secrets via environment variables only.

Tech Stack
----------
- Backend: FastAPI (Python), SQLAlchemy, Alembic
- Frontend: React, TypeScript, Vite, Tailwind
- Database: PostgreSQL + PostGIS

Run (Local / Dev)
-----------------

Backend
~~~~~~~
```bash
cd app_backend

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create a local env file (do not commit)
cp .env.example .env

# Edit .env and set at least:
# - DATABASE_URL=postgresql+psycopg2://...
# - SECRET_KEY=...

alembic upgrade head

# Port 8000 is reserved for backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend
~~~~~~~~
```bash
cd app_frontend
npm install

# Dev server (recommended)
npm run dev -- --host 0.0.0.0 --port 5173
```

Project Structure
-----------------
```text
/
  app_backend/      # FastAPI backend (routers/services/models/schemas)
  app_frontend/     # React frontend
  deployment/       # Deployment templates/runbooks (nginx, compose, etc.)
  docs/             # Documentation and audits
  evidence/         # Proof artifacts (screenshots/json) if present
  MASTER_SYSTEM_DOSSIER.md
  KNOWN_ISSUES_ROADMAP.md
  DOCUMENTATION.md
  README.md
```

Current Status
--------------
- Runtime database is PostgreSQL/PostGIS (Postgres-only alignment).
- Map docs moved under `docs/maps/`.
- Audit snapshots moved under `docs/audits/2026-02-02/`.

Known Issues / Roadmap
----------------------
See `KNOWN_ISSUES_ROADMAP.md`.

