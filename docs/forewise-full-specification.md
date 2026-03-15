# מסמך אפיון מלא — מערכת Forewise לניהול יערות

## 1. תיאור המערכת

מערכת Forewise היא מערכת ניהול פעילות שטח ביערות עבור ארגון לאומי.
המערכת מנהלת: פרויקטי יער, ספקים, ציוד מכני, הזמנות עבודה, דיווחי שעות, חשבוניות ותקציבים.
כוללת תמיכה לעבודה אופליין (Offline-First) לעובדי שטח.

---

## 2. שחקנים (Actors) — 6 משתמשים

| # | שחקן | תיאור | סוג |
|---|-------|--------|-----|
| 1 | **מנהל מערכת** | גישה מלאה — ניהול משתמשים, פרויקטים, תקציבים, ספקים, ציוד, הגדרות | פנימי |
| 2 | **מנהל מרחב** | ניהול ברמת מרחב — פרויקטים, הזמנות, תקציבים, אישור העברות, דוחות | פנימי |
| 3 | **מנהל אזור** | ניהול ברמת אזור — פרויקטים, הזמנות, אישור דוחות, בקשות העברת תקציב | פנימי |
| 4 | **מנהל עבודה** | פרויקטים מוקצים — יצירת הזמנות עבודה, שליחה לספק, דיווח עבודה, סריקת ציוד QR | פנימי |
| 5 | **מנהלת חשבונות** | ניהול פיננסי — ניהול תקציבים, אישור דיווחים, הפקת חשבוניות, צפייה בדוחות | פנימי |
| 6 | **ספק** | ספק חיצוני — גישה דרך פורטל Token בלבד, קבלה או דחייה של הזמנת עבודה | חיצוני |

---

## 3. תרחישי שימוש (Use Cases) — 12 תרחישים

| UC | שם | תיאור | שחקנים מעורבים |
|----|-----|--------|----------------|
| UC1 | התחברות למערכת | כניסה עם שם משתמש וסיסמה, אימות דו-שלבי (OTP), אימות ביומטרי | כל המשתמשים הפנימיים |
| UC2 | ניהול משתמשים | יצירה, עדכון, מחיקה, השעיה, שינוי תפקיד, הקצאת הרשאות | מנהל מערכת |
| UC3 | ניהול פרויקטים | יצירת פרויקטי יער, שיוך לאזור ומרחב, הקצאת מנהל עבודה, הגדרת תקציב | מנהל מערכת, מנהל מרחב, מנהל אזור |
| UC4 | ניהול תקציב | הקצאת תקציב לפרויקט, הקפאה בעת יצירת הזמנה, שחרור בסגירה, העברות בין תקציבים | מנהל מערכת, מנהל מרחב, מנהל אזור, מנהלת חשבונות |
| UC5 | יצירת הזמנת עבודה | יצירת הזמנת עבודה לפרויקט — כולל ציוד, ספק, תאריכים, הקפאת תקציב | מנהל מרחב, מנהל אזור, מנהל עבודה |
| UC6 | שליחת הזמנה לספק | שליחת אימייל לספק עם קישור לפורטל ייעודי. קישור תקף 3 שעות | מנהל עבודה |
| UC7 | אישור / דחיית הזמנה | הספק פותח קישור, רואה את פרטי ההזמנה, מאשר (עם מספר רכב) או דוחה (עם סיבה) | ספק |
| UC8 | דיווח עבודה | דיווח שעות עבודה מהשטח — כולל תמיכה אופליין, סגמנטים (עבודה/מנוחה/נסיעה/לילה) | מנהל עבודה |
| UC9 | סריקת ציוד QR | סריקת קוד QR של ציוד בשטח באמצעות מצלמה, תמיכה אופליין עם סנכרון אוטומטי | מנהל עבודה |
| UC10 | אישור דיווח עבודה | אישור או דחיית דיווחי עבודה על ידי מנהל אזור או מנהלת חשבונות | מנהל אזור, מנהלת חשבונות |
| UC11 | הפקת חשבונית | יצירת חשבונית חודשית מדיווחי עבודה מאושרים — לפי ספק, פרויקט וחודש | מנהלת חשבונות |
| UC12 | צפייה בדוחות | דוחות תמחור, ייצוא Excel/PDF, דוחות לפי פרויקט/ספק/סוג ציוד | מנהל מרחב, מנהלת חשבונות |

