# Forewise — סיכום מנהלים של ה-Discovery

> **מצב:** Discovery בלבד · אין שינויי קוד · 8 נושאים נסקרו מה-codebase האמיתי.
> **תאריך:** אפריל 2026.

---

## 1. מסמכי הסקירה

| # | נושא | קובץ |
|---|---|---|
| 1 | Work Order Template | `01_WorkOrder_Template.md` |
| 2 | Equipment Intake (קליטת כלי) | `02_Equipment_Intake.md` |
| 3 | Worklog Template (דיווח שעות) | `03_Worklog_Template.md` |
| 4 | Coordinator Screen (מתאם הזמנות) | `04_Coordinator_Screen.md` |
| 5 | Supplier Portal (פורטל ספק) | `05_Supplier_Portal.md` |
| 6 | Accounting / Invoice (חשבונאות) | `06_Accounting_Invoice.md` |
| 7 | Status Table (טבלת סטטוסים) | `07_Status_Table.md` |
| 8 | Permissions Matrix (הרשאות) | `08_Permissions_Matrix.md` |
| ⭐ | **Action Plan** | `99_Action_Plan.md` |

---

## 2. הזרימה המרכזית — End-to-End (Source of Truth: הקוד)

```
[מנהל עבודה]
   ↓ דרישת כלים (NewWorkOrder.tsx)
[WorkOrder: PENDING] + freeze budget + portal_token
   ↓ מתאם — send-to-supplier
[WorkOrder: DISTRIBUTING] + email לספק
   ↓ ספק - פורטל - accept
[WorkOrder: SUPPLIER_ACCEPTED_PENDING_COORDINATOR] + equipment_id+plate
   ↓ מתאם — approve
[WorkOrder: APPROVED_AND_SENT] + 3 emails
   ↓ מנהל עבודה — סורק כלי בשטח (3 מצבים)
[WorkOrder: IN_PROGRESS]
   ↓ מנהל עבודה — דיווח שעות
[Worklog: PENDING → SUBMITTED]
   ↓ אקאונטנט/אזור — approve
[Worklog: APPROVED] ← זה ה"צבוע" + budget update
   ↓ אקאונטנט — generate-monthly או from-worklogs
[Invoice: DRAFT] + Worklog: INVOICED
   ↓ approve → SENT (status only) → mark-paid
[Invoice: PAID]
```

---

## 3. דירוג חומרה של הממצאים

### 🔴 קריטי — חוסם flow או אבטחה

| # | בעיה | נושא | קובץ:שורה |
|---|---|---|---|
| C1 | **שני מסלולי קליטת ציוד** — `WorkOrderDetail` דולג על בדיקת 3 מצבים | 2 | `WorkOrderDetail.tsx`, `ScanEquipmentModal.tsx` |
| C2 | **`approve` לא מוודא `equipment_id` קיים** למרות docstring | 4 | `work_order_service.py:1020` |
| C3 | **`update_rotation_after_rejection` עלול לעדכן ספק שגוי** | 4, 5 | `supplier_portal.py:528-541` |
| C4 | **`AccountantDashboard from-worklogs` שולח קריאה שבורה** | 6 | `AccountantDashboard.tsx:130-145` |
| C5 | **Frontend שולח permissions UPPERCASE** מול Backend lowercase — non-admins נכשלים | 8 | `permissions.ts` ↔ routers |
| C6 | **Invoice scoping לא נאכף בפועל** — ה-service מתעלם מ-area_id | 6, 8 | `invoice_service.py:list` |
| C7 | **`check_project_access` לא זורק חריגה** במקרי כשל | 8 | `dependencies.py:338-375` |

### 🟡 גבוה — נכון לוגית אבל drift מסכן

