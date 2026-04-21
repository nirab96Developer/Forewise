# Checklist בדיקות ידניות — אחרי גל 1+2

> **מטרה:** לוודא שכל ה-flow עובד end-to-end לפני המשך לגל 3.
> **הוראות:** תעבור משימה אחר משימה. סמן ✔️ אם עובר, ❌ אם נכשל.
> אם נכשל — תפסיק, תרשום מה ראית, ותשלח לי.

---

## ⚙️ 0. הכנות (Pre-flight) — חובה לפני שמתחילים

### 0.1 — Backend: הרצת migrations חדשות
- [ ] `cd app_backend && source .venv/bin/activate`
- [ ] `alembic upgrade head` — חייב להסתיים בהצלחה
- [ ] בדיקה ב-DB:
  ```sql
  SELECT code FROM work_order_statuses WHERE code = 'NEEDS_RE_COORDINATION';
  -- אמור להחזיר שורה אחת
  ```
- [ ] בדיקה ב-DB:
  ```sql
  SELECT column_name FROM information_schema.columns
  WHERE table_name = 'invoices'
    AND column_name IN ('paid_at','payment_reference','paid_by','sent_at');
  -- אמור להחזיר 4 שורות
  ```

### 0.2 — Backend: הפעלה מחדש
- [ ] `systemctl restart forewise-backend` (או דרך הפיתוח: kill+start)
- [ ] `curl http://localhost:8000/api/v1/health` → 200 OK
- [ ] בדיקת לוגים: `journalctl -u forewise-backend -f` → אין ERROR ב-startup

### 0.3 — Frontend: build חדש
- [ ] `cd app_frontend && npm run build` — חייב לעבור ב-0 errors
- [ ] רענון hard ב-browser (`Ctrl+Shift+R`) כדי לטעון את הקוד החדש

### 0.4 — נתוני בדיקה זמינים
- [ ] לפחות **3 פרויקטים פעילים** עם תקציב חיובי
- [ ] לפחות **2 ספקים פעילים** עם ציוד מסוג זהה (לבדיקת different_plate)
- [ ] לפחות **1 ספק** עם ציוד מסוג שונה (לבדיקת wrong_type)
- [ ] משתמשים זמינים: ADMIN, ORDER_COORDINATOR, WORK_MANAGER, ACCOUNTANT
- [ ] מנהל עבודה משוייך לפרויקט הבדיקה (`project_assignments`)

---

## 🔄 1. Flow מלא: מהזמנה ועד תשלום

> **משך משוער:** 30 דק' · **משתמשים:** 4 (Work Manager, Coordinator, Supplier via portal, Accountant)

### 1.1 — יצירת WorkOrder (כלי בודד)
- [ ] התחברות כ-**WORK_MANAGER**
- [ ] מסך פרויקט → "דרישת כלים"
- [ ] בחירת סוג כלי + 1 ימי עבודה + **כמות = 1**
- [ ] שיטת הקצאה: סבב הוגן
- [ ] לחיצה על "שלח דרישה"
- [ ] **תוצאה:** Toast "ההזמנה נשלחה בהצלחה" · נוצרה הזמנה ב-status PENDING
- [ ] בדיקה ב-DB: `SELECT id, status, priority, equipment_id, supplier_id FROM work_orders ORDER BY id DESC LIMIT 1;`
- [ ] **ציפיות:** status=PENDING, priority=MEDIUM, equipment_id=NULL, supplier_id=NULL

### 1.2 — שליחה לספק (Coordinator)
- [ ] התחברות כ-**ORDER_COORDINATOR**
- [ ] מסך "תיאום הזמנות"
- [ ] ההזמנה החדשה מופיעה בטאב "ממתינות"
- [ ] לחיצה על "שלח לספק (סבב הוגן)"
- [ ] **תוצאה:** Toast הצלחה · status → DISTRIBUTING
- [ ] בקונסול דפדפן: `[Supplier Portal] https://forewise.co/supplier-portal/<token>` — שמור ה-token

