# Permissions Matrix — Forewise

**תאריך**: 2026-04-23
**מקור**: 418 routes ב-FastAPI + 169 permissions ב-DB + 409 role-perm mappings + 185 matched FE↔BE.
**הערה**: דו"ח בלבד. אין שינויי קוד.

---

## 1. סיכום מנהלים

| מטריקה | מספר |
|---|---|
| סך הכל endpoints | 418 |
| 🔴 קריטיים — אין enforcement (mutation/sensitive) | 84 |
| 🟡 בינוניים — auth-only על read endpoints | 33 |
| 🟢 תקינים — יש require_permission או public legitimate | 301 |
| Permissions ב-DB | 178 |
| Permissions שמוזכרים בקוד | 130 |
| Permissions בקוד שאין ב-DB (בעיה) | 52 |
| Permissions ב-DB שלא משמשים בקוד (יתומים) | 100 |
| Permissions עם duplicate case (UPPER + lower) | 15 |

---

## 2. תפקידים והיקף ההרשאות בהם

| תפקיד | מספר הרשאות | scope לוגי שצריך להיות |
|---|---|---|
| `ADMIN` (מנהל מערכת) | 178 | גלובלי |
| `REGION_MANAGER` (מנהל מרחב) | 70 | מרחב |
| `AREA_MANAGER` (מנהל אזור) | 63 | אזור |
| `ORDER_COORDINATOR` (מתאם הזמנות) | 38 | תיאום הזמנות (region/area) |
| `WORK_MANAGER` (מנהל עבודה) | 42 | פרויקטים שלו |
| `ACCOUNTANT` (מנהלת חשבונות) | 20 | אזור/מרחב לפי שיוך |
| `SUPPLIER` (ספק) | 15 | טוקן ספק (חיצוני) |

---

## 3. בעיות ב-Permission Set הקיים

### 3.1 Permissions בקוד שלא קיימים ב-DB

הקוד קורא ל-`require_permission` עם code שלא קיים ב-DB. התוצאה: כל בקשה מחזירה 403 Forbidden גם אם המשתמש לכאורה צריך גישה.

- `budget_items.delete`
- `budget_items.restore`
- `budgets.edit`
- `budgets.restore`
- `budgets.view`
- `equipment.assign`
- `equipment.create`
- `equipment.manage`
- `equipment.update`
- `equipment.view`
- `equipment_categories.create`
- `equipment_categories.delete`
- `equipment_categories.restore`
- `equipment_categories.update`
- `equipment_types.create`
- `equipment_types.delete`
- `equipment_types.restore`
- `equipment_types.update`
- `invoice_payments.delete`
- `invoice_payments.restore`
- `invoice_payments.update`
- `invoices.restore`
- `permissions.create`
- `permissions.delete`
- `permissions.list`
- `permissions.update`
- `projects.delete`
- `region_manager`
- `report_runs.create`
- `report_runs.update`
- `reports.restore`
- `role_assignments.create`
- `role_assignments.delete`
- `role_assignments.list`
- `roles.list`
- `roles.manage_permissions`
- `settings.manage`
- `supplier_constraint_reasons.create`
- `supplier_constraint_reasons.delete`
- `supplier_constraint_reasons.restore`
- `supplier_constraint_reasons.update`
- `system.settings`
- `work_orders.cancel`
- `work_orders.close`
- `work_orders.create`
- `work_orders.delete`
- `work_orders.restore`
- `work_orders.update`
- `worklogs.approve`
- `worklogs.create`
- `worklogs.restore`
- `worklogs.update`

### 3.2 Permissions ב-DB שלא משמשים בקוד

סה"כ 100 permissions יתומים ב-DB. ייתכן שיש להם שימושים שאני לא תפסתי, או שהם dead. להלן קטגוריזציה לפי convention:

- **UPPERCASE legacy** (50): נראים legacy, יש להם duplicates lowercase ב-DB.

  ```
  AREAS.MANAGE
  AREAS.VIEW
  BUDGETS.APPROVE
  BUDGETS.CREATE
  BUDGETS.UPDATE
  BUDGETS.VIEW
  DASHBOARD.VIEW
  EQUIPMENT.CREATE
  EQUIPMENT.REQUEST
  EQUIPMENT.SCAN
  EQUIPMENT.UPDATE
  EQUIPMENT.VIEW
  INVOICES.APPROVE
  INVOICES.CREATE
  INVOICES.UPDATE
  INVOICES.VIEW
  PROJECTS.CREATE
  PROJECTS.DELETE
  PROJECTS.UPDATE
  PROJECTS.VIEW
  ... (30 נוספים)
  ```

