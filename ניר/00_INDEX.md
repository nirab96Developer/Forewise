# Forewise — תיקיית תיעוד ניר

## מה יש פה?

תיקייה זו מכילה **11 מסמכי תיעוד** עם **תרשימי Mermaid** של כל הפרויקט.

---

## רשימת הקבצים

| קובץ | תוכן |
|------|------|
| `01_ARCHITECTURE_OVERVIEW.md` | ארכיטקטורה עליונה — Tech Stack, System Diagram |
| `02_BACKEND_LAYERS.md` | כל שכבות הבאקאנד — core, routers, services, models |
| `03_DATABASE_ERD.md` | ERD מלא — 57+ טבלאות, FK relationships |
| `04_FRONTEND_STRUCTURE.md` | כל קבצי הפרונטאנד — pages, components, services, utils |
| `05_AUTH_FLOWS.md` | כל זרימות Auth — Login, OTP, Device Token, Refresh, RBAC |
| `06_BUSINESS_FLOWS.md` | זרימות עסקיות — Work Order, Fair Rotation, Worklog→Invoice, Budget |
| `07_API_ENDPOINTS_MAP.md` | מפת כל 200+ endpoints לפי router |
| `08_DATA_MODELS.md` | כל המודלים מפורטים — User, WorkOrder, Project, Equipment, Auth |
| `09_SECURITY_RBAC.md` | אבטחה — Middleware Stack, Permissions Matrix, Token Specs |
| `10_DEPLOYMENT_OPS.md` | Deployment — Nginx config, ENV, Deploy procedure, Monitoring |
| `11_COMPONENT_HIERARCHY.md` | היררכיית React — Route tree, Dashboard routing, ProtectedRoute, Map |

---

## סטטוס המערכת (עדכני — מרץ 2026)

```
Backend:    38/38 routers ✅  (היה 37/38 — pricing router תוקן)
Database:   57+ tables, נקי + hardened ✅
Frontend:   52 pages active (3 נמחקו), מחוברים לbackend ✅
Auth:       OTP + JWT + Device Token ✅
Maps:       Leaflet + PostGIS ✅
Email:      Brevo SMTP ✅
Portal:     Supplier Portal flow ✅
Offline:    IndexedDB queue + auto-sync ✅
PDF:        weasyprint worklog PDFs ✅
```

---

## שינויים אחרונים — Session מרץ 2026

### Frontend — מחיקות וניקוי
| קובץ | סטטוס | סיבה |
|------|--------|-------|
| `Suppliers/UpdateSupplierEquipmentRate.tsx` | 🗑️ נמחק | Dead link — אף route לא הוביל אליו |
| `components/common/StatusBadge.tsx` | 🗑️ נמחק | קובץ ריק (6 שורות), לא יובא לשום מקום |
| `Settings/EquipmentRates.tsx` | 🗑️ נמחק | מוזג לתוך `EquipmentCatalog.tsx` |

### Frontend — שינויים
| שינוי | תיאור |
|-------|--------|
| `EquipmentCatalog.tsx` | מוזג עם Rates — עכשיו 2 tabs: "כרטיסים" + "תעריפים" |
| Badge תעריף על כרטיסים | ירוק אם מוגדר, כתום "תעריף לא הוגדר" אם חסר |
| `tailwind.config.js` | `kkl-green` אוחד ל-`#00994C` (היה `#009557`) |
| `/settings/equipment-rates` | Redirect → `/settings/equipment-catalog?tab=rates` |
| `PricingReports.tsx` | Badge ⚠️ "ללא אימות תעריף" + באנר כולל |

### Backend — שינויים
| שינוי | תיאור |
|-------|--------|
| `rate_service.py` | נוסף `get_rate_service(db)`, `resolve_rate()`, `compute_worklog_cost()` |
| `pricing.py` router | **תוקן** — ImportError מנע טעינה. עכשיו 38/38 routers |
| `pricing.py` reports | `unverified_count` + `total_unverified_worklogs` בכל response |
| `compute_worklog_cost()` | Guard: equipment=None + snapshot=None → cost=0, flag=missing_rate_source |

### צבע ירוק — אוחד
```css
/* index.css */          --kkl-green: #00994C;
/* tailwind.config.js */ "kkl-green": "#00994C"  /* היה #009557 */
```

---

## נתוני DB נוכחיים (עדכני)

| ישות | כמות |
|------|------|
| פרויקטים | 60 |
| משתמשים | 8+ |
| ספקים | 17 |
| ציוד פעיל | 47 |
| הזמנות עבודה | 10+ |
| דיווחי שעות | 22+ |
| תקציבים | 147+ |
| פוליגוני יער | 273 |
| מחלקות | 3 (הנהלה / חשבונות / מנהלי עבודה) |

---

## URLs

| URL | מה |
|-----|-----|
| `https://forewise.co` | האפליקציה |
| `https://forewise.co/docs` | Swagger UI |
| `https://forewise.co/api/v1/health` | health check |
| `https://forewise.co/supplier-portal/{token}` | פורטל ספקים |

---

## DB Connection

| שדה | ערך |
|-----|-----|
| SSH Host | `167.99.228.10` |
| SSH Port | `22` |
| SSH User | `root` |
| DB Host | `localhost` |
| DB Port | `5432` |
| Database | `kkl_forest_prod` |
| Username | `kkl_app` |
| Password | `KKL_Prod_2026!` |
