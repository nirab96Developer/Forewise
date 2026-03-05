# Forewise — תיקיית תיעוד ניר (עדכני מרץ 2026)

## מה יש פה?

תיקייה זו מכילה **11 מסמכי תיעוד** עם **תרשימי Mermaid ודיאגרמות מלאות** של כל הפרויקט.

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

## שינויים אחרונים — Session מרץ 2026 (עדכון 05/03/2026)

### Frontend — מחיקות וניקוי
| קובץ | סטטוס | סיבה |
|------|--------|-------|
| `Suppliers/UpdateSupplierEquipmentRate.tsx` | 🗑️ נמחק | Dead link — אף route לא הוביל אליו |
| `components/common/StatusBadge.tsx` | 🗑️ נמחק | קובץ ריק (6 שורות), לא יובא לשום מקום |
| `Settings/EquipmentRates.tsx` | 🗑️ נמחק | מוזג לתוך `EquipmentCatalog.tsx` |

### Frontend — נוסף
| קובץ | נתיב | תיאור |
|------|------|--------|
| `Login/ChangePassword.tsx` | `/change-password` | שינוי סיסמה חובה בכניסה ראשונה (must_change_password) |
| `Budget/BudgetTransfers.tsx` | `/budget-transfers` | בקשות העברת תקציב — AREA_MANAGER + REGION_MANAGER |
| `PendingSync/PendingSync.tsx` | `/pending-sync` | רשימת offline items ממתינים לסנכרון + כפתור "סנכרן הכל" |
| `OfflineBanner.tsx` | (component) | פס כתום בראש המסך כשאין חיבור |
| `utils/offlineStorage.ts` | (util) | IndexedDB API: saveOfflineWorklog/Scan/WorkOrder + getPendingItems |

### Frontend — שינויים
| שינוי | תיאור |
|-------|--------|
| `EquipmentCatalog.tsx` | מוזג עם Rates — עכשיו 2 tabs: "כרטיסים" + "תעריפים" + badge תעריף |
| `tailwind.config.js` | `kkl-green` אוחד ל-`#00994C` (היה `#009557`) |
| `/settings/equipment-rates` | Redirect → `/settings/equipment-catalog?tab=rates` |
| `PricingReports.tsx` | Badge ⚠️ "ללא אימות תעריף" + באנר כולל + expandable rows + PDF export |
| `WorkManagerDashboard.tsx` | נתונים אמיתיים מ-API: שעות שבוע / הזמנות / מפה |
| `AccountantInbox.tsx` | כפתור "הפק חשבונית חודשית" עם modal |
| `Users.tsx` | badges מושהה/נמחק + SuspendModal + ChangeRoleModal |
| `WorklogDetail.tsx` | badge "🌙 שמירת לילה" אם is_overnight=true |
| `Navigation.tsx` | badge 📤 "N ממתינים" ל-WORK_MANAGER + OfflineBanner |
| `ProjectWorkspaceNew.tsx` | Budget card: total/committed/spent/available + WO progress bar |
| `ProjectWorkspaceNew.tsx` | **מפה:** נקודה כתומה תמיד מוצגת — centroid כש-has_forest=true, GPS כש-false |
| `ProjectWorkspaceNew.tsx` | **פרטי פרויקט:** שדה "מנהל עבודה" (WORK_MANAGER מ-project_assignments) |
| `ProjectWorkspaceNew.tsx` | **פרטי פרויקט:** שדה "מנהל אזור" (AREA_MANAGER מ-area_id) |
| `ProjectWorkspaceNew.tsx` | **פרטי פרויקט:** שדה "מנהלת חשבונות אזורית" (ACCOUNTANT מ-area_id) |
| `ProjectWorkspaceNew.tsx` | sticky header: top-0 → top-16 (מתחת ל-navbar) + z-10 |
| `Invoices.tsx` | 4 summary cards: total/amount/balance_due/paid עם overdue badge |
| `SmartHelpWidget.tsx` | FAQ 10 שאלות בעברית + זרימה BOT → ticket |
| `select` elements | pl-10 + font-size:16px + min-height:44px במובייל |
| header padding | pt-20 → pt-16 בכל דפי wrapper |