### קשרים בין תרחישים

- UC5 → UC6: **include** — יצירת הזמנה כוללת שליחה לספק
- UC7 → UC6: **extend** — אישור/דחייה הוא תוצאה של שליחה לספק
- UC8 → UC10: **include** — דיווח עבודה מוביל לאישור
- UC10 → UC11: **include** — אישור דיווח מוביל להפקת חשבונית

---

## 4. תהליך עסקי מרכזי — Activity Diagram: הזמנת עבודה מקצה לקצה

```
[התחלה]
    ↓
מנהל עבודה יוצר הזמנת עבודה (סטטוס: PENDING)
    ↓
המערכת בודקת תקציב זמין
    ↓
  ┌──── תקציב מספיק? ────┐
  ↓ כן                    ↓ לא
הקפאת תקציב           הצגת שגיאה → [סוף]
  ↓
מנהל עבודה שולח לספק (סטטוס: DISTRIBUTING)
  ↓
המערכת מייצרת Token ושולחת אימייל לספק
  ↓
ספק פותח קישור בפורטל
  ↓
  ┌──── ספק מגיב ────┐
  ↓ מאשר              ↓ דוחה
  ↓                   ↓
סטטוס: APPROVED     רוטציה לספק הבא
  ↓                   ↓ (חוזר לשליחה)
  ↓                   ↓ אם אין ספקים → סטטוס: REJECTED → [סוף]
  ↓
מתאם מתחיל הזמנה (סטטוס: ACTIVE)
  ↓
ביצוע עבודה בשטח
  ↓
מנהל עבודה מדווח שעות (Worklog)
  ↓
מנהל אזור / חשבונאית מאשר/ת דיווח
  ↓
מתאם סוגר הזמנה (סטטוס: COMPLETED)
  ↓
שחרור תקציב מוקפא
  ↓
חשבונאית מפיקה חשבונית חודשית
  ↓
[סוף]
```

### סטטוסי הזמנת עבודה

```
PENDING → DISTRIBUTING → APPROVED → ACTIVE → COMPLETED
                ↓                      ↓
             REJECTED              CANCELLED
```

### סטטוסי דיווח עבודה

```
PENDING → APPROVED → INVOICED
    ↓
  REJECTED
```

---

## 5. מודל נתונים — Class Diagram (ישויות עיקריות)

### User (משתמש)
| שדה | סוג | הערה |
|------|------|------|
| id | int | מפתח ראשי |
| username | string | ייחודי |
| email | string | ייחודי |
| full_name | string | |
| password_hash | string | הצפנת bcrypt |
| role_id | int | מפתח זר → Role |
| region_id | int | מפתח זר → Region |
| area_id | int | מפתח זר → Area |
| is_active | bool | |
| two_factor_enabled | bool | |
| status | string | active / suspended / deleted |

### Role (תפקיד)
| שדה | סוג |
|------|------|
| id | int |
| code | string (ייחודי) |
| name | string |

### Permission (הרשאה)
| שדה | סוג |
|------|------|
| id | int |
| code | string |
| module | string |
| action | string |

### Region (מרחב)
| שדה | סוג |
|------|------|
| id | int |
| code | string |
| name | string |
| geom | PostGIS MULTIPOLYGON |
| total_budget | decimal |

### Area (אזור)
| שדה | סוג |
|------|------|
| id | int |
| code | string |
| name | string |
| region_id | int → Region |

### Project (פרויקט)
| שדה | סוג |
|------|------|
| id | int |
| code | string (ייחודי, למשל YR-001) |
| name | string |
| region_id | int → Region |
| area_id | int → Area |
| budget_id | int → Budget |
| manager_id | int → User |
| status | string |
| start_date | date |
| end_date | date |
| location_geom | PostGIS POINT |

### Budget (תקציב)
| שדה | סוג |
|------|------|
| id | int |
| code | string |
| total_amount | decimal |
| allocated_amount | decimal |
| spent_amount | decimal |
| committed_amount | decimal (מוקפא) |
| project_id | int → Project |
| status | string |