### 1.3 — אישור ספק דרך הפורטל
- [ ] פתיחת `https://<host>/supplier-portal/<token>` בחלון אינקוגניטו (אין JWT)
- [ ] בחירת ציוד מה-dropdown
- [ ] לחיצה על "אשר ההזמנה"
- [ ] **תוצאה:** "ההזמנה אושרה בהצלחה"
- [ ] DB: status=`SUPPLIER_ACCEPTED_PENDING_COORDINATOR`, equipment_id ו-equipment_license_plate מאוכלסים

### 1.4 — אישור סופי של מתאם
- [ ] חזרה ל-Coordinator
- [ ] טאב "ספק אישר — ממתין"
- [ ] לחיצה על "אשר ושלח לביצוע"
- [ ] **תוצאה:** status → APPROVED_AND_SENT
- [ ] התקבלו 3 התראות (יוצר, ספק, in-app)

### 1.5 — קליטת כלי בשטח (Work Manager)
- [ ] התחברות חזרה כ-WORK_MANAGER
- [ ] מסך WorkOrder → "סרוק כלי"
- [ ] **scenario A:** הזנת ה-license plate **המדויק** של הכלי שאישר הספק
- [ ] **תוצאה:** "כלי תואם — אומת בהצלחה" · status → IN_PROGRESS

### 1.6 — דיווח שעות
- [ ] מסך WorkLogs → "דיווח חדש"
- [ ] בחירת ה-WO החדש, 8 שעות תקן
- [ ] לחיצה "שמור והגש"
- [ ] **תוצאה:** Worklog נוצר ב-status SUBMITTED

### 1.7 — אישור Worklog (Accountant/Manager)
- [ ] התחברות כ-**ACCOUNTANT**
- [ ] AccountantInbox → דיווחים מסוננים SUBMITTED
- [ ] לחיצה "אשר"
- [ ] **תוצאה:** status → APPROVED · WO budget מתעדכן (`spent_amount` עולה)

### 1.8 — יצירת חשבונית
- [ ] AccountantDashboard → סינון APPROVED → סימון checkbox
- [ ] לחיצה "צור חשבונית"
- [ ] **תוצאה:** "נוצרה חשבונית בהצלחה" · Worklog → INVOICED · Invoice ב-DRAFT

### 1.9 — אישור + שליחה
- [ ] InvoiceDetail → "אשר" → "שלח לספק"
- [ ] DB: `SELECT status, sent_at FROM invoices WHERE id = ?` — sent_at אמור להיות מאוכלס

### 1.10 — סימון "שולם"
- [ ] InvoiceDetail → "סמן שולם"
- [ ] **תוצאה:** status=PAID, paid_at, paid_by מאוכלסים
- [ ] DB: `SELECT status, paid_at, paid_by FROM invoices WHERE id = ?`

✅ **Section 1 PASS** אם כל 10 הצעדים עברו ללא שגיאה.

---

## 🔧 2. שלושת מצבי קליטת הכלי (הליבה של גל 2)

> **משך:** 20 דק' · **דרישה:** 3 הזמנות מוכנות עד `APPROVED_AND_SENT`

### 2.1 — תרחיש A: התאמה מלאה
- [ ] WO חדש APPROVED_AND_SENT, equipment_license_plate ידוע
- [ ] "סרוק כלי" → הקלד את הרישוי המדויק (גם עם רווחים מסביב!)
- [ ] **ציפייה:** "כלי תואם — אומת בהצלחה" · status → IN_PROGRESS
- [ ] **בדיקת normalize:** הקלד עם case שונה — אמור עדיין להתאים
- [ ] DB: `equipment_license_plate` נשמר ב-UPPER, ללא רווחים

