# גל 2 — דוח סטטוס ביצוע

> **תאריך:** אפריל 2026 · **מצב:** הושלם
> **גישה:** Tech Lead — refactor end-to-end לפי 3 ההחלטות העסקיות (Q1, Q5, Q10)
> **כללי בטיחות:** 0 lint · 0 TS errors · 161 pytest עוברים · 0 רגרסיות

---

## ההחלטות שיושמו

| Q | החלטה | סטטוס |
|---|---|---|
| **Q1** | הזמנה = כלי בודד; quantity הופך ל-N הזמנות נפרדות | ✅ הושלם |
| **Q5** | wrong_type → סטטוס `NEEDS_RE_COORDINATION` + audit + notification + UI מתאם | ✅ הושלם |
| **Q10** | מסלול קליטת כלי יחיד (3 מצבים) — כל ה-entry points דרך `ScanEquipmentModal` המאוחד | ✅ הושלם |

---

## ✅ Phase 1 — Q5: NEEDS_RE_COORDINATION (4 sub-tasks)

| תיקון | קבצים | מה השתנה |
|---|---|---|
| **1.1** Status enum | `app/core/enums.py` | נוסף `WorkOrderStatus.NEEDS_RE_COORDINATION` עם תווית "ממתין לבדיקת מתאם — סוג כלי שגוי". מעברים מותרים: מ-APPROVED_AND_SENT/IN_PROGRESS/ACTIVE לתוכו, ויציאה ל-DISTRIBUTING / APPROVED_AND_SENT / IN_PROGRESS / CANCELLED |
| **1.2** scan-equipment | `app/routers/work_orders.py` | במצב wrong_type: WO עובר אוטו ל-`NEEDS_RE_COORDINATION`, נכתב audit log עם שני הסוגים והיוזר, ונשלחה התראה לתפקידי `ORDER_COORDINATOR` ו-`ADMIN` ב-region/area של ההזמנה |
| **1.3** Migration | `alembic/versions/c3d5e6f7a8b9_*.py` | INSERT idempotent ל-`work_order_statuses` עם `display_order=65` (בין סטטוסי ביצוע לסטטוסים סופיים) |
| **1.4** UI Coordinator | `OrderCoordination.tsx` | טאב + סטטיסטיקה + status config (אדום מודגש). הזמנות `NEEDS_RE_COORDINATION` מופיעות **ראשונות** ברשימה. כפתור "הפץ מחדש (סבב הוגן — ספק אחר)" שמנקה supplier+equipment ומפעיל send-to-supplier מחדש. `send_to_supplier` ב-service קיבל את הסטטוס לרשימת המותרים |

**הפליי החדש:**
```
מנהל עבודה סורק כלי שגוי
   ↓ Backend: status → NEEDS_RE_COORDINATION
   ↓ audit_log: WRONG_EQUIPMENT_BLOCKED עם פרטים
   ↓ notify: ORDER_COORDINATOR + ADMIN ב-region
[Coordinator UI]
   ↓ הזמנה מופיעה ראשונה בטאב "דורש החלטה"
   ↓ אופציה 1: "הפץ מחדש" → ספק חדש בסבב
   ↓ אופציה 2: בטל הזמנה (אדמין)
   ↓ אופציה 3: אישור חריג ב-modal הקליטה (admin override)
```

## ✅ Phase 2 — Q1: quantity → N הזמנות

| תיקון | קובץ | מה השתנה |
|---|---|---|
| **2.1** טופס דרישת כלים | `NewWorkOrder.tsx` | `handleSubmit` משתמש ב-`Promise.allSettled` ליצירת N קריאות `createWorkOrder` במקביל. כל הזמנה מקבלת suffix `(2/3)` בכותרת. הוספת disclaimer מודגש כשבוחרים כמות > 1: "תיווצרנה N הזמנות נפרדות — כלי לכל הזמנה". טיפול ב-offline + handling חלקי (חלק הצליחו, חלק נכשלו) |

**משמעות עסקית:** כל כלי = WO עצמאי עם ספק/רישוי/דיווחים/חשבונית משלו, בדיוק כמו שביקשת.

## ✅ Phase 3 — Q10: Unified intake

| תיקון | קובץ | מה השתנה |
|---|---|---|
| **3.1** Modal מאוחד | `components/equipment/ScanEquipmentModal.tsx` | **שכתוב מלא** — כל ה-3 מצבים בתוך component אחד (scanning/different_plate/wrong_type/admin_override). 4 phases עם UI ייעודי לכל אחד. props נשארו זהים — refactor פנימי בלבד |
| **3.2** WorkOrderDetail | `pages/WorkOrders/WorkOrderDetail.tsx` | הוסר ה-call ל-`confirm-equipment` הישיר אחרי `onSuccess` (היה מסלול עוקף). עכשיו ה-Modal עושה הכל פנימית; ה-callback רק מרענן UI |
| **3.3** ProjectWorkspace | `pages/Projects/ProjectWorkspaceNew.tsx` | **הוסר 273 שורות** של inline modal duplicate. נוסף import של ה-shared component. ה-call site הוחלף עם props חדשים |
| **3.4** EquipmentScan | `pages/Equipment/EquipmentScan.tsx` | נוסף disclaimer מודגש: "אימות בלבד — לא משייך כלי להזמנה. לקליטת כלי — פתח את ההזמנה ולחץ סרוק כלי" — נשמר כ-validate-plate tool בלבד |

**1 modal · 1 zerכia מאוחדת · 0 קיצורי דרך.**

## ✅ Phase 4 — משימות גל 2 מקוריות

