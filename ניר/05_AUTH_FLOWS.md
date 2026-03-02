# Auth Flows — כל זרימות האימות

## 1. Login רגיל (Username + Password)

```mermaid
sequenceDiagram
    participant U as 👤 משתמש
    participant FE as 🖥️ Frontend
    participant BE as ⚙️ Backend
    participant DB as 🗄️ PostgreSQL

    U->>FE: מזין username + password
    FE->>BE: POST /api/v1/auth/login
    BE->>DB: SELECT user WHERE username=?
    DB-->>BE: user record
    BE->>BE: bcrypt.verify(password, hash)
    alt 2FA מופעל
        BE-->>FE: {requires_2fa: true, user_id}
        FE->>FE: navigate('/otp')
        Note over U,FE: → זרימת OTP
    else Login ישיר
        BE->>DB: INSERT session
        BE->>BE: create_access_token (30min JWT)
        BE->>BE: create_refresh_token (7/30 days)
        BE-->>FE: {access_token, refresh_token, user}
        FE->>FE: setAuthSession(localStorage/sessionStorage)
        FE->>FE: window.location.replace('/')
        FE->>FE: ProtectedRoute checks auth
        FE-->>U: Dashboard לפי role
    end
```

---

## 2. OTP / 2FA Flow

```mermaid
sequenceDiagram
    participant U as 👤 משתמש
    participant FE as 🖥️ Frontend
    participant BE as ⚙️ Backend
    participant EMAIL as 📧 Email

    Note over U,EMAIL: זרימה מתוך Login שהחזיר requires_2fa=true
    BE->>BE: generate 6-digit OTP
    BE->>DB: INSERT otp_tokens (code_hash, expires_at=now+5min)
    BE->>EMAIL: send_email(code)
    U->>FE: מזין קוד OTP
    FE->>BE: POST /api/v1/auth/verify-otp-v2 {identifier, code}
    BE->>DB: SELECT otp_token (not expired, not used)
    BE->>BE: SHA256(code) == code_hash?
    alt קוד שגוי
        BE->>DB: attempts++
        alt attempts >= 3
            BE-->>FE: 429 Too Many Attempts
        else
            BE-->>FE: 400 + remaining attempts
        end
    else קוד נכון
        BE->>DB: otp.is_used=true
        BE->>BE: create JWT tokens
        BE->>DB: INSERT device_token (if device_id provided)
        BE-->>FE: {access_token, refresh_token, device_token}
        FE->>FE: שמירה + navigate('/')
    end
```

---

## 3. Device Token / Biometric Flow

```mermaid
sequenceDiagram
    participant U as 👤 משתמש
    participant FE as 🖥️ Frontend
    participant KEYCHAIN as 🔑 Keychain/Storage
    participant BE as ⚙️ Backend

    Note over U,BE: פתיחת אפליקציה מחדש

    FE->>KEYCHAIN: יש device_token?
    alt יש device_token
        FE->>U: בקש ביומטריה (FaceID/TouchID)
        U->>FE: ביומטריה הצליחה
        FE->>BE: POST /api/v1/auth/device-login {device_token}
        BE->>DB: SELECT device_tokens WHERE token_hash=SHA256(token)
        BE->>BE: is_active=true AND expires_at > NOW()?
        alt תקין
            BE->>DB: last_used_at=NOW()
            BE->>BE: create new JWT tokens
            BE-->>FE: {access_token, refresh_token}
            FE-->>U: נכנס ישירות
        else פג תוקף
            BE-->>FE: 401 token_expired
            FE-->>U: מסך OTP מחדש
        end
    else אין device_token
        FE-->>U: מסך Login רגיל → OTP → device_token נשמר
    end
```

---

## 4. Auto Refresh Token