### Backend — שינויים
| שינוי | תיאור |
|-------|--------|
| `rate_service.py` | `get_rate_service(db)`, `resolve_rate()`, `compute_worklog_cost()` עם guard |
| `pricing.py` router | **תוקן ImportError** — עכשיו 38/38 routers טוענים |
| `pricing.py` reports | `unverified_count` + `total_unverified_worklogs` + `worklogs_detail` per project |
| `users.py` router | `/suspend`, `/reactivate`, `/role` endpoints |
| `budget_transfers.py` | router חדש — request/approve/reject |
| `budget_service.py` | `freeze_budget_for_work_order`, `release_budget_freeze`, transfers |
| `worklog_service.py` | `calculate_worklog_totals`, `save_worklog_with_segments`, 12hr guard |
| `invoice_service.py` | `generate_monthly_invoice`, `get_uninvoiced_suppliers` |
| `pdf_report_service.py` | `generate_and_save_worklog_pdf` (weasyprint) + email |
| `user_lifecycle.py` | CRON: `anonymize_expired_users()` + lifespan integration |
| `audit_logs` trigger | INSERT on suspend/role-change/invoice-status-change |
| `sync_queue` | X-Offline-Sync header → INSERT audit record |
| `projects.py` | `list_projects` — סינון אוטומטי לפי role (REGION_MANAGER/AREA_MANAGER/WORK_MANAGER) |
| `projects.py` | `GET /code/{code}` — מחזיר `manager` (WORK_MANAGER), `accountant`, `area_manager` |
| `schemas/project.py` | `ProjectResponse` — הוספת שדות: `manager`, `accountant`, `area_manager` (UserBasic) |
| `models/__init__.py` | **תוקן ImportError** — הוספת `ProjectAssignment` לexports |
| `activity_log.py` schema | `activity_type: Optional[str]` (תוקן ResponseValidationError) |

### DB — שינויים
| שינוי | תיאור |
|-------|--------|
| `users` | +4 columns: suspended_at, suspension_reason, scheduled_deletion_at, previous_role_id |
| `worklogs` | +8 columns: is_overnight, overnight_*, net_hours, paid_hours, pdf_path, pdf_generated_at |
| `worklog_segments` | טבלה חדשה — פירוט שעות per segment |
| `equipment_types` | +2 columns: hourly_rate, overnight_rate |
| `equipment_rate_history` | טבלה חדשה — היסטוריית שינויי תעריף |
| `locations` | +4 columns: polygon, geojson, center_lat, center_lng |
| `forest_map` (ForestInfo schema) | +2 fields: center_lat, center_lng — centroid פוליגון |
| `audit_logs` | טבלה חדשה — audit trail |
| `sync_queue` | טבלה חדשה — offline sync audit |
| `budget_transfers` | +1 column: rejected_reason |
| `departments` | נוקו — נשארו 3 בלבד (הנהלה/חשבונות/מנהלי עבודה) |
| `notifications` | נוקו — כל הישנות לפני 2026-03-01 נמחקו |
| `roles` | נמחקו 6 test roles "Delete Test Role" |
| `users.status` | נורמל ל-lowercase: 'active' בלבד |

### Bug Fixes — תיקוני באגים
| באג | תיקון |
|-----|--------|
| `GET /projects/code/{code}` → 500 | תהליך uvicorn ישן נשאר על port 8000 — `fuser -k 8000/tcp && systemctl restart` |
| `ImportError: ProjectAssignment` | הוספה ל-`app/models/__init__.py` + `__all__` |
| `ImportError: get_rate_service` | מימוש `RateService` class + factory function ב-`rate_service.py` |
| `ResponseValidationError: activity_type` | שינוי ל-`Optional[str] = None` ב-`activity_log.py` |
| Pricing reports — 404 | תוקן ImportError שגרם לrouter לא לטעון |

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
