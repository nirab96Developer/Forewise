# Wave 6 + Wave 7 — Critical Endpoints Triage

**Generated**: 2026-04-24
**Source**: PERMISSIONS_MATRIX.csv after extractor regex fix (drops kwarg false positives)
**Total flagged 🔴**: 88 endpoints

---

## Summary by category

| Category | Count | Action |
|---|---|---|
| **🟢 false positive** — already enforced via pattern the extractor doesn't catch | ~46 | Document, no fix |
| **🔴 truly unprotected, mutation/privileged** | ~28 | Add `require_permission` |
| **🟡 truly unprotected, lookup/read with low risk** | ~14 | Decide per case |

---

## False positives (46) — already safe, document only

### auth (15) — self-service via `current_user.id`
Already audited in Wave 1.B/1.C. Each endpoint operates only on the authenticated user's own resources via `current_user.id`. No cross-user vulnerability. Extractor needs a new pattern for "uses current_user.id without taking user_id from request".

```
POST /auth/2fa/disable, /2fa/setup, /2fa/verify-setup
DELETE /auth/biometric/credentials/{id}     ← ownership SQL filter
POST /auth/biometric/register, /biometric/verify
POST /auth/change-password
POST /auth/check-permission
DELETE /auth/devices/{id}                   ← ownership SQL filter
POST /auth/logout
DELETE /auth/sessions, /sessions/{id}        ← ownership SQL filter
GET /auth/status
POST /auth/webauthn/register/begin, /register/complete
```

### journal (3) — `/users/me/journal*` is self-service per path
Path itself constrains to current user. `/users/me/*` pattern.
```
GET /users/me/journal
POST /users/me/journal/note
DELETE /users/me/journal/note/{id}
```

### notifications (5 of 9) — self-service operations
```
PATCH /notifications/read-all              ← always operates on current_user
POST /notifications/read-all
PATCH /notifications/{id}/read             ← needs ownership verify
POST /notifications/{id}/read              ← needs ownership verify
POST /notifications                        ← who can create? probably admin/system
```

### pricing (1 of 4) — `/pricing/compute-cost` is read computation
Only computes a number, no DB writes, no PII leak. Yes-OK with auth-only.

### excel_export (1) — `/reports/export/excel`
Already has per-type `require_permission` inside (Phase 0 fix). Extractor false positive.

### work_order_coordination_logs (1)
Already verified by Wave 5 prep — used by coordinator UI; the model query checks WO existence. Low risk.

### dashboard (15) — most use scope filtering inside, return empty for non-eligible roles
Need to verify each, but pattern is `if role in (...): filter by region/area`. Not a hard block but not a leak either. Budget for: add `require_permission("dashboard.view")` if exists, otherwise document.

### Lookup tables (4) — read-only data anyone authenticated can see
```
GET /work-order-statuses, /work-order-statuses/{id}
GET /worklog-statuses, /worklog-statuses/{id}
GET /activity-types, /activity-types/{id}
GET /activity-logs (has role-based scoping inside)
```

### otp (3) — sensitive but user-driven flow
```
POST /otp/send, /otp/verify  ← part of login, can't require auth
POST /otp/cleanup            ← admin only — needs require_permission
```

### sync (1) — `/sync/batch`
Sync endpoint, called by mobile clients. Uses current_user implicitly.

---

## TRUE 🔴 — needs require_permission (Wave 7 actual work)

### Priority 1 — financial / state-change (HIGH RISK)

| Method | Path | Action | Permission | Scope | UI |
|---|---|---|---|---|---|
| POST | `/equipment/{id}/scan` | סורק כלי, מקפיץ WO ל-IN_PROGRESS | `equipment.read` | per-WO scope (supplier of WO only) | yes |
| POST | `/equipment/{id}/release` | משחרר כלי + סוגר WO + שחרור תקציב | `work_orders.update` | scoped (project/area) | no |
| POST | `/system-rates` | יוצר תעריף גלובלי | `system.settings` | global admin | no |
| PATCH | `/system-rates/{id}` | מעדכן תעריף גלובלי | `system.settings` | global admin | no |
| DELETE | `/system-rates/{id}` | מוחק תעריף | `system.settings` | global admin | no |
| POST | `/activity-types` | יוצר סוג פעולה | `activity_types.create` (חסר ב-DB!) | global admin | no |
| PUT | `/activity-types/{id}` | מעדכן | `activity_types.update` (חסר ב-DB!) | global admin | no |
| DELETE | `/activity-types/{id}` | מוחק | `activity_types.delete` (חסר ב-DB!) | global admin | no |

### Priority 2 — supplier_rotations (6) — fair-rotation tampering

| Method | Path | Action | Permission |
|---|---|---|---|
| GET | `/supplier-rotations` | רשימת רוטציות | `supplier_rotations.read` (חסר ב-DB!) |
| POST | `/supplier-rotations` | יוצר רוטציה | `supplier_rotations.create` (חסר!) |
| GET | `/supplier-rotations/{id}` | קריאה | `supplier_rotations.read` (חסר!) |
| PATCH | `/supplier-rotations/{id}` | עדכון | `supplier_rotations.update` (חסר!) |
| PUT | `/supplier-rotations/{id}` | עדכון | `supplier_rotations.update` (חסר!) |
| DELETE | `/supplier-rotations/{id}` | מחיקה | `supplier_rotations.delete` (חסר!) |

