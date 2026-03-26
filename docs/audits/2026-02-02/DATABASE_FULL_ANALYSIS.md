# 🗄️ ניתוח מלא של מסד הנתונים - Forewise

**תאריך:** 2 בפברואר 2026, 18:16  
**Database:** `forewise_prod`  
**PostgreSQL:** 16.11  
**סה"כ טבלאות:** 35

---

## 📊 סיכום מנהלים

### נתונים במערכת:

| ישות | כמות | סטטוס |
|------|------|-------|
| 🌲 **פרויקטים (יערות)** | 60 | פעילים |
| 🌳 **יערות (Forests)** | 3 | עם גיאומטריה |
| 🗺️ **פוליגונים** | 273 | PostGIS |
| 🏢 **מרחבים** | 3 | צפון, מרכז, דרום |
| 📍 **אזורים** | 12 | 4 לכל מרחב |
| 📝 **הזמנות עבודה** | 18 | 17 ביער בירייה |
| ⏰ **דיווחי שעות** | 7 | כולם ביער בירייה |
| 👷 **ספקים** | 13 | פעילים |
| 🚜 **ציוד** | 43 | יחידות |
| 👥 **משתמשים** | 13 | 8 אמיתיים + 5 טסט |

### תקציב כולל:
- **סה"כ תקציב פרויקטים:** ₪247.6 מיליון
  - צפון: ₪188.7M (76%)
  - מרכז: ₪31.1M (13%)
  - דרום: ₪27.7M (11%)

---

## 🏢 מבנה ארגוני

### 1. Regions (מרחבים)

```
┌─────────────────────────────────────────────────────────┐
│  ID │ שם   │ קוד    │ פרויקטים │ תקציב        │
├─────────────────────────────────────────────────────────┤
│  1  │ צפון │ NORTH  │    23    │ ₪188.7M      │
│  2  │ מרכז │ CENTER │    21    │ ₪31.1M       │
│  3  │ דרום │ SOUTH  │    16    │ ₪27.7M       │
└─────────────────────────────────────────────────────────┘
```

### 2. Areas (אזורים) - 12 אזורים

#### מרחב צפון (4):
| ID | שם | קוד | פרויקטים |
|----|-----|-----|----------|
| 12 | גליל עליון ורמת הגולן | GALIL_UPPER_GOLAN | 7 |
| 13 | גליל מערבי וכרמל | GALIL_WEST_CARMEL | 6 |
| 14 | גליל תחתון וגלבוע | GALIL_LOWER_GILBOA | 6 |
| 16 | עמק החולה | EMEK_HULA | 4 |

#### מרחב מרכז (4):
| ID | שם | קוד | פרויקטים |
|----|-----|-----|----------|
| 31 | שפלה וחוף | SHFELA_COAST | 8 |
| 33 | ההר | HAHAR | 7 |
| 34 | מנשה ושרון | MENASHE_SHARON | 4 |
| 37 | מנסרה מרכז | MENSARA_CENTER | 2 |

#### מרחב דרום (4):
| ID | שם | קוד | פרויקטים |
|----|-----|-----|----------|
| 41 | נגב צפוני | NEGEV_NORTH | 8 |
| 42 | נגב מערבי | NEGEV_WEST | 6 |
| 43 | הר הנגב וערבה | HAR_NEGEV_ARAVA | 2 |
| 45 | שימור קרקע | LAND_CONSERVATION | 0 |

---

## 🌲 פרויקטים (60 יערות)

### דוגמאות לפרויקטים:

#### מרחב צפון:

**1. יער בירייה (YR-001)** ⭐ הפרויקט הפעיל ביותר
- תקציב: ₪320,000
- אזור: גליל עליון ורמת הגולן
- סוג: פיתוח שבילים
- Work Orders: **17** (כל ההזמנות!)
- Worklogs: **7** (כל הדיווחים!)
- תיאור: פיתוח ושימור יער בירייה, שבילי הליכה ונקודות תצפית

