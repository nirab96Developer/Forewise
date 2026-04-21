# נושא 1 — Work Order Template (טמפלייט הזמנת עבודה)

> **שלב:** Discovery בלבד · אין שינויי קוד.
> **מקור:** `app_backend/app/models/work_order.py`, `app_backend/app/schemas/work_order.py`,
> `app_backend/app/services/work_order_service.py`, `app_frontend/src/pages/WorkOrders/NewWorkOrder.tsx`.

---

## 1. מבט-על — מי יוצר ואיך זה נראה למשתמש

| נתון | ערך בפועל בקוד |
|---|---|
| מי יוצר הזמנה | מנהל עבודה (משתמש מחובר) — דרך מסך `NewWorkOrder.tsx` |
| כותרת המסך | "דרישת כלים" (לא "הזמנת עבודה") |
| נקודת כניסה | `/projects/:code/new-work-order` או `/work-orders/new?project=ID` |
| נעילת פרויקט | אם נכנסים מתוך פרויקט — שדה הפרויקט נעול ולא ניתן לשינוי |
| Endpoint יעד | `POST /api/v1/work-orders/` |
| Service backend | `WorkOrderService.create_work_order()` |

**הערה:** הקוד עצמו לא מסנן פרויקטים לפי "משוייכים אליי" במסך זה — נטען כל ה-`projects.getProjects({})`.
Scoping (אם קיים) מבוצע ברמת ה-API (בשירות הפרויקטים), לא בטופס.

---

## 2. כל השדות בטופס — מה רואה המשתמש

הטופס מחולק ל-**4 בלוקים**:

### בלוק 1 — פרטי עבודה

| שדה (UI) | שם פנימי (state) | חובה? | מקור הערך | הערות |
|---|---|---|---|---|
| פרויקט | `selectedProject` | **כן** | drop-down של `projectService.getProjects()` | ננעל אם נכנסים מהקשר פרויקט |
| תאריך התחלה | `start_date` | **כן** | input תאריך | ברירת מחדל: היום |
| מספר ימים | `work_days` | **כן** | input מספר (≥1) | בסיס לכל החישובים |
| סה"כ שעות | `totalHours` | מחושב | `work_days × 9` | 9 = `BILLABLE_HOURS_PER_DAY` (קבוע בקוד) |
| תאריך סיום | `endDate` | מחושב | `start_date + work_days - 1` | לא נערך ידנית |
| תצוגת תקציב | `selectedProject.allocated_budget - spent_budget` | תצוגה | מהפרויקט | מציג אזהרה אדומה אם חרגו |

### בלוק 2 — הגדרת כלים

| שדה (UI) | שם פנימי | חובה? | מקור הערך | הערות |
|---|---|---|---|---|
| סוג כלי | `tool_type` (+`selectedCategoryId`) | **כן** | `equipmentService.getEquipmentCategories()` | קטגוריה בלבד — לא דגם ספציפי |
| כמות כלים | `quantity` | **כן** | input מספר (1–5) | **min=1, max=5** מקודד בטופס |
| כלי עם שמירה (לינת שטח) | `has_overnight` | לא | checkbox | מציג בלוק שמירה אם מסומן |
| מספר ימי שמירה | `guard_days` | לא | input מספר (0 עד `work_days`) | מתחשב אוטומטית ל-`work_days - 1` |

### בלוק 3 — שיטת הקצאת ספק

שני מסלולים בלעדיים זה לזה:

#### מסלול A — סבב הוגן (ברירת מחדל)
- `allocation_method = 'fair_rotation'`
- אין שדות נוספים
- המערכת מציגה preview של "הספק הבא בתור" מ-`POST /work-orders/preview-allocation`
- בעת שליחה — נשלח `allocation_method=FAIR_ROTATION` ללא `supplier_id`

#### מסלול B — בחירת ספק (אילוץ)
- `allocation_method = 'supplier_selection'`
- שדות חובה נוספים:

| שדה | חובה? | מקור |
|---|---|---|
| בחר ספק | **כן** | `supplierService.getActiveSuppliersByCategory(categoryId)` |
| סיבת אילוץ | **כן** | `GET /supplier-constraint-reasons?is_active=true` |
| הסבר סיבת האילוץ | **כן אם** `reason.requires_additional_text` | textarea — מינימום 10 תווים |

- בעת שליחה — `allocation_method=MANUAL`, `is_forced_selection=true`

