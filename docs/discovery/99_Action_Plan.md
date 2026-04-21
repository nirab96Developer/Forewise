# Forewise — תוכנית פעולה מסודרת

> **מבוסס על:** מסמכי Discovery 01–08 + Executive Summary.
> **עיקרון:** קודם אפיון והחלטות עסקיות → אחר כך קוד.
> **גישה:** 4 גלים, מהקריטי לפיצ'רים.

---

## ⚠️ לפני הכל — החלטות עסקיות שחייבות לקרות

אי אפשר להתחיל קוד לפני שיש תשובות לשאלות הבאות. **אלה לא שאלות טכניות — אלה שאלות לבעלי המוצר/הארגון:**

### א. שאלות יסוד

| # | שאלה | חשיבות |
|---|---|---|
| Q1 | האם הזמנה היא לכלי **בודד** או לכמות (`quantity`)? אם כמות — האם WOs מרובים? | 🔴 חוסם תיקון בסיסי |
| Q2 | האם `priority=HIGH/URGENT` נדרש בטופס? איך זה משפיע על rotation/SLA? | 🟡 |
| Q3 | האם 9 שעות נטו תמיד? יש סוגי כלים עם שעות אחרות? | 🟡 |
| Q4 | תוקף Token לספק (כרגע 3 שעות) — האם להאריך לסופ"ש? | 🟡 |
| Q5 | במצב `wrong_type` — האם WO צריך לחזור אוטומטית למתאם? איזה סטטוס? | 🔴 |
| Q6 | האם Email ב-`send invoice to supplier` הוא חובה (אוטומטי) או ידני? | 🟡 |
| Q7 | Region-only Accountant (בלי area) — תרחיש קיים? | 🟢 |
| Q8 | SMS לספקים — להחזיר לפיתוח או להוריד מתיעוד? | 🟢 |
| Q9 | Self-approval חוקים — איפה עוד נדרשת הגנה? | 🟡 |
| Q10 | האם לאחד את שני מסלולי קליטת הכלי, או להשאיר 2 UX? | 🔴 |

---

## 🌊 גל 1 — Hot Fixes (שבוע 1-2)

**מטרה:** לסגור באגים שעלולים להזיק לדאטה / להפיל flow.

| # | תיקון | קובץ | סוג | סיכון |
|---|---|---|---|---|
| F1.1 | תיקון `update_rotation_after_rejection` — לעדכן את הספק הדוחה, לא את הבא בתור | `supplier_portal.py:528-541` | קוד | 🔴 |
| F1.2 | תיקון `AccountantDashboard.tsx:130` — להוסיף `supplier_id`, `project_id` בקריאה | `AccountantDashboard.tsx` | קוד | 🔴 |
| F1.3 | יישור Frontend permissions לסגנון lowercase של Backend (או הפוך) | `permissions.ts` + DB | קוד + DB | 🔴 |
| F1.4 | תיקון `check_project_access` — לזרוק 403 במקרי כשל | `dependencies.py:338-375` | קוד | 🔴 |
| F1.5 | הוספת ולידציה: `approve` של WO חייב `equipment_id` | `work_order_service.py:1020` | קוד | 🟡 |
| F1.6 | trim/normalize ל-license plate (להסיר רווחים, אחיד) | `work_orders.py:1037` | קוד | 🟢 |
| F1.7 | יישור הסטטוסים — להוסיף `IN_PROGRESS`, `ACTIVE` ל-`WO_LABELS` ול-`WO_TRANSITIONS` | `core/enums.py` | קוד | 🟡 |
| F1.8 | אחידות sortof error message ב-`mark-paid` להוסיף `paid_at` | `routers/invoices.py:585-601` + `models/invoice.py` | קוד + DB migration | 🟡 |

**Definition of Done לגל 1:**
- [ ] כל הבאגים נפתרו ב-PR נפרד עם בדיקות
- [ ] Pytest מלא עובר
- [ ] Smoke test ידני על Production-like
- [ ] תיעוד בעברית במסמך הזה

---

## 🌊 גל 2 — Consistency & Hardening (שבוע 3-5)

**מטרה:** ליישר drift, להחזיר אכיפה מרכזית.

| # | משימה | היקף |
|---|---|---|
| F2.1 | אכיפת `validate_wo_transition` בכל עדכון סטטוס בקוד | מעבר על `work_order_service.py` כולו + רישום middleware |
| F2.2 | יצירת DB seeds מסודרים: `roles`, `permissions`, `role_permissions`, `work_order_statuses`, `worklog_statuses` | קובץ Python מקור Source-of-Truth |
| F2.3 | ייצוא מטריצת `role × permission` ל-CSV מתעדכן + השוואה ל-DB | סקריפט CI |
| F2.4 | יישור Invoice statuses בין 4 מקומות | enum + schema + frontend + migration |
| F2.5 | תיקון `WorklogResponse` — להוסיף `is_standard`, `non_standard_reason` | schema + tests |
| F2.6 | שמירת `rejection_reason` ב-Worklog בעת `reject` | service |
| F2.7 | יצירת FK חסרים ב-`invoices` (supplier_id, project_id, created_by) | DB migration |
| F2.8 | Scoping אזורי לחשבוניות — להוסיף `area_id` ב-`InvoiceService.list` | service |
| F2.9 | טיפול ב-`Region-only Accountant` (אם Q7 = כן) | `scope.py` |
| F2.10 | הוספת Region/Area scoping ל-VIEWER/SUPPLIER (אם רלוונטי) | `projects.py` list |
| F2.11 | הוספת `RoleCode` enum: ORDER_COORDINATOR, FIELD_WORKER, SUPER_ADMIN, SUPPLIER_MANAGER | `models/role.py` |