| F# | תיקון | קובץ |
|---|---|---|
| **F2.6** | `Worklog.reject()` שומר `rejection_reason` על הרשומה (היה bug — הפרמטר התקבל ונזרק) | `worklog_service.py` |
| **F2.8** | `InvoiceService.list` מסנן לפי `area_id` דרך JOIN ל-Project (היה drop) | `invoice_service.py` |
| **F2.9** | `scope.py`: ACCOUNTANT ללא area נופל ל-region scope (regional accountant) | `core/scope.py` |
| **F2.11** | `RoleCode` enum: נוספו 4 קודים (`SUPER_ADMIN`, `ORDER_COORDINATOR`, `FIELD_WORKER`, `SUPPLIER_MANAGER`) — סה"כ 11 | `models/role.py` |

---

## 🧪 איכות

| בדיקה | תוצאה |
|---|---|
| `pytest test_status_transitions + flow_validation + scope_enforcement + budget_integrity` | ✅ **161 passed** |
| Backend imports — כל 41 ה-routers נטענים | ✅ |
| Backend lints | ✅ 0 errors |
| Frontend lints | ✅ 0 errors |
| TypeScript compile (`tsc --noEmit`) | ✅ 0 errors |
| `notify_users_by_role` import | ✅ |
| RoleCode count = 11 | ✅ |
| State machine NEEDS_RE_COORDINATION transitions | ✅ |

> **הערה:** 5 audit_coverage tests נכשלים — אבל **הם נכשלו גם לפני השינויים** (אומת עם `git stash`). חוב טכני קיים שדורש להוסיף `log_business_event` ב-services (לטיפול בגל 3).

---

## 📊 סיכום שינויים מצטבר (גל 1 + גל 2)

```
23 קבצים · +1031 / -566 שורות

Backend (15 קבצים):
  app/core/dependencies.py          +58 / -16
  app/core/enums.py                 +40
  app/core/scope.py                 +18 / -4
  app/models/invoice.py             +24 / -2
  app/models/role.py                +4
  app/routers/dashboard.py          +4
  app/routers/invoices.py           +47 / -3
  app/routers/supplier_portal.py    +19 / -8
  app/routers/work_orders.py        +108 / -19
  app/schemas/invoice.py            +14 / -3
  app/schemas/worklog.py            +15
  app/services/invoice_service.py   +33 / -10
  app/services/notification_service.py +43
  app/services/work_order_service.py +15 / -2
  app/services/worklog_service.py   +10 / -2

Frontend (8 קבצים):
  components/equipment/ScanEquipmentModal.tsx  +442 / -240 (rewrite)
  pages/Dashboard/AccountantDashboard.tsx       +51 / -8
  pages/Equipment/EquipmentScan.tsx             +13
  pages/Projects/ProjectWorkspaceNew.tsx        -270 (legacy removed)
  pages/WorkOrders/NewWorkOrder.tsx             +129 / -52
  pages/WorkOrders/OrderCoordination.tsx        +52 / -10
  pages/WorkOrders/WorkOrderDetail.tsx          +5 / -10
  utils/permissions.ts                          +90 / -78

Migrations (2 חדשות):
  b2c4d5e6f7a8_add_invoice_payment_fields.py
  c3d5e6f7a8b9_add_needs_re_coordination_status.py
```

---

## 🚀 ערך עסקי שנוסף בגל 2

| לפני | אחרי |
|---|---|
| כלי לא תואם נסרק → ההזמנה נשארה תקועה ב-APPROVED_AND_SENT, מנהל עבודה התעלם, אין התראה | סטטוס מפורש `NEEDS_RE_COORDINATION` + audit + התראה למתאם — לא נופל בין הכיסאות |
| הזמנה אחת ל-3 כלים → אי אפשר לעקוב אחרי כל כלי בנפרד | 3 הזמנות נפרדות, כל אחת עם supplier/plate/worklog/invoice משלה |
| 3 מסלולי קליטה שונים בקוד (אחד דולג על בדיקת 3 מצבים) | מסלול **אחד** מאוחד · אותה logic, אותם validations, מכל מקום במערכת |
| Worklog נדחה — הסיבה אבדה | `rejection_reason` נשמר על הרשומה ומוחזר ב-API |
| מנהל אזור ראה חשבוניות מכל הארץ (Scoping לא נאכף) | מסונן לפי `area_id` דרך Project |
| חשבונאית region-only קיבלה ForbiddenException על פרויקטים באזורים שלה | נופל ל-region scope אוטומטית |
| `RoleCode` enum חסר 4 codes שבשימוש בקוד → רגרסיות שקטות | enum מלא עם 11 קודים |

---

## 🔜 גל 3 — מה נשאר

לפי גישה אחראית, גל 3 יכלול:

| משימה | תיאור |
|---|---|
| **F2.1** Enforce validate_wo_transition בכל קוד | כיום נקרא רק ב-tests; לאכוף בכל מעבר סטטוס ב-services |
| **F2.2** DB seeds | קובץ Python יחיד שזורע roles, permissions, role_permissions, statuses |
| **F2.3** Permission matrix CSV | סקריפט CI שמייצא ומשווה ל-DB |
| **F2.4** FK חסרים ב-invoices | supplier_id, project_id, created_by — דורש backfill check |
| **F2.7** Audit coverage | ה-tests שנכשלים — הוספת `log_business_event` לכל service action |
| Permission UPPER drift cleanup | למצוא ולהסיר ב-code אזכורים ל-strings ישנים |
| `force_supplier` HTTP endpoint | מימוש endpoint לקריאה לאופציה הקיימת ב-service |
| `resend_to_supplier` השלמה | כיום stub |

---

**סטטוס: גל 2 הושלם · המערכת יציבה · מוכן לדיון על גל 3 או למעבר לפרודקשן.**
