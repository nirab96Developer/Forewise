# נושא 3 — Worklog Template (דיווח שעות)

> **שלב:** Discovery בלבד · אין שינויי קוד.

---

## 1. מודל Worklog — `app_backend/app/models/worklog.py`

### שדות ליבה

| שדה | סוג | חובה? | הערות |
|---|---|---|---|
| `id` | Integer PK | כן | |
| `report_number` | Integer indexed | כן | |
| `report_type` | String(50) | כן | "standard" / "manual" |
| `work_order_id` | FK → work_orders | optional במודל, **חובה ברצונה** | service זורק שגיאה אם חסר |
| `user_id` | FK → users | optional | |
| `project_id` | FK → projects | optional | |
| `equipment_id` | FK → equipment | optional | |
| `activity_type_id` | FK → activity_types | optional | |
| `status` | FK → worklog_statuses.code | optional | מגיע מ-Enum |
| `report_date` | Date | כן | |
| `start_time` / `end_time` | Time | optional | |
| `work_hours` | Numeric | כן | gt=0 ב-schema |
| `break_hours` | Numeric | optional | |
| `total_hours` / `net_hours` / `paid_hours` | Numeric | optional | |
| `is_standard` | Boolean | optional | תקן/לא תקן |
| `non_standard_reason` | String | optional | סיבת חריגה |
| `approved_by_user_id` | Integer (no FK!) | optional | |
| `approved_at` | DateTime | optional | |
| `submitted_at` / `submitted_by_id` | DT/Int | optional | |
| `rejection_reason` | String | optional | |
| `hourly_rate_snapshot` | Numeric | snapshot | |
| `cost_before_vat` / `cost_with_vat` | Numeric | | |
| `vat_rate` | Numeric default 0.18 | כן | |

### אי-עקביות מודל ↔ service

ה-service כותב `metadata_json` ו-`total_amount` ש**לא קיימים במודל** (`worklog_service.py:353-358, 539-545, 986`). או שהשדות בפועל ב-DB ולא במודל, או שזה באג סמוי.

---

## 2. סטטוסים (Worklog)

| Code | תוויות | מצב |
|---|---|---|
| `PENDING` | ממתין | ברירת מחדל ביצירה |
| `SUBMITTED` | הוגש | אחרי `submit()` |
| `APPROVED` | אושר | אחרי `approve()` |
| `REJECTED` | נדחה | אחרי `reject()` |
| `INVOICED` | הופק חשבון | אחרי הכנסה לחשבונית |

**מעברים:** PENDING → SUBMITTED → APPROVED → INVOICED · מ-SUBMITTED → REJECTED · מ-REJECTED → SUBMITTED מחדש.

**בפועל ב-`approve()`:** מאפשר אישור גם מ-`PENDING` (לא רק SUBMITTED) — חריגה מה-state machine.

---

## 3. סיווג תקן / לא תקן / חריגות

| שאלה | תשובה מהקוד |
|---|---|
| מי קובע? | **המשתמש** דרך toggle בטופס (`isNonStandard`) |
| יש auto-detection (>9 שעות → לא תקן)? | **לא** — אין auto |
| איפה "חריגות"? | זה אותו דבר כמו "לא תקן" — אין enum נפרד |
| תקן | קבוע 9 שעות נטו + 1.5 הפסקה (10.5 נוכחות) |
| לא תקן | חובה לבחור `non_standard_reason` + segments זמן |
| השפעה על תעריף | **אין** — תעריף אחד מ-`resolve_supplier_pricing()`. סיווג משפיע רק על **כמה שעות** נספרות |

---

## 4. זרימה ל-Invoice

```
Worklog נוצר (PENDING)
   ↓ submit()
Worklog SUBMITTED
   ↓ approve() — לא יכול לאשר את עצמו
Worklog APPROVED ← זה ה"צבוע" (ready for billing)
   ↓ invoice_service.generate_monthly_invoice()
   ↓ או POST /invoices/from-worklogs (ידני)
Worklog INVOICED + invoice_items.worklog_id מוזן
```

**אין דגל "צבוע"** — APPROVED הוא הסימן הברור היחיד שמשהו מוכן לחיוב.

---

## 5. מי יכול לאשר Worklog

- ב-**Backend:** רק `worklogs.approve` (permission) + לא יכול לאשר את עצמך
- ב-**Frontend:** `WorklogApproval.tsx` בודק רק `role in [ADMIN, AREA_MANAGER, ACCOUNTANT]`

→ אי-עקביות: ROLE_MANAGER לא יכול ב-UI אבל ב-Backend אם יש לו ההרשאה — כן.

---

## 6. מסכים בפרונט (`pages/WorkLogs/`)

| קובץ | תפקיד |
|---|---|
| `WorklogFormUnified.tsx` | יצירה — POST /worklogs |
| `WorkLogs.tsx` | רשימה |
| `WorklogApproval.tsx` | אישור |
| `WorklogDetail.tsx` | פרטים + Submit/Approve/Reject |
| `AccountantInbox.tsx` | תיבת חשבונאות + יצירת חשבונית |

---

## 7. בעיות פתוחות שגיליתי

1. **`reject_reason`** מועבר ל-service אבל **לא נשמר** על הרשומה (`worklog_service.py:656-664`)
2. **`metadata_json` ו-`total_amount`** ב-service לא קיימים ב-model
3. **`WorklogResponse`** ב-schema לא מכיל `is_standard` ו-`non_standard_reason` — אבל ה-frontend מציג אותם
4. **`work_order_id`** ב-Schema מסומן optional אך service דורש (חוסר עקביות)
5. **`approve()` מאפשר מ-PENDING** — דילוג על SUBMITTED
6. **Permission mismatch** בין UI (role-based) לבין Backend (permission-based)
