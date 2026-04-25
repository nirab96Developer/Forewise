# Phase 3 Wave 1.2 — work_orders — **BLOCKED on policy clarification**

**תאריך**: 2026-04-26
**סטטוס**: עצרתי לפני תיקון. דרושה החלטה אסטרטגית.

---

## למה עצרתי

ה-scope של work_orders **אינקונסיסטנטי** בקוד הקיים, ובלתי-תואם למטריצה ב-`PHASE3_WAVE1_POLICY_ENGINE.md` (שורה 87 בproposal). אם אכתוב `WorkOrderScopeStrategy` עכשיו אצטרך לבחור בין:

- **שכפול הקוד הקיים** — ינציח את האי-עקביות
- **כפיית מטריצה אחידה** — שובר התנהגות שוטפת

לפי המנדט שלך: "אם scope לא ברור → לעצור ולדווח."

---

## מה מצאתי בקוד היום

### `GET /work-orders` (list, line 124-127)
```python
require_permission(current_user, "work_orders.read")
if current_user.area_id is not None:
    search.area_id = current_user.area_id
```
**הקוד הזה רץ ל-כל user שיש לו area_id**, ללא תלות בrole. כלומר:
- ADMIN עם `area_id=10` → רואה רק את אזור 10 ❌ (אדמין אמור לראות הכל)
- WORK_MANAGER עם `area_id=10` → רואה רק את אזור 10 ❌ (אמור לראות לפי פרויקטים שלו, לא אזור)
- ACCOUNTANT עם `area_id=10` → רואה רק את אזור 10 ❌ (אמור לראות הרבה יותר רחב)

### `GET /work-orders/{id}` (line 230-232)
```python
role_code = current_user.role.code.upper()
if current_user.area_id is not None and role_code not in (
    'ADMIN', 'SUPER_ADMIN', 'WORK_MANAGER', 'ORDER_COORDINATOR', 'ACCOUNTANT'
):
    query = query.where(Project.area_id == current_user.area_id)
```
**הגיון אחר לחלוטין**:
- ADMIN, COORDINATOR, ACCOUNTANT, WORK_MANAGER → סין כל ה-WOs
- REGION_MANAGER, AREA_MANAGER, SUPPLIER → מסונן לפי area

הבעיות:
1. WORK_MANAGER חופשי לראות **כל** WO במערכת (לא רק פרויקטים שלו)
2. REGION_MANAGER מסונן לפי `area_id` שלו — אבל REGION_MANAGER הוא מנהל **מרחב** (region), לא אזור! יכול להיות שאין לו area_id בכלל וייכשל
3. SUPPLIER מסונן לפי area_id — אבל ספק לא מקבל area_id, אמור להיות מסונן לפי `WO.supplier_id == current_user.supplier_id` או דומה

### חוסר עקביות בין list ו-get_single
- **list**: filter ע"י `area_id` ל-**כל** user שיש לו area_id (כולל admin!)
- **get_single**: filter ע"י `area_id` רק ל-REGION/AREA/SUPPLIER, לא ל-WORK/COORDINATOR/ACCOUNT/ADMIN

אותו user יראה רשימה מסוננת אבל ייכנס בהצלחה ל-WO ספציפי שלא ברשימה. או ההפך — get יחזיר 404 אבל list לא יציג אותו. **שתי לוגיקות שונות לאותה ישות**.

---

## מה ה-proposal הציע (השורה ב-PHASE3_WAVE1_POLICY_ENGINE.md:87)

| Resource | Admin | REGION | AREA | WORK | ACCT | COORD | SUPPLIER |
|---|---|---|---|---|---|---|---|
| WorkOrder | all | region | area | assigned project | global | global | own only |

**4 מ-7 התפקידים שונים** מהקוד הנוכחי:
- REGION_MANAGER: proposal=region, code=area (ולא בכל endpoint)
- WORK_MANAGER: proposal=assigned project, code=ALL (אין שום filter)
- ACCOUNTANT: proposal=global, code=area בlist / global ב-get_single
- SUPPLIER: proposal=own only (`supplier_id`), code=area_id (שלא קיים לספק)

---

## אופציות להחלטה

### אופציה A — לשכפל את הקוד הקיים כמו שהוא
- **יתרון**: אפס שינוי behavior. tests קיימים ימשיכו לעבוד.
- **חיסרון**: מעביר את האי-עקביות ל-strategy. לא משפר כלום.
- **סיכון**: 0
- **זמן**: 30 דק'

### אופציה B — לכפות מטריצה אחידה (לפי proposal)
- **יתרון**: מערכת עקבית. WORK_MANAGER יראה רק פרויקטים שלו. SUPPLIER יראה רק WOs שלו.
- **חיסרון**: שובר behavior של 4 תפקידים. ייתכן ש-frontend מסתמך על האי-עקביות.
- **סיכון**: גבוה — דורש בדיקה מקיפה של frontend לפני
- **זמן**: 2-3 שעות + בדיקות

### אופציה C — recon ידני per-role בfrontend לפני החלטה
- מה ה-frontend באמת מציג לכל role בעמוד `/work-orders`?
- מה ספק רואה בפורטל שלו?
- האם work_manager אמור לראות WOs שלא בפרויקטים שלו?
- **המלצה שלי**: זה השלב הנכון לפני בחירה בין A ו-B.

---

## ההמלצה הסופית שלי

לעצור את Wave 1.2 כאן עד שנדבר על מה ה-scope **אמור** להיות פר-role. בלי החלטה אסטרטגית כל strategy שאכתוב יהיה ניחוש.

**הצעה**: להמשיך לdomain אחר ב-Wave 1.X — `Notification` או `SupportTicket` שיש להם ownership פשוט וברור — ולחזור ל-work_orders אחרי שתאשר את ה-scope policy.

מה אתה מעדיף?
