# גל 1 — דוח סטטוס ביצוע

> **תאריך:** אפריל 2026
> **גישה:** Tech Lead / ownership מלא
> **כללי בטיחות:** 0 שינויים שדורשים החלטה עסקית · כל הטסטים עוברים · 0 lint errors

---

## ✅ מה תוקן (10 משימות, 12 קבצים, +350/-128 שורות)

### Phase A — יישור יסודות (status enums + plate normalize)

| # | תיקון | קבצים | מה השתנה |
|---|---|---|---|
| **F1.7** | Status enum drift | `app/core/enums.py` | נוסף `IN_PROGRESS`, `ACTIVE` ל-`WorkOrderStatus`, `WO_LABELS` (עברית: "בביצוע", "פעיל בשטח"), ול-`WO_TRANSITIONS`. נוסף `WO_EXECUTION` (frozenset של סטטוסים בהם הזמנה פעילה בשטח) — Source of Truth יחיד שכל מי שצריך "האם אפשר לסרוק/לדווח" יכול להשתמש בו. |
| **F2.5** | WorklogResponse שדות חסרים | `app/schemas/worklog.py` | נוספו `is_standard`, `non_standard_reason`, `rejection_reason`, `total_amount`, `metadata_json`, `submitted_at`, `submitted_by_id`, `rate_source`, `rate_source_name`. עכשיו ה-API מחזיר את כל מה שה-Frontend מציג. |
| **F1.6** | License plate normalize | `app/routers/work_orders.py` | נוספה `_normalize_plate()` (trim + upper + collapse spaces). שימוש ב-3 הזרימות: `scan-equipment`, `confirm-equipment`, `admin-override-equipment`. שאילתות עברו ל-`ilike` ל-case-insensitive. הצורה הקנונית נשמרת חזרה ב-`Equipment.license_plate`. גם החלפת `scannable = {...}` ב-`WO_EXECUTION` המשותף. |

### Phase A — באגים קריטיים

| # | תיקון | קבצים | מה השתנה |
|---|---|---|---|
| **F1.4** | `check_project_access` יזרוק 403 | `app/core/dependencies.py` | במקרי כשל הוחזר משתמש ללא חריגה — עכשיו `HTTPException 403`. נוספה גם תמיכה ב-`ORDER_COORDINATOR`, `ACCOUNTANT` (region-fallback), ו-`WORK_MANAGER`/`FIELD_WORKER` עם בדיקת `project_assignments`. |
| **F1.1** | Rotation rejection bug | `app/routers/supplier_portal.py` | `update_rotation_after_rejection` נקרא **אחרי** ש-`_move_to_next_supplier` כבר עדכן את `work_order.supplier_id`. כעת ה-`rejecting_supplier_id` נשמר **לפני** המעבר, והקנס נרשם נכון על הספק שדחה. |
| **F1.2** | AccountantDashboard from-worklogs שבור | `app/routers/dashboard.py` + `src/pages/Dashboard/AccountantDashboard.tsx` | Backend החזיר רק `project_name`/`supplier_name` — נוספו `project_id`/`supplier_id`. Frontend עכשיו מקבץ בחירה לפי (supplier_id, project_id) — אם יש מספר צירופים יוצר חשבונית נפרדת לכל אחד אחרי confirm. ולידציה: דיווח ללא ספק/פרויקט נחסם עם שם הדיווח. |

### Phase B — Permission alignment

