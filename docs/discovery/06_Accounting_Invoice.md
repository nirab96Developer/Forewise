# נושא 6 — Accounting / Invoice Flow (תהליך חשבונאות)

> **שלב:** Discovery בלבד · אין שינויי קוד.

---

## 1. מודל Invoice

| שדה | סוג | חובה? | הערות |
|---|---|---|---|
| `id` | Integer PK | כן | |
| `invoice_number` | String(50) UNIQUE | כן | פורמט: `INV-{year}-{seq}` |
| `supplier_id` | Integer indexed | כן | **אין FK ב-DB** |
| `project_id` | Integer optional | | **אין FK** |
| `created_by` | Integer | optional | **אין FK** |
| `issue_date` / `due_date` | Date | | due_date default = issue + 30 days |
| `subtotal` / `tax_amount` / `total_amount` | Numeric(18,2) | | |
| `paid_amount` | Numeric default 0 | | |
| `status` | String(50) indexed | | DRAFT/PENDING/APPROVED/SENT/PAID/CANCELLED |
| `payment_method` | String(50) | optional | |
| `notes` | String | optional | |
| `pdf_path` | String(500) | optional | |
| `metadata_json` | String | optional | |

**שדות חסרים שהיית מצפה לראות:**
- `paid_at` ❌ לא קיים
- `payment_reference` ❌ לא קיים
- FK לפרויקט/ספק ❌ אינטגריטי DB חלש

---

## 2. אי-עקביות Status בין שכבות

| מקור | רשימת סטטוסים |
|---|---|
| `models/invoice.py` (comment) | DRAFT, PENDING, APPROVED, PAID, CANCELLED |
| `schemas/invoice.py` Pydantic | DRAFT, **PENDING**, APPROVED, SENT, PAID, CANCELLED |
| `core/enums.py` InvoiceStatus | DRAFT, APPROVED, SENT, PAID, CANCELLED (**אין PENDING**) |
| `frontend statusTranslation.ts` | מכיל PENDING, SENT, ועוד |

**Drift בין 4 מקומות.**

---

## 3. בחירת Worklogs לחשבונית

**אין דגל "צבוע".** ההכשר היחיד הוא `Worklog.status == 'APPROVED'`.

### מסלולים ליצירת חשבונית

| מסלול | API | בחירה |
|---|---|---|
| **חודשי** | `POST /invoices/generate-monthly` | לפי supplier + project + month/year, כל ה-APPROVED של החודש |
| **ידני** | `POST /invoices/from-worklogs` | רשימת `worklog_ids` מפורשת |
| **מ-WO** | `POST /invoices/from-work-order/{id}` | **stub** — `total_amount=0` |

לאחר חיוב, worklogs → status `INVOICED`.

---

## 4. VAT

- ברירת מחדל קבועה: **18%** (`VAT_RATE = 0.18`)
- ב-`generate_monthly_invoice` משתמש ב-`worklogs[0].vat_rate` כברירת מחדל אם קיים
- בכל מקרה אחר — 18% hard-coded

---

## 5. תהליך מ-DRAFT עד PAID

```
[Worklogs APPROVED]
   ↓ אקאונטנט יוצר חשבונית
   ↓ POST /invoices/from-worklogs
[Invoice DRAFT]
   ↓ POST /invoices/{id}/approve  (permission: invoices.approve)
[Invoice APPROVED] + מתעדכן project.spent_amount
   ↓ POST /invoices/{id}/send  (permission: invoices.update)
[Invoice SENT] ⚠️ רק שינוי סטטוס — לא שולח email!
   ↓ POST /invoices/{id}/mark-paid  (permission: invoices.approve)
[Invoice PAID] + paid_amount = total_amount
   ⚠️ לא נשמר payment_method, payment_reference, paid_at
```

---

## 6. PDF + Email

### PDF
- ✅ מומש ב-`generate_invoice_pdf` (WeasyPrint, RTL)
- חשוף דרך `GET /invoices/{id}/pdf?token=...`
- PDF נוצר on-the-fly — לא נשמר ל-disk למרות שיש שדה `pdf_path`

### Email
- ✅ נשלח אוטומטית ב-`generate_monthly_invoice` (PDF מצורף)
- ❌ **לא נשלח** ב-`POST /invoices/{id}/send` — רק שינוי סטטוס
- ❌ **לא נשלח** ב-`from-worklogs` ידני
- → ה-toast בפרונט "נשלח לספק במייל" לפעמים שקרי

---

## 7. Scoping אזורי

| תפקיד | רשימת חשבוניות | חשבונית בודדת |
|---|---|---|
| ADMIN | הכל | הכל |
| REGION_MANAGER | הכל | הכל (לא מוגבל לאזור!) |
| ACCOUNTANT | הכל | הכל |
| AREA_MANAGER | אמור להיות מוגבל ל-area | מוגבל לאזור (Project.area_id) |
| WORK_MANAGER עם area | אמור להיות מוגבל | כן |

**Bug:** ה-router מגדיר `search.area_id = current_user.area_id` אבל ה-`InvoiceService.list` **לא מסנן לפי `area_id`** — Scoping בפועל לא מופעל ברשימה.

**גאפ נוסף:** `scope.py` מגדיר `ACCOUNTANT` כ-`AREA_ROLES`, אבל אקאונטנט region-only (עם `area_id=None`) לא מטופל היטב.

---

## 8. מסכי Frontend

| קובץ | תפקיד |
|---|---|
| `Invoices/Invoices.tsx` | רשימה, ייצוא Excel, פתיחת PDF |
| `Invoices/InvoiceDetail.tsx` | פרטים, שלח, סמן שולם |
| `WorkLogs/AccountantInbox.tsx` | תיבת אקאונטנט — יצירת חשבונית מ-worklogs |
| `WorkLogs/AccountantDashboard.tsx` | בחירה מרובה — **שולח קריאה שבורה!** (חסרים supplier_id, project_id) |

---

## 9. בעיות פתוחות שגיליתי

1. **AccountantDashboard `from-worklogs` שבור** — לא שולח `supplier_id`/`project_id`
2. **`mark-paid` חסר שדות** — לא שומר payment_method, reference, paid_at
3. **`POST /send` רק משנה סטטוס** — אין email למרות tooltip בפרונט
4. **`get_uninvoiced_suppliers`** לא מסנן באמת לפי "uninvoiced"
5. **שמות routes:** `GET /uninvoiced-suppliers` עלול להיתפס כ-`/{invoice_id}` (תלוי סדר רישום)
6. **Status enum drift** — 4 מקומות שונים, 4 רשימות שונות
7. **אין FK ב-DB** ל-supplier/project/created_by — אינטגריטי חלש
8. **Scoping אזורי לא מופעל** ב-list של חשבוניות
9. **VAT hard-coded** — קבוע 18%, אין הגדרה גמישה
10. **`from-work-order` stub** — total_amount=0, לא משתמש בקוד