| # | בעיה | נושא |
|---|---|---|
| H1 | `IN_PROGRESS` ו-`ACTIVE` בשימוש אך לא ב-`WO_TRANSITIONS` enum | 7 |
| H2 | `validate_*_transition` לא נאכף ב-runtime — רק בטסטים | 7 |
| H3 | `quantity` בטופס WO מוזן (1-5) **אבל לא נשמר** במודל | 1 |
| H4 | `priority` קבוע `medium` — אין HIGH/URGENT דרך הטופס | 1 |
| H5 | `wrong_type` לא מחזיר WO לסטטוס מתאם — נשאר תקוע | 2 |
| H6 | `reject_reason` עובר ל-service אבל לא נשמר ב-Worklog | 3 |
| H7 | `WorklogResponse` חסרים `is_standard`, `non_standard_reason` | 3 |
| H8 | רשימת סיבות דחייה בפורטל **hardcoded** במקום מ-DB | 5 |
| H9 | `mark-paid` לא שומר `paid_at`, `payment_method`, `payment_reference` | 6 |
| H10 | `POST /invoices/{id}/send` לא שולח email — רק שינוי סטטוס | 6 |
| H11 | `RoleCode` enum חסר 4 codes שבשימוש (ORDER_COORDINATOR, FIELD_WORKER, SUPER_ADMIN, SUPPLIER_MANAGER) | 8 |
| H12 | אין FK ב-DB ל-Invoice → supplier/project/created_by | 6 |
| H13 | `force_supplier` ב-service אך אין HTTP endpoint | 4 |
| H14 | `resend_to_supplier` הוא stub — לא עושה כלום | 4 |

### 🟢 בינוני — לטיפול אבל לא דחוף

| # | בעיה | נושא |
|---|---|---|
| M1 | אי-עקביות case ב-license plate (אין trim/upper) | 2 |
| M2 | `wrong_type` יורה גם כשהכלי לא קיים (לא רק mismatch) | 2 |
| M3 | `Worklog.approve` מקבל גם מ-PENDING (דילוג על SUBMITTED) | 3 |
| M4 | מסך `OrderCoordination` ללא רענון בלחיצה (רק auto-30s) | 4 |
| M5 | טקסט `is_forced_selection` ב-UI לא נשלח לפעמים — bug? | 4 |
| M6 | `/supplier-portal/{token}/status` endpoint יתום | 5 |
| M7 | Rate limiter in-memory — לא מסונכרן בין workers | 5 |
| M8 | `from-work-order` invoice הוא stub (`total_amount=0`) | 6 |
| M9 | `get_uninvoiced_suppliers` שם מטעה — לא מסנן INVOICED | 6 |
| M10 | סדר routes: `/uninvoiced-suppliers` עלול לטעון `/{invoice_id}` | 6 |
| M11 | `Invoice.PENDING` ב-3 מקומות שונים — drift | 6, 7 |
| M12 | אין DB seeds בקוד (statuses, roles, permissions) | 7, 8 |
| M13 | Project status field לא מנוהל state machine | 7 |
| M14 | VIEWER/SUPPLIER ללא scoping פרויקטים מפורש | 8 |
| M15 | Region-only ACCOUNTANT (area_id=None) לא ב-`scope.py` | 8 |

---

## 4. נושאים לעיון עסקי (לא רק טכני)

| נושא | שאלה |
|---|---|
| `quantity` כלים | האם יצירת WO אחד עם כמות, או כמה WOs נפרדים? |
| `priority` | האם נדרש HIGH/URGENT? איך זה משפיע על rotation? |
| 9 שעות נטו | האם תמיד? יש סוגי כלים עם שעות אחרות? |
| 3 שעות תוקף token | מספיק? סופ"ש? |
| `wrong_type` הזמנה | האם להחזיר אוטומטית למתאם? להישאר ב-WO? |
| Email ב-`send invoice` | חובה לשלוח אוטומטית, או ידני? |
| Region-only Accountant | האם זה תרחיש קיים? |
| SMS לספקים | מומש כתרחיש בעבר — להשאיר/להחזיר? |
| Self-approval חוקים | איפה עוד צריך להגן? Currently רק worklog |

---

## 5. מספרים מהירים

- **~140** הרשאות מובחנות נמצאו ב-routers
- **11** סטטוסי WO בשימוש (9 ב-enum רשמי + 2 drift)
- **5** סטטוסי Worklog
- **6** סטטוסי Invoice (אחד drift)
- **11** תפקידים (7 ב-enum + 4 בקוד)
- **3** מסלולי קליטת ציוד שונים בפרונט
- **2** מסלולי יצירת חשבונית (חודשי + ידני)
- **4** מקומות שונים שמגדירים status enums (drift)

---

## 6. מה הצעד הבא

ראה `99_Action_Plan.md` — **תוכנית עבודה מסודרת ב-4 גלים** עם החלטות עסקיות שצריך לקבל לפני קוד.
