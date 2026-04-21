# נושא 7 — Status Table (טבלת סטטוסים מלאה)

> **שלב:** Discovery בלבד · אין שינויי קוד.

---

## 0. אזהרות מקדימות

1. **אין `app_backend/app/db/seeds/`** — לא נמצאו INSERTs לטבלאות `work_order_statuses` / `worklog_statuses`. הנתונים הללו קיימים ב-DB ייצור אבל לא מתועדים בקוד.
2. **`validate_*_transition()`** ב-`enums.py` נקראים רק ב-tests — **אכיפה לא מרכזית** ב-runtime.
3. **Drift קוד-אנום:** `IN_PROGRESS`, `ACTIVE` בשימוש נרחב אבל לא ב-`WO_TRANSITIONS`.
4. **Drift `PENDING` ב-Invoice:** ב-schema ובקומנט אך לא ב-`InvoiceStatus` enum.

---

## 1. WorkOrder Statuses

| Code | תווית עברית (`WO_LABELS`) | בשימוש בפועל |
|---|---|---|
| `PENDING` | ממתין | ✅ |
| `DISTRIBUTING` | בהפצה לספקים | ✅ |
| `SUPPLIER_ACCEPTED_PENDING_COORDINATOR` | ספק אישר - ממתין לאישור | ✅ |
| `APPROVED_AND_SENT` | אושר ונשלח | ✅ |
| `IN_PROGRESS` | (חסר ב-WO_LABELS!) | ✅ — חוסר drift |
| `ACTIVE` | (חסר!) | ✅ — חוסר drift |
| `COMPLETED` | הושלם | ✅ |
| `REJECTED` | נדחה | ✅ |
| `CANCELLED` | בוטל | ✅ |
| `EXPIRED` | פג תוקף | ✅ (cron portal_expiry) |
| `STOPPED` | הופסק | ✅ (release_equipment) |

### מטריצת מעברים (intended)
| מ- | ל- | מי |
|---|---|---|
| (יצירה) | `PENDING` | מנהל עבודה |
| `PENDING` | `DISTRIBUTING` | מתאם — `send-to-supplier` |
| `PENDING` | `CANCELLED` | אדמין/יוצר |
| `DISTRIBUTING` | `DISTRIBUTING` | מתאם — `move-to-next-supplier` |
| `DISTRIBUTING` | `SUPPLIER_ACCEPTED_PENDING_COORDINATOR` | ספק (פורטל accept) |
| `DISTRIBUTING` | `REJECTED` | ספק (פורטל reject, אין הבא) או מתאם |
| `DISTRIBUTING` | `EXPIRED` | מערכת (cron) |
| `SUPPLIER_ACCEPTED_PENDING_COORDINATOR` | `APPROVED_AND_SENT` | מתאם — `approve` |
| `SUPPLIER_ACCEPTED_PENDING_COORDINATOR` | `REJECTED` | מתאם — `reject` |
| `APPROVED_AND_SENT` | `IN_PROGRESS` | מנהל עבודה — `scan-equipment` |
| `APPROVED_AND_SENT` | `STOPPED` | מערכת — release_equipment |
| `APPROVED_AND_SENT` | `CANCELLED` | משתמש עם הרשאה |
| `IN_PROGRESS` / `APPROVED_AND_SENT` | `COMPLETED` | אקאונטנט/אדמין — close או auto מ-worklog approve |
| Terminal | — | COMPLETED, REJECTED, CANCELLED, EXPIRED, STOPPED |

### Side effects לפי מעבר
| מעבר | תופעות לוואי |
|---|---|
| → `PENDING` | freeze budget (committed_amount) |
| → `DISTRIBUTING` | token חדש (3h), email, rotation update |
| → `SUPPLIER_ACCEPTED_PENDING_COORDINATOR` | equipment_id+plate, התראה למתאם |
| → `APPROVED_AND_SENT` | activity log, 3 emails (Waze, יוצר, in-app) |
| → `IN_PROGRESS` | equipment_id+plate (אם לא היה) |
| → `STOPPED` | release frozen, equipment cleared, log |
| → `REJECTED` | release frozen, rotation update |
| → `CANCELLED` | release frozen |
| → `COMPLETED` | release frozen, emails, notifications |

---

## 2. Worklog Statuses

| Code | תווית | מעבר מ- |
|---|---|---|
| `PENDING` | ממתין | (יצירה) |
| `SUBMITTED` | הוגש | PENDING |
| `APPROVED` | אושר | SUBMITTED, **גם PENDING** (הקלה) |
| `REJECTED` | נדחה | SUBMITTED |
| `INVOICED` | הופק חשבון | APPROVED |

**Side effects ב-`approve`:**
- שחרור frozen מ-WO, הוספה ל-spent_amount
- אם `remaining_frozen` יורד ל-0 → WO → `COMPLETED`
- מיילים והתראות

---

## 3. Invoice Statuses

| Code | תווית | מ- | ל- |
|---|---|---|---|
| `DRAFT` | טיוטה | (יצירה) | APPROVED, CANCELLED |
| `PENDING` | (drift!) | בשימוש בפרונט בלבד | — |
| `APPROVED` | אושר | DRAFT | SENT, PAID, CANCELLED |
| `SENT` | נשלח | APPROVED | PAID, CANCELLED |
| `PAID` | שולם | APPROVED, SENT | (terminal) |
| `CANCELLED` | בוטל | DRAFT, APPROVED, SENT | (terminal) |

---

## 4. Project Statuses

- שדה `status` (String 50) ברירת מחדל `"active"` (lowercase)
- שדה נפרד `is_active` (Boolean)
- ערכים בפרונט: `PLANNING`, `ACTIVE`, `ON_HOLD`, `COMPLETED`, `CANCELLED`
- **אין state machine מוגדר**
- `is_active` חוסם יצירת WO

---

## 5. Supplier Statuses

- **רק `is_active`** (Boolean) — אין enum
- אין `verified` או `blocked` ברמת ספק
- "Blocked" בפורטל מחושב ל-**equipment** (אם משויך ל-WO פעיל אחר)

---

## 6. Equipment Statuses

- שדה `status` עם הערה: `available`, `in_use`, `maintenance`, `retired`
- ברירת מחדל: `available`
- helpers: `is_available`, `is_in_use`, `needs_maintenance`
- `SupplierEquipment.status = 'busy'` בעת accept בפורטל

---

## 7. סיכום Drift לפי דחיפות

| Drift | רמה | כיצד מתבטא |
|---|---|---|
| `IN_PROGRESS`/`ACTIVE` בקוד אך לא ב-enum | **קריטי** | תוויות עברית חסרות לסטטוסים פעילים |
| `validate_*_transition` לא נאכף | **גבוה** | אין הגנה מפני מעברים אסורים ב-runtime |
| Invoice `PENDING` ב-3 רמות שונות | בינוני | בלבול UX |
| ` accountant` accept מ-PENDING | בינוני | חוסר עקביות לוגית |
| אין DB seeds בקוד | בינוני | קשה לשחזר ייצור |
