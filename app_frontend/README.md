# KKL Time Report - מערכת דיווח שעות

## התקנה מהירה

### שלב 1: התקנה

הפעל את הקובץ `install.bat` - זה יתקין את כל הדרוש.

### שלב 2: הפעלה

יש לך 3 אפשרויות:

#### אפשרות 1: הפעלה מלאה (מומלץ)

הפעל את `run-all.bat` - זה יפעיל את שרת הדמה ואת האפליקציה יחד.

#### אפשרות 2: הפעלה נפרדת

1. הפעל את `run-mock-server.bat` (חלון נפרד)
2. הפעל את `run-app.bat` (חלון נפרד)

#### אפשרות 3: הפעלה ידנית

```bash
# חלון 1 - שרת דמה
cd mock-server
npm start

# חלון 2 - אפליקציה
npm run electron:preview
```

## נתוני התחברות

- **Username:** `admin`
- **Password:** `password`

או:

- **Username:** `manager`
- **Password:** `password`

או:

- **Username:** `worker`
- **Password:** `password`

## פתרון בעיות

### אם ההתחברות לא עובדת:

1. ודא ששרת הדמה רץ על פורט 3001
2. ודא שהאפליקציה בנויה (הפעל `install.bat` שוב)
3. ודא שהלוגו נמצא בתיקיית `dist`

### אם יש שגיאות:

1. הפעל `install.bat` מחדש
2. ודא שיש לך Node.js מותקן
3. ודא שיש לך npm מותקן

## בניית אפליקציה להפצה

```bash
npm run electron:build
```

הקובץ יהיה בתיקיית `dist_electron/win-unpacked/`