### בלוק 4 — הערות נוספות

| שדה | חובה? | משמש כ |
|---|---|---|
| הערות | לא | `description` של ההזמנה |

---

## 3. ולידציות מצד הלקוח (Frontend)

ב-`handleSubmit` רץ הסדר הבא **(שורות 359–406):**

1. `selectedProject` — חובה ("יש לבחור פרויקט")
2. `tool_type` — חובה ("יש לבחור סוג כלי")
3. `workDaysNumber >= 1` — חובה ("יש להזין מספר ימי עבודה תקין")
4. `quantityNumber >= 1` — חובה ("יש להזין כמות כלים תקינה")
5. אם `supplier_selection`: `supplier_id` — חובה
6. אם `supplier_selection`: `constraint_reason_id` — חובה
7. אם `requires_additional_text`: `constraint_explanation.length >= 10`

---

## 4. שדות שנשלחים בפועל ל-Backend

```typescript
// NewWorkOrder.tsx :410-431 — workOrderData
{
  title:           `דרישת כלי: ${tool_type} (${quantity} יחידות)`,  // ← מורכב אוטומטית
  description:     notes || `דרישת כלי ${tool_type} לפרויקט ${name}`, // ← אוטו אם ריק
  project_id:      selectedProject.id,
  supplier_id:     <אם supplier_selection בלבד>,
  equipment_type:  tool_type,                           // שם הקטגוריה כטקסט
  work_start_date: start_date,
  work_end_date:   endDate,                             // ← מחושב, לא נערך ידנית
  priority:        'medium',                            // ← קבוע! הטופס לא מאפשר שינוי
  estimated_hours: totalHours,                          // = days × 9
  days:            workDaysNumber,
  has_overnight:   formData.has_overnight,
  overnight_nights: workDaysNumber - 1 (אם has_overnight, אחרת 0),
  allocation_method: 'FAIR_ROTATION' | 'MANUAL',
  is_forced_selection: (allocation_method === 'supplier_selection'),
  constraint_reason_id: <אם supplier_selection>,
  constraint_notes:     constraint_explanation,
  requires_guard:  has_overnight,
  guard_days:      formData.guard_days,
}
```

**שדות שלא נשלחים בכלל מהטופס** (גם אם קיימים ב-Schema):
`order_number, status, equipment_id, location_id, hourly_rate, total_amount, frozen_amount, requested_equipment_model_id, equipment_license_plate, portal_token`

---

## 5. ולידציות והעשרות בצד השרת

`WorkOrderService.create_work_order` — `work_order_service.py:114–`:

| שלב | פעולה | מקור |
|---|---|---|
| 1 | `order_number` יוסר מה-dict (auto-generated ב-DB) | שורה 127 |
| 2 | `status` מנורמל ל-`'PENDING'` באותיות גדולות | שורה 129 |
| 3 | מוסר `hourly_rate, total_amount, frozen_amount` שהגיעו מהלקוח | 131-133 |
| 4 | **חובה:** `estimated_hours > 0` → אחרת `400` | 136-137 |
| 5 | אם יש `project_id`: הפרויקט חייב להיות `is_active=True` | 144-145 |
| 6 | לפרויקט חייב להיות תקציב פעיל עם `total_amount > 0` | 146-153 |
| 7 | **חובה:** `equipment_type` → אחרת `400 חובה לציין סוג כלי` | 158-162 |
| 8 | פתרון אוטומטי של `requested_equipment_model_id` לפי שם הקטגוריה | 156-173 |
| 9 | אם לא נמצא דגם → `400 לא נמצא דגם ציוד לקטגוריה` | 168-172 |
| 10 | `hourly_rate` נקבע מ-`resolve_supplier_pricing()` (Source of Truth: הגדרות ספקים) | 175-176 |
| 11 | `total_amount = estimated_hours × hourly_rate + overnight_nights × overnight_rate` | 179-185 |
| 12 | `frozen_amount = total_amount` (מקפיא תקציב) | 185 |
| 13 | בדיקת תקציב — אם `committed + frozen > budget` → דחייה | 188-228 (ראה לקטע 6) |
| 14 | `portal_token` נוצר אוטומטית (`secrets.token_urlsafe(32)`) | 122 |
| 15 | `token_expires_at = now + 3 hours` | 123 |

---

## 6. ערכי ברירת מחדל לאחר יצירה (במסד הנתונים)

לאחר ה-INSERT — ערכי ה-WorkOrder יהיו:

