# 🧪 חבילת בדיקות Cypress - KKL Time Report

חבילת בדיקות אוטומטיות מלאה לבדיקת כל הכפתורים והניווטים באפליקציה.

## 📁 מבנה הקבצים

```
cypress/
├── e2e/
│   ├── login.cy.ts              # בדיקות התחברות
│   ├── work_manager.cy.ts       # בדיקות מנהל עבודה
│   ├── area_manager.cy.ts       # בדיקות מנהל אזור
│   ├── region_manager.cy.ts     # בדיקות מנהל מרחב
│   ├── accountant.cy.ts         # בדיקות רואה חשבון
│   ├── supplier_portal.cy.ts    # בדיקות פורטל ספק
│   ├── common_actions.cy.ts     # בדיקות פעולות כלליות
│   ├── offline.cy.ts           # בדיקות מצב לא מקוון
│   └── security.cy.ts          # בדיקות אבטחה
├── fixtures/
│   └── users.json              # נתוני משתמשים לבדיקות
└── support/
    ├── commands.ts             # פקודות עזר מותאמות אישית
    └── e2e.ts                  # הגדרות Cypress
```

## 🚀 הרצה מקומית

### 1. התקנת תלויות

```bash
cd app_frontend
npm install
```

### 2. הגדרת משתני סביבה

הקבצים הבאים כבר נוצרו:

- `.env` - משתני סביבה ל-Frontend
- `cypress.env.json` - משתני סביבה ל-Cypress

### 3. הרצת הבדיקות

#### פתיחת Cypress GUI:

```bash
npm run cy:open
```

#### הרצה במצב headless:

```bash
npm run cy:run
```

## 🔧 הגדרות נדרשות

### משתני סביבה

עדכן את הקבצים הבאים לפי הסביבה שלך:

**`.env`:**

```env
VITE_APP_BASE_URL=http://localhost:3000
VITE_API_BASE_URL=http://localhost:8000
```

**`cypress.env.json`:**

```json
{
  "APP_BASE_URL": "http://localhost:3000",
  "API_BASE_URL": "http://localhost:8000",
  "ADMIN_EMAIL": "admin@demo.local",
  "ADMIN_PASSWORD": "123456"
}
```

## 🎯 data-testid נדרשים

כדי שהבדיקות יעבדו, יש להוסיף את ה-`data-testid` הבאים לקוד ה-UI:

### Login

- `[data-testid=login-submit]`
- `[data-testid=login-get-otp]`
- `[data-testid=login-verify-otp]`

### Navigation

- `[data-testid=nav-my-projects]`
- `[data-testid=nav-activity]`
- `[data-testid=nav-area-projects]`

### Projects

- `[data-testid=project-view]`
- `[data-testid=project-order-supplier]`
- `[data-testid=project-report-hours]`

### Forms

- `[data-testid=fair-tool-type]`
- `[data-testid=fair-start-date]`
- `[data-testid=fair-submit]`

### Messages

- `[data-testid=toast-success]`
- `[data-testid=toast-error]`

## 🔄 CI/CD

הבדיקות רצות אוטומטית ב-GitHub Actions על כל push ו-pull request.

קובץ: `.github/workflows/e2e.yml`

## 📝 הוראות שימוש

### לפני הרצה ראשונה:

1. ודא שה-Frontend רץ על פורט 3000
2. ודא שה-Backend רץ על פורט 8000
3. ודא שיש משתמש admin עם הנתונים ב-`cypress.env.json`
4. הוסף את כל ה-`data-testid` הנדרשים לקוד

### הרצה מהירה:

```bash
# Terminal 1: הפעלת Frontend
cd app_frontend
npm run dev

# Terminal 2: הרצת בדיקות
cd app_frontend
npm run cy:run
```

## 🐛 פתרון בעיות

### שגיאות נפוצות:

1. **"Element not found"** - ודא שה-`data-testid` נוסף לקוד
2. **"Network error"** - ודא שה-Backend רץ
3. **"Login failed"** - בדוק את נתוני המשתמש ב-`cypress.env.json`

### דיבוג:

```bash
# הרצה עם GUI לדיבוג
npm run cy:open

# הרצה עם וידאו
npx cypress run --record
```

## 📊 דוחות

הבדיקות מייצרות:

- וידאו של כל בדיקה
- צילומי מסך במקרה של כשל
- דוחות JSON עם תוצאות

## 🔗 קישורים שימושיים

- [Cypress Documentation](https://docs.cypress.io/)
- [Testing Library for Cypress](https://testing-library.com/docs/cypress-testing-library/intro/)
- [GitHub Actions](https://docs.github.com/en/actions)
