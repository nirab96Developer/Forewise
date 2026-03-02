# Forewise — ארכיטקטורה כללית

## מה המערכת עושה?
מערכת לניהול פעילות שטח ביערות קק"ל: פרויקטים, ציוד, ספקים, הזמנות עבודה, דיווחי שעות, חשבוניות, תקציבים.

---

## תרשים ארכיטקטורה עליון

```mermaid
flowchart TB
    subgraph CLIENT["🖥️ לקוח"]
        BROWSER["דפדפן / PWA\nReact 18 + TypeScript + Vite"]
    end

    subgraph NGINX["🔁 Reverse Proxy"]
        NG["Nginx\nforewise.co\nHTTPS / SSL"]
    end

    subgraph BACKEND["⚙️ Backend"]
        API["FastAPI\nPython 3.10\nPort 8000"]
        subgraph LAYERS["שכבות"]
            ROUTERS["Routers Layer\n35 API routers"]
            SERVICES["Services Layer\n25+ business services"]
            MODELS["Models Layer\n50+ SQLAlchemy models"]
            SCHEMAS["Schemas Layer\n50+ Pydantic schemas"]
        end
    end

    subgraph DB["🗄️ Database"]
        PG["PostgreSQL 16\n+ PostGIS\nkkl_forest_prod"]
    end

    subgraph AUTH["🔐 Auth"]
        JWT["JWT Access Token\n30 min TTL"]
        REFRESH["Refresh Token\n7-30 days"]
        OTP["OTP Tokens\n5 min TTL"]
        DEVICE["Device Token\n90 days TTL"]
    end

    subgraph EXTERNAL["🌐 External"]
        EMAIL["SMTP / Brevo\nמיילים"]
        WS["WebSocket\nreal-time"]
    end

    BROWSER -->|"HTTPS"| NG
    NG -->|"HTTP :8000"| API
    NG -->|"dist/"| BROWSER
    API --> ROUTERS --> SERVICES --> MODELS
    MODELS -->|"SQLAlchemy ORM"| PG
    API --> AUTH
    API --> EMAIL
    API --> WS
```

---

## Tech Stack מלא

| שכבה | טכנולוגיה | גרסה |
|------|-----------|-------|
| **Frontend** | React | 18 |
| **Frontend Build** | Vite | 6 |
| **Frontend Language** | TypeScript | 5 |
| **Frontend Styles** | Tailwind CSS | 3 |
| **Frontend Maps** | Leaflet | ---|
| **Frontend Routing** | React Router | 6 |
| **Backend** | FastAPI | ---|
| **Backend Language** | Python | 3.10 |
| **ORM** | SQLAlchemy | 2.0 |
| **Migrations** | Alembic | ---|
| **Validation** | Pydantic | 2 |
| **Database** | PostgreSQL | 16 |
| **Geo Extensions** | PostGIS | ---|
| **Reverse Proxy** | Nginx | 1.18 |
| **Auth** | JWT + OTP + Device Token | ---|
| **Email** | SMTP / Brevo | ---|

---

## כתובות

| שירות | URL |
|-------|-----|
| אפליקציה | https://forewise.co |
| API Docs | https://forewise.co/docs |
| Backend health | https://forewise.co/api/v1/health |
| Supplier Portal | https://forewise.co/supplier-portal/{token} |