---

## 🌊 גל 3 — UX Unification (שבוע 6-8)

**מטרה:** אחידות ב-UI לפי החלטות עסקיות מ-Q10.

| # | משימה | תלוי ב |
|---|---|---|
| F3.1 | איחוד 2 מסלולי Equipment Intake ל-1 (לפי Q10) | החלטה |
| F3.2 | החזרת WO לסטטוס מתאם בעת `wrong_type` (אם Q5 = אוטו) | החלטה |
| F3.3 | סנכרון רשימת סיבות דחייה בפורטל מ-DB (לא hardcoded) | endpoint + UI |
| F3.4 | תיקון tooltip "נשלח במייל" שיתאים למימוש | UI או הוספת email |
| F3.5 | הוספת רענון ידני ב-OrderCoordination | UI |
| F3.6 | הוספת UI לסטטוסים החדשים (IN_PROGRESS, ACTIVE) — צבעים, אייקונים | `statusTranslation.ts` |
| F3.7 | תיקון תצוגת VIEWER (כיום מוצג כ"מנהל מרחב") | `permissions.ts` |
| F3.8 | הוספת sort/filter עמודות במסך מתאם | UI |

---

## 🌊 גל 4 — Features & Cleanup (חודש 2-3)

**מטרה:** השלמות פיצ'רים שתועדו אך לא מומשו.

| # | משימה | תלוי ב |
|---|---|---|
| F4.1 | מימוש HTTP endpoint ל-`force_supplier` | מקיים אם רלוונטי |
| F4.2 | מימוש מלא של `resend_to_supplier` (כיום stub) | |
| F4.3 | החזרת SMS לספקים (אם Q8 = כן) | |
| F4.4 | החלפת Rate Limiter ל-Redis (במקום in-memory) | תשתית |
| F4.5 | מימוש `from-work-order` invoice עם חישוב אמיתי | |
| F4.6 | תיקון/מחיקת `get_uninvoiced_suppliers` (שם מטעה) | |
| F4.7 | הוספת Email אוטומטי בכל זרימה רלוונטית (לפי Q6) | |
| F4.8 | סדר routes — `/uninvoiced-suppliers` לפני `/{invoice_id}` | refactor |
| F4.9 | Email טמפלטים — מאוחדים, RTL, עם logo | UI/Email |
| F4.10 | Audit log מקיף לכל מעבר סטטוס | middleware |

---

## 📋 לוח Kanban מוצע

| To Do | In Progress | Done |
|---|---|---|
| 10 שאלות עסקיות | — | Discovery 8/8 |
| גל 1 (8 fixes) | | |
| גל 2 (11 fixes) | | |
| גל 3 (8 fixes) | | |
| גל 4 (10 fixes) | | |

**סך הכל ~37 משימות מסודרות, 4 גלים, אסטרטגיה ברורה מקריטי לפיצ'רי.**

---

## 🎯 מה אני ממליץ לעשות עכשיו (היום)

### צעד 1 — שלח את 10 השאלות לבעלי המוצר
**אסור לכתוב קוד לפני שיש תשובות**. השאלות הקריטיות:
- Q1, Q5, Q10 — חוסמים תיקונים בגל 1

### צעד 2 — הקפאת המאגרים
- אל תוסיף features חדשים עד שגל 1 מסתיים
- כל באג חדש שנמצא — נוסף לרשימה, לא מתוקן באד-הוק

### צעד 3 — צוות / Owner לכל גל
- גל 1: Backend dev + QA (שבוע 1-2)
- גל 2: Backend lead + DBA (שבוע 3-5)
- גל 3: Frontend + UX (שבוע 6-8)
- גל 4: Full team (חודש 2-3)

### צעד 4 — בקרה
- Daily standup מצב גל
- Weekly demo של תיקונים
- מעבר לגל הבא רק אחרי DoD מלא

---

## ❌ מה לא לעשות

1. **לא לתקן באד-הוק** — כל תיקון עובר את הגלים
2. **לא להוסיף features** עד שהבסיס יציב
3. **לא לעבוד בלי החלטות עסקיות** — להחזיק את הקוד עד שיש תשובה
4. **לא להחליף DB schema** בלי migration נפרדת + plan rollback
5. **לא לעשות big-bang refactor** — כל גל עובר בנפרד

---

**מסמך זה הוא הצעה. כל החלטה סופית — של בעלי המוצר.**
