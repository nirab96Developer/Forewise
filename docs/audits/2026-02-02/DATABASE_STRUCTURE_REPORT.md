# 📊 דוח מבנה מסד הנתונים - KKL Forest Management System

**תאריך:** 2 בפברואר 2026  
**Database:** kkl_forest_prod  
**סוג:** PostgreSQL 16.11

---

## 🎯 סיכום מהיר

| ישות | כמות | תיאור |
|------|------|-------|
| **Projects (פרויקטים)** | 60 | פרויקטי יער |
| **Forests (יערות)** | 3 | יערות עיקריים |
| **Forest Polygons** | 273 | פוליגונים גיאוגרפיים |
| **Regions (מרחבים)** | 3 | צפון, מרכז, דרום |
| **Areas (אזורים)** | 12 | אזורים בתוך מרחבים |
| **Work Orders** | 18 | הזמנות עבודה |
| **Worklogs** | 7 | דיווחי שעות |
| **Suppliers** | 13 | ספקים |
| **Equipment** | 43 | ציוד כבד |
| **Users** | 13 | משתמשים |

---

## 🗂️ מבנה ארגוני

### Regions (מרחבים) - 3

| ID | שם | קוד |
|----|-----|-----|
| 1 | צפון | NORTH |
| 2 | מרכז | CENTER |
| 3 | דרום | SOUTH |

### Areas (אזורים) - 12

**מרחב צפון (4 אזורים):**
- גליל עליון ורמת הגולן
- גליל מערבי וכרמל
- גליל תחתון וגלבוע
- עמק החולה

**מרחב מרכז (4 אזורים):**
- שפלה וחוף
- ההר
- מנשה ושרון
- מנסרה מרכז

**מרחב דרום (4 אזורים):**
- נגב צפוני
- נגב מערבי
- הר הנגב וערבה
- שימור קרקע

---

## 🌲 יערות (Forests)

### 3 יערות עיקריים עם גיאומטריה:

| ID | שם | קוד | פוליגונים |
|----|-----|-----|-----------|
| 1 | יער אשתאול | ESHTAOL | מערכת MultiPolygon |
| 2 | יער חולדה | HULDA | מערכת MultiPolygon |
| 3 | יער ירושלים | JERUSALEM | מערכת MultiPolygon |

**תכונות טבלת Forests:**
- ✅ PostGIS geometry (MultiPolygon, SRID 4326)
- ✅ שטח בקמ"ר (area_km2)
- ✅ Spatial index (GIST)
- ✅ קוד ייחודי לכל יער

**Forest Polygons:** 273 פוליגונים נפרדים
- גיאומטריה מדויקת
- Hash לזיהוי ייחודי
- קישור לפרויקטים

---

## 📋 פרויקטים (Projects)

### מבנה טבלת Projects:

```sql
-- 31 עמודות
id                INTEGER PRIMARY KEY
code              VARCHAR(50) UNIQUE NOT NULL  -- קוד פרויקט
name              VARCHAR(200) NOT NULL         -- שם
description       TEXT
region_id         INTEGER FK -> regions
area_id           INTEGER FK -> areas
budget_id         INTEGER FK -> budgets
manager_id        INTEGER FK -> users
forest_id         BIGINT FK -> forests
forest_polygon_id BIGINT FK -> forest_polygons
location_geom     GEOMETRY(Point, 4326)         -- מיקום נקודתי
status            VARCHAR(50) DEFAULT 'active'
budget            NUMERIC(15,2)
start_date        DATE
end_date          DATE
work_type         VARCHAR(100)
execution_type    VARCHAR(100)
contractor_name   VARCHAR(255)
permit_required   BOOLEAN DEFAULT false
scope             TEXT
total_hours       NUMERIC(10,2)
priority          INTEGER
notes             TEXT
metadata_json     TEXT
is_active         BOOLEAN DEFAULT true
created_at        TIMESTAMP DEFAULT now()
updated_at        TIMESTAMP DEFAULT now()
deleted_at        TIMESTAMP
version           INTEGER DEFAULT 1
```

### דוגמאות פרויקטים:

**1. יער בירייה (YR-001)**
- תקציב: ₪320,000
- אזור: גליל עליון ורמת הגולן
- סוג עבודה: פיתוח שבילים
- תיאור: פיתוח ושימור יער בירייה, כולל שבילי הליכה ונקודות תצפית

**2. יער מתת (YR-002)**
- תקציב: ₪280,000
- אזור: גליל עליון ורמת הגולן
- סוג עבודה: שיקום יער
- תיאור: שיקום ופיתוח לאחר שריפות, כולל נטיעות חדשות

**3. יער הכרמל (YR-005)**
- תקציב: ₪450,000
- אזור: גליל מערבי וכרמל
- סוג עבודה: שימור טבע
- תיאור: שימור מערכות אקולוגיות ייחודיות

---

## 🔗 קשרים (Foreign Keys)

### Projects מתקשר ל:

```
Projects
├── regions (region_id)
├── areas (area_id)
├── budgets (budget_id)
├── users (manager_id)
├── forests (forest_id)
└── forest_polygons (forest_polygon_id)

Referenced by:
├── work_orders (project_id)
└── worklogs (project_id)
```

---

## 📦 Work Orders (הזמנות עבודה)

**18 הזמנות עבודה במערכת**

### מבנה:
- מקושר לפרויקט
- מקושר לספק
- מקושר לציוד
- סטטוס (DRAFT, PENDING, APPROVED, ACTIVE, COMPLETED, etc.)
- שעות משוערות + תעריף שעתי
- Portal token לספקים

---

## ⏰ Worklogs (דיווחי שעות)