**2. יער הכרמל (YR-005)**
- תקציב: ₪450,000 (הגבוה ביותר בצפון)
- סוג: שימור טבע
- תיאור: שימור מערכות אקולוגיות ייחודיות

**3. יער החרמון (YR-034)**
- תקציב: ₪890,000 (הגבוה ביותר במערכת!)
- אזור: עמק החולה
- סוג: פיתוח

#### מרחב מרכז:

**4. יער בן שמן (YR-008)**
- תקציב: ₪385,000
- סוג: שיקום צמחייה

**5. יער שוהם (YR-049)**
- תקציב: ₪350,000
- סוג: שיקום

#### מרחב דרום:

**6. יער יתיר (YR-015)**
- תקציב: ₪520,000
- סוג: מחקר וניטור

**7. יער שקמים (YR-051)**
- תקציב: ₪720,000
- סוג: נטיעה

---

## 🗺️ מערכת הגיאומטריה (PostGIS)

### 3 רבדים גיאוגרפיים:

#### 1. **Forests** - יערות עיקריים (3)
```sql
id: bigint
name: text
code: varchar(50) UNIQUE
geom: geometry(MultiPolygon, 4326)  -- SRID: WGS84
area_km2: numeric(10,2)
```

**יערות:**
- יער אשתאול (ESHTAOL)
- יער חולדה (HULDA)
- יער ירושלים (JERUSALEM)

#### 2. **Forest Polygons** - פוליגונים מפורטים (273)
```sql
id: bigint
geom: geometry(MultiPolygon, 4326)
geom_hash: text UNIQUE  -- לזיהוי ייחודי
created_at: timestamp
```

**מאפיינים:**
- 273 פוליגונים נפרדים
- Hash ייחודי לכל פוליגון
- Spatial index (GIST) לשאילתות מהירות

#### 3. **Projects** - מיקום פרויקטים
```sql
location_geom: geometry(Point, 4326)
forest_id: bigint FK -> forests
forest_polygon_id: bigint FK -> forest_polygons
```

**קשרים:**
- פרויקט יכול להיות מקושר ליער (forest_id)
- פרויקט יכול להיות מקושר לפוליגון (forest_polygon_id)
- פרויקט יכול לכלול מיקום נקודתי (location_geom)

### Spatial Indexes:
```sql
✅ idx_forests_geom_gist (forests.geom)
✅ idx_forest_polygons_geom (forest_polygons.geom)
✅ idx_projects_location_geom_gist (projects.location_geom)
```

---

## 📝 Work Orders (הזמנות עבודה)

### 18 הזמנות במערכת:

**התפלגות:**
- יער בירייה: **17 הזמנות** (95%!)
- יער אופקים: 1 הזמנה

**מבנה Work Order:**
```sql
id, order_number (unique)
title, description
project_id FK -> projects
supplier_id FK -> suppliers
equipment_id FK -> equipment
status (DRAFT, PENDING, APPROVED, ACTIVE, COMPLETED, etc.)
priority (LOW, MEDIUM, HIGH, URGENT)
work_start_date, work_end_date
estimated_hours, hourly_rate
frozen_amount (תקציב מוקפא)
portal_token (לפורטל ספקים)
```

**דוגמה:**
```
ID: 4
Order Number: 1
Title: "דרישת כלי: יעה אופני זעיר (1 יחידות)"
Project: יער אופקים
Estimated Hours: 63
```

---

## ⏰ Worklogs (דיווחי שעות)

### 7 דיווחים במערכת:

**כולם ביער בירייה!**

```
Report #1-7: יער בירייה
Report Date: 2026-01-31
Work Hours: 8.00 כל אחד
Reporter: "Updated Name"
Status: (empty - probably DRAFT or PENDING)
```

**מבנה Worklog:**
```sql
id, report_number (unique)
report_date
work_order_id FK -> work_orders
user_id FK -> users (reporter)
project_id FK -> projects
equipment_id FK -> equipment
start_time, end_time
work_hours, break_hours
is_standard (עבודה תקנית?)
status (DRAFT, PENDING, APPROVED, REJECTED)
hourly_rate_snapshot (תעריף מוקפא)
cost_before_vat, cost_with_vat
sent_to_supplier, sent_to_accountant, sent_to_area_manager
equipment_scanned
```

