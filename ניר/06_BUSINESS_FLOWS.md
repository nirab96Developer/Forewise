# Business Flows — זרימות עסקיות

## 1. Work Order Flow מקצה לקצה

```mermaid
stateDiagram-v2
    [*] --> PENDING : מנהל עבודה יוצר WO

    PENDING --> DISTRIBUTING : שלח לספק\n(POST /work-orders/{id}/send-to-supplier)
    DISTRIBUTING --> DISTRIBUTING : ספק דחה\n(move-to-next-supplier)
    DISTRIBUTING --> APPROVED : ספק אישר\n(POST /supplier-portal/{token}/accept)
    DISTRIBUTING --> REJECTED : ספק דחה סופי
    APPROVED --> ACTIVE : התחל עבודה\n(POST /work-orders/{id}/start)
    ACTIVE --> COMPLETED : סיים עבודה\n(POST /work-orders/{id}/close)
    APPROVED --> CANCELLED : בטל
    ACTIVE --> CANCELLED : בטל
    COMPLETED --> [*]
    CANCELLED --> [*]
    REJECTED --> PENDING : צור מחדש
```

---

## 2. Work Order — Sequence מלא

```mermaid
sequenceDiagram
    participant WM as 👷 מנהל עבודה
    participant COORD as 📋 מתאם הזמנות
    participant BE as ⚙️ Backend
    participant SUPP as 🚛 ספק
    participant PORTAL as 🌐 Supplier Portal

    WM->>BE: POST /work-orders {project_id, equipment_model_id, ...}
    BE-->>WM: WO created (status=PENDING)

    WM->>BE: POST /work-orders/{id}/send-to-supplier
    BE->>BE: generate portal_token (expires+3h)
    BE->>BE: status = DISTRIBUTING
    BE->>SUPP: 📧 מייל עם קישור\nhttps://forewise.co/supplier-portal/{token}
    BE-->>WM: {portal_url, expires_at}

    SUPP->>PORTAL: פותח קישור
    PORTAL->>BE: GET /supplier-portal/{token}
    BE-->>PORTAL: פרטי הזמנה (שם, תאריכים, עלות)

    alt ספק מאשר
        SUPP->>PORTAL: מזין מספר רישוי + לוחץ "אשר"
        PORTAL->>BE: POST /supplier-portal/{token}/accept {license_plate}
        BE->>BE: status = APPROVED
        BE->>COORD: 🔔 התראה "ספק אישר"
    else ספק דוחה
        SUPP->>PORTAL: לוחץ "דחה" + סיבה
        PORTAL->>BE: POST /supplier-portal/{token}/reject {reason}
        BE->>BE: status = REJECTED
        BE->>COORD: 🔔 התראה "ספק דחה" → Fair Rotation לספק הבא
    end

    COORD->>BE: POST /work-orders/{id}/start
    BE->>BE: status = ACTIVE

    WM->>BE: POST /worklogs {start_time, end_time, hours}
    BE-->>WM: Worklog created

    COORD->>BE: POST /work-orders/{id}/close {actual_hours}
    BE->>BE: status = COMPLETED
    BE->>BE: Release frozen budget → invoice generation
```

---

## 3. Fair Rotation Algorithm

```mermaid
flowchart TD
    START["בקשת ציוד חדשה\n(equipment_model_id)"]
    
    START --> FILTER1["סנן ספקים:\nיש להם equipment_model זה?"]
    FILTER1 --> FILTER2["סנן לפי אזור/מרחב\n(normal mode)"]
    FILTER2 --> FILTER3["סנן: status='available'\n(לא תפוסים כרגע)"]
    
    FILTER3 --> ROTATE["Fair Rotation:\nמיין לפי rotation_position\nבחר הבא בתור"]
    
    ROTATE -->|"יש ספקים"| SEND["שלח לספק"]
    ROTATE -->|"אין ספקים בסינון"| FORCE["מצב אילוץ:\nהסר סינון אזור\nרק equipment match"]
    
    FORCE -->|"יש ספקים"| SEND
    FORCE -->|"אין בכלל"| ERROR["שגיאה: אין ספק מתאים"]
    
    SEND --> RESPOND{"תגובת ספק"}
    RESPOND -->|"אישר"| UPDATE["UPDATE supplier_rotations\nrotation_position++\ntotal_assignments++"]
    RESPOND -->|"דחה"| NEXT["move_to_next_supplier\nדחה → ספק הבא"]
    
    subgraph CONSTRAINT["אילוץ ספק (Override)"]
        NOTE["מנהל בוחר ספק ידנית\nחייב: constraint_reason_id\nחייב: notes"]
    end
```

---

## 4. Worklog → Invoice Flow

