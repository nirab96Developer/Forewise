# Phase 3 Wave 1.2 — work_orders Frontend Recon

**תאריך**: 2026-04-26
**מטרה**: למפות איזה role רואה מה במסכי work_orders, לפני שכותבים `WorkOrderScopeStrategy`.

---

## 1. מסכי frontend שמשתמשים ב-work_orders

| Screen | קובץ | endpoint נקרא | Route guard (frontend) |
|---|---|---|---|
| **Work Orders list** | `pages/WorkOrders/WorkOrders.tsx` | `GET /work-orders?...filters` | `WORK_ORDERS_VIEW` |
| **Work Order detail** | `pages/WorkOrders/WorkOrderDetail.tsx` | `GET /work-orders/{id}` | `WORK_ORDERS_VIEW` |
| **New work order** | `pages/WorkOrders/NewWorkOrder.tsx` | `POST /work-orders` + `/preview-allocation` | `WORK_ORDERS_CREATE` |
| **Edit work order** | `pages/WorkOrders/EditWorkOrder.tsx` | `GET` then `PATCH /work-orders/{id}` | `WORK_ORDERS_UPDATE` |
| **Order Coordination** (queue) | `pages/WorkOrders/OrderCoordination.tsx` | `GET /work-orders?status=...` × 6 statuses + actions (`approve`, `reject`, `send-to-supplier`, `move-to-next-supplier`, `cancel`, `delete`) | `WORK_ORDERS_COORDINATE` |
| **Project workspace WOs** | `pages/Projects/ProjectWorkspaceNew.tsx` | `GET /work-orders?project_id=N` | `WORK_ORDERS_VIEW` |
| **Worklog form** | `pages/WorkLogs/WorklogFormUnified.tsx` | needs WO context | `WORKLOGS_CREATE` |
| **Accountant inbox** | `pages/WorkLogs/AccountantInbox.tsx` | shows WOs via worklog join | (Accountant role) |
| **Equipment scan** | `pages/Equipment/EquipmentScan.tsx` | `POST /work-orders/{id}/scan-equipment` | (Supplier scans in field) |
| **My Journal** | `pages/Journal/MyJournal.tsx` | `GET /work-orders` calendar shape | `JOURNAL_VIEW` |
| **Coordinator Dashboard** | `pages/Dashboard/OrderCoordinatorDashboard.tsx` | dashboard endpoints | `DASHBOARD_VIEW` |
| **Default Dashboard** | `pages/Dashboard/DefaultDashboard.tsx` | dashboard summary | `DASHBOARD_VIEW` |
| **Invoices** | `pages/Invoices/Invoices.tsx` | shows WO names via lookup | `INVOICES_VIEW` |
| **Budget Detail** | `pages/Settings/BudgetDetail.tsx` | committed/spent endpoints | `BUDGETS_VIEW` |
| **Activity Log** | `pages/ActivityLog/ActivityLogNew.tsx` | reads activity rows that link to WOs | `ACTIVITY_LOGS_VIEW` |
| **Equipment requests** | `pages/Equipment/EquipmentRequestsStatus.tsx` | calls `/work-orders` | (any auth) |
| **Supplier Portal** | `pages/SupplierPortal/SupplierPortal.tsx` | uses `/api/v1/supplier-portal/{token}/...` — **NOT** `/work-orders` directly | (token-based, no role) |

**13 מסכים פעילים**, **3 endpoints מרכזיים** של work_orders משמשים: `GET /` (list), `GET /{id}` (detail), והפעולות.

---

## 2. Role × Endpoint × Frontend matrix

| Role | מסכים שרואה | endpoint שנקרא | Scope **בקוד** היום | Scope **רצוי** (לפי המסך) | פער |
|---|---|---|---|---|---|
| **ADMIN** | הכל | list + detail + actions | אם יש לאדמין `area_id` → מסונן לarea ❌ | רואה הכל בלי שום סינון | 🔴 admin עם area_id מקבל view חלקי |
| **REGION_MANAGER** | list + detail + dashboard | list + detail | מסונן לפי `area_id` שלו, אבל REGION_MANAGER הוא role ברמת **מרחב** ולא אזור | scope לפי `region_id` (כל הWOs במרחב, לא רק area אחד) | 🔴 קריטי — Region Manager לא רואה את כל המרחב שלו |
| **AREA_MANAGER** | list + detail + dashboard | list + detail | מסונן לפי `area_id` ✅ | אותו | ✅ אין פער |
| **WORK_MANAGER** | list (פילטר project) + detail + create + edit + project workspace | list + detail + create | בlist: מסונן לפי `area_id` (אם יש). בdetail: רואה הכל ❌ | רק WOs של פרויקטים שמוקצים אליו (`project_assignments`) | 🔴 קריטי — מנהל עבודה רואה כל WO, גם של פרויקטים שלא שלו |
| **ORDER_COORDINATOR** | OrderCoordination queue + list + detail + dashboard | list × 6 statuses + actions (`approve`/`reject`/`send`/`cancel`/`delete`) | global (אין filter ב-detail; בlist גם global אם אין area_id) | global — מתאם רואה הכל לפי הגדרה | ✅ אין פער |
| **ACCOUNTANT** | Accountant Inbox + Invoices view (WOs דרך worklog) | reads WOs לקריאה בלבד | global (אין filter) | global או מסונן לפי area/region לפי שיוך | 🟡 פוטנציאלי — אם יש מנהלת חשבונות מוקצית לאזור, אולי לא צריכה לראות הכל |
| **SUPPLIER** | SupplierPortal דרך token (לא דרך `/work-orders`) | `GET /supplier-portal/{token}` | בקוד: מסונן לפי `area_id` שלא קיים לספק → תמיד ריק | אין צורך — ספק לא משתמש ב`/work-orders` ישירות, רק בportal | ✅ ספק לא יגיע ל-`/work-orders` בכלל ב-UI; backend עדיין דולף 200/404 שגוי אם יקרא |

