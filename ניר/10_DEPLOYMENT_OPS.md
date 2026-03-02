# Deployment & Operations

## Production Environment

```mermaid
flowchart TD
    subgraph INTERNET["🌐 Internet"]
        USER["👤 משתמש\nforewise.co"]
        SUPPLIER["🚛 ספק\nforewise.co/supplier-portal/token"]
    end

    subgraph SERVER["☁️ Production Server\nDigitalOcean Droplet\nIP: 167.99.228.10"]
        subgraph NGINX_SRV["Nginx 1.18"]
            HTTP_RD["Port 80 → 301 HTTPS"]
            HTTPS_SRV["Port 443 (SSL)\nssl_certificate: Let's Encrypt\nforewise.co + www.forewise.co"]
            STATIC["dist/ → React SPA\ntry_files → /index.html"]
            PROXY["location /api/ → localhost:8000"]
        end

        subgraph BACKEND["FastAPI Backend"]
            UVICORN["uvicorn app.main:app\nPort 8000\nPID managed manually"]
        end

        subgraph DB["PostgreSQL"]
            PG["PostgreSQL 16\n+ PostGIS\nkkl_forest_prod DB\nUser: kkl_app"]
        end

        subgraph FILES["Files"]
            FE_DIST["app_frontend/dist/\n← npm run build output\n← nginx serves this"]
            BE_SRC["app_backend/\n.venv/ (Python deps)"]
            ENV[".env (NOT in git!)\nDATABASE_URL\nSECRET_KEY\nSMTP_*"]
        end
    end

    USER -->|"HTTPS 443"| HTTPS_SRV
    SUPPLIER -->|"HTTPS 443"| HTTPS_SRV
    HTTPS_SRV -->|"/api/"| PROXY
    PROXY -->|"localhost:8000"| UVICORN
    HTTPS_SRV -->|"/*.html,js,css"| STATIC
    UVICORN --> PG
    BACKEND --> ENV
```

---

## Nginx Configuration

```nginx
# /etc/nginx/sites-available/forewise

server {
    listen 80;
    server_name forewise.co www.forewise.co;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name forewise.co www.forewise.co;

    ssl_certificate /etc/letsencrypt/live/forewise.co/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/forewise.co/privkey.pem;

    root /root/kkl-forest/app_frontend/dist;
    index index.html;

    # React SPA
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Swagger
    location /docs {
        proxy_pass http://localhost:8000;
    }

    location /openapi.json {
        proxy_pass http://localhost:8000;
    }
}
```

---

## Deploy Procedure

```bash
# 1. Backend changes
cd /root/kkl-forest/app_backend
# Edit code
# Apply DB migrations if needed:
python3 -c "from app.core.database import get_db; from sqlalchemy import text; ..."

# 2. Restart backend
kill $(pgrep -f "uvicorn app.main")
sleep 2
.venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# 3. Frontend changes
cd /root/kkl-forest/app_frontend
# Edit code
npm run build

# 4. Reload nginx
systemctl reload nginx

# 5. Verify
curl https://forewise.co/api/v1/health
```

---

## Environment Variables (.env)

```bash
# Database
DATABASE_URL=postgresql+psycopg2://kkl_app:PASSWORD@localhost:5432/kkl_forest_prod

# Security
SECRET_KEY=<64-char random>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# App
APP_HOST=0.0.0.0
APP_PORT=8000
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO

# Email (Brevo/SMTP)
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=<brevo_login>
SMTP_PASSWORD=<brevo_password>
BREVO_API_KEY=<key>
EMAIL_FROM=noreply@forewise.co

# Redis (optional)
REDIS_ENABLED=false
REDIS_URL=redis://localhost:6379

# Safe Mode
SAFE_MODE=false

# CORS
CORS_ORIGINS=https://forewise.co,https://www.forewise.co
```

---

## Health Checks

```bash
# Backend
GET https://forewise.co/health
→ {"status":"ok","timestamp":"...","version":"1.0.0","environment":"production"}

GET https://forewise.co/api/v1/health/db
→ {"database":"connected","status":"ok"}

# Check routers loaded
GET https://forewise.co/info
→ {"routers":{"פעילים":[...],"נכשלו":[],"סהכ":35}}
```

---

## Monitoring (Current State)

| What | Status |
|------|--------|
| Health endpoint | ✅ `/health` |
| Error logging | ✅ loguru → `app_backend/logs/development.log` |
| Activity logging | ✅ DB → `activity_logs` table (731 rows) |
| APM / Alerting | ❌ לא מוגדר (Sentry רצוי) |
| Backup strategy | ❌ לא מוגדר |
| Auto-restart uvicorn | ❌ manual (systemd/supervisor מומלץ) |

---

## Git Repository

```
Remote: https://github.com/nirab96Developer/Forewise.git
Branch: main
Commits:
  01851a7 🌲 Initial commit - Forewise v1.0
  e04c145 chore: update gitignore, nginx config, env.production...
```

---

## File Structure (Root)

```
/root/kkl-forest/
├── app_backend/          ← FastAPI backend
│   ├── app/              ← Application code
│   │   ├── core/         ← Config, DB, Security
│   │   ├── models/       ← SQLAlchemy models (50+)
│   │   ├── schemas/      ← Pydantic schemas (50+)
│   │   ├── services/     ← Business logic (25+)
│   │   ├── routers/      ← API endpoints (35)
│   │   └── main.py       ← FastAPI app
│   ├── alembic/          ← DB migrations
│   │   └── versions/     ← Migration scripts
│   ├── tests/            ← pytest tests
│   ├── .env              ← ⚠️ NOT IN GIT
│   ├── requirements.txt
│   └── .venv/            ← Python virtualenv (NOT in git)
│
├── app_frontend/         ← React frontend
│   ├── src/              ← Source code
│   │   ├── pages/        ← 53+ page components
│   │   ├── components/   ← Reusable components
│   │   ├── services/     ← API service layer
│   │   ├── contexts/     ← React contexts
│   │   ├── hooks/        ← Custom hooks
│   │   └── utils/        ← Utilities
│   ├── dist/             ← Built output (nginx serves this)
│   ├── public/           ← Static assets + sw.js
│   ├── .env.production   ← VITE_API_URL
│   └── package.json
│
├── deployment/           ← nginx config, docker-compose
├── docs/                 ← Documentation
│   ├── audits/2026-02-02/
│   ├── maps/
│   ├── geodata/
│   └── ui/
├── ניר/                  ← THIS FOLDER - Diagrams
├── MASTER_SYSTEM_DOSSIER.md
├── KNOWN_ISSUES_ROADMAP.md
├── DOCUMENTATION.md
├── README.md
└── .gitignore
```