```mermaid
sequenceDiagram
    participant FE as 🖥️ Frontend
    participant BE as ⚙️ Backend

    Note over FE,BE: API call מחזיר 401

    FE->>FE: interceptor נתפס
    FE->>FE: getRefreshToken() מ-storage
    FE->>BE: POST /api/v1/auth/refresh {refresh_token}
    alt refresh תקין
        BE-->>FE: {access_token חדש}
        FE->>FE: שמירת access_token חדש
        FE->>BE: retry original request
    else refresh פג
        BE-->>FE: 401
        FE->>FE: clearAuthSession()
        FE->>FE: window.location.href='/login'
    end
```

---

## 5. Forgot Password Flow

```mermaid
sequenceDiagram
    participant U as 👤 משתמש
    participant FE as 🖥️ Frontend
    participant BE as ⚙️ Backend
    participant EMAIL as 📧 Email

    U->>FE: מזין אימייל
    FE->>BE: POST /api/v1/auth/request-otp {identifier: email}
    BE->>DB: user exists?
    Note over BE: תמיד מחזיר 200 (לא מגלה אם email קיים)
    BE->>BE: generate OTP + hash
    BE->>DB: INSERT otp_tokens
    BE->>EMAIL: שלח קוד
    BE-->>FE: {message: "קוד נשלח", expires_in: 300}
    U->>FE: מזין קוד חדש
    FE->>BE: POST /api/v1/auth/reset-password/confirm {token, new_password}
    BE->>DB: verify token
    BE->>DB: UPDATE user SET password_hash=bcrypt(new_password)
    BE->>DB: otp.is_used=true
    BE-->>FE: 200 OK
    FE-->>U: ← חזרה ל-Login
```

---

## 6. Remember Me — Storage Policy

```mermaid
flowchart TD
    LOGIN["POST /auth/login\n{remember_me: bool}"]
    
    LOGIN -->|"remember_me=true"| LOCAL["localStorage\naccess_token\nrefresh_token\nuser\nisAuthenticated"]
    LOGIN -->|"remember_me=false"| SESSION["sessionStorage\naccess_token\nrefresh_token\nuser\nisAuthenticated"]
    
    LOCAL -->|"tab/browser סגור ← פתוח"| PERSIST["נשמר ✅\nRefresh אוטומטי"]
    SESSION -->|"tab סגור"| GONE["נמחק ✅\nחייב login מחדש"]

    subgraph READS["קריאה (ProtectedRoute + permissions.ts + authService)"]
        READ["localStorage.getItem(key)\nOR\nsessionStorage.getItem(key)"]
    end
```

---

## 7. RBAC — Roles & Permissions

```mermaid
flowchart LR
    subgraph ROLES["Roles"]
        ADMIN["ADMIN\nגישה מלאה"]
        REGION["REGION_MANAGER\nמרחב ספציפי"]
        AREA["AREA_MANAGER\nאזור ספציפי"]
        WORK["WORK_MANAGER\nניהול עבודה"]
        ACCT["ACCOUNTANT\nכספים"]
        COORD["ORDER_COORDINATOR\nתיאום הזמנות"]
        FIELD["FIELD_WORKER\nדיווחים"]
        SUPPLIER["SUPPLIER\nפורטל חיצוני"]
        VIEWER["VIEWER\nצפייה בלבד"]
    end

    subgraph PERMS["Permission Examples"]
        P1["PROJECTS.VIEW"]
        P2["WORK_ORDERS.CREATE"]
        P3["WORK_ORDERS.APPROVE"]
        P4["WORKLOGS.APPROVE"]
        P5["SUPPLIERS.UPDATE"]
        P6["INVOICES.APPROVE"]
        P7["USERS.CREATE"]
    end

    subgraph SCOPE["Scope Filtering"]
        SCP["Backend filters:\nregion_id == user.region_id\nOR area_id == user.area_id\n404 for unauthorized by-id"]
    end

    ADMIN --> P1 & P2 & P3 & P4 & P5 & P6 & P7
    REGION --> P1 & P3
    AREA --> P1
    WORK --> P1 & P2
    ACCT --> P6
    COORD --> P3
    FIELD --> P4
```