### WorkOrder (הזמנת עבודה)
| שדה | סוג |
|------|------|
| id | int |
| order_number | int (ייחודי) |
| title | string |
| project_id | int → Project |
| supplier_id | int → Supplier |
| equipment_id | int → Equipment |
| status | string (PENDING/DISTRIBUTING/APPROVED/ACTIVE/COMPLETED/REJECTED/CANCELLED) |
| priority | string |
| work_start_date | date |
| work_end_date | date |
| estimated_hours | decimal |
| hourly_rate | decimal |
| frozen_amount | decimal |
| portal_token | string (ייחודי) |
| portal_expiry | datetime |

### Supplier (ספק)
| שדה | סוג |
|------|------|
| id | int |
| code | string |
| name | string |
| contact_name | string |
| phone | string |
| email | string |
| region_id | int → Region |
| area_id | int → Area |
| rating | decimal |
| total_jobs | int |

### Equipment (ציוד)
| שדה | סוג |
|------|------|
| id | int |
| code | string |
| name | string |
| category_id | int → EquipmentCategory |
| equipment_type_id | int → EquipmentType |
| supplier_id | int → Supplier |
| status | string |

### Worklog (דיווח עבודה)
| שדה | סוג |
|------|------|
| id | int |
| work_order_id | int → WorkOrder |
| project_id | int → Project |
| user_id | int → User |
| equipment_id | int → Equipment |
| supplier_id | int → Supplier |
| status | string (PENDING/APPROVED/REJECTED/INVOICED) |
| work_date | date |
| start_time | time |
| end_time | time |
| work_hours | decimal |
| net_hours | decimal |
| paid_hours | decimal |
| hourly_rate_snapshot | decimal |
| cost_before_vat | decimal |
| cost_with_vat | decimal |
| is_overnight | bool |
| overnight_total | decimal |

### Invoice (חשבונית)
| שדה | סוג |
|------|------|
| id | int |
| invoice_number | string (ייחודי) |
| supplier_id | int → Supplier |
| project_id | int → Project |
| month | int |
| year | int |
| status | string |
| total_amount | decimal |
| paid_amount | decimal |
| is_approved | bool |

### InvoiceItem (פריט חשבונית)
| שדה | סוג |
|------|------|
| id | int |
| invoice_id | int → Invoice |
| worklog_id | int → Worklog |
| quantity | decimal |
| unit_price | decimal |
| total_price | decimal |

### BudgetTransfer (העברת תקציב)
| שדה | סוג |
|------|------|
| id | int |
| from_budget_id | int → Budget |
| to_budget_id | int → Budget |
| amount | decimal |
| reason | string |
| status | string (PENDING/APPROVED/REJECTED) |
| requested_by | int → User |
| approved_by | int → User |

### SupplierRotation (רוטציית ספק)
| שדה | סוג |
|------|------|
| id | int |
| supplier_id | int → Supplier |
| area_id | int → Area |
| rotation_position | int |
| total_assignments | int |
| rejection_count | int |

### קשרי ישויות (Relationships)

```
User → Role (Many-to-One)
User → Region (Many-to-One)
User → Area (Many-to-One)
Role → Permission (Many-to-Many, דרך role_permissions)

Region → Area (One-to-Many)
Area → Project (One-to-Many)
Project → Budget (One-to-One)
Project → WorkOrder (One-to-Many)
Project → Worklog (One-to-Many)

Supplier → WorkOrder (One-to-Many)
Supplier → SupplierEquipment (One-to-Many)
Supplier → SupplierRotation (One-to-Many)

WorkOrder → Worklog (One-to-Many)
Worklog → InvoiceItem (One-to-Many)
Invoice → InvoiceItem (One-to-Many)

Equipment → EquipmentCategory (Many-to-One)
Equipment → EquipmentType (Many-to-One)

Budget → BudgetTransfer (One-to-Many, from/to)
```

---

## 6. ארכיטקטורת שכבות — Package Diagram

### שכבה 1: Presentation Layer (Frontend)