- **lowercase יתומים** (50): permissions לישויות שאין להן endpoint, או לפעולות שלא נאכפות.

  ```
  activity_logs.read
  balance_releases.approve
  balance_releases.create
  balance_releases.read
  budget_allocations.approve
  budget_allocations.create
  budget_allocations.read
  budget_transfers.approve
  budget_transfers.create
  budget_transfers.read
  budgets.list
  equipment_categories.manage
  equipment_maintenance.create
  equipment_maintenance.read
  equipment_maintenance.update
  equipment_scans.create
  equipment_scans.read
  invoice_payments.approve
  invoice_payments.read_own
  invoices.list
  invoices.read_own
  lookups.manage
  notifications.manage
  permissions.manage
  project_assignments.create
  project_assignments.delete
  project_assignments.read
  projects.list
  reports.run
  settings.read
  ... (20 נוספים)
  ```

### 3.3 Duplicate case (UPPER vs lower)

סה"כ 15 זוגות. הקוד משתמש בlowercase, אבל ה-DB מחזיק את שני הוריאנטים.
דוגמה: `BUDGETS.VIEW` ו-`budgets.view` — שניהם מוקצים לתפקידים, חלקם רק UPPER, חלקם רק lower.

```
  BUDGETS.CREATE / budgets.create
  budgets.update / BUDGETS.UPDATE
  invoices.approve / INVOICES.APPROVE
  invoices.create / INVOICES.CREATE
  INVOICES.UPDATE / invoices.update
  PROJECTS.CREATE / projects.create
  PROJECTS.UPDATE / projects.update
  ROLES.CREATE / roles.create
  ROLES.UPDATE / roles.update
  suppliers.create / SUPPLIERS.CREATE
  suppliers.delete / SUPPLIERS.DELETE
  SUPPLIERS.UPDATE / suppliers.update
  USERS.CREATE / users.create
  USERS.DELETE / users.delete
  users.update / USERS.UPDATE
```

---

## 4. Endpoints קריטיים בלי enforcement (🔴)

סה"כ 84 endpoints מבצעים פעולות רגישות ללא בדיקת הרשאה. כל משתמש מאומת (כולל ספק עם session גנוב) יכול לקרוא להם בהצלחה.

### לפי domain (top 15)

| Domain | מספר 🔴 |
|---|---|
| `dashboard` | 18 |
| `auth` | 15 |
| `project_assignments` | 12 |
| `notifications` | 9 |
| `supplier_rotations` | 6 |
| `pricing` | 4 |
| `otp` | 3 |
| `support_tickets` | 3 |
| `journal` | 3 |
| `activity_types` | 2 |
| `work_order_statuses` | 2 |
| `worklog_statuses` | 2 |
| `activity_logs` | 1 |
| `excel_export` | 1 |
| `suppliers` | 1 |

### דוגמאות בולטות (top 30 by sensitivity)

| Method | Path | Action | Recommended permission | UI? |
|---|---|---|---|---|
| `GET` | `/api/v1/activity-logs` | list | `activity_logs.list` | yes |
| `GET` | `/api/v1/activity-types` | list | `activity_types.list` | yes |
| `GET` | `/api/v1/activity-types/{activity_type_id}` | read | `activity_types.read` | yes |
| `POST` | `/api/v1/auth/2fa/disable` | create | `auth.create` | no |
| `POST` | `/api/v1/auth/2fa/setup` | create | `auth.create` | no |
| `POST` | `/api/v1/auth/2fa/verify-setup` | create | `auth.create` | no |
| `DELETE` | `/api/v1/auth/biometric/credentials/{credential_id}` | delete | `auth.delete` | no |
| `POST` | `/api/v1/auth/biometric/register` | create | `auth.create` | no |
| `POST` | `/api/v1/auth/biometric/verify` | create | `auth.create` | no |
| `POST` | `/api/v1/auth/change-password` | create | `auth.create` | no |
| `POST` | `/api/v1/auth/check-permission` | create | `auth.create` | no |
| `DELETE` | `/api/v1/auth/devices/{device_id}` | delete | `auth.delete` | no |
| `POST` | `/api/v1/auth/logout` | create | `auth.create` | no |
| `DELETE` | `/api/v1/auth/sessions` | delete | `auth.delete` | no |
| `DELETE` | `/api/v1/auth/sessions/{session_id}` | delete | `auth.delete` | no |
| `GET` | `/api/v1/auth/status` | list | `auth.list` | no |
| `POST` | `/api/v1/auth/webauthn/register/begin` | create | `auth.create` | no |
| `POST` | `/api/v1/auth/webauthn/register/complete` | complete | `auth.complete` | no |
| `GET` | `/api/v1/dashboard/accountant-overview` | list | `dashboard.list` | yes |
| `GET` | `/api/v1/dashboard/activity` | list | `dashboard.list` | yes |
| `GET` | `/api/v1/dashboard/alerts` | list | `dashboard.list` | yes |
| `GET` | `/api/v1/dashboard/area-overview` | list | `dashboard.list` | yes |
| `GET` | `/api/v1/dashboard/coordinator-queue` | list | `dashboard.list` | yes |
| `GET` | `/api/v1/dashboard/financial-summary` | list | `dashboard.list` | no |
| `GET` | `/api/v1/dashboard/hours` | list | `dashboard.list` | yes |
| `GET` | `/api/v1/dashboard/live-counts` | list | `dashboard.list` | yes |
| `GET` | `/api/v1/dashboard/map` | list | `dashboard.list` | yes |
| `GET` | `/api/v1/dashboard/monthly-costs` | list | `dashboard.list` | no |
| `GET` | `/api/v1/dashboard/my-tasks` | list | `dashboard.list` | yes |
| `GET` | `/api/v1/dashboard/projects` | list | `dashboard.list` | yes |