### 2.2 — תרחיש B: אותו סוג, רישוי שונה
- [ ] **הכנה:** וודא שכלי X מאותו סוג קיים במערכת ומשוייך ל-WO אחר פעיל
- [ ] WO חדש APPROVED_AND_SENT שמצפה לאותו סוג כלי
- [ ] "סרוק כלי" → הקלד את הרישוי של הכלי X
- [ ] **ציפייה:** מסך מודאל אמבר: "הכלי שנסרק שונה ממספר הרישוי בהזמנה"
- [ ] מוצג שם הפרויקט/הזמנה הקודמת
- [ ] לחיצה "אישור והעברה"
- [ ] **תוצאה:**
  - WO החדש → IN_PROGRESS עם הציוד
  - WO הישן → STOPPED
  - תקציב מוקפא של WO הישן שוחרר
  - audit log: `EQUIPMENT_TRANSFERRED`

### 2.3 — תרחיש C: סוג שונה (wrong_type)
- [ ] **הכנה:** WO חדש עם `equipment_type = 'מחפרון'`. כלי שונה (`equipment_type = 'מכלית מים'`) קיים במערכת
- [ ] APPROVED_AND_SENT
- [ ] "סרוק כלי" → הזן רישוי של מכלית המים
- [ ] **ציפייה:** מסך מודאל אדום: "סוג הכלי שנסרק שונה מההזמנה"
- [ ] מציג: "הוזמן: מחפרון · נסרק: מכלית מים"
- [ ] טקסט: "ההזמנה הוחזרה אוטומטית לטיפול מתאם הזמנות"
- [ ] **בדיקת DB:**
  ```sql
  SELECT status FROM work_orders WHERE id = ?;
  -- אמור להחזיר: NEEDS_RE_COORDINATION
  ```
- [ ] **בדיקת audit:**
  ```sql
  SELECT description FROM activity_logs
  WHERE entity_type = 'work_order' AND entity_id = ?
  AND action = 'WRONG_EQUIPMENT_BLOCKED';
  ```

### 2.4 — Admin Override (תרחיש C+admin)
- [ ] חוזר על 2.3 כ-ADMIN
- [ ] במסך "סוג כלי שגוי" — מופיע כפתור "אישור חריג (מנהל)"
- [ ] לחיצה → modal כתום → הזנת סיבה (לפחות 5 תווים)
- [ ] לחיצה "אשר חריג"
- [ ] **תוצאה:** equipment_id ו-license_plate מתעדכנים, status → IN_PROGRESS
- [ ] audit: `ADMIN_EQUIPMENT_OVERRIDE` עם הסיבה

### 2.5 — חסימת קליטה במצב NEEDS_RE_COORDINATION
- [ ] WO ב-NEEDS_RE_COORDINATION (מ-2.3)
- [ ] WORK_MANAGER מנסה לסרוק שוב
- [ ] **ציפייה:** 400 — "לא ניתן לסרוק כלי — ההזמנה טרם אושרה ע״י מתאם הזמנות"
- [ ] WORK_MANAGER מנסה לדווח שעות על ה-WO הזה
- [ ] **ציפייה:** נחסם — Worklog לא מתקבל

✅ **Section 2 PASS** אם כל 5 התרחישים עובדים.

---

## 🚦 3. NEEDS_RE_COORDINATION — flow מלא

> **משך:** 10 דק'

### 3.1 — תצוגה במסך מתאם
- [ ] התחברות כ-ORDER_COORDINATOR
- [ ] מסך "תיאום הזמנות"
- [ ] **כרטיס סטטיסטיקה אדום:** "דורש החלטה — סוג כלי שגוי" עם המספר הנכון
- [ ] **טאב חדש:** "דורש החלטה" עם הסטטיסטיקה
- [ ] ההזמנה מופיעה **ראשונה** ברשימה (statusOrder=0)
- [ ] Badge אדום: "דורש החלטה — סוג כלי שגוי בשטח"

### 3.2 — Panel הסבר
- [ ] הרחבת כרטיס ההזמנה
- [ ] מופיע banner אדום עם: "סוג כלי שגוי דווח בשטח"
- [ ] טקסט מסביר: "מנהל העבודה ניסה לקלוט כלי שאינו תואם להזמנה. קליטה בשטח חסומה."
- [ ] כפתור כחול: "הפץ מחדש (סבב הוגן — ספק אחר)"