```
React 18 + TypeScript + Vite + Tailwind CSS

├── Pages (53+ דפים)
│   ├── Auth: Login, OTP, ForgotPassword, ResetPassword
│   ├── Dashboard: 9 גרסאות לפי תפקיד
│   ├── Projects: רשימה, Workspace (5 טאבים), יצירה, עריכה
│   ├── WorkOrders: רשימה, פרטים, יצירה, תיאום
│   ├── WorkLogs: רשימה, יצירה, פרטים, אישור
│   ├── Suppliers: רשימה, יצירה, עריכה, פורטל ספק (חיצוני)
│   ├── Equipment: מלאי, סריקת QR, יתרות
│   ├── Finance: חשבוניות, תקציבים, העברות
│   ├── Settings: הגדרות מערכת, תפקידים, תעריפים, רוטציה
│   ├── Map: מפת יערות (Leaflet + PostGIS)
│   └── Reports: דוחות תמחור, ייצוא PDF/Excel
│
├── Components (רכיבים משותפים)
│   ├── Navigation (Sidebar + תפריט לפי תפקיד)
│   ├── Map (Leaflet wrapper, פוליגונים, נקודות)
│   ├── Common UI (Button, Input, Modal, Toast, Loader, Badge)
│   ├── Equipment (QRScanner, AttachEquipmentModal)
│   └── Help (SmartHelpWidget, HumanSupportChat)
│
├── Services (שכבת API)
│   ├── api.ts — Axios instance + interceptors + refresh token
│   ├── authService, projectService, workOrderService...
│   └── 15+ service files
│
├── Contexts (ניהול State)
│   ├── AuthContext — מצב משתמש, login/logout
│   ├── LoadingContext — טעינה גלובלית
│   └── NotificationContext — התראות real-time
│
├── Hooks
│   ├── useOfflineSync — סנכרון אופליין אוטומטי
│   ├── useWebSocket — חיבור WebSocket
│   └── useAuth, useApi, useIsMobile
│
└── Utils
    ├── authStorage — ניהול tokens ב-localStorage
    ├── permissions — בדיקת הרשאות בצד לקוח
    ├── offlineStorage — תור IndexedDB לעבודה אופליין
    └── date, format, statusTranslation
```

### שכבה 2: API Layer (Backend Routers)

```
FastAPI — 38 API Routers

├── Auth: /auth — login, OTP, refresh, device-login, biometric, change-password
├── Users: /users — CRUD, suspend, reactivate, change role
├── Roles & Permissions: /roles, /permissions, /role-assignments
├── Geography: /regions, /areas, /locations, /geo (PostGIS layers)
├── Projects: /projects — CRUD, workspace, statistics, by-code
├── WorkOrders: /work-orders — CRUD, send-to-supplier, start, close, approve, reject
├── Worklogs: /worklogs — CRUD, approve
├── Supplier Portal: /supplier-portal/{token} — accept, reject (ללא auth)
├── Suppliers: /suppliers — CRUD, equipment, rotations, constraint-reasons
├── Equipment: /equipment — CRUD, scan, assign, categories, types, rates
├── Finance: /budgets, /budget-transfers, /invoices, /pricing, /system-rates
├── Dashboard: /dashboard — statistics, summary, map data
├── Other: /notifications, /activity-logs, /support-tickets, /reports, /ws (WebSocket)
└── PDF: /pdf/preview — הפקת תצוגת PDF
```

### שכבה 3: Business Logic Layer (Services)

```
25+ שירותים עסקיים

├── auth_service — אימות, OTP, איפוס סיסמה, 2FA
├── project_service — CRUD פרויקטים, סינון לפי תפקיד
├── work_order_service — יצירה, שליחה לספק, ניהול סטטוסים
├── worklog_service — דיווח שעות, חישוב עלויות, סגמנטים
├── supplier_rotation_service — אלגוריתם רוטציה הוגנת
├── budget_service — הקפאה, שחרור, העברות תקציב
├── rate_service — חישוב תעריף: ספק → ציוד → סוג ציוד
├── invoice_service — הפקת חשבונית חודשית, אישור
├── equipment_service — הקצאת ציוד, סריקות QR
├── pdf_report_service — הפקת PDF ושליחה במייל
├── notification_service — יצירת התראות
├── forest_map_service — פוליגוני יער, PostGIS
├── activity_log_service — לוג פעילות
└── user_lifecycle (CRON task) — ניקוי משתמשים פגי תוקף (כל חצות)
```