```mermaid
flowchart LR
    WO["Work Order\nAPPROVED+"] --> WL["Worklog\nstart_time/end_time\nhourly_rate snapshot"]
    WL --> CALC["חישוב:\ntotal_hours\ntotal_cost = hours × rate\nstorage_cost = days × daily_rate"]
    CALC --> APPROV["אישור worklog\nby AREA_MANAGER/ACCOUNTANT"]
    APPROV --> INV_ITEM["invoice_items\nworklog_id FK\nquantity=hours\nunit_price=rate"]
    INV_ITEM --> INV["Invoice\nSupplier\ntotal_amount\nstatus=draft"]
    INV --> INV_APP["אישור חשבונית\nby ACCOUNTANT"]
    INV_APP --> PAYMENT["invoice_payments\npaid_amount\npayment_date"]

    subgraph BUDGET["Budget Flow"]
        FROZEN["frozen_amount\nבעת יצירת WO"] --> RELEASE["balance_releases\nשחרור עם כל worklog"]
        RELEASE --> SPENT["budget.spent_amount\nעדכון שוטף"]
    end
```

---

## 5. Project Hierarchy

```mermaid
flowchart TD
    ORG["קק\"ל\n(הארגון)"]
    ORG --> REGION1["מרחב צפון\n23 פרויקטים\n₪188.7M תקציב"]
    ORG --> REGION2["מרחב מרכז\n20 פרויקטים\n₪31.1M תקציב"]
    ORG --> REGION3["מרחב דרום\n16 פרויקטים\n₪27.7M תקציב"]

    REGION1 --> AREA1["גליל עליון\n7 פרויקטים"]
    REGION1 --> AREA2["גליל מערבי+כרמל\n6 פרויקטים"]
    REGION1 --> AREA3["גליל תחתון+גלבוע\n6 פרויקטים"]
    REGION1 --> AREA4["עמק החולה\n4 פרויקטים"]

    AREA1 --> PROJ1["יער בירייה (YR-001)\n₪728K תקציב\n10 WOs"]
    AREA1 --> PROJ2["יער מתת (YR-002)"]
    AREA1 --> PROJ3["..."]

    subgraph PROJ_DATA["לכל פרויקט"]
        WO_LIST["Work Orders"]
        WL_LIST["Worklogs"]
        BUDGET["Budget"]
        EQUIP["Equipment"]
        MAP_P["Location (PostGIS Point)"]
        FOREST["Forest Polygon (PostGIS)"]
    end
```

---

## 6. Supplier Portal Flow

```mermaid
sequenceDiagram
    participant WM as 👷 מנהל עבודה
    participant BE as ⚙️ Backend
    participant SUPP as 🚛 ספק
    participant PORTAL as 🌐 forewise.co/supplier-portal/{token}

    WM->>BE: POST /work-orders/{id}/send-to-supplier
    BE->>BE: token = secrets.token_urlsafe(32)
    BE->>BE: work_order.portal_token = token
    BE->>BE: work_order.portal_expiry = NOW() + 3h
    BE->>SUPP: 📧 מייל:\nhttps://forewise.co/supplier-portal/{token}
    BE-->>WM: {portal_url, expires_at, status: "DISTRIBUTING"}

    SUPP->>PORTAL: פותח לינק (ללא auth!)
    PORTAL->>BE: GET /api/v1/supplier-portal/{token}
    BE->>DB: SELECT work_order WHERE portal_token=token
    BE->>BE: is_expired? already_responded?
    BE-->>PORTAL: {order_number, title, dates, amount, supplier_name, time_remaining}

    PORTAL->>PORTAL: מציג countdown timer
    PORTAL->>PORTAL: טופס: license_plate + notes

    alt ספק מאשר
        SUPP->>PORTAL: מלא license_plate + לחץ "אשר"
        PORTAL->>BE: POST /supplier-portal/{token}/accept {license_plate, notes}
        BE->>DB: UPDATE work_order status=APPROVED
        BE-->>PORTAL: 200 OK
        PORTAL-->>SUPP: "✅ ההזמנה אושרה!"
    else ספק דוחה
        SUPP->>PORTAL: בחר סיבה + לחץ "דחה"
        PORTAL->>BE: POST /supplier-portal/{token}/reject {reason}
        BE->>DB: UPDATE work_order status=REJECTED
        BE-->>PORTAL: 200 OK
        PORTAL-->>SUPP: "ההזמנה נדחתה"
    else פג תוקף
        PORTAL-->>SUPP: "פג תוקף הקישור"
    end
```

---

## 7. Equipment QR Scan Flow

```mermaid
sequenceDiagram
    participant FIELD as 👷 עובד שטח
    participant APP as 📱 PWA App
    participant BE as ⚙️ Backend
    participant DB as 🗄️ DB

    FIELD->>APP: פותח Equipment Scan
    APP->>APP: מפעיל מצלמה (QRScanner.tsx)
    FIELD->>APP: סורק QR code של ציוד
    APP->>BE: POST /equipment/{id}/scan {location, project_id, timestamp}
    BE->>DB: INSERT equipment_scans
    BE->>DB: UPDATE equipment.status
    BE-->>APP: 200 OK
    APP-->>FIELD: ✅ סריקה הצליחה

    Note over APP,BE: גם ב-Offline:\nuseOffline hook\ncached locally\nsynced when online
```