---

## 👷 ספקים (13 ספקים)

### רשימת ספקים:

| קוד | שם | ציוד |
|-----|-----|------|
| SUP001 | אחים יקוטי בע"מ | 3 |
| SUP002 | איאד חוגיראת בע"מ | 6 |
| SUP003 | ת.א.המרכז תשתיות הנגב בע"מ | 7 |
| SUP004 | מ.ס. פיתוח הצפון | 5 |
| SUP005 | בני עפיף סואעד בע"מ | 3 |
| SUP006 | א.ג. הובלות יתיר בע"מ | 3 |
| SUP007 | דחפורי השחר בע"מ | 3 |
| SUP008 | אבו אלקיעאן עלי | 2 |
| SUP009 | מובילי דרום הר להב בע"מ | 1 |
| SUP010 | אבו אלקיעאן תאופיק | 1 |
| SUP011 | א.א.שארב בע"מ | 1 |
| SUP012 | חסן שחאדה בע"מ | 0 |

**סה"כ ציוד:** 43 יחידות

---

## 👥 משתמשים (13)

### משתמשים אמיתיים (8):

| ID | Username | שם מלא | תפקיד | מרחב | אזור |
|----|----------|--------|-------|------|------|
| 1 | admin | מנהל מערכת | ADMIN (1) | - | - |
| 2 | region_north | מנהל מרחב צפון | REGION_MANAGER (2) | צפון | - |
| 3 | region_center | מנהל מרחב מרכז | REGION_MANAGER (2) | מרכז | - |
| 4 | region_south | מנהל מרחב דרום | REGION_MANAGER (2) | דרום | - |
| 5 | area_manager | מנהל אזור גליל עליון | AREA_MANAGER (3) | צפון | 12 |
| 6 | work_manager | מנהל עבודה | WORK_MANAGER (4) | צפון | 12 |
| 7 | accountant | מנהלת חשבונות | ACCOUNTANT (5) | - | - |
| 8 | coordinator | מתאם הזמנות | ORDER_COORDINATOR (10) | - | - |

### משתמשי טסט (5):
- testuser_1769890956
- updatetest_1769890956
- deletetest_1769890958 (inactive)
- locktest_1769890959
- first_1769890959

---

## 🔗 קשרים בין טבלאות

### המבנה המרכזי:

```
┌─────────────┐
│   Regions   │ (3 מרחבים)
└──────┬──────┘
       │ 1:N
       ▼
┌─────────────┐
│    Areas    │ (12 אזורים)
└──────┬──────┘
       │ 1:N
       ▼
┌─────────────┐        ┌─────────────┐
│  Projects   │◄───────┤   Forests   │ (3 יערות)
│  (60 יערות) │ N:1    │ (Geometry)  │
└──────┬──────┘        └─────────────┘
       │ 1:N           
       │               ┌─────────────┐
       ├──────────────►│Forest       │ (273 פוליגונים)
       │ N:1           │Polygons     │
       │               └─────────────┘
       │ 1:N
       ▼
┌─────────────┐        ┌─────────────┐
│Work Orders  │───────►│  Suppliers  │ (13 ספקים)
│(18 הזמנות) │ N:1    └─────────────┘
└──────┬──────┘              │ 1:N
       │ 1:N                 ▼
       ▼               ┌─────────────┐
┌─────────────┐        │  Equipment  │ (43 יחידות)
│  Worklogs   │◄───────┤             │
│(7 דיווחים) │ N:1    └─────────────┘
└─────────────┘
```

---

## 📋 טבלת Projects - פירוט מלא

### עמודות (31):

#### מזהים ומפתחות:
```sql
id              INTEGER PRIMARY KEY
code            VARCHAR(50) UNIQUE NOT NULL  -- YR-001, YR-002, etc.
name            VARCHAR(200) NOT NULL        -- שם היער
```

