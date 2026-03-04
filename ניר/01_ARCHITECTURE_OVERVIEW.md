# Forewise — ארכיטקטורה כללית (עדכני מרץ 2026)

## מה המערכת עושה?
מערכת לניהול פעילות שטח ביערות קק"ל:  
פרויקטים, ציוד, ספקים, הזמנות עבודה, דיווחי שעות, חשבוניות, תקציבים.  
כולל תמיכה Offline-First לעובדי שטח + ניהול מחזור חיים של משתמשים.

---

## תרשים ארכיטקטורה עליון

```mermaid
flowchart TB
    subgraph CLIENT["🖥️ לקוח"]
        BROWSER["דפדפן / PWA\nReact 18 + TypeScript + Vite"]
        IDB["IndexedDB\nOffline Queue\n(worklogs / scans / work_orders)"]
        BROWSER -.->|"offline"| IDB
    end

    subgraph NGINX["🔁 Reverse Proxy"]
        NG["Nginx\nforewise.co\nHTTPS / SSL\nServes dist/ + proxy to :8000"]
    end

    subgraph BACKEND["⚙️ Backend"]
        API["FastAPI\nPython 3.10\nPort 8000"]
        subgraph LAYERS["שכבות"]
            ROUTERS["Routers Layer\n38 API routers"]
            SERVICES["Services Layer\n25+ business services"]
            MODELS["Models Layer\n55+ SQLAlchemy models"]
            SCHEMAS["Schemas Layer\n55+ Pydantic schemas"]
        end
        CRON["CRON Task\nschedule_nightly_cleanup()\nPython asyncio — כל חצות\nמאחד users פגי-תוקף"]
    end

    subgraph DB["🗄️ Database"]
        PG["PostgreSQL 16\n+ PostGIS\nkkl_forest_prod\n57+ tables"]
    end

    subgraph AUTH["🔐 Auth"]
        JWT["JWT Access Token\n30 min TTL"]
        REFRESH["Refresh Token\n7-30 days"]
        OTP["OTP Tokens\n5 min TTL\nBrevo email"]
        DEVICE["Device Token\n90 days TTL"]
    end

    subgraph EXTERNAL["🌐 External"]
        EMAIL["Brevo SMTP\nמיילים: OTP / WO / PDF"]
        WS["WebSocket\nreal-time notifications"]
        PDF["weasyprint\nPDF worklogs"]
    end

    BROWSER -->|"HTTPS"| NG
    NG -->|"HTTP :8000"| API
    NG -->|"dist/"| BROWSER
    IDB -->|"auto-sync online event"| BROWSER
    API --> ROUTERS --> SERVICES --> MODELS
    MODELS -->|"SQLAlchemy ORM"| PG
    API --> AUTH
    API --> EMAIL
    API --> WS
    API --> PDF
    CRON --> PG
```

---

## Tech Stack מלא

| שכבה | טכנולוגיה | גרסה | הערות |
|------|-----------|-------|--------|
| **Frontend** | React | 18 | |
| **Frontend Build** | Vite | 6 | |
| **Frontend Language** | TypeScript | 5 | |
| **Frontend Styles** | Tailwind CSS | 3 | `kkl-green: #00994C` |
| **Frontend Maps** | Leaflet | latest | PostGIS data |
| **Frontend Routing** | React Router | 6 | lazy loading |
| **Frontend Offline** | IndexedDB | native | worklog/scan/WO queue |
| **Backend** | FastAPI | latest | |
| **Backend Language** | Python | 3.10 | |
| **ORM** | SQLAlchemy | 2.0 | |
| **Migrations** | Alembic | latest | + direct SQL |
| **Validation** | Pydantic | 2 | |
| **Database** | PostgreSQL | 16 | |
| **Geo Extensions** | PostGIS | latest | SRID=4326 |
| **Reverse Proxy** | Nginx | 1.18 | |
| **Auth** | JWT + OTP + Device Token | | |
| **Email** | Brevo SMTP | | OTP + PDF |
| **PDF** | weasyprint | latest | worklog reports |
| **Task Scheduling** | asyncio (Python) | | CRON לילי |

---

## System Components Map

```mermaid
flowchart LR
    subgraph FE["Frontend (React)"]
        direction TB
        NAV["Navigation\n(sidebar + role menu)"]
        PAGES["52 Pages\n(lazy loaded)"]
        OFFLINE["Offline Layer\nIndexedDB + OfflineBanner\nuseOfflineSync hook"]
        HELP["SmartHelpWidget\nHumanSupportChat\nBOT → Ticket"]
    end

    subgraph BE["Backend (FastAPI)"]
        direction TB
        AUTH_M["Auth Middleware\nJWT decode + rate limit"]
        R38["38 Routers\n/api/v1/*"]
        SVC["Services\nbusiness logic"]
        CRON_T["CRON Task\nnightly anonymize"]
    end

    subgraph STORE["Storage"]
        PG_DB["PostgreSQL\n57+ tables"]
        FILES["File System\n/reports/worklogs/*.pdf"]
    end

    FE -->|"Axios + Bearer"| BE
    BE --> STORE
    OFFLINE -.->|"reconnect"| BE
    BE -->|"email"| BREVO["📧 Brevo"]
```

---

## Role-to-Dashboard Map

```mermaid
flowchart TD
    LOGIN["POST /auth/login"] --> ROLE{"תפקיד?"}
    ROLE -->|"ADMIN"| D1["AdminDashboard\nכל המערכת"]
    ROLE -->|"REGION_MANAGER"| D2["RegionManagerDashboard\nמרחב ספציפי"]
    ROLE -->|"AREA_MANAGER"| D3["AreaManagerDashboard\nאזור ספציפי"]
    ROLE -->|"WORK_MANAGER"| D4["WorkManagerDashboard\nפרויקטים שלי + מפה\nשעות שבוע + הזמנות"]
    ROLE -->|"ACCOUNTANT"| D5["AccountantInbox\nחשבוניות + generate monthly"]
    ROLE -->|"ORDER_COORDINATOR"| D6["OrderCoordination\nauto-refresh 30s"]
    ROLE -->|"FIELD_WORKER"| D7["FieldWorkerDashboard\nמשימות שטח"]
    ROLE -->|"SUPPLIER"| D8["SupplierPortal\nחיצוני - ללא auth"]
    ROLE -->|"VIEWER"| D9["ViewerDashboard\nצפייה בלבד"]
```

---

## כתובות

| שירות | URL |
|-------|-----|
| אפליקציה | https://forewise.co |
| API Docs (Swagger) | https://forewise.co/docs |
| Backend health | https://forewise.co/api/v1/health |
| Supplier Portal | https://forewise.co/supplier-portal/{token} |

---

## שרת Production

| פרמטר | ערך |
|-------|-----|
| IP | `167.99.228.10` |
| SSH User | `root` |
| Backend Service | `forewise.service` (systemctl) |
| DB | `kkl_forest_prod` @ localhost:5432 |
| DB User | `kkl_app` / `KKL_Prod_2026!` |
| Frontend | nginx serves `/root/kkl-forest/app_frontend/dist/` |
| Logs | `journalctl -u forewise -f` |
