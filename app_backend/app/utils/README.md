# 🛠️ Utility Functions - פונקציות עזר

## 📁 מבנה התיקיות

### 🔧 **Core Utilities**
- `common.py` - פונקציות עזר כלליות
- `__init__.py` - ייבוא מודולים

### 💰 **Budget Management**
- `budgets/` - כלים לניהול תקציבים
  - `calculations.py` - חישובי תקציב
  - `validators.py` - בדיקות תקציב

### 🗄️ **Model Utilities**
- `models/` - כלים למודלים
  - `serializers.py` - המרת מודלים
  - `validators.py` - בדיקות מודלים

### ✅ **Validation**
- `validators/` - בדיקות תקינות
  - `email.py` - בדיקות אימייל
  - `phone.py` - בדיקות טלפון
  - `budget.py` - בדיקות תקציב

### 💾 **Cache Management**
- `cache/` - ניהול מטמון
  - `redis.py` - חיבור Redis
  - `decorators.py` - עיטורי מטמון

### 📅 **Date & Time**
- `dates/` - כלי תאריכים
  - `hebrew_calendar.py` - לוח שנה עברי
  - `workdays.py` - ימי עבודה

### 📁 **File Management**
- `files/` - ניהול קבצים
  - `upload.py` - העלאת קבצים
  - `storage.py` - אחסון קבצים

### 📝 **Formatting**
- `formatters/` - עיצוב נתונים
  - `currency.py` - עיצוב מטבע
  - `phone.py` - עיצוב טלפון

### 🇮🇱 **Hebrew Support**
- `hebrew/` - תמיכה בעברית
  - `text.py` - עיבוד טקסט עברי
  - `numbers.py` - מספרים עבריים

## 🔗 קשרים עיקריים
- **Common** → **All Utilities**
- **Validators** → **Models** → **Services**

## 📊 סטטיסטיקות
- **סה"כ תיקיות:** 8
- **סה"כ קבצים:** 15+
- **סה"כ שורות קוד:** 1,500+