_ועוד 54 ב-CSV._

---

## 5. Endpoints בינוניים (🟡)

סה"כ 33 — בעיקר read/list בלי `require_permission`. פחות חמור מ-🔴 (אין side effect) אבל עדיין דליפת מידע אם משתמש לא מורשה ניגש.

דוגמאות (10 ראשונות):

| Method | Path | Recommended permission |
|---|---|---|
| `GET` | `/api/v1/activity-logs/{log_id}` | `activity_logs.read` |
| `GET` | `/api/v1/admin/projects/by-area/{area_id}` | `projects.read` |
| `GET` | `/api/v1/auth/biometric/credentials` | `auth.list` |
| `GET` | `/api/v1/auth/devices` | `auth.list` |
| `GET` | `/api/v1/auth/sessions` | `auth.list` |
| `GET` | `/api/v1/dashboard/equipment/active` | `dashboard.list` |
| `GET` | `/api/v1/dashboard/stats` | `dashboard.list` |
| `GET` | `/api/v1/dashboard/suppliers/active` | `dashboard.list` |
| `GET` | `/api/v1/dashboard/work-manager-overview` | `dashboard.list` |
| `GET` | `/api/v1/equipment-models` | `equipment_models.list` |

---

## 6. Endpoints בלי UI

סה"כ 201 endpoints שלא קיים להם UI. לפי domain:

| Domain | בלי UI |
|---|---|
| `admin` | 15 |
| `work_orders` | 11 |
| `geo` | 9 |
| `departments` | 8 |
| `reports` | 8 |
| `notifications` | 7 |
| `project_assignments` | 7 |
| `budget_items` | 7 |
| `equipment_categories` | 7 |
| `equipment_types` | 6 |
| `invoice_payments` | 6 |
| `invoices` | 6 |
| `dashboard` | 5 |
| `pricing` | 5 |
| `system_rates` | 5 |
| `areas` | 5 |
| `budgets` | 5 |
| `report_runs` | 5 |
| `worklogs` | 5 |
| `suppliers` | 4 |

ראה CSV לרשימה מלאה (סינון: `ui_exposed=no`).

---

## 7. פיצ'רים שלמים בלי UI (קבוצות שמומלצות להחלטה)

