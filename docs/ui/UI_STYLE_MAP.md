# UI Style Map (Frontend)

מסמך זה מרכז את כל שכבות ה-UI בצד לקוח: עיצוב גלובלי, קומפוננטות משותפות, ניווט, דפי מערכת ומפה.

## 1) Design Foundation

- `app_frontend/tailwind.config.js`
  - פלטת צבעים (KKL + Hillan + legacy)
  - keyframes + animations גלובליות
  - Tailwind forms plugin
- `app_frontend/src/index.css`
  - משתני `:root` (צבעים, צללים, radius)
  - RTL בסיסי (`[dir="rtl"]`)
  - scrollbars, utilities, כפתורים, כרטיסים, loading
  - התאמות מובייל (`@media`)
- `app_frontend/src/styles/animations.css`
  - אנימציות נוספות (fade/slide/shimmer/float וכו')
- `app_frontend/src/pages/SupplierPortal/SupplierPortal.css`
  - עיצוב נקודתי למסך פורטל ספק בלבד

## 2) Reusable UI Components

תיקיה: `app_frontend/src/components/common/`

- `Button.tsx` - וריאנטים וגדלים
- `Card.tsx` - Card/Header/Title/Content
- `Modal.tsx` - חלון קופץ עם overlay
- `Tabs.tsx` - לשוניות (underline/contained/pills)
- `Input.tsx`, `Select.tsx`, `DatePicker.tsx`
- `Badge.tsx`, `StatusBadge.tsx`, `Alert.tsx`
- `Loader.tsx`, `LoadingScreen.tsx`, `PageLoader.tsx`, `UnifiedLoader.tsx`, `Skeleton.tsx`
- `Toast.tsx`, `EmptyState.tsx`
- `ProtectedRoute.tsx`, `RedirectRoute.tsx`

## 3) Layout + Navigation

- `app_frontend/src/components/Navigation/Navigation.tsx`
  - Header עליון
  - Sidebar ימני
  - Mobile menu
  - User block + notifications
  - תפריט דינמי לפי role
- `app_frontend/src/components/layout/PageContainer.tsx`
- `app_frontend/src/components/layout/Card.tsx`

## 4) Map UI Ownership

- `app_frontend/src/pages/Map/ForestMap.tsx`
  - UI של דף המפה
  - פאנל שכבות/מרחבים
  - spacing, widths, toggles, back-to-menu
  - popup content business text
- `app_frontend/src/components/Map/LeafletMap.tsx`
  - מנוע המפה (Leaflet)
  - tiles, marker rendering, polygons, popups, fit-bounds
- `app_frontend/src/components/Map/ProjectMap.tsx`
  - מפה נקודתית/ייעודית לפרויקט

## 5) Pages by Domain

תיקיה: `app_frontend/src/pages/`

- Auth: `Login/*`, `OTP/OTP.tsx`
- Dashboard: `Dashboard/*`
- Projects: `Projects/*`
- Work Orders: `WorkOrders/*`
- Work Logs: `WorkLogs/*`
- Suppliers: `Suppliers/*`
- Equipment: `Equipment/*`
- Settings: `Settings/*`
- Regions/Areas/Locations: `Regions/*`, `Areas/*`, `Locations/*`
- Invoices/Reports/Notifications/Support: `Invoices/*`, `Reports/*`, `Notifications/*`, `Support/*`

## 6) Where to Change What (Quick Guide)

- צבעים/טיפוגרפיה/אנימציות גלובליות: `tailwind.config.js`, `src/index.css`, `src/styles/animations.css`
- קומפוננטה בסיסית לכל המערכת (כפתור/מודאל/לשוניות): `src/components/common/*`
- תפריט רגיל של האפליקציה: `src/components/Navigation/Navigation.tsx`
- UI של פאנל המפה: `src/pages/Map/ForestMap.tsx`
- התנהגות מפת Leaflet עצמה: `src/components/Map/LeafletMap.tsx`

## 7) Conventions

- ברירת מחדל: RTL-first
- לא משנים Layout/Theme באופן נקודתי בדפים בלי צורך מוצרי
- מעדיפים שימוש ב-common components במקום CSS מקומי חדש
- עיצוב דף יחיד רק אם יש צורך ברור (כמו `SupplierPortal.css`)