#### קשרים ארגוניים:
```sql
region_id       INTEGER FK -> regions        -- מרחב
area_id         INTEGER FK -> areas          -- אזור
manager_id      INTEGER FK -> users          -- מנהל הפרויקט
budget_id       INTEGER FK -> budgets        -- תקציב מקושר
```

#### קשרים גיאוגרפיים:
```sql
forest_id         BIGINT FK -> forests           -- יער עיקרי
forest_polygon_id BIGINT FK -> forest_polygons  -- פוליגון ספציפי
location_geom     GEOMETRY(Point, 4326)         -- נקודת מיקום
```

#### פרטי פרויקט:
```sql
description       TEXT
status            VARCHAR(50) DEFAULT 'active'
priority          INTEGER
start_date        DATE
end_date          DATE
```

#### תקציב ועבודה:
```sql
budget            NUMERIC(15,2)               -- תקציב בש"ח
total_hours       NUMERIC(10,2)              -- סה"כ שעות
work_type         VARCHAR(100)               -- סוג העבודה
execution_type    VARCHAR(100)               -- סוג ביצוע
contractor_name   VARCHAR(255)               -- שם קבלן
permit_required   BOOLEAN DEFAULT false      -- נדרש אישור?
```

#### נוספים:
```sql
scope             TEXT
notes             TEXT
metadata_json     TEXT
supplier_id       INTEGER FK -> suppliers
location_id       INTEGER FK -> locations
```

#### Audit Fields:
```sql
is_active         BOOLEAN DEFAULT true
created_at        TIMESTAMP DEFAULT now()
updated_at        TIMESTAMP DEFAULT now()
deleted_at        TIMESTAMP                  -- soft delete
version           INTEGER DEFAULT 1          -- optimistic locking
```

### Indexes:
- ✅ PRIMARY KEY (id)
- ✅ UNIQUE constraint (code)
- ✅ Index על region_id
- ✅ Index על forest_polygon_id
- ✅ **Spatial index (GIST)** על location_geom

---

## 🌳 Forests - היערות העיקריים

### 3 יערות עם גיאומטריה:

```sql
CREATE TABLE forests (
    id         BIGINT PRIMARY KEY,
    name       TEXT NOT NULL,
    code       VARCHAR(50) UNIQUE,
    geom       GEOMETRY(MultiPolygon, 4326) NOT NULL,  -- PostGIS
    area_km2   NUMERIC(10,2),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);
```

| ID | שם | קוד | גיאומטריה |
|----|-----|-----|-----------|
| 1 | יער אשתאול | ESHTAOL | MultiPolygon (WGS84) |
| 2 | יער חולדה | HULDA | MultiPolygon (WGS84) |
| 3 | יער ירושלים | JERUSALEM | MultiPolygon (WGS84) |

**SRID 4326** = WGS84 (GPS coordinates)

---

## 🗺️ Forest Polygons - 273 פוליגונים

```sql
CREATE TABLE forest_polygons (
    id         BIGINT PRIMARY KEY,
    geom       GEOMETRY(MultiPolygon, 4326) NOT NULL,
    geom_hash  TEXT UNIQUE,  -- MD5/SHA hash של הגיאומטריה
    created_at TIMESTAMP DEFAULT now()
);
```

**שימוש:**
- כל פוליגון מייצג אזור ספציפי ביער
- ניתן לקשר מספר פרויקטים לאותו פוליגון
- Hash מונע כפילויות

---

## 📝 Work Orders - מבנה מלא

```sql
id                INTEGER PRIMARY KEY
order_number      INTEGER UNIQUE NOT NULL
title             VARCHAR(500)
description       TEXT
project_id        INTEGER FK -> projects
supplier_id       INTEGER FK -> suppliers
equipment_id      INTEGER FK -> equipment
status            VARCHAR(50)
priority          VARCHAR(50)  -- LOW, MEDIUM, HIGH, URGENT
work_start_date   DATE
work_end_date     DATE
estimated_hours   NUMERIC(10,2)
hourly_rate       NUMERIC(10,2)
frozen_amount     NUMERIC(15,2)  -- תקציב מוקפא
portal_token      VARCHAR(255)   -- טוקן לפורטל ספקים
portal_expiry     TIMESTAMP
created_at, updated_at, deleted_at
is_active, version
```