| קבוצה | endpoints | מצב | המלצה |
|---|---|---|---|
| 2FA (`/auth/2fa/*`) | 4 | אין UI | להחליט: לחבר או למחוק |
| Biometric (`/auth/biometric/*`) | 6 | יש `biometricService.ts` בfrontend אבל לא רוץ | להחליט: לחבר או למחוק |
| WebAuthn (`/auth/webauthn/*`) | 4 | אין UI | להחליט: לחבר או למחוק |
| Sessions/Devices (`/auth/sessions`, `/auth/devices`) | 4 | אין UI | אדמין UI? |
| Admin security (`/auth/admin/*`) | 4 | אין UI | אדמין UI? |
| Notifications מתקדם (`/notifications/bulk-action` וכו') | 4 | אין UI | להחליט |
| Restore endpoints (`/{entity}/{id}/restore`) | 12 | אין UI | אדמין UI? |
| Lock/Unlock users | 3 | אין UI | אדמין UI? |
| PDF downloads (work-orders, invoices, worklogs) | 4 | יש pdf-preview, לא ברור אם UI מתחבר | לאמת בלייב |

---

## 8. המלצות לפי סדר חומרה

### 🔴 דחוף — אכיפת הרשאות בendpoints קריטיים

להוסיף `require_permission` ל-84 endpoints. הכי קריטי לפי החתכים האלה:

- **`dashboard`** (18 endpoints) — כל ה-`/dashboard/*` חשוף — דליפת KPIs, תקציבים, work orders. read endpoints, אבל ה-payload מכיל data רגיש לפי תפקיד.
- **`auth`** (15 endpoints) — endpoints של 2FA/biometric/WebAuthn — אין UI, אבל אם API נחשף משתמש מאומת יכול register passkey לחשבון אחר. דורש חידוד.
- **`project_assignments`** (12 endpoints) — כל ה-CRUD בלי בדיקה. user יכול לשנות הקצאת פרויקטים של אחרים.
- **`notifications`** (9 endpoints) — bulk-action, cleanup, read-all — user יכול לסמן הודעות של אחרים כנקראו.
- **`supplier_rotations`** (6 endpoints) — מנגנון הסבב ההוגן. mutation שלו = שיבוש החלוקה לספקים.
- **`pricing`** (4 endpoints) — endpoints מציגים תעריפים — דליפה ל-supplier אם הוא מאומת.
- **`otp`** (3 endpoints) — להחליט פר-endpoint לפי לוגיקה עסקית.
- **`support_tickets`** (3 endpoints) — create/update/list — user יכול לערוך טיקטים של אחרים.
- **`journal`** (3 endpoints) — להחליט פר-endpoint לפי לוגיקה עסקית.
- **`activity_types`** (2 endpoints) — lookup table. mutation = החלפת activity codes שמתעדים worklogs.

### 🔴 דחוף — לתקן permissions שלא קיימים ב-DB

52 permissions בקוד שלא יוגדרו לעולם → 403 קבוע.

### 🟡 חוב טכני — duplicate UPPER/lower

15 זוגות duplicates. נדרש איחוד ל-convention יחיד (lowercase) ועדכון role_permissions assignments.

### 🟡 חוב טכני — permissions יתומים

100 permissions ב-DB שאין להם שימוש. ניתן למחוק אחרי איחוד case.

### 🟡 בינוני — להגדיר scope

הקוד הנוכחי לא אוכף scope (region/area/project) ב-DB level. ה-`test_scope_enforcement.py` מאמת חלק (174/174 עוברים) אבל לא בכל endpoint. צריך להגדיר policy אחיד.

### 🟢 לאחר אכיפה — UI alignment

אחרי שה-backend אוכף, frontend צריך לבדוק `user.role.permissions` לפני הצגת כפתורים. זה כבר חלקי — Login.tsx טוען את הרשימה — רק להוסיף בדיקה לכל כפתור פעולה.

---

## 9. Audited domains (false positives שאומתו ידנית)

Domains שנסקרו endpoint-by-endpoint ידנית ומצאתי שהם **כבר מוגנים במלואם**, גם אם ה-extractor הראשון פספס. ה-extractor שודרג מאז כך שיתפוס את הפטרנים האלה אוטומטית.

### `work_orders` (25 endpoints) — נסקר ב-Phase 2 Wave 2

- 19 endpoints עם `require_permission(...)` ישיר (read/list/create/update/delete/restore/approve×2/cancel/close/start/distribute/etc.)
- 4 endpoints PATCH wrappers שמפנים לפונקציות מוגנות (frontend back-compat aliases)
- 2 endpoints עם inline admin check (scan-equipment + admin-override-equipment)
- **0 endpoints חשופים**. Wave 2 נסגר ללא שינוי קוד.

### `worklogs` (17 endpoints) — נסקר ב-Phase 2 Wave 3

- 14 endpoints עם `require_permission(...)` ישיר
- 1 endpoint self-service (`/my-worklogs`) שמסנן `search.user_id = current_user.id` לפני query
- 2 endpoints lookup (`/activity-codes`, `/by-work-order/{id}`) — readonly, אומתו ידנית
- **0 endpoints חשופים**. Wave 3 נסגר ללא שינוי קוד.

**הפטרנים שה-extractor לא תפס לפני השדרוג**:

1. *Wrappers* — `def patch_X(...): return X(...)` — נדרש call-graph עם hops.
2. *Indirect admin* — `is_admin = ... role.code in (...); if not is_admin: raise 403`.
3. *Helper calls* — `_require_order_coordinator_or_admin(current_user)`.
4. *Self-service scope filter* — `search.user_id = current_user.id` לפני query.

כל הארבעה כעת מוכרים אוטומטית. ראה `app_backend/scripts/audit/README.md` להרחבה.

---

## 10. CSV מצורף

`PERMISSIONS_MATRIX.csv` מכיל את כל ה-418 הendpoints עם כל העמודות (severity, current_perms, recommended_perm, ui_exposed, וכו'). פתח באקסל לסינון.

עמודות:
- `method, path, domain, action, summary, func, file`
- `auth_status` — anonymous / authenticated / permission
- `current_perms` — מה require_permission קורא היום
- `ui_exposed` — yes/no
- `recommended_perm` — המלצה ליישור עם DB convention (lowercase entity.action)
- `recommended_scope` — global / region / area / project / supplier_token / scoped
- `severity` — 🔴/🟡/🟢
- `is_mutation` — yes/no
- `sensitive_kw` — מילות מפתח רגישות בקוד
- `roles_with_current_perm` — אילו roles יש להם את הרשאה הנוכחית
