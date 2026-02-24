# 🔑 Google Maps API Key - הבעיה והפתרון

**תאריך:** 2 בפברואר 2026  
**בעיה:** המפה "טוען מפה..." ולא נטענת  
**סיבה:** API Key מוגבל לdomains אחרים

---

## 🔍 הבעיה

יש לך **2 API Keys שונים**:

### Development (.env):
```
VITE_GOOGLE_MAPS_API_KEY=AIzaSyCxYnvuDsofgDxi_KOczhLnuEW80xH06jU
```

### Production (.env.production):
```
VITE_GOOGLE_MAPS_API_KEY=AIzaSyAhfG1czq1pQN3dWC0EYD1E37lz5N520d8
```

**הבעיה:** כל API key מוגבל ל-domains מסוימים, ו-**http://167.99.228.10** לא ברשימה!

---

## ⚡ פתרון מהיר (5 דקות)

### אופציה 1: הסר הגבלות זמנית

1. **גש ל-Google Cloud Console:**  
   https://console.cloud.google.com/apis/credentials

2. **בחר את ה-API Key:**
   - AIzaSyCxYnvuDsofgDxi_KOczhLnuEW80xH06jU (development)
   - AIzaSyAhfG1czq1pQN3dWC0EYD1E37lz5N520d8 (production)

3. **Application restrictions:**
   ```
   בחר: None (לא מומלץ לפרודקשן, אבל עובד לבדיקה)
   
   או:
   
   HTTP referrers → הוסף:
   http://167.99.228.10/*
   http://localhost:5173/*
   ```

4. **שמור**

5. **המתן 2-5 דקות** לעדכון

6. **Hard Refresh:** Ctrl+Shift+R

---

## ✅ פתרון מומלץ (Production)

### צעד 1: עדכן API Key Restrictions

```
Google Cloud Console → API Key → Application restrictions

הוסף את ה-domains שלך:

Production:
http://167.99.228.10/*

Development:
http://localhost:5173/*
http://localhost:5174/*
http://127.0.0.1:5173/*
http://10.0.0.20:5173/*
```

### צעד 2: וודא שהשירותים מופעלים

```
Google Cloud Console → APIs & Services → Enabled APIs

וודא שפעילים:
✅ Maps JavaScript API
✅ Places API (אם משתמש)
✅ Geocoding API (אם משתמש)
```

---

## 🔧 פתרון חלופי: השתמש ב-API key ללא הגבלות

### צור API key חדש לבדיקות:

```
1. Google Cloud Console → Create Credentials → API Key
2. לא להגדיר הגבלות (None)
3. העתק את ה-key
4. עדכן ב-.env:
   VITE_GOOGLE_MAPS_API_KEY=<NEW_KEY>
5. npm run build
6. העתק ל-production
```

---

## 🧪 בדיקה אם ה-API key עובד

### Test 1: מהטרמינל
```bash
curl "https://maps.googleapis.com/maps/api/js?key=AIzaSyCxYnvuDsofgDxi_KOczhLnuEW80xH06jU&libraries=places"

# אמור לקבל: JavaScript code (לא שגיאה)
```

### Test 2: מהדפדפן
```
1. פתח: http://167.99.228.10/regions/3
2. F12 → Console
3. חפש: "RefererNotAllowedMapError"
   
   אם רואה את זה → API key מוגבל!
```

---

## 📋 מה עושה כל API Key

### AIzaSyCxYnvuDsofgDxi_KOczhLnuEW80xH06jU
- נמצא ב-.env (development)
- נבנה לתוך dist/ כברירת מחדל
- **צריך הרשאה ל:** http://167.99.228.10

### AIzaSyAhfG1czq1pQN3dWC0EYD1E37lz5N520d8
- נמצא ב-.env.production
- לא נכלל ב-build (אלא אם עושים `npm run build` עם הקובץ הזה)
- **צריך הרשאה ל:** http://167.99.228.10

---

## 🎯 המלצה שלי

### לטווח קצר (עכשיו):

```
1. גש ל-Google Cloud Console
2. בחר API key: AIzaSyCxYnvuDsofgDxi_KOczhLnuEW80xH06jU
3. Application restrictions → None
4. שמור
5. המתן 3 דקות
6. Hard refresh: http://167.99.228.10/regions/3
```

### לטווח ארוך (production):

```
1. צור API key חדש ייעודי לproduction
2. הגבל אותו רק ל: http://167.99.228.10/*
3. שמור ב-.env (לא ב-git!)
4. Build ו-deploy
```

---

## ⚠️ הערת אבטחה

### כרגע ב-production יש API key חשוף:

```
📁 /var/www/html/assets/main-*.js
🔑 AIzaSyCxYnvuDsofgDxi_KOczhLnuEW80xH06jU (exposed!)
```

**זה בסדר לבדיקות, אבל לפני production אמיתי:**
1. צור API key חדש
2. הגבל אותו לdomain שלך
3. הגדר Billing alerts
4. עקוב אחר usage

---

## 🚀 Quick Fix כרגע:

### אופציה 1: הסר הגבלות (5 דקות)
```
Google Cloud Console → API Key → None → Save
המתן 3 דקות
Hard Refresh
```

### אופציה 2: הוסף domain (5 דקות)
```
Google Cloud Console → API Key → HTTP referrers
הוסף: http://167.99.228.10/*
Save
המתן 3 דקות  
Hard Refresh
```

---

## 📞 עזרה נוספת

אם לא מסתדר, אני יכול:
1. לעזור עם Google Cloud Console
2. ליצור API key חדש ללא הגבלות
3. לבדוק logs של המפה

---

**תעדכן אותי אחרי שתנסה את הפתרון!** 🎯

---

*נוצר ב: 2 בפברואר 2026*