**7 דיווחים במערכת**

### מבנה:
- מקושר ל-Work Order
- מקושר לפרויקט
- מקושר למשתמש (reporter)
- שעות עבודה + הפסקות
- סטטוס (DRAFT, PENDING, APPROVED, REJECTED)
- תעריף מוקפא (snapshot)
- עלות לפני/אחרי מע"מ

---

## 🚜 ציוד (Equipment)

**43 יחידות ציוד במערכת**

### קטגוריות:
- Equipment_categories (סוגי ציוד)
- Equipment_types (דגמים)
- קישור לספקים (supplier_equipment)
- מעקב תחזוקה
- סריקות ציוד (equipment_scans)

---

## 👷 ספקים (Suppliers)

**13 ספקים במערכת**

### תכונות:
- פרטי קשר
- ציוד בבעלות
- מערכת רוטציה הוגנת (supplier_rotations)
- סיבות אילוץ (supplier_constraint_reasons)
- קישור ל-Work Orders

---

## 👥 משתמשים (Users)

**13 משתמשים במערכת**

### מבנה:
- Authentication (email, password_hash)
- 2FA support (two_factor_enabled)
- קישור לתפקיד (role_id)
- קישור למרחב/אזור
- מנהל ישיר (manager_id)
- Scope level
- Sessions + Refresh tokens

---

## 🔐 מערכת הרשאות

### Roles (תפקידים):
- ADMIN
- REGION_MANAGER
- AREA_MANAGER
- WORK_MANAGER
- ORDER_COORDINATOR
- ACCOUNTANT
- SUPPLIER
- VIEWER

### Permissions (הרשאות):
- Granular permissions (resource.action)
- קישור לתפקידים דרך role_permissions

---

## 🗺️ PostGIS Features

### Spatial Tables:

**1. forests**
- geometry: MultiPolygon, SRID 4326
- Spatial index: idx_forests_geom_gist

**2. forest_polygons**
- geometry: MultiPolygon, SRID 4326
- Spatial index: idx_forest_polygons_geom
- Unique hash: ux_forest_polygons_geom_hash

**3. projects**
- location_geom: Point, SRID 4326
- Spatial index: idx_projects_location_geom_gist

### PostGIS Extensions:
- ✅ spatial_ref_sys (טבלת מערכות ייחוס)
- ✅ geography_columns
- ✅ geometry_columns

---

## 📊 טבלאות נוספות

### System:
- activity_logs (לוג פעילות)
- activity_types (סוגי פעילות)
- notifications (התראות)
- system_settings (הגדרות מערכת)

### Finance:
- budgets (תקציבים)
- invoices (חשבוניות)
- invoice_items (פריטי חשבונית)
- invoice_payments (תשלומים)

### Reference:
- departments (מחלקות)
- locations (מיקומים)
- work_order_statuses (סטטוסי הזמנות)
- worklog_statuses (סטטוסי דיווחים)

---

## 🔍 Indexes

### Projects:
- ✅ PRIMARY KEY (id)
- ✅ UNIQUE (code)
- ✅ Index על region_id
- ✅ Index על forest_polygon_id
- ✅ Spatial index על location_geom

### Forests:
- ✅ PRIMARY KEY (id)
- ✅ UNIQUE (code)
- ✅ Spatial index על geom

### Forest Polygons:
- ✅ PRIMARY KEY (id)
- ✅ Spatial index על geom
- ✅ UNIQUE על geom_hash

---

## 📈 סטטיסטיקות

### פרויקטים לפי מרחב:
```
צפון: ~25 פרויקטים (יער בירייה, מתת, עמיעד, הכרמל, וכו')
מרכז: ~20 פרויקטים (בן שמן, חולדה, הזורעים, וכו')
דרום: ~15 פרויקטים
```

### תקציבים:
- ממוצע: ~₪250,000 לפרויקט
- טווח: ₪185,000 - ₪450,000

### סוגי עבודה:
- פיתוח שבילים
- שיקום יער
- תחזוקה
- פיתוח נופש
- שימור טבע

---

## ⚠️ הערות חשובות

### 1. הקשר Projects ↔ Forests
**כרגע:** רוב הפרויקטים **לא** מקושרים ישירות ליערות (forest_id = NULL)

זה כנראה מכוון - הפרויקטים מקושרים ל:
- Regions & Areas (מבנה ארגוני)
- Forest Polygons (גיאומטריה ספציפית)

**3 היערות** משמשים כטבלת reference עם גיאומטריה כללית.

### 2. Dual Geometry System
המערכת משתמשת ב-**2 מערכות גיאומטריה**:
- **forests.geom** - MultiPolygon של יער שלם
- **projects.location_geom** - Point של מיקום פרויקט
- **forest_polygons.geom** - MultiPolygon ספציפי לפרויקט

### 3. Unicode Support
✅ כל השמות בעברית מאוכסנים נכון (UTF-8)

---

## 🎯 סיכום

המערכת מכילה:
- ✅ **60 פרויקטים** פעילים
- ✅ **3 יערות** עיקריים עם גיאומטריה
- ✅ **273 פוליגונים** גיאוגרפיים מדויקים
- ✅ **3 מרחבים** ו-**12 אזורים**
- ✅ **18 הזמנות עבודה** ו-**7 דיווחי שעות**
- ✅ **13 ספקים** ו-**43 יחידות ציוד**
- ✅ תמיכה מלאה ב-**PostGIS** (גיאומטריה)
- ✅ מערכת הרשאות מתקדמת
- ✅ תמיכה בעברית (Unicode)

---

*נוצר ב: 2 בפברואר 2026*