### שכבה 4: Data Access Layer (Models + Schemas)

```
├── Models — 55+ SQLAlchemy ORM Models (Python classes → DB tables)
│   ├── user.py, role.py, permission.py
│   ├── project.py, budget.py, work_order.py, worklog.py
│   ├── supplier.py, equipment.py, invoice.py
│   ├── region.py, area.py, location.py, forest.py
│   └── notification.py, activity_log.py, audit_log.py, ...
│
├── Schemas — 55+ Pydantic validation schemas (request/response)
│   ├── UserCreate, UserUpdate, UserResponse
│   ├── ProjectCreate, WorkOrderCreate, WorklogCreate
│   └── ...
│
└── Core
    ├── config.py — הגדרות מ-environment variables
    ├── database.py — חיבור PostgreSQL, SessionLocal, get_db()
    ├── security.py — JWT, bcrypt, token TTL
    ├── dependencies.py — get_current_user, require_permission
    ├── email.py — שליחת מיילים (SMTP)
    ├── rate_limiting.py — 100 בקשות/דקה/IP
    └── exceptions.py — שגיאות מותאמות
```

### שכבה 5: Database Layer

```
PostgreSQL 16 + PostGIS Extension

├── 57+ טבלאות
├── SRID 4326 (WGS84) לכל הנתונים הגיאוגרפיים
├── Alembic migrations + SQL ישיר
└── קטגוריות טבלאות:
    ├── Identity & Access (9 טבלאות): users, roles, permissions, sessions, otp_tokens...
    ├── Geography (6 טבלאות): regions, areas, locations, forests, forest_polygons...
    ├── Projects (7 טבלאות): projects, project_assignments, budgets, budget_items...
    ├── Work Execution (6 טבלאות): work_orders, worklogs, worklog_segments...
    ├── Suppliers (7 טבלאות): suppliers, supplier_equipment, supplier_rotations...
    ├── Equipment (7 טבלאות): equipment, equipment_models, equipment_categories...
    ├── Finance (6 טבלאות): invoices, invoice_items, invoice_payments, budget_transfers...
    └── Reporting (7 טבלאות): activity_logs, notifications, audit_logs, support_tickets...
```

---