### 3.3 — הפצה מחדש
- [ ] לחיצה על "הפץ מחדש"
- [ ] **תוצאה:**
  - status → DISTRIBUTING
  - supplier_id ב-DB אמור להתאפס ולהיבחר חדש
  - equipment_id, equipment_license_plate → NULL
  - portal_token חדש נוצר
  - email נשלח לספק החדש
- [ ] בדיקה ב-DB:
  ```sql
  SELECT status, supplier_id, equipment_id, portal_token FROM work_orders WHERE id = ?;
  ```

### 3.4 — Notification למתאם
- [ ] התחברות כ-ORDER_COORDINATOR
- [ ] בדיקת notifications (פעמון בנאב-בר)
- [ ] **ציפייה:** התראה "הזמנה הוחזרה לטיפול — סוג כלי שגוי"
- [ ] לחיצה → ניווט אוטומטי ל-`/work-orders/<id>`

### 3.5 — Cancel במקום הפצה
- [ ] WO אחר ב-NEEDS_RE_COORDINATION
- [ ] התחברות כ-ADMIN
- [ ] לחיצה "בטל הזמנה (מנהל)"
- [ ] **תוצאה:** status → CANCELLED · frozen_amount שוחרר

✅ **Section 3 PASS** אם 5 התרחישים עובדים.

---

## 🔢 4. יצירת מספר WorkOrders במקביל (Q1)

> **משך:** 5 דק'

### 4.1 — quantity = 1 (single)
- [ ] טופס דרישת כלים → quantity = 1
- [ ] **ציפייה:** אין disclaimer / hint לגבי "מספר הזמנות"
- [ ] שליחה → toast רגיל "ההזמנה נשלחה בהצלחה"
- [ ] DB: נוצרה הזמנה אחת

### 4.2 — quantity = 3 (multi)
- [ ] טופס → quantity = 3
- [ ] **ציפייה:** מופיע hint כחול: "תיווצרנה 3 הזמנות נפרדות — כלי לכל הזמנה"
- [ ] שליחה
- [ ] **תוצאה:** toast "נוצרו 3 הזמנות נפרדות"
- [ ] DB:
  ```sql
  SELECT title, status FROM work_orders ORDER BY id DESC LIMIT 3;
  -- אמור להיות:
  -- 'דרישת כלי: <type> (1/3)' PENDING
  -- 'דרישת כלי: <type> (2/3)' PENDING
  -- 'דרישת כלי: <type> (3/3)' PENDING
  ```
- [ ] כל הזמנה עם order_number ייחודי

### 4.3 — handling חלקי (סימולציה — אופציונלי)
- [ ] במידת האפשר: יצירה כשתקציב הפרויקט מספיק לשנייה אחת בלבד
- [ ] **ציפייה:** toast "נוצרו 1/3 הזמנות. 2 נכשלו..." — נכון

### 4.4 — Numbering
- [ ] בדיקה: 3 ההזמנות אינן מקבילות מבחינת order_number — כל אחת ייחודית
- [ ] בדיקה: ניתן לפתוח כל אחת ולעבור עליה בנפרד

✅ **Section 4 PASS** אם 3 הזמנות נוצרות עם numbering נכון.

---

## 🛡️ 5. Permissions — כל תפקיד רואה מה שצריך

> **משך:** 15 דק' · **דרישה:** משתמש מכל role

### 5.1 — WORK_MANAGER
- [ ] רואה רק פרויקטים משוייכים אליו (`project_assignments`)
- [ ] לא רואה הזמנות מאזורים אחרים
- [ ] רואה את ה-WOs שלו במסך הפרויקט
- [ ] לא רואה Order Coordination ב-menu
- [ ] לא רואה Invoices ב-menu
- [ ] **בדיקה ב-Console:** `localStorage.getItem('user')` → permissions עם lowercase