| שדה | ערך |
|---|---|
| `id` | autoincrement |
| `order_number` | רצף ייחודי (UNIQUE constraint) |
| `status` | `PENDING` |
| `priority` | `MEDIUM` (תמיד — הטופס לא מאפשר אחרת) |
| `created_by_id` | המשתמש המחובר (`current_user.id`) |
| `equipment_id` | **NULL** ← מתמלא רק בשלב מאוחר יותר (סריקת כלי בשטח) |
| `equipment_license_plate` | **NULL** ← מתמלא בסריקה / אישור ספק |
| `actual_hours` | **NULL** ← נצבר מ-Worklogs |
| `charged_amount` | 0 |
| `remaining_frozen` | = `frozen_amount` (מתעדכן בעת חיוב) |
| `is_active` | True |
| `version` | 1 (מ-`BaseModel`) |

---

## 7. מצב התחלתי לפי האפיון העסקי שלך

לפי התיאור שלך:
> "מנהל עבודה פותח הזמנת עבודה לפי פרמטרים קיימים → ההזמנה נוצרת במצב `PENDING` → עוברת למתאם הזמנות"

**עקבית עם הקוד:**
- `status='PENDING'` בעת יצירה ✓
- אין יצירה אוטומטית של supplier_id במסלול A — זה רק preview, ההקצאה האמיתית קורית בשלב המתאם ✓
- במסלול B — `supplier_id` מוגדר כבר ביצירה + `is_forced_selection=True` ✓

> "כל ההזמנה צריכה להיות לפי כלי בפועל ומספר רישוי"

**אבחנה:** ביצירה — `equipment_id` ו-`equipment_license_plate` נשארים NULL.
זה תקין כי בשלב היצירה לא יודעים עדיין איזה כלי ספציפי יישלח.
המידע מתמלא **בשלב הסריקה בשטח** (נושא #2).

---

## 8. דברים שצריך לסכם איתך לפני המשך

| נושא | מה כתוב בקוד | מה צריך החלטה |
|---|---|---|
| **כמות כלים `quantity`** | מ-1 עד 5 בטופס | אבל **לא נשמר במסד** — אין שדה `quantity` ב-WorkOrder. האם ההזמנה צריכה להיות לכל יחידה בנפרד? |
| **`priority`** | קבוע `medium` בטופס | האם זה רצוי? צריך לאפשר HIGH/URGENT? |
| **שעות בילבל** | קבוע 9 שעות ליום (קבוע בקוד) | האם זה תמיד 9? יש סוגי כלים אחרים? |
| **טוקן פורטל** | תוקף 3 שעות | האם זה מספיק לספק לאשר? לעיתים סופ"ש? |
| **scoping פרויקטים** | הטופס לא מסנן | האם המסך צריך להגביל למשוייכים בלבד? (כנראה כבר נעשה ב-API של פרויקטים) |
| **שדה quantity לא נשמר** | בטופס מקבל ערך אבל לא נשלח | באג סמוי או fly-by-night? |

---

## 9. סיכום זרימת היצירה

```
[מנהל עבודה]
   ↓ פותח /projects/:code/new-work-order
[NewWorkOrder.tsx]
   ↓ טוען: projects, equipment_categories, constraint_reasons
   ↓ מציג טופס בן 4 בלוקים
   ↓ ולידציה צד-לקוח (8 בדיקות)
   ↓ POST /api/v1/work-orders/  (workOrderData)
[WorkOrderService.create_work_order]
   ↓ ולידציה: estimated_hours > 0, project active, budget קיים
   ↓ פתרון: requested_equipment_model_id מ-equipment_type
   ↓ חישוב: hourly_rate, total_amount, frozen_amount
   ↓ ולידציה: budget commitment OK
   ↓ INSERT INTO work_orders (status='PENDING', priority='MEDIUM', ...)
   ↓ INSERT budget_commitment (frozen_amount)
   ↓ portal_token נוצר (תוקף 3 שעות)
[WorkOrder created]
   ↓ status=PENDING, supplier_id=NULL (במסלול A)
   ↓ equipment_id=NULL, equipment_license_plate=NULL
   ↓ ממתין למתאם הזמנות
```

---

**הסתיים נושא 1.**
**הבא בתור (נושא 2):** Equipment Intake — קליטת כלי בשטח (3 המצבים: התאמה / רישוי שונה / כלי שונה).
