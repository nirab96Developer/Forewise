# 🌲 Forest Management System - מערכת ניהול יערות

מערכת ניהול מתקדמת לקק"ל (קרן קיימת לישראל) לניהול פרויקטים, ציוד, ספקים ודיווחי שעות.

## 🎯 יכולות המערכת

### 📋 ניהול פרויקטים

- יצירה ועדכון פרויקטים
- מעקב אחר התקדמות ומיליונים
- הקצאת צוותים ומשאבים
- ניהול תקציבים וזמנים

### 🚜 ניהול ציוד

- רישום וסיווג ציוד
- הקצאת ציוד לפרויקטים
- תחזוקה מונעת ותקלות
- סריקות QR ומיקום

### 👷 ניהול ספקים

- סבב הוגן בין ספקים
- הזמנות עבודה אוטומטיות
- מעקב ביצועים ואיכות
- ניהול חוזים ותשלומים

### ⏰ דיווחי שעות

- דיווח שעות עבודה מפורט
- חישוב אוטומטי של עלויות
- אישור דיווחים
- דוחות יומיים ושבועיים

### 💰 כספים וחשבוניות

- הפקת חשבוניות אוטומטיות
- ניהול תקציבים והקצאות
- מעקב תשלומים
- דוחות כספיים

### 🔐 אבטחה והרשאות

- הזדהות מאובטחת עם JWT
- ניהול הרשאות מתקדם (RBAC)
- תיעוד כל הפעולות במערכת
- אימות דו-שלבי (2FA)

## 🏗️ ארכיטקטורה

המערכת בנויה בשכבות:

### 1. Database Schema Layer

- מודלים של SQLAlchemy
- קשרים בין טבלאות
- אינדקסים ואילוצים

### 2. Business Logic Layer (Services)

- לוגיקה עסקית
- חוקים ותהליכים
- חישובים ואימותים

### 3. API Validation Layer (Schemas)

- Pydantic schemas
- וולידציה של קלט ופלט
- תיעוד אוטומטי

### 4. API Endpoints Layer (Routers)

- FastAPI endpoints
- ניהול בקשות ותגובות
- הרשאות ואבטחה

## 🚀 התקנה והרצה

### דרישות מערכת

- Python 3.11+
- PostgreSQL 13+
- Redis (אופציונלי)

### התקנה

```bash
# שכפול הפרויקט
git clone <repository-url>
cd app_backend

# יצירת סביבה וירטואלית
py -m venv venv
source venv/bin/activate  # Linux/Mac
# או
venv\Scripts\activate  # Windows

# התקנת תלויות
pip install -r requirements.txt

# הגדרת משתני סביבה
cp .env.example .env
# ערוך את .env עם ההגדרות שלך

# הרצת מיגרציות
alembic upgrade head

# יצירת משתמש מנהל
py app/scripts/create_admin.py

# הרצת השרת
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### משתני סביבה

```env
# Database
DATABASE_URL=postgresql://user:password@localhost/forest_db

# Security
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis (אופציונלי)
REDIS_URL=redis://localhost:6379

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# App Settings
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=True
ENVIRONMENT=development
```

## 📚 תיעוד API

לאחר הרצת השרת, ניתן לגשת לתיעוד האוטומטי:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔧 פיתוח

### מבנה הפרויקט

```
app_backend/
├── app/
│   ├── core/           # הגדרות בסיסיות
│   ├── models/         # מודלי בסיס נתונים
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # לוגיקה עסקית
│   ├── routers/        # API endpoints
│   ├── utils/          # כלי עזר
│   └── scripts/        # סקריפטים
├── alembic/            # מיגרציות בסיס נתונים
├── tests/              # בדיקות
└── requirements.txt    # תלויות
```

### הרצת בדיקות

```bash
# כל הבדיקות
pytest

# בדיקות עם כיסוי
pytest --cov=app

# בדיקות ספציפיות
pytest tests/test_auth.py
```

### עיצוב קוד

```bash
# עיצוב אוטומטי
black app/

# בדיקת איכות קוד
flake8 app/

# בדיקת טיפוסים
mypy app/
```

## 🗄️ בסיס נתונים

### מודלים עיקריים

#### היררכיה גיאוגרפית

- **Regions** (מרחבים) - רמה עליונה
- **Areas** (אזורים) - רמה בינונית
- **Locations** (מיקומים) - רמה תחתונה

#### משתמשים והרשאות

- **Users** - משתמשים
- **Roles** - תפקידים
- **Permissions** - הרשאות
- **Sessions** - הפעלות

#### פרויקטים ועבודה

- **Projects** - פרויקטים
- **Work Orders** - הזמנות עבודה
- **Worklogs** - דיווחי שעות
- **Milestones** - אבני דרך

#### ציוד ותחזוקה

- **Equipment** - ציוד
- **Equipment Categories** - קטגוריות ציוד
- **Equipment Assignments** - הקצאות ציוד
- **Equipment Maintenance** - תחזוקה

#### כספים

- **Budgets** - תקציבים
- **Invoices** - חשבוניות
- **Payments** - תשלומים
- **Budget Allocations** - הקצאות תקציב

### מיגרציות

```bash
# יצירת מיגרציה חדשה
alembic revision --autogenerate -m "description"

# הרצת מיגרציות
alembic upgrade head

# חזרה למיגרציה קודמת
alembic downgrade -1
```

## 🔐 אבטחה

### הזדהות

- JWT tokens עם refresh
- אימות דו-שלבי (2FA)
- נעילת חשבונות לאחר ניסיונות כושלים
- ניהול הפעלות

### הרשאות

- Role-Based Access Control (RBAC)
- הרשאות ברמת משאב
- סינון נתונים לפי תפקיד
- תיעוד כל הפעולות

### הגנה

- CORS מוגדר
- Rate limiting
- SQL injection protection
- XSS protection

## 📊 דוחות ואנליטיקס

### דוחות זמינים

- דוח פרויקטים
- דוח שעות עבודה
- דוח תקציבים
- דוח ציוד
- דוח ספקים

### ייצוא נתונים

- Excel/CSV
- PDF
- JSON API

## 🚀 פריסה

### Docker

```bash
# בניית תמונה
docker build -t forest-management .

# הרצה
docker run -p 8000:8000 forest-management
```

### Docker Compose

```bash
# הרצה עם בסיס נתונים
docker-compose up -d
```

### פריסה לייצור

- השתמש ב-Gunicorn
- הגדר Nginx כפרוקסי
- השתמש ב-PostgreSQL בייצור
- הגדר Redis לקאש
- השתמש ב-SSL/TLS

## 🤝 תרומה לפרויקט

1. Fork את הפרויקט
2. צור branch חדש (`git checkout -b feature/amazing-feature`)
3. Commit את השינויים (`git commit -m 'Add amazing feature'`)
4. Push ל-branch (`git push origin feature/amazing-feature`)
5. פתח Pull Request

## 📝 רישיון

פרויקט זה הוא קנייני של קק"ל (קרן קיימת לישראל).

## 📞 תמיכה

לשאלות ותמיכה:

- Email: dev@forest-system.com
- תיעוד: /docs
- Issues: GitHub Issues

## 🏷️ גרסאות

### v1.0.0 (נוכחית)

- מערכת בסיסית מלאה
- ניהול פרויקטים וציוד
- דיווחי שעות וחשבוניות
- אבטחה והרשאות

### תכניות עתידיות

- אפליקציה מובייל
- אינטגרציה עם מערכות חיצוניות
- AI לניתוח נתונים
- דוחות מתקדמים יותר

---

**פותח עם ❤️ עבור קק"ל**