**סטטוסים אפשריים:**
- DRAFT - טיוטה
- PENDING - ממתין לאישור ספק
- APPROVED - אושר על ידי ספק
- ACTIVE - בביצוע
- COMPLETED - הושלם
- REJECTED - נדחה
- CANCELLED - בוטל

---

## ⏰ Worklogs - מבנה מלא

```sql
id                      INTEGER PRIMARY KEY
report_number           INTEGER UNIQUE NOT NULL
report_date             DATE NOT NULL
work_order_id           INTEGER FK -> work_orders
user_id                 INTEGER FK -> users (reporter)
project_id              INTEGER FK -> projects
equipment_id            INTEGER FK -> equipment
start_time              TIME
end_time                TIME
work_hours              NUMERIC(10,2)
break_hours             NUMERIC(10,2)
is_standard             BOOLEAN DEFAULT true
status                  VARCHAR(50)
hourly_rate_snapshot    NUMERIC(10,2)  -- תעריף מוקפא
cost_before_vat         NUMERIC(15,2)
cost_with_vat           NUMERIC(15,2)
sent_to_supplier        BOOLEAN DEFAULT false
sent_to_accountant      BOOLEAN DEFAULT false
sent_to_area_manager    BOOLEAN DEFAULT false
equipment_scanned       BOOLEAN DEFAULT false
created_at, updated_at, deleted_at
is_active, version
```

**Workflow Flags:**
- `sent_to_supplier` - נשלח לספק לאישור
- `sent_to_accountant` - נשלח לחשב לתשלום
- `sent_to_area_manager` - נשלח למנהל אזור לאישור
- `equipment_scanned` - הציוד נסרק (QR/לוחית רישוי)

---

## 💰 Budget & Finance

### Budgets:
```sql
id, name, code
total_amount
allocated_amount
spent_amount
remaining_amount
region_id, area_id
fiscal_year
status
```

### Invoices:
```sql
id, invoice_number
supplier_id FK -> suppliers
project_id FK -> projects
issue_date, due_date, payment_date
subtotal, tax_amount, total_amount, paid_amount
status (DRAFT, PENDING, APPROVED, PAID, CANCELLED)
```

### Invoice Items:
```sql
invoice_id FK -> invoices
worklog_id FK -> worklogs
description, quantity, unit_price, total_price
```

---

## 🚜 Equipment (43 יחידות)

### מבנה:
```sql
id, name, code
license_plate      -- לוחית רישוי
equipment_type_id FK -> equipment_types
category_id FK -> equipment_categories
supplier_id FK -> suppliers
status (available, in_use, maintenance, retired)
purchase_date, last_maintenance_date
hourly_rate
```

### Categories:
- equipment_categories (קטגוריות)
- equipment_types (סוגים)

### פילוח לפי ספק:
- ת.א.המרכז תשתיות הנגב: 7 יחידות
- איאד חוגיראת: 6 יחידות
- מ.ס. פיתוח הצפון: 5 יחידות
- אחים יקוטי, בני עפיף, א.ג. הובלות, דחפורי השחר: 3 כל אחד
- אחרים: 1-2 יחידות

---

## 🔐 System Tables

### Authentication & Authorization:

**Users (13):**
- email, username (UNIQUE)
- password_hash (bcrypt)
- two_factor_enabled
- role_id FK -> roles
- region_id, area_id, manager_id
- scope_level

**Roles:**
- ADMIN (id: 1)
- REGION_MANAGER (id: 2)
- AREA_MANAGER (id: 3)
- WORK_MANAGER (id: 4)
- ACCOUNTANT (id: 5)
- ORDER_COORDINATOR (id: 10)

**Permissions:**
- Granular permissions (resource.action)
- role_permissions (junction table)