## 7. ארכיטקטורת פריסה — Deployment Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        אינטרנט                              │
│   [משתמש בדפדפן]  ←──HTTPS──→  [ספק בפורטל]               │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS (443)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  שרת Production (Cloud VPS)                  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              Nginx (Reverse Proxy)                      │  │
│  │  Port 80 → Redirect to HTTPS                           │  │
│  │  Port 443 → SSL (Let's Encrypt)                        │  │
│  │  /           → React SPA (static files from dist/)      │  │
│  │  /api/       → Proxy to Backend (localhost:8000)         │  │
│  └───────┬──────────────────────┬─────────────────────────┘  │
│          │ static files         │ proxy                       │
│          ▼                      ▼                             │
│  ┌──────────────┐    ┌─────────────────────────────────────┐ │
│  │  Frontend     │    │  Backend (FastAPI)                   │ │
│  │  React SPA    │    │  Python + Uvicorn                   │ │
│  │  dist/ folder │    │  Port 8000                          │ │
│  │  (built by    │    │  38 API Routers                     │ │
│  │   Vite)       │    │  25+ Services                       │ │
│  └──────────────┘    │  55+ Models                          │ │
│                       │  CRON Task (חצות)                    │ │
│                       └────────────┬────────────────────────┘ │
│                                    │ SQLAlchemy ORM            │
│                                    ▼                           │
│                       ┌─────────────────────────────────────┐ │
│                       │  PostgreSQL 16 + PostGIS             │ │
│                       │  57+ Tables                          │ │
│                       │  Port 5432 (localhost)               │ │
│                       └─────────────────────────────────────┘ │
│                                                               │
└───────────────────────────────────────────────────────────────┘
              │                              │
              ▼                              ▼
    ┌──────────────────┐          ┌────────────────────┐
    │  שירות SMTP       │          │  IndexedDB          │
    │  (שליחת מיילים)   │          │  (בצד הלקוח)        │
    │  OTP, PDF,        │          │  תור אופליין:       │
    │  הזמנות לספקים    │          │  worklogs, scans,   │
    └──────────────────┘          │  work_orders        │
                                  │  סנכרון אוטומטי     │
                                  └────────────────────┘
```

### טכנולוגיות פריסה

| רכיב | טכנולוגיה |
|-------|-----------|
| שרת | Cloud VPS (Linux) |
| Web Server | Nginx 1.18 |
| SSL | Let's Encrypt (auto-renew) |
| Backend Runtime | Uvicorn (ASGI) |
| Backend Framework | FastAPI (Python 3.10) |
| Database | PostgreSQL 16 + PostGIS |
| Frontend Build | Vite 6 → dist/ folder |
| Frontend Framework | React 18 + TypeScript 5 |
| CSS | Tailwind CSS 3 |
| מפות | Leaflet + PostGIS |
| שליחת מיילים | SMTP (Brevo) |
| הפקת PDF | weasyprint |
| Offline Storage | IndexedDB (בדפדפן) |
| Real-time | WebSocket |

---

## 8. אבטחה ו-RBAC

### מנגנון אימות
1. **Login** → שם משתמש + סיסמה → JWT Access Token (30 דקות)
2. **Refresh Token** → 7-30 ימים
3. **OTP** → קוד 6 ספרות באימייל, תוקף 5 דקות
4. **Device Token** → אימות ביומטרי, תוקף 90 ימים
5. **סיסמאות** → הצפנת bcrypt

### הרשאות
- 267 הרשאות פרטניות (module + action)
- 13 תפקידים מוגדרים
- 359 מיפויי תפקיד-הרשאה
- בדיקת הרשאות בצד שרת (middleware) וצד לקוח (ProtectedRoute)

### הגנות
- Rate Limiting: 100 בקשות/דקה/IP
- CORS: רק מהדומיין המאושר
- Security Headers
- HTTPS בלבד (HTTP מפנה ל-HTTPS)
- פורטל ספק: Token-based, ללא JWT, תוקף 3 שעות, חד-פעמי

---

## 9. היררכיה ארגונית

```
ארגון
├── מרחב צפון (19 מרחבים סה"כ)
│   ├── אזור גליל עליון (21 אזורים סה"כ)
│   │   ├── פרויקט YR-001 (60 פרויקטים סה"כ)
│   │   │   ├── תקציב
│   │   │   ├── הזמנות עבודה
│   │   │   ├── דיווחי שעות
│   │   │   ├── ציוד משויך
│   │   │   └── מיקום (GPS + פוליגון יער)
│   │   ├── פרויקט YR-002
│   │   └── ...
│   ├── אזור גליל מערבי
│   └── ...
├── מרחב מרכז
└── מרחב דרום
```

---

## 10. אלגוריתם רוטציה הוגנת (Fair Rotation)

1. סינון ספקים לפי סוג ציוד נדרש
2. סינון לפי אזור/מרחב
3. סינון לפי זמינות (לא תפוסים)
4. מיון לפי rotation_position (הנמוך ביותר = הבא בתור)
5. שליחה לספק הנבחר
6. אם ספק דוחה → עובר לספק הבא ברשימה
7. אם אין ספקים באזור → הסרת סינון אזור (מצב אילוץ)
8. אם אין ספקים בכלל → שגיאה

---

## 11. תמיכה אופליין (Offline-First)

- **IndexedDB** בצד הלקוח מאחסן: דיווחי עבודה, סריקות ציוד, הזמנות עבודה
- **OfflineBanner** — פס כתום בראש המסך כשאין חיבור
- **Badge** בתפריט — מספר פריטים ממתינים לסנכרון
- **אירוע online** — סנכרון אוטומטי כשחיבור חוזר
- **Header מיוחד** — `X-Offline-Sync: true` לזיהוי בקשות שסונכרנו

---

## 12. סיכום מספרי

| מדד | כמות |
|------|-------|
| שחקנים (Actors) | 6 |
| תרחישי שימוש (Use Cases) | 12 |
| טבלאות בבסיס הנתונים | 57+ |
| מודלים (ORM) | 55+ |
| Routers (API) | 38 |
| Services (Business Logic) | 25+ |
| דפי Frontend | 53+ |
| Endpoints (API) | 200+ |
| הרשאות | 267 |
| תפקידים | 13 |
