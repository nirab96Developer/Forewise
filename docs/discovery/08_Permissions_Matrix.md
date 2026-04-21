# נושא 8 — Permissions & Roles Matrix (מטריצת הרשאות)

> **שלב:** Discovery בלבד · אין שינויי קוד.

---

## 0. אזהרות מקדימות

1. **אין seeds בקוד** — חלוקת `role_permissions` חיה רק ב-DB ייצור.
2. **Frontend ↔ Backend mismatch:** Frontend משתמש ב-UPPERCASE (`WORK_ORDERS.VIEW`); Backend ב-lowercase (`work_orders.read`). אם DB מכיל אחד הסגנונות — הצד השני נשבר עבור non-admins.
3. **`RoleCode` enum חסר** קודים שמשמשים בקוד: `ORDER_COORDINATOR`, `FIELD_WORKER`, `SUPER_ADMIN`, `SUPPLIER_MANAGER`.

---

## 1. רשימת תפקידים

### ב-RoleCode enum (`models/role.py`)

| Code | שם עברי (frontend) |
|---|---|
| `ADMIN` | מנהל מערכת |
| `REGION_MANAGER` | מנהל מרחב |
| `AREA_MANAGER` | מנהל אזור |
| `WORK_MANAGER` | מנהל עבודה |
| `ACCOUNTANT` | מנהלת חשבונות |
| `SUPPLIER` | ספק |
| `VIEWER` | (מוצג כמנהל מרחב) |

### בשימוש בקוד אך לא ב-enum

| Code | היכן בקוד |
|---|---|
| `ORDER_COORDINATOR` | `projects.py`, `work_orders.py`, `scope.py` |
| `FIELD_WORKER` | `worklogs.py`, `excel_export.py` |
| `SUPER_ADMIN` | `work_orders.py`, scan endpoints |
| `SUPPLIER_MANAGER` | `permissions.ts` |

---

## 2. רשימת ההרשאות לפי דומיין

**~140 קודים מוצאים ב-routers** (לא 169 — ההפרש כנראה ב-DB בלבד).

### ליבה

| דומיין | פעולות עיקריות |
|---|---|
| `work_orders` | read, create, update, delete, restore, approve, cancel, close, distribute |
| `worklogs` | read, create, update, delete, restore, approve, submit |
| `invoices` | read, create, update, delete, restore, approve |
| `projects` | read, create, update, delete, restore |
| `budgets` | read, create, update, delete, restore, view, edit |
| `equipment` | read, create, update, delete, restore, assign, view, manage |
| `suppliers` | list, read, create, update, delete |

### ניהול

| דומיין | פעולות |
|---|---|
| `users` | list, read, create, update, delete, manage, lock, unlock, edit |
| `roles` | list, read, create, update, delete, manage_permissions |
| `permissions` | list, read, create, update, delete |
| `role_assignments` | list, create, delete |
| `system` | settings |
| `settings` | manage |

### Master data

`regions`, `areas`, `locations`, `departments`, `equipment_categories`, `equipment_types`, `supplier_constraint_reasons`, `budget_items`, `invoice_items`, `invoice_payments`, `project_assignments`, `report_runs`, `reports` — לכל אחד CRUD מלא.

---

## 3. אכיפה בקוד

### Backend
- `require_permission(current_user, "code")` — תבנית עיקרית
- ADMIN bypass: כל `role.code == 'ADMIN'` עובר
- `system.admin` bypass: גם הרשאת super
- Cache פר process

### Frontend
- `hasPermission(perm)` — exact string match
- `ROUTE_PERMISSIONS` — לפי URL prefix
- `getMenuItemsForRole(role)` — רשימה סטטית פר role + סינון לפי הרשאות

---

## 4. Data Scoping (נפרד מהרשאות)

### בעת רשימת פרויקטים (`GET /projects`)

| תפקיד | מה רואה |
|---|---|
| `ADMIN` | הכל |
| `ORDER_COORDINATOR` | מסנן ל-`region_id` |
| `REGION_MANAGER` | מסנן ל-`region_id` |
| `AREA_MANAGER` | מסנן ל-`area_id` (fallback region) |
| `ACCOUNTANT` | area אם יש, אחרת region |
| `WORK_MANAGER` | רק פרויקטים משוייכים (`project_assignments`) |
| `VIEWER` / `SUPPLIER` / `FIELD_WORKER` | **אין סינון מפורש!** |

### בעת כתיבה (`scope.py`)

| תפקיד | חוק |
|---|---|
| `REGION_MANAGER` | פרויקט באותו region |
| `AREA_MANAGER` / `ACCOUNTANT` / `WORK_MANAGER` | פרויקט באותו area |
| `ORDER_COORDINATOR` | פרויקט באותו region |

**`check_project_access` באג:** למקרים שלא תואמים — מחזיר user **בלי לזרוק חריגה**! קוראים חייבים לבדוק ידנית.

### בעת רשימת WO (`work_orders.py`)
- אם למשתמש `area_id` → `search.area_id` נכפה (לכל אחד עם area, לא רק area_manager)

### בעת רשימת חשבוניות
- ה-router מגדיר `search.area_id` אבל ה-service **מתעלם** — Scoping לא נאכף בפועל!

---

## 5. מטריצת תפריטים בפרונט (`menuConfig.ts`)

| תפקיד | פריטי תפריט |
|---|---|
| `ADMIN` | dashboard, projects, workOrders, orderCoordination, reports, map, support, settings |
| `REGION_MANAGER` | dashboard, projectsRegion, budgets, reports, map |
| `AREA_MANAGER` | dashboard, projectsArea, budgets, reports, map |
| `WORK_MANAGER` | dashboard, projects |
| `ORDER_COORDINATOR` | dashboard, projectsArea, orderCoordination, budgets, reports, map |
| `ACCOUNTANT` | dashboard, accountantInbox, invoices, reports |
| `SUPPLIER_MANAGER` | dashboard, projects, workOrders, accountantInbox, invoices, reports, map, support, settings |
| `FIELD_WORKER` | dashboard, projects |
| `SUPPLIER` | (ריק) |
| `VIEWER` | dashboard, projectsRegion, budgets, reports, map |

---

## 6. בעיות פתוחות שגיליתי

1. **Frontend/Backend permission mismatch** — סגנון שונה לחלוטין (UPPER vs lower)
2. **`RoleCode` חסר 4 ערכים** הנמצאים בשימוש בקוד
3. **`check_project_access` לא זורק חריגה** במקרים לא תואמים
4. **Invoice scoping לא נאכף** למרות שה-router מנסה
5. **VIEWER/SUPPLIER ללא סינון פרויקטים** — אין branch ייעודי
6. **Region-only `ACCOUNTANT`** (area_id=None) לא מטופל ב-`scope.py`
7. **אין role-permission seeds** בקוד — לא ניתן לשחזר production
8. **VIEWER מוצג בעברית כ"מנהל מרחב"** — UX מבלבל
9. **`USER` role בפרונט** — לא ב-Backend enum
