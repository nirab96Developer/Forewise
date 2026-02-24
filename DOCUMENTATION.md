# תיעוד מערכת ניהול יערות קק"ל
## KKL Forest Management System

---

# 📑 תוכן עניינים

1. [סקירה כללית](#סקירה-כללית)
2. [מבנה ארגוני](#מבנה-ארגוני)
3. [תהליכי עבודה](#תהליכי-עבודה)
4. [מערכת משתמשים](#מערכת-משתמשים)
5. [תפקידים והרשאות](#תפקידים-והרשאות)
6. [מודולים](#מודולים)
7. [Git ו-Worktrees](#git-ו-worktrees)

---

# סקירה כללית

## מה זה?
מערכת ניהול יערות עבור **קק"ל (קרן קיימת לישראל)**. המערכת מנהלת:
- פרויקטים ביערות
- הזמנות עבודה לספקים
- דיווחי שעות
- חשבוניות ותשלומים
- ציוד כבד

## טכנולוגיות
| רכיב | טכנולוגיה |
|------|----------|
| Backend | Python FastAPI |
| Frontend | React + TypeScript |
| Database | SQL Server (MSSQL) + PostGIS |
| Authentication | JWT + 2FA (OTP) |

---

# מבנה ארגוני

```
┌─────────────────────────────────────────────────────────────┐
│                     Region (מרחב)                            │
│                  למשל: "מרחב צפון"                           │
├─────────────────────────────────────────────────────────────┤
│    ┌─────────────┐  ┌─────────────┐  ┌──────────┐           │
│    │ Area (אזור) │  │ Area (אזור) │  │   ...    │           │
│    │  "גליל"     │  │  "כרמל"     │  │          │           │
│    └──────┬──────┘  └──────┬──────┘  └──────────┘           │
│           │                │                                │
│    ┌──────▼──────┐  ┌──────▼──────┐                         │
│    │  Projects   │  │  Projects   │                         │
│    │ (פרויקטים)  │  │ (פרויקטים)  │                         │
│    └─────────────┘  └─────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## ישויות ארגוניות

| ישות | טבלה | תיאור |
|------|------|-------|
| Region | `regions` | מרחב (צפון, דרום, מרכז...) |
| Area | `areas` | אזור בתוך מרחב |
| Project | `projects` | פרויקט יער ספציפי |
| Location | `locations` | מיקום פיזי |
| Department | `departments` | מחלקה ארגונית |

---

# תהליכי עבודה

## זרימה ראשית

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Project    │──────│  Work Order  │──────│   Worklog    │──────│   Invoice    │
│   (פרויקט)   │      │ (הזמנת עבודה)│      │ (דיווח שעות) │      │  (חשבונית)   │
└──────────────┘      └──────────────┘      └──────────────┘      └──────────────┘
```

---

## 1. Work Order (הזמנת עבודה)

### תיאור
בקשה לספק לבצע עבודה בפרויקט מסוים (כריתה, פיתוח, גיזום וכו').

### State Machine

```
                    ┌──────────┐
                    │  DRAFT   │ (טיוטה)
                    └────┬─────┘
                         │ שליחה לספק
                         ▼
                    ┌──────────┐
          ┌─────────│ PENDING  │─────────┐
          │         │ (ממתין)  │         │
          │         └────┬─────┘         │
     הספק │              │          הספק │
     דוחה │              │ הספק     מבטל │
          ▼              │ מאשר          ▼
    ┌──────────┐         │         ┌──────────┐
    │ REJECTED │         │         │CANCELLED │
    │ (נדחה)   │         │         │ (בוטל)   │
    └──────────┘         ▼         └──────────┘
                    ┌──────────┐
                    │ APPROVED │ (אושר)
                    └────┬─────┘
                         │ העבודה מתחילה
                         ▼
                    ┌──────────┐
                    │  ACTIVE  │ (פעיל)
                    └────┬─────┘
                         │ העבודה הסתיימה
                         ▼
                    ┌──────────┐
                    │COMPLETED │ (הושלם)
                    └──────────┘
```

### שדות עיקריים

| שדה | סוג | תיאור |
|-----|-----|-------|
| `id` | Integer | מזהה ייחודי |
| `order_number` | Integer | מספר הזמנה (ייחודי) |
| `title` | String | כותרת |
| `description` | Text | תיאור מפורט |
| `project_id` | FK | פרויקט |
| `supplier_id` | FK | ספק |
| `equipment_id` | FK | ציוד |
| `status` | Enum | סטטוס |
| `priority` | Enum | עדיפות (LOW/MEDIUM/HIGH/URGENT) |
| `work_start_date` | Date | תאריך התחלה |
| `work_end_date` | Date | תאריך סיום |
| `estimated_hours` | Decimal | שעות משוערות |
| `hourly_rate` | Decimal | תעריף שעתי |
| `frozen_amount` | Decimal | סכום מוקפא בתקציב |
| `portal_token` | String | טוקן לפורטל ספקים |
| `portal_expiry` | DateTime | תוקף טוקן |

---

## 2. Worklog (דיווח שעות)

### תיאור
תיעוד העבודה שבוצעה בפועל - שעות, ציוד, פעילות.

### State Machine

```
    ┌──────────┐
    │  DRAFT   │ (טיוטה - טרם הוגש)
    └────┬─────┘
         │ הגשה
         ▼
    ┌──────────┐
    │ PENDING  │ (ממתין לאישור)
    └────┬─────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────┐
│APPROVED│ │ REJECTED │
│ (אושר) │ │ (נדחה)   │
└───┬────┘ └──────────┘
    │
    ▼
 לחשבונית
```

### שדות עיקריים

| שדה | סוג | תיאור |
|-----|-----|-------|
| `id` | Integer | מזהה ייחודי |
| `report_number` | Integer | מספר דוח |
| `report_date` | Date | תאריך הדוח |
| `work_order_id` | FK | הזמנת עבודה |
| `user_id` | FK | משתמש מדווח |
| `project_id` | FK | פרויקט |
| `equipment_id` | FK | ציוד |
| `start_time` | Time | שעת התחלה |
| `end_time` | Time | שעת סיום |
| `work_hours` | Decimal | שעות עבודה |
| `break_hours` | Decimal | שעות הפסקה |
| `is_standard` | Boolean | עבודה תקנית? |
| `status` | Enum | סטטוס |
| `hourly_rate_snapshot` | Decimal | תעריף (מוקפא) |
| `cost_before_vat` | Decimal | עלות לפני מע"מ |
| `cost_with_vat` | Decimal | עלות כולל מע"מ |

### Workflow Flags

| שדה | תיאור |
|-----|-------|
| `sent_to_supplier` | נשלח לספק |
| `sent_to_accountant` | נשלח לחשב |
| `sent_to_area_manager` | נשלח למנהל אזור |
| `equipment_scanned` | ציוד נסרק |

---

## 3. Invoice (חשבונית)

### State Machine

```
    ┌──────────┐
    │  DRAFT   │
    └────┬─────┘
         ▼
    ┌──────────┐
    │ PENDING  │ (ממתין לאישור)
    └────┬─────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌──────────┐ ┌──────────┐
│ APPROVED │ │CANCELLED │
│ (אושר)   │ │ (בוטל)   │
└────┬─────┘ └──────────┘
     │
     ▼
┌──────────┐
│   PAID   │ (שולם)
└──────────┘
```

### שדות עיקריים

| שדה | סוג | תיאור |
|-----|-----|-------|
| `id` | Integer | מזהה ייחודי |
| `invoice_number` | String | מספר חשבונית |
| `supplier_id` | FK | ספק |
| `project_id` | FK | פרויקט |
| `issue_date` | Date | תאריך הנפקה |
| `due_date` | Date | תאריך פירעון |
| `subtotal` | Decimal | סכום לפני מע"מ |
| `tax_amount` | Decimal | סכום מע"מ |
| `total_amount` | Decimal | סכום כולל |
| `paid_amount` | Decimal | סכום ששולם |
| `status` | Enum | סטטוס |

---

## 4. זרימה מלאה - דוגמה

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. מנהל אזור יוצר Work Order                                    │
│    - בוחר פרויקט: "יער בירייה - כריתת אקליפטוסים"              │
│    - בוחר ציוד: "כורת שרשראות גדול"                             │
│    - מזין שעות משוערות: 8                                       │
│    - מערכת מקפיאה תקציב                                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. רכז הזמנות מקצה ספק (Fair Rotation)                          │
│    - מערכת בוחרת ספק לפי רוטציה הוגנת                           │
│    - נשלח טוקן לפורטל ספקים                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. ספק נכנס לפורטל ומאשר/דוחה                                   │
│    - אם מאשר: סטטוס → APPROVED                                  │
│    - אם דוחה: מערכת עוברת לספק הבא                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. ספק מגיע לשטח ומדווח Worklog                                 │
│    - סורק ציוד (QR/לוחית רישוי)                                 │
│    - מדווח שעות עבודה                                           │
│    - מצרף תמונות (אופציונלי)                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. מנהל אזור מאשר Worklog                                       │
│    - בודק שהעבודה בוצעה                                         │
│    - מאשר → מחושבת עלות                                         │
│    - נוצר PDF דוח                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. חשב יוצר חשבונית                                             │
│    - מאגד Worklogs מאושרים                                      │
│    - יוצר Invoice                                               │
│    - מבצע תשלום                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

# מערכת משתמשים

## מבנה User

```
┌─────────────────────────────────────────────────────────────┐
│                         USER                                 │
├─────────────────────────────────────────────────────────────┤
│  📧 פרטים בסיסיים                                            │
│  • id              - מזהה ייחודי                            │
│  • username        - שם משתמש (ייחודי)                      │
│  • email           - אימייל (ייחודי)                        │
│  • full_name       - שם מלא                                 │
│  • phone           - טלפון                                  │
│  • password_hash   - סיסמה מוצפנת                           │
├─────────────────────────────────────────────────────────────┤
│  🔐 אבטחה ואימות                                             │
│  • two_factor_enabled  - 2FA מופעל?                         │
│  • must_change_password - חייב להחליף סיסמה?                │
│  • is_locked           - חשבון נעול?                        │
│  • locked_until        - נעול עד מתי                        │
│  • last_login          - כניסה אחרונה                       │
│  • status              - סטטוס: ACTIVE / INACTIVE           │
├─────────────────────────────────────────────────────────────┤
│  🏢 שיוך ארגוני                                              │
│  • role_id        - תפקיד                                   │
│  • department_id  - מחלקה                                   │
│  • region_id      - מרחב                                    │
│  • area_id        - אזור                                    │
│  • manager_id     - מנהל ישיר                               │
│  • scope_level    - רמת היקף                                │
└─────────────────────────────────────────────────────────────┘
```

## תהליך אימות

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Login     │────▶│  Password   │────▶│    2FA      │
│  (אימייל)   │     │  (סיסמה)    │     │   (OTP)     │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │   Token     │
                                        │   (JWT)     │
                                        └─────────────┘
```

---

# תפקידים והרשאות

## תפקידים במערכת

| קוד | שם | תיאור | Dashboard |
|-----|-----|-------|-----------|
| `ADMIN` | מנהל מערכת | גישה מלאה | `AdminDashboard` |
| `REGION_MANAGER` | מנהל מרחב | ניהול מרחב שלם | `RegionManagerDashboard` |
| `AREA_MANAGER` | מנהל אזור | ניהול אזור ופרויקטים | `AreaManagerDashboard` |
| `WORK_MANAGER` | מנהל עבודה | ניהול הזמנות עבודה | `WorkManagerDashboard` |
| `ORDER_COORDINATOR` | מתאם הזמנות | תיאום ספקים | `OrderCoordinatorDashboard` |
| `ACCOUNTANT` | חשב | חשבוניות ותשלומים | `AccountantDashboard` |
| `AREA_ACCOUNTANT` | הנה"ח אזורית | חשבונאות אזורית | `AccountantDashboard` |
| `SUPPLIER` | ספק | גישה לפורטל ספקים | `SupplierPortal` |
| `VIEWER` | צופה | צפייה בלבד | `ViewerDashboard` |

## היררכיה

```
                    ┌──────────────┐
                    │    ADMIN     │
                    │ (מנהל מערכת) │
                    └──────┬───────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │   REGION    │ │   REGION    │ │ ACCOUNTANT  │
    │   MANAGER   │ │   MANAGER   │ │    (חשב)    │
    │  (מרחב צפון)│ │  (מרחב דרום)│ │             │
    └──────┬──────┘ └──────┬──────┘ └─────────────┘
           │               │
    ┌──────┴──────┐ ┌──────┴──────┐
    ▼             ▼ ▼             ▼
┌────────┐  ┌────────┐  ┌────────┐
│  AREA  │  │  AREA  │  │ ORDER  │
│MANAGER │  │MANAGER │  │ COORD  │
└───┬────┘  └───┬────┘  └────────┘
    │           │           
    ▼           ▼           
┌────────┐  ┌────────┐  
│ WORK   │  │ WORK   │  
│MANAGER │  │MANAGER │  
└────────┘  └────────┘  
```

---

## ORDER_COORDINATOR - מתאם הזמנות

### תיאור
מתאם ההזמנות אחראי על **תיאום הזמנות עבודה מול ספקים**.

### תהליך עבודה

```
┌─────────────────────────────────────────────────────────────────┐
│                    תהליך תיאום הזמנות                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   מנהל אזור         רכז הזמנות           ספק                   │
│       │                 │                  │                    │
│       │   יוצר הזמנה    │                  │                    │
│       ├────────────────▶│                  │                    │
│       │                 │                  │                    │
│       │                 │  שולח לספק       │                    │
│       │                 ├─────────────────▶│                    │
│       │                 │                  │                    │
│       │                 │◀─ טיימר 3 שעות ─▶│                    │
│       │                 │                  │                    │
│       │                 │  לא הגיב? →      │                    │
│       │                 │  מעביר לספק הבא  │                    │
│       │                 │                  │                    │
│       │                 │◀── תשובה ───────│                    │
│       │                 │                  │                    │
│       │  עדכון סטטוס    │                  │                    │
│       │◀────────────────│                  │                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### הרשאות

| קטגוריה | הרשאות |
|---------|--------|
| ארגון | `regions.read`, `areas.read`, `locations.read` |
| פרויקטים | `projects.read` |
| ספקים | `suppliers.read`, `supplier_constraints.read/create` |
| הזמנות | `work_orders.read`, `create`, `update`, `assign` (**ללא approve!**) |
| דיווחים | `worklogs.read` |
| ציוד | `equipment.read`, `equipment_types.read` |

### פעולות

| פעולה | תיאור |
|-------|-------|
| שלח לספק | שולח הזמנה לספק דרך הפורטל |
| שלח מחדש | שולח שוב לספק שלא הגיב |
| העבר לספק הבא | מעביר לספק הבא ברוטציה |
| תעד שיחה | מתעד שיחת טלפון עם ספק |

### טיימר 3 שעות

```
⏱️ אם הספק לא מגיב תוך 3 שעות,
   ההזמנה עוברת אוטומטית לספק הבא בסבב.
```

---

## מבנה הרשאות

### פורמט
```
resource.action
   │       │
   │       └── view / create / update / delete / approve
   │
   └── projects / work_orders / worklogs / invoices / users / ...
```

### דוגמאות

| קוד הרשאה | משמעות |
|-----------|--------|
| `projects.view` | צפייה בפרויקטים |
| `projects.create` | יצירת פרויקט חדש |
| `work_orders.approve` | אישור הזמנות עבודה |
| `worklogs.approve` | אישור דיווחי שעות |
| `invoices.create` | יצירת חשבוניות |
| `users.manage` | ניהול משתמשים |

---

# מודולים

## Equipment (ציוד)

ניהול ציוד כבד (טרקטורים, כורתים וכו'):
- סריקת ציוד לפי לוחית רישוי
- מעקב מיקום ותחזוקה
- שיוך לספקים

### טבלאות
| טבלה | תיאור |
|------|-------|
| `equipment` | ציוד |
| `equipment_types` | סוגי ציוד |
| `equipment_categories` | קטגוריות |

---

## Budget (תקציב)

ניהול תקציבים:
- תקציב לכל מרחב/אזור/פרויקט
- הקפאת סכומים בעת יצירת Work Order
- שחרור בעת סגירה

### טבלאות
| טבלה | תיאור |
|------|-------|
| `budgets` | תקציבים |
| `budget_items` | פריטי תקציב |

---

## Supplier (ספקים)

ניהול ספקים:
- פרטי ספק
- ציוד בבעלות
- רוטציה הוגנת

### טבלאות
| טבלה | תיאור |
|------|-------|
| `suppliers` | ספקים |
| `supplier_constraint_reasons` | סיבות אילוץ |
| `supplier_rejection_reasons` | סיבות דחייה |

---

## Fair Rotation (רוטציה הוגנת)

מנגנון לחלוקה הוגנת של עבודות בין ספקים:

```
ספקים זמינים לציוד "כורת שרשראות גדול":
┌─────────────────────────────────────────────────────────────┐
│  #  │ ספק                    │ עבודות אחרונות │ תור        │
│ ─── │ ────────────────────── │ ────────────── │ ────────── │
│  1  │ אבי ציוד כבד           │ 3 (לפני שבוע)  │ ← הבא!     │
│  2  │ משה טרקטורים           │ 5              │            │
│  3  │ יוסי כלי עבודה         │ 4              │            │
│  4  │ דני שירותי יער         │ 2              │            │
└─────────────────────────────────────────────────────────────┘

* הספק עם הכי פחות עבודות אחרונות מקבל קדימות
* אפשר לעקוף רוטציה עם "אילוץ ספק" (צריך סיבה)
```

---

## Forest Map (מפת יערות)

- PostGIS polygons
- הצגת גבולות יערות
- מיקום פרויקטים על מפה

### טבלאות
| טבלה | תיאור |
|------|-------|
| `forests` | פוליגוני יערות |

---

# Git ו-Worktrees

## מה זה Git Worktree?

בדרך כלל, יש לך **repo אחד = תיקייה אחת**. אבל Git מאפשר ליצור **עותקים מקושרים** של אותו repo בתיקיות שונות.

```
/root/kkl-forest/                    ← הריפו הראשי (main)
    │
    └── .git/                        ← כל ההיסטוריה נשמרת כאן
          │
          ├── worktree: abc  ──────→ /root/.cursor/worktrees/.../abc/
          ├── worktree: xyz  ──────→ /root/.cursor/worktrees/.../xyz/
          └── ...
```

## למה Cursor יוצר worktrees?

כשפותחים את הפרויקט ב-Cursor דרך SSH, הוא יוצר worktree חדש כדי:
1. **לא לפגוע בריפו הראשי**
2. **לאפשר עריכה מקבילה**
3. **בידוד** - כל session עובד בנפרד

## חיבורי Git (Remotes)

| שם | כתובת | פלטפורמה |
|----|-------|----------|
| origin | `git@github.com:nirab96Developer/forest-management-system.git` | GitHub |
| gitlab | `git@gitlab.com:nirab96Developer/forest-management-system.git` | GitLab |
| backendv2 | `git@github.com:nirab96Developer/backendv2.git` | GitHub |

## ניקוי worktrees

```bash
# הצג כל ה-worktrees
git worktree list

# מחק worktree ספציפי
git worktree remove /path/to/worktree
```

---

# סיכום ישויות

| ישות | טבלה | תיאור |
|------|------|-------|
| User | `users` | משתמש מערכת |
| Role | `roles` | תפקיד |
| Permission | `permissions` | הרשאה |
| RoleAssignment | `role_assignments` | הקצאת תפקיד |
| Region | `regions` | מרחב |
| Area | `areas` | אזור |
| Project | `projects` | פרויקט |
| Location | `locations` | מיקום |
| Supplier | `suppliers` | ספק |
| Equipment | `equipment` | ציוד |
| EquipmentType | `equipment_types` | סוג ציוד |
| WorkOrder | `work_orders` | הזמנת עבודה |
| Worklog | `worklogs` | דיווח שעות |
| Invoice | `invoices` | חשבונית |
| Budget | `budgets` | תקציב |
| BudgetItem | `budget_items` | פריט תקציב |
| ActivityLog | `activity_logs` | לוג פעילות |
| Forest | `forests` | פוליגון יער |

---

---

# Database - מסד הנתונים

## מיגרציה: PostgreSQL → Azure SQL Server

### לפני (PostgreSQL מקומי)

```
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL (Local)                        │
├─────────────────────────────────────────────────────────────┤
│  Host:     localhost                                        │
│  Port:     5432                                             │
│  Database: forest_local_db                                  │
│  User:     forest_admin                                     │
│  Features: PostGIS, native JSONB                            │
└─────────────────────────────────────────────────────────────┘
```

### אחרי (Azure SQL Server)

```
┌─────────────────────────────────────────────────────────────┐
│                 Azure SQL Server (Cloud)                     │
├─────────────────────────────────────────────────────────────┤
│  Server:   projmgmt-db.database.windows.net                 │
│  Port:     1433                                             │
│  Database: reporting_app_db_dev                             │
│  User:     nir_admin                                        │
│  Driver:   ODBC Driver 17 for SQL Server                    │
│  Features: Full-text search, Azure integration              │
└─────────────────────────────────────────────────────────────┘
```

### תהליך המיגרציה

```
PostgreSQL ───────────────────────────────> Azure SQL Server
     │                                            │
     │  1. migrate_data_only.py                   │
     │     - psycopg2 (PostgreSQL driver)         │
     │     - pymssql (SQL Server driver)          │
     │                                            │
     │  2. העברת טבלאות לפי סדר FK:               │
     │     regions → areas → departments →        │
     │     roles → permissions → users →          │
     │     projects → equipment → suppliers       │
     │                                            │
     │  3. המרת סוגי נתונים:                      │
     │     - bool → bit                           │
     │     - dict → nvarchar                      │
     │     - JSONB → nvarchar(max)                │
     │                                            │
     │  4. SET IDENTITY_INSERT ON/OFF             │
     │     (לשמירת IDs המקוריים)                  │
     │                                            │
     └────────────────────────────────────────────┘
```

### קבצי מיגרציה

| קובץ | תיאור |
|------|-------|
| `migrate_data_only.py` | העברת נתונים מ-PostgreSQL ל-SQL Server |
| `transfer_remaining.py` | העברת טבלאות שנותרו |
| `verify_sqlserver_alignment.py` | אימות התאמה בין המסדים |
| `postgresql_diagnostic.sql` | סקריפט אבחון PostgreSQL |

### השוואת מסדי הנתונים

| תכונה | PostgreSQL | Azure SQL Server |
|--------|-----------|------------------|
| **סוג** | Open Source | Microsoft Cloud |
| **Driver Python** | psycopg2 | pyodbc / pymssql |
| **Boolean** | `boolean` | `bit` |
| **JSON** | `jsonb` (native) | `nvarchar(max)` |
| **Unicode** | `text` | `nvarchar` |
| **Geometry** | PostGIS | - (אין תמיכה מובנית) |
| **Auto-increment** | `SERIAL` | `IDENTITY` |
| **Timestamp** | `NOW()` | `SYSUTCDATETIME()` |

---

## סוג מסד הנתונים (נוכחי)

| פרמטר | ערך |
|-------|-----|
| **סוג** | Microsoft SQL Server (Azure SQL) |
| **שרת** | `projmgmt-db.database.windows.net` |
| **מסד נתונים** | `reporting_app_db_dev` |
| **Driver** | ODBC Driver 17 for SQL Server |
| **ORM** | SQLAlchemy 2.0 |
| **Migrations** | Alembic |

## Connection String

```
mssql+pyodbc://user:pass@projmgmt-db.database.windows.net:1433/reporting_app_db_dev
    ?driver=ODBC+Driver+17+for+SQL+Server
    &Encrypt=yes
    &TrustServerCertificate=no
    &Connection+Timeout=30
```

## הגדרות Pool

| פרמטר | ערך | תיאור |
|-------|-----|-------|
| `DB_POOL_SIZE` | 10 | גודל pool בסיסי |
| `DB_MAX_OVERFLOW` | 20 | חיבורים נוספים מותרים |
| `DB_POOL_TIMEOUT` | 30 | timeout לחיבור (שניות) |
| `DB_POOL_RECYCLE` | 1800 | זמן מחזור חיבור (שניות) |

---

## קטגוריות טבלאות

### CORE_ENTITIES (ישויות עסקיות מרכזיות)
עמודות: `created_at`, `updated_at`, `deleted_at`, `is_active`, `version`

| טבלה | תיאור |
|------|-------|
| `users` | משתמשים |
| `roles` | תפקידים |
| `permissions` | הרשאות |
| `regions` | מרחבים |
| `areas` | אזורים |
| `departments` | מחלקות |
| `projects` | פרויקטים |
| `suppliers` | ספקים |
| `equipment` | ציוד |
| `equipment_types` | סוגי ציוד |
| `equipment_categories` | קטגוריות ציוד |
| `work_orders` | הזמנות עבודה |
| `worklogs` | דיווחי עבודה |
| `budgets` | תקציבים |
| `budget_items` | פריטי תקציב |
| `invoices` | חשבוניות |
| `invoice_items` | פריטי חשבונית |
| `reports` | דוחות |

### TRANSACTIONS (טרנזקציות)
עמודות: `created_at`, `updated_at`, `is_active`

| טבלה | תיאור |
|------|-------|
| `budget_allocations` | הקצאות תקציב |
| `budget_transfers` | העברות תקציב |
| `balance_releases` | שחרור יתרות |
| `invoice_payments` | תשלומי חשבוניות |
| `equipment_assignments` | שיוך ציוד |
| `equipment_maintenance` | תחזוקת ציוד |
| `supplier_rotations` | רוטציות ספקים |
| `equipment_scans` | סריקות ציוד |
| `report_runs` | הרצות דוחות |

### JUNCTION (טבלאות קשר)
עמודות: `created_at`

| טבלה | תיאור |
|------|-------|
| `role_permissions` | קשר תפקיד-הרשאה |
| `role_assignments` | הקצאת תפקידים |

### LOGS_HISTORY (לוגים)
עמודות: `created_at`

| טבלה | תיאור |
|------|-------|
| `activity_logs` | לוג פעילות |
| `supplier_constraint_logs` | לוג אילוצי ספקים |

### LOOKUP (טבלאות בסיס)
עמודות: `created_at`, `updated_at`, `is_active`

| טבלה | תיאור |
|------|-------|
| `supplier_constraint_reasons` | סיבות אילוץ ספק |
| `supplier_rejection_reasons` | סיבות דחיית ספק |
| `worklog_statuses` | סטטוסי דיווח |
| `work_order_statuses` | סטטוסי הזמנה |

---

## Base Models

### BaseModel
מודל בסיס עם עמודות audit סטנדרטיות:

```python
class BaseModel(Base):
    __abstract__ = True
    
    created_at: datetime      # NOT NULL, DEFAULT SYSUTCDATETIME()
    updated_at: datetime      # NOT NULL, AUTO-UPDATE by trigger
    deleted_at: datetime      # NULLABLE (soft delete)
    is_active: bool           # NULLABLE, DEFAULT True
    version: int              # NULLABLE, DEFAULT 1 (optimistic locking)
```

### Database Triggers
48 triggers נוצרו לעדכון אוטומטי של `updated_at`:

```sql
CREATE TRIGGER TR_users_updated_at ON users
AFTER UPDATE AS
BEGIN
    UPDATE users SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted)
END
```

---

## PostGIS - מפות

### טבלת forests
אחסון פוליגוני יערות:

```python
class Forest(Base):
    __tablename__ = "forests"
    
    id: int
    name: str                             # שם היער
    code: str                             # קוד יער (unique)
    geom: Geometry('MULTIPOLYGON', 4326)  # גבולות היער
    area_km2: Decimal                     # שטח בקמ"ר
```

### Geometry Type
- **סוג**: `MULTIPOLYGON`
- **SRID**: `4326` (WGS84 - קואורדינטות GPS)

---

## רשימת כל הטבלאות

### ישויות ארגוניות
| טבלה | עמודות מרכזיות |
|------|----------------|
| `users` | id, email, full_name, password_hash, role_id, region_id, area_id |
| `roles` | id, code, name, description |
| `permissions` | id, code, name, resource, action |
| `role_permissions` | role_id, permission_id |
| `role_assignments` | user_id, role_id, scope_type, scope_id |
| `regions` | id, name, code, manager_id |
| `areas` | id, name, code, region_id, manager_id |
| `departments` | id, name, code |
| `locations` | id, name, area_id, coordinates |

### פרויקטים ועבודה
| טבלה | עמודות מרכזיות |
|------|----------------|
| `projects` | id, name, code, area_id, status, budget |
| `work_orders` | id, order_number, project_id, supplier_id, status, priority |
| `worklogs` | id, report_number, work_order_id, report_date, work_hours |
| `worklog_segments` | id, worklog_id, activity_type_id, hours |
| `activity_types` | id, code, name |

### ספקים וציוד
| טבלה | עמודות מרכזיות |
|------|----------------|
| `suppliers` | id, name, code, phone, email, rating |
| `equipment` | id, name, license_plate, supplier_id, equipment_type_id |
| `equipment_types` | id, code, name, category_id |
| `equipment_categories` | id, code, name |
| `equipment_scans` | id, equipment_id, scan_time, location |
| `supplier_rotations` | id, supplier_id, equipment_type_id, last_assigned |

### כספים ותקציב
| טבלה | עמודות מרכזיות |
|------|----------------|
| `budgets` | id, name, total_amount, region_id, year |
| `budget_items` | id, budget_id, project_id, allocated_amount |
| `invoices` | id, invoice_number, supplier_id, total_amount, status |
| `invoice_items` | id, invoice_id, worklog_id, amount |
| `invoice_payments` | id, invoice_id, amount, payment_date |

### מערכת
| טבלה | עמודות מרכזיות |
|------|----------------|
| `sessions` | id, user_id, token, expires_at |
| `otp_tokens` | id, user_id, code, expires_at |
| `activity_logs` | id, user_id, action, entity_type, entity_id |
| `notifications` | id, user_id, title, message, is_read |
| `support_tickets` | id, user_id, subject, status |

### גיאוגרפיה
| טבלה | עמודות מרכזיות |
|------|----------------|
| `forests` | id, name, code, geom (PostGIS), area_km2 |

---

## Migrations שבוצעו

| קובץ | תיאור |
|------|-------|
| `01_fix_timestamps.sql` | תיקון עמודות timestamp |
| `02_backfill_timestamps.sql` | מילוי ערכים חסרים |
| `03_create_triggers.sql` | יצירת triggers ל-updated_at |
| `04_verification.sql` | אימות המיגרציה |
| `08_fix_defaults_clean.sql` | תיקון ערכי default |

---

## Unicode / עברית

המערכת תומכת בעברית באמצעות:

1. **סוגי עמודות**: `nvarchar` / `Unicode` (במקום `varchar`)
2. **Collation**: SQL Server default
3. **ORM**: SQLAlchemy `Unicode` ו-`UnicodeText`

```python
# דוגמה
name: Mapped[str] = mapped_column(Unicode(200), nullable=False)
description: Mapped[str] = mapped_column(UnicodeText, nullable=True)
```

---

*תיעוד זה נוצר ב-1 בפברואר 2026*