**Sessions & Tokens:**
- sessions (JWT sessions)
- refresh_tokens
- OTP support for 2FA

### Activity Tracking:

**activity_logs:**
- user_id, action, entity_type, entity_id
- metadata_json
- ip_address, user_agent
- created_at

**activity_types:**
- סוגי פעילות במערכת

---

## 📊 סטטיסטיקות מתקדמות

### לפי מרחב:

```
┌──────────────────────────────────────────────────────┐
│ מרחב │ אזורים │ פרויקטים │ תקציב      │ WO │ WL │
├──────────────────────────────────────────────────────┤
│ צפון │   4    │    23    │ ₪188.7M    │ 17 │ 7  │
│ מרכז │   4    │    21    │ ₪31.1M     │ 0  │ 0  │
│ דרום │   4    │    16    │ ₪27.7M     │ 1  │ 0  │
└──────────────────────────────────────────────────────┘

WO = Work Orders
WL = Worklogs
```

### פרויקט פעיל ביותר:

**🏆 יער בירייה (YR-001)**
- 17 Work Orders (95% מכל ההזמנות!)
- 7 Worklogs (100% מכל הדיווחים!)
- תקציב: ₪320,000
- פעיל מאז: 2025-01-15

---

## 🔍 תובנות

### 1. ריכוזיות בפעילות
**95% מהעבודות** מרוכזות ביער בירייה בלבד!
- ייתכן שזה בגלל שאר הפרויקטים חדשים
- או שזה פרויקט pilot למערכת

### 2. מבנה גיאוגרפי מתקדם
- ✅ 3 יערות עיקריים עם גיאומטריה
- ✅ 273 פוליגונים מפורטים
- ✅ PostGIS מלא
- ✅ Spatial indexes

### 3. מוכנות למערכת מלאה
- ✅ 13 ספקים מוכנים
- ✅ 43 יחידות ציוד
- ✅ 13 משתמשים (8 אמיתיים)
- ✅ מערכת הרשאות מלאה

### 4. תקציבים גדולים
- טווח: ₪175K - ₪890K
- ממוצע: ~₪413K לפרויקט
- סה"כ: ₪247.6M

---

## ⚠️ המלצות

### 1. התחל לעבוד עם פרויקטים נוספים
רוב הפרויקטים (59/60) ללא Work Orders.  
שקול:
- להתחיל Work Orders בפרויקטים נוספים
- או לנקות פרויקטים שלא בשימוש

### 2. קישור יערות לפרויקטים
כרגע `forest_id` NULL ברוב הפרויקטים.  
שקול לקשר פרויקטים ליערות העיקריים.

### 3. השלם פרטי ספקים
חסרים: phone, email, rating  
זה ישפר את מערכת הרוטציה ההוגנת.

---

## 📈 גודל מסד הנתונים

```
סה"כ טבלאות: 35
סה"כ רשומות: ~550
  - Projects: 60
  - Forest Polygons: 273
  - Equipment: 43
  - Work Orders: 18
  - Worklogs: 7
  - Suppliers: 13
  - Users: 13
  - Areas: 12
  - Regions: 3
  - Forests: 3
  - אחרים: ~115
```

---

## 🎯 סיכום

המערכת מכילה:
- ✅ **60 פרויקטי יער** ממשיים עם תקציבים אמיתיים
- ✅ **3 יערות** עם גיאומטריה מלאה (PostGIS)
- ✅ **273 פוליגונים** גיאוגרפיים מדויקים
- ✅ **מבנה ארגוני** מלא (3 מרחבים, 12 אזורים)
- ✅ **13 ספקים** אמיתיים
- ✅ **43 יחידות ציוד**
- ✅ **מערכת הרשאות** מלאה עם 8 משתמשים אמיתיים
- ✅ **פעילות ממשית** - 18 Work Orders ו-7 Worklogs

**המערכת מוכנה לשימוש production!** (אחרי תיקוני האבטחה)

---

*נוצר ב: 2 בפברואר 2026, 18:16*  
*Database: forewise_prod*  
*PostgreSQL 16.11 + PostGIS*