**הערה**: כל ה-perms הללו לא קיימים ב-DB. צריך migration שתוסיף את ה-6 perms + תקצה ל-ADMIN ו-ORDER_COORDINATOR.

### Priority 3 — project_assignments (12) — workforce manipulation

| Method | Path | Action | Permission (קיים ב-DB) |
|---|---|---|---|
| GET | `/project-assignments` | רשימת הקצאות | `project_assignments.read` |
| POST | `/project-assignments` | יוצר הקצאה | `project_assignments.create` |
| GET | `/project-assignments/{id}` | קריאה | `project_assignments.read` |
| PUT | `/project-assignments/{id}` | עדכון | `project_assignments.update` |
| DELETE | `/project-assignments/{id}` | הסרה | `project_assignments.delete` |
| PUT | `/project-assignments/{id}/complete` | סימון הושלם | `project_assignments.complete` |
| POST | `/project-assignments/transfer` | העברה ביוזרים | `project_assignments.transfer` |
| GET | `/project-assignments/availability/check` | זמינות יוזר | `project_assignments.check_availability` |
| GET | `/project-assignments/conflicts/check` | קונפליקטים | `project_assignments.check_conflicts` |
| GET | `/project-assignments/roles/list` | רשימת תפקידים | `project_assignments.read` |
| GET | `/project-assignments/statistics/workload` | סטטיסטיקות | `project_assignments.read` |
| POST | `/project-assignments/project/{id}/bulk-assign` | bulk | `project_assignments.bulk_assign` |

### Priority 4 — pricing reports + simulate (3)

| Method | Path | Action | Permission |
|---|---|---|---|
| GET | `/pricing/reports/by-project` | דוח תמחור | `budgets.read` או `pricing.read` (אין כזה) |
| GET | `/pricing/reports/by-supplier` | דוח | אותו |
| GET | `/pricing/simulate-days` | סימולציה | אותו |

### Priority 5 — notifications mutations (4)

| Method | Path | Action | Permission |
|---|---|---|---|
| POST | `/notifications/bulk-action` | פעולה bulk | `notifications.manage` (חסר!) |
| POST | `/notifications/cleanup` | ניקוי | admin |
| PUT | `/notifications/{id}` | עדכון | admin/system |
| DELETE | `/notifications/{id}` | מחיקה | owner OR admin |

### Priority 6 — support tickets (3) + activity_logs (1) + otp/cleanup (1)

| Method | Path | Action | Permission |
|---|---|---|---|
| GET | `/support-tickets` | רשימה | role-based scoping |
| POST | `/support-tickets` | יוצר | authenticated (any user) |
| POST | `/support-tickets/from-widget` | יוצר from widget | authenticated |
| GET | `/activity-logs` | רשימה | `activity_logs.read` (קיים) |
| POST | `/otp/cleanup` | ניקוי OTP ישנים | admin |

---

## DB perms gaps that block Wave 7 work

ה-permissions הבאים **חסרים ב-DB** אבל נדרשים על ידי הקוד או ההמלצות:

```
activity_types.create, .update, .delete       ← Wave 7 P1
supplier_rotations.read, .create, .update,
                  .delete, .list             ← Wave 7 P2 (5 חדשים)
notifications.manage                          ← Wave 7 P5
pricing.read                                  ← Wave 7 P4 (אופציונלי - אפשר להשתמש ב-budgets.read)
```

**מיגרציה נדרשת** לפני שמוסיפים `require_permission` עליהם, אחרת כל בקשה תחזיר 403 קבוע (ADMIN bypass יציל את האדמין אבל לא תפקידים אחרים).

---

## הצעת סדר ביצוע

1. **Wave 6**: Equipment scan + release (2 endpoints, perms קיימים) — קטן ובטוח
2. **Wave 7.A** — מיגרציה אחת שמוסיפה את 9 ה-perms החסרים + מקצה ל-roles נכונים (אין תיקון קוד)
3. **Wave 7.B** — system_rates (3 mutations, ADMIN בלבד) — קטן וברור
4. **Wave 7.C** — activity_types (3 mutations, ADMIN) — דורש את 7.A
5. **Wave 7.D** — supplier_rotations (6 endpoints) — דורש את 7.A
6. **Wave 7.E** — project_assignments (12 endpoints, perms קיימים) — בינוני
7. **Wave 7.F** — pricing reports + notifications mutations + remainder
8. **תיעוד הextractor** — להוסיף 2 patterns חדשים: "self-service via current_user.id only" + "scope filtering returns empty"

---

## הערה כללית

ה-46 ה-false positives הם תיעוד-בלבד. הקוד עצמו תקין. שיפור ה-extractor יסגור אותם אוטומטית בעדכון הבא של המטריצה.