---

## 3. List vs Detail mismatch — האימות

המקרים הבאים מציגים **שתי לוגיקות שונות** לאותה ישות:

| Scenario | List | Detail | תוצאה ל-user |
|---|---|---|---|
| ADMIN שיש לו `area_id=10` (לדוגמה אדמין שמקבל גם ניהול אזור) | רואה רק WOs של area 10 | רואה כל WO שמזהה (גם out-of-area) | אדמין לא רואה ברשימה את WO-X אבל יכול לקרוא לו ישירות → "מאיפה זה הופיע?" |
| WORK_MANAGER עם `area_id=10` | רואה רק area 10 | רואה כל WO שמזהה | מנהל עבודה לא רואה ברשימה אבל יכול לפתוח URL ישירות → דליפת מידע |
| REGION_MANAGER עם `region_id=5, area_id=NULL` | רואה את כל ה-WOs (אין area filter) | אם בעתיד נוסיף region filter — מסונן | יציאה מסונכרון בעתיד |

**זו הבעיה המרכזית** — ה-frontend מציג רשימה לפי לוגיקה אחת, ה-detail עובד לפי לוגיקה אחרת. כל מאמץ scope לא יעיל אם הוא לא עקבי.

---

## 4. הצעת policy אחידה ל-work_orders

לפי המסכים שמוצגים בפרונט, כל role צריך:

| Role | Read scope (list + detail זהה) | Mutation perms |
|---|---|---|
| ADMIN | ALL | full |
| ORDER_COORDINATOR | ALL | approve/reject/send/cancel/distribute (ללא delete) |
| REGION_MANAGER | `WO.project.region_id == user.region_id` | read + update + close |
| AREA_MANAGER | `WO.project.area_id == user.area_id` | read + update |
| WORK_MANAGER | `WO.project_id IN (user's project_assignments)` | read + create + update WO של הפרויקטים שלו |
| ACCOUNTANT | ALL (read-only) — דרך worklog→WO | read בלבד |
| SUPPLIER | אסור ב-`/work-orders` (משתמש רק ב-portal) | none |

---

## 5. סיכונים בכל שינוי policy

| שינוי | מי שובר |
|---|---|
| ADMIN לא יסונן לפי area_id | אם יש admin שמקבל area_id במקרה — אין כזה ב-prod, בטוח |
| REGION_MANAGER יקבל region_id filter במקום area_id | הקוד הנוכחי רץ על area_id; חייבים לוודא של-region managers יש `region_id` ב-DB |
| WORK_MANAGER יסונן לפי project_assignments | יבטל גישה ל-WOs במצבים שWORK_MANAGER עוזר לשלם בפרויקט שלא מוקצה אליו רשמית. לבדוק שיש project_assignment לכל work_manager |
| SUPPLIER → 403 על `/work-orders` | ייתכן שבportal יש fallback fetch ל-`/work-orders/{id}` שיישבר. ל-recon |

---

## 6. ההמלצה

**Option C.1 — לוודא בDB ובfrontend לפני שינוי policy**:
1. לבדוק ש-REGION_MANAGER ב-prod עם region_id מוגדר (נדגום ב-DB)
2. לבדוק ש-WORK_MANAGER יש project_assignments פעיל (נדגום ב-DB)
3. לבדוק שsupplier portal **לא** קורא ל-`/work-orders/{id}` ישירות
4. רק אז לכתוב WorkOrderScopeStrategy לפי הטבלה ב-§4
5. tests מקיפים לכל role × scenario

**זמן משוער**: 2 שעות (1 שעה DB checks + 1 שעה strategy + tests).

**סיכון**: בינוני — רוב התפקידים יראו אותו דבר או יותר ממה שראו (REGION_MANAGER יקבל יותר WOs, WORK_MANAGER יקבל פחות אבל רק את שלו).

---

## ממתין לאישור Option C.1, או אופציה אחרת