### 5.2 — AREA_MANAGER
- [ ] רואה רק פרויקטים ב-area שלו
- [ ] רואה Reports + Map בתפריט
- [ ] לא רואה settings/admin
- [ ] חשבוניות (אם רלוונטי) מסוננות לאזור

### 5.3 — REGION_MANAGER
- [ ] רואה הכל ב-region שלו
- [ ] לא רואה אזורים אחרים
- [ ] תפריט: dashboard, projectsRegion, budgets, reports, map

### 5.4 — ORDER_COORDINATOR
- [ ] רואה רק פרויקטים ב-region שלו
- [ ] יש לו גישה למסך "תיאום הזמנות"
- [ ] רואה כל הסטטוסים כולל NEEDS_RE_COORDINATION
- [ ] יכול לבצע: send-to-supplier, approve, move-to-next-supplier

### 5.5 — ACCOUNTANT (עם area_id)
- [ ] רואה חשבוניות מהאזור שלו בלבד
- [ ] **בדיקה:** SQL — `SELECT COUNT(*) FROM invoices WHERE project_id IN (SELECT id FROM projects WHERE area_id = X)` משווה ל-מה שמופיע בUI
- [ ] גישה ל-AccountantInbox
- [ ] יכול לאשר Worklogs

### 5.6 — ACCOUNTANT (region-only, area_id=NULL)
- [ ] משתמש ספציפי עם `area_id=NULL` ו-`region_id` מוגדר
- [ ] רואה פרויקטים מכל האזורים ב-region שלו
- [ ] **בדיקה ב-Backend:** ניסיון לערוך פרויקט באזור אחר ב-region — מתקבל
- [ ] ניסיון לערוך באזור אחר (region אחר) — נחסם 403

### 5.7 — ADMIN
- [ ] רואה הכל
- [ ] גישה ל-Settings
- [ ] יכול לבצע admin override במסך הקליטה

### 5.8 — Permission strings (CRITICAL)
- [ ] DevTools → Console:
  ```js
  JSON.parse(localStorage.user).permissions
  ```
- [ ] **ציפייה:** strings ב-lowercase (`work_orders.read`, `worklogs.approve`)
- [ ] אם UPPERCASE — סימן שה-DB עוד לא יושר. עדיין צריך לעבוד בזכות case-insensitive `hasPermission`

✅ **Section 5 PASS** אם כל role רואה מה שצריך לראות, ולא יותר.

---

## 💰 6. חשבוניות

> **משך:** 15 דק'

### 6.1 — יצירת חשבונית (single)
- [ ] AccountantDashboard → 1 worklog APPROVED → checkbox → "צור חשבונית"
- [ ] **תוצאה:** "נוצרה 1 חשבונית בהצלחה" (לא הודעה ישנה)
- [ ] Worklog → INVOICED, Invoice → DRAFT

### 6.2 — יצירת חשבונית (multi groups)
- [ ] בחירת 4 worklogs: 2 מ-supplier A/project X, 2 מ-supplier B/project Y
- [ ] לחיצה "צור חשבונית"
- [ ] **ציפייה:** Confirm dialog: "הבחירה כוללת 2 צירופי ספק/פרויקט שונים. תיווצרנה 2 חשבוניות"
- [ ] OK → "נוצרו 2 חשבוניות בהצלחה"

### 6.3 — Worklog ללא ספק/פרויקט
- [ ] worklog ללא supplier_id (אם קיים בנתונים)
- [ ] בחירה + "צור חשבונית"
- [ ] **ציפייה:** alert מבלוק: "לא ניתן ליצור חשבונית — דיווחים ללא ספק/פרויקט: <numbers>"

### 6.4 — Scoping אזורי (CRITICAL)
- [ ] התחברות כ-AREA_MANAGER (area=X)
- [ ] /invoices
- [ ] **ציפייה:** רק חשבוניות מפרויקטים ב-area=X
- [ ] **השוואה ב-DB:**
  ```sql
  SELECT COUNT(*) FROM invoices i
  JOIN projects p ON p.id = i.project_id
  WHERE p.area_id = <X>;
  ```
  הספירה אמורה להתאים למה שמוצג ב-UI

