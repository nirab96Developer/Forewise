# Forewise — תיקיית תיעוד ניר

## מה יש פה?

תיקייה זו מכילה **11 מסמכי תיעוד** עם **תרשימי Mermaid** של כל הפרויקט.

---

## רשימת הקבצים

| קובץ | תוכן |
|------|------|
| `01_ARCHITECTURE_OVERVIEW.md` | ארכיטקטורה עליונה — Tech Stack, System Diagram |
| `02_BACKEND_LAYERS.md` | כל שכבות הבאקאנד — core, routers, services, models |
| `03_DATABASE_ERD.md` | ERD מלא — 54 טבלאות, FK relationships, ספירת שורות |
| `04_FRONTEND_STRUCTURE.md` | כל קבצי הפרונטאנד — 53 pages, components, services, utils |
| `05_AUTH_FLOWS.md` | כל זרימות Auth — Login, OTP, Device Token, Refresh, RBAC |
| `06_BUSINESS_FLOWS.md` | זרימות עסקיות — Work Order, Fair Rotation, Worklog→Invoice, Supplier Portal |
| `07_API_ENDPOINTS_MAP.md` | מפת כל 200+ endpoints לפי router |
| `08_DATA_MODELS.md` | כל המודלים מפורטים — User, WorkOrder, Project, Equipment, Auth |
| `09_SECURITY_RBAC.md` | אבטחה — Middleware Stack, Permissions Matrix, Token Specs, DB Hardening |
| `10_DEPLOYMENT_OPS.md` | Deployment — Nginx config, ENV, Deploy procedure, Monitoring |
| `11_COMPONENT_HIERARCHY.md` | היררכיית React — Route tree, Dashboard routing, ProtectedRoute, Map |

---

## סטטוס המערכת (נכון לעכשיו)

```
Backend:    35/35 routers ✅
Database:   54 tables, נקי + hardened ✅
Frontend:   53 pages, מחוברים לbackend ✅
Auth:       OTP + JWT + Device Token ✅
Maps:       Leaflet + PostGIS ✅
Email:      SMTP/Brevo ✅
Portal:     Supplier Portal flow ✅
```

---

## נתוני DB נוכחיים

| ישות | כמות |
|------|------|
| פרויקטים | 60 |
| משתמשים אמיתיים | 8 |
| ספקים | 17 |
| ציוד | 47 |
| הזמנות עבודה | 10 |
| דיווחי שעות | 14 |
| תקציבים | 147 |
| פוליגוני יער | 273 |

---

## URLs

| URL | מה |
|-----|-----|
| `https://forewise.co` | האפליקציה |
| `https://forewise.co/docs` | Swagger UI |
| `https://forewise.co/api/v1/health` | health check |
| `https://forewise.co/supplier-portal/{token}` | פורטל ספקים |