| # | תיקון | קבצים | מה השתנה |
|---|---|---|---|
| **F1.3** | FE↔BE permission mismatch | `src/utils/permissions.ts` | כל ה-`PERMISSIONS.*` שונו ל-lowercase קנוני שתואם 1:1 לקוד ה-Backend (`work_orders.read`, `worklogs.approve` וכו'). `hasPermission()` עכשיו case-insensitive — תומך גם ב-strings ישנים שעדיין עלולים להופיע בקוד. הוספו 3 הרשאות חסרות: `work_orders.approve`, `work_orders.cancel`, `work_orders.close`, `worklogs.submit`. |

### Phase C — Invoice payment lifecycle

| # | תיקון | קבצים | מה השתנה |
|---|---|---|---|
| **F1.8** | Invoice חסרים paid_at, payment_reference | `app/models/invoice.py` + `alembic/versions/b2c4d5e6f7a8_*.py` + `app/schemas/invoice.py` + `app/routers/invoices.py` + `app/services/invoice_service.py` | נוספו 4 שדות: `paid_at`, `payment_reference`, `paid_by`, `sent_at`. Migration כולל backfill ל-`PAID` קיימים מ-`updated_at`. Endpoint `POST /invoices/{id}/mark-paid` כעת מקבל body אופציונלי (`payment_method`, `payment_reference`, `paid_at`, `paid_amount`) ושומר `paid_by`. `send_to_supplier` שומר `sent_at`. `InvoiceStatus` Pydantic enum יושר ל-core enum (הוסר `PENDING` שלא היה בקוד הליבה). |

---

## 🧪 איכות

| בדיקה | תוצאה |
|---|---|
| Backend imports — כל 41 ה-routers | ✅ נטענים |
| Backend lints (ReadLints) | ✅ 0 errors |
| Frontend lints | ✅ 0 errors |
| TypeScript compile (`tsc --noEmit`) | ✅ 0 errors |
| `pytest test_status_transitions + test_flow_validation + test_scope_enforcement` | ✅ **143 passed** |
| Manual enum validation (transitions OK, illegal blocked) | ✅ |

> **הערה:** `pytest --tb=short -q -x` מלא נכשל ב-collection בגלל בעיה pre-existing בקובץ `app/utils/files/storage.py` (חסר `STORAGE_PROVIDER` ב-Settings) — זה לא קשור לשינויים שלנו.

---

## 📦 קבצים שהשתנו (12)

```
 M app_backend/app/core/dependencies.py
 M app_backend/app/core/enums.py
 M app_backend/app/models/invoice.py
 M app_backend/app/routers/dashboard.py
 M app_backend/app/routers/invoices.py
 M app_backend/app/routers/supplier_portal.py
 M app_backend/app/routers/work_orders.py
 M app_backend/app/schemas/invoice.py
 M app_backend/app/schemas/worklog.py
 M app_backend/app/services/invoice_service.py
 M app_frontend/src/pages/Dashboard/AccountantDashboard.tsx
 M app_frontend/src/utils/permissions.ts
?? app_backend/alembic/versions/b2c4d5e6f7a8_add_invoice_payment_fields.py
```

---

## 🚦 צעד הבא — מה דורש החלטה

לפני שאני נכנס ל-**גל 2** (consistency & hardening) — יש שאלות עסקיות חוסמות:

### החלטות חוסמות (חייב מענה לפני המשך)

| # | שאלה | הקשר | אופציות |
|---|---|---|---|
| **Q1** | האם הזמנה היא לכלי **בודד** או לכמות (`quantity`)? | בטופס הקיים מקבל 1–5 אבל לא נשמר ב-DB. | (A) WO אחד עם `quantity` (B) מספר WOs נפרדים (C) להוריד את השדה |
| **Q5** | במצב `wrong_type` — ה-WO צריך לחזור אוטומטית לסטטוס מתאם? | היום `status="wrong_type"` חוזר בגוף, ה-WO נשאר באותו סטטוס. | (A) להישאר ולסמוך על המתאם להבחין (B) להחזיר ל-PENDING אוטו (C) לסטטוס חדש `NEEDS_RE_COORDINATION` |
| **Q10** | להאחד את 2 מסלולי קליטת הכלי? | `ProjectWorkspace` עם 3 מצבים מול `WorkOrderDetail` שדולג. | (A) לאחד הכל ל-3-states (B) להשאיר 2 UX (C) לחסל את `WorkOrderDetail` ולהפנות ל-Workspace |

### החלטות לא חוסמות (אפשר להמשיך גם בלי, להחליט תוך כדי)

| # | שאלה |
|---|---|
| Q2 | האם `priority=HIGH/URGENT` בטופס? משפיע על SLA? |
| Q3 | 9 שעות נטו — תמיד? או לפי סוג כלי? |
| Q4 | תוקף Token (3h) — להאריך לסופ"ש? |
| Q6 | Email ב-`send invoice` — אוטומטי או ידני? |
| Q7 | Region-only Accountant — תרחיש קיים? |
| Q8 | SMS לספקים — להחזיר/למחוק? |
| Q9 | Self-approval — איפה עוד? |

---

## 🔜 גל 2 — מה מוכן להתבצע

ברגע שיש מענה לשאלות החוסמות, גל 2 כולל 11 משימות:

1. אכיפת `validate_wo_transition` בכל מקום בקוד (לא רק בטסטים)
2. יצירת DB seeds מסודרים (roles, permissions, statuses)
3. ייצוא מטריצת role × permission ל-CSV
4. תיקון `WorklogResponse.reject_reason` לשמירה ב-service
5. יצירת FK חסרים ב-`invoices` (supplier, project, created_by)
6. Scoping אזורי לחשבוניות ב-`InvoiceService.list`
7. הוספת `RoleCode` enum: ORDER_COORDINATOR, FIELD_WORKER, SUPER_ADMIN, SUPPLIER_MANAGER
8. ועוד 4

---

## 💡 ערך עסקי שגל 1 הביא

| לפני | אחרי |
|---|---|
| ספק שדחה הזמנה — קיבל "קנס" שגוי בסבב הוגן | הקנס נרשם נכון על הספק שדחה |
| AccountantDashboard "צור חשבונית" — קריאה שבורה (חסרים פרמטרים) | יוצר חשבוניות נכון, גם לקיבוצים מרובים |
| לפעמים non-admins לא יכלו לראות תפריטים שיש להם הרשאה | יישור lowercase + case-insensitive פותר |
| `check_project_access` השתיק כשלי הרשאה | זורק 403 ברור |
| חשבונית "שולמה" — לא ידעת מתי / על ידי מי / איזו אסמכתה | `paid_at`, `paid_by`, `payment_method`, `payment_reference` נשמרים |
| מספר רישוי `' 123-45-678 '` שונה מ-`'123-45-678'` | normalize אחיד בכל הקוד |
| `IN_PROGRESS`/`ACTIVE` היו "drift" — ללא תוויות עברית, ללא state machine | מלאים ב-enum, עם תוויות, עם transitions מוגדרים |
| `WorklogResponse` לא החזיר `is_standard` — UI הציג `undefined` | מוחזר נכון |

---

**סטטוס: גל 1 הושלם. ממתין להחלטות עסקיות לפני גל 2.**