### 6.5 — Scoping ל-ADMIN/ACCOUNTANT/REGION_MANAGER
- [ ] התחברות כ-ADMIN → רואה הכל
- [ ] התחברות כ-ACCOUNTANT → רואה הכל
- [ ] התחברות כ-REGION_MANAGER → רואה הכל

### 6.6 — Mark-paid עם payload מלא
- [ ] InvoiceDetail → "סמן שולם"
- [ ] **בדיקה:** עכשיו ה-`mark-paid` מקבל body — ב-DevTools Network תראה POST עם body
- [ ] **תוצאה ב-DB:**
  ```sql
  SELECT status, paid_amount, paid_at, paid_by, payment_method, payment_reference
  FROM invoices WHERE id = ?;
  ```
  - status=PAID
  - paid_at=current time (לא NULL)
  - paid_by=user_id

### 6.7 — Send to supplier
- [ ] /invoices/{id}/send (דרך כפתור "שלח לספק")
- [ ] **בדיקה DB:** sent_at מאוכלס

### 6.8 — Send invoice — TOAST תואם
- [ ] **שים לב:** הקוד עדיין אומר "נשלח לספק במייל" אבל ב-backend זה רק שינוי סטטוס. **הערה ל-Wave 3** — לא bug, אבל לא נכון.

✅ **Section 6 PASS** אם כל זרימת החשבונית עובדת + scoping אזורי.

---

## 🧪 7. בדיקות רגרסיה (5 דק')

### 7.1 — Login לכל role
- [ ] לכל אחד מ-7 ה-roles — login מצליח, /dashboard נפתח

### 7.2 — Dashboard endpoints
- [ ] לכל role — `/dashboard/*` נטען בלי 500

### 7.3 — Reports
- [ ] /reports נפתח לכל מי שיש לו `reports.read`

### 7.4 — Map
- [ ] מפה עובדת + שכבות (Google Hybrid + OpenWeather)

### 7.5 — Notifications
- [ ] פעמון מעדכן notifications ב-real-time

---

## 🚨 אם משהו נכשל — protocol

1. **תפסיק מיד.** אל תמשיך לבדיקה הבאה.
2. **תרשום בדיוק:**
   - מה ניסית לעשות (steps)
   - מה ראית (screenshot של מסך + console + Network tab)
   - מה היית מצפה לראות
   - איזה role היית מחובר אליו
3. **תבדוק ב-DB** את המצב שאחרי הכישלון — לפעמים הפעולה הצליחה חלקית
4. **תשלח לי** עם המידע המלא

אני אעבור על הבעיה, אתקן, ואמשיך אחרי שהבדיקה עוברת.

---

## ✅ סיום בדיקות — אחרי שהכל עובר

- [ ] Section 1 — Flow מלא ✅
- [ ] Section 2 — 3 תרחישי קליטה ✅
- [ ] Section 3 — NEEDS_RE_COORDINATION ✅
- [ ] Section 4 — Multi-WO creation ✅
- [ ] Section 5 — Permissions ✅
- [ ] Section 6 — חשבוניות ✅
- [ ] Section 7 — רגרסיה ✅

**רק אז** — אישור עיני לעבור לגל 3.

---

## 📊 סיכום לדיווח אחרי הבדיקות

תכין לי דיווח קצר במבנה הזה:

```
✅ עברו: 7/7 sections, 53/53 בדיקות
❌ נכשל: <תיאור>
⚠️ הערות: <דברים שנראו מוזרים אבל לא בלוקרים>

מצב לחזור לעבודה: כן / לא
```

---

> **כלי עזר:** אם רוצה checklist מודפס — הוסף `--print-friendly` ל-renderer.
> **משך כולל מוערך:** ~90 דקות לבדיקה יסודית.
