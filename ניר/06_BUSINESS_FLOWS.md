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
    participant IDB as 💾 IndexedDB
    participant BE as ⚙️ Backend

    FIELD->>APP: פותח Equipment Scan
    APP->>APP: מפעיל מצלמה (QRScanner.tsx)
    FIELD->>APP: סורק QR code של ציוד

    alt Online
        APP->>BE: POST /equipment/{id}/scan {location, project_id, timestamp}
        BE-->>APP: 200 OK
        APP-->>FIELD: ✅ סריקה הצליחה
    else Offline
        APP->>IDB: saveOfflineScan({equipment_id, timestamp, ...})
        APP-->>FIELD: 📱 "הסריקה נשמרה — תסונכרן כשיחזור חיבור"
        Note over APP,IDB: אירוע 'online' → auto-sync
    end
```

---

## 8. Offline-First Sync Flow

```mermaid
flowchart TD
    ACTION["פעולת משתמש\n(worklog / scan / work_order)"]

    ACTION --> ONLINE{"navigator.onLine?"}

    ONLINE -->|"כן"| API["POST /api/v1/..."]
    API -->|"200"| SUCCESS["✅ שמור בשרת"]
    API -->|"fail"| FALLBACK["שמור ב-IndexedDB\nstatus='pending'"]

    ONLINE -->|"לא"| IDB_SAVE["saveOfflineItem()\nIndexedDB → status='pending'"]
    IDB_SAVE --> BANNER["📵 OfflineBanner מוצג\n(פס כתום בראש המסך)"]
    IDB_SAVE --> BADGE["Badge בניווט:\n📤 N ממתינים\n(WORK_MANAGER בלבד)"]

    subgraph RECONNECT["כשחיבור חוזר (online event)"]
        DETECT["window.addEventListener('online')"]
        DETECT --> FETCH["getPendingItems() מ-IndexedDB"]
        FETCH --> LOOP["לכל פריט:"]
        LOOP -->|"worklog"| S1["POST /worklogs"]
        LOOP -->|"scan"| S2["POST /equipment/{id}/scan"]
        LOOP -->|"work_order"| S3["POST /work-orders"]
        S1 & S2 & S3 -->|"200"| REMOVE["removePendingItem(id)"]
        S1 & S2 & S3 -->|"error"| FAIL["markItemFailed(id)"]
        REMOVE --> TOAST2["Toast: ✅ X פריטים סונכרנו"]
    end

    BANNER -.->|"חיבור חזר"| DETECT
```

---

## 9. Budget Freeze & Release Flow

```mermaid
sequenceDiagram
    participant WM as 👷 מנהל עבודה
    participant BE as ⚙️ Backend
    participant DB as 🗄️ PostgreSQL

    WM->>BE: POST /work-orders (create)
    BE->>DB: INSERT work_order (status=PENDING)

    WM->>BE: POST /work-orders/{id}/send-to-supplier
    BE->>DB: SELECT budget WHERE project_id=X AND is_active=true
    BE->>BE: available = total - committed - spent
    alt מספיק תקציב
        BE->>DB: budget.committed_amount += amount
        BE->>DB: budget.remaining_amount = total - committed - spent
        BE->>DB: work_order.frozen_amount = amount
        BE-->>WM: ✅ בוצע, frozen=₪X
    else תקציב לא מספיק
        BE-->>WM: 400 "אין מספיק תקציב. זמין: ₪Y"
    end

    Note over BE,DB: כשהזמנה נסגרת (COMPLETED)
    BE->>DB: budget.committed_amount -= frozen_amount
    BE->>DB: budget.spent_amount += actual_cost
    BE->>DB: work_order.frozen_amount = 0
```

---

## 10. Budget Transfer Flow

```mermaid
sequenceDiagram
    participant AM as 🏢 מנהל אזור
    participant RM as 🌍 מנהל מרחב
    participant BE as ⚙️ Backend
    participant FE as 🖥️ BudgetTransfers.tsx

    AM->>FE: "בקש תוספת תקציב"
    FE->>BE: POST /budget-transfers/request {from_area, to_area, amount, reason}
    BE->>DB: INSERT budget_transfers (status=PENDING)
    BE->>RM: 🔔 notification "בקשת העברה ממתינה"
    BE-->>FE: {transfer_id, status: PENDING}

    RM->>FE: רואה בקשה → "אשר / דחה"

    alt אישור (מלא או חלקי)
        RM->>FE: approve_amount
        FE->>BE: POST /budget-transfers/{id}/approve {approved_amount}
        BE->>DB: from_budget.total_amount -= approved_amount
        BE->>DB: to_budget.total_amount += approved_amount
        BE->>DB: transfer.status = APPROVED
        BE->>AM: 🔔 "בקשתך אושרה: ₪X"
    else דחייה
        RM->>FE: reason
        FE->>BE: POST /budget-transfers/{id}/reject {reason}
        BE->>DB: transfer.status = REJECTED
        BE->>AM: 🔔 "בקשתך נדחתה: reason"
    end
```

---

## 11. Monthly Invoice Generation Flow

```mermaid
sequenceDiagram
    participant ACCT as 💼 מנהלת חשבונות
    participant FE as 🖥️ AccountantInbox
    participant BE as ⚙️ Backend
    participant DB as 🗄️ DB

    ACCT->>FE: לוחץ "הפק חשבונית חודשית"
    FE->>FE: modal: פרויקט, ספק, חודש, שנה
    ACCT->>FE: בוחר: YR-001, ספק X, פברואר 2026
    FE->>BE: POST /invoices/generate-monthly {supplier_id, project_id, month, year}

    BE->>DB: SELECT worklogs WHERE status=APPROVED AND month=2 AND year=2026
    BE->>BE: GROUP BY equipment_id
    BE->>DB: INSERT invoices (status=DRAFT)
    BE->>DB: INSERT invoice_items per equipment group
    BE->>DB: UPDATE worklogs SET status=INVOICED

    BE-->>FE: {invoice_id, total_amount, items_count}
    FE-->>ACCT: ✅ "חשבונית נוצרה: ₪X ל-N דיווחים"
```

---

## 12. Worklog Rate Resolution Flow

```mermaid
flowchart TD
    WL["יצירת דיווח שעות\n(WorklogForm)"]
    WL --> CHECK{"equipment_id + supplier_id?"}

    CHECK -->|"כן"| P1["בדוק supplier_equipment.hourly_rate"]
    P1 -->|"יש ו->0"| RATE1["✅ תעריף מ-supplier_equipment\nsource='supplier_equipment'"]

    P1 -->|"אין"| P2["בדוק equipment.hourly_rate"]
    P2 -->|"יש ו->0"| RATE2["✅ תעריף מ-equipment\nsource='equipment'"]

    P2 -->|"אין"| P3["בדוק equipment_types.hourly_rate"]
    P3 -->|"יש ו->0"| RATE3["✅ תעריף מ-equipment_type\nsource='equipment_type'"]

    P3 -->|"אין"| NONE["⚠️ cost=0\nflag='missing_rate_source'\nUnverified badge בדוחות"]

    CHECK -->|"equipment=NULL"| GUARD["🛑 Guard:\ncost=0\nflag='missing_rate_source'"]

    RATE1 & RATE2 & RATE3 --> CALC["חישוב:\ntotal_cost = hours × rate\nVAT = cost × 1.17\nhourly_rate_snapshot נשמר"]
```

---

## 13. Support Ticket Flow

```mermaid
sequenceDiagram
    participant U as 👤 משתמש
    participant BOT as 🤖 SmartHelpWidget
    participant ADMIN as 👨‍💼 Admin
    participant BE as ⚙️ Backend

    U->>BOT: כותב שאלה בchat
    BOT->>BOT: חיפוש ב-FAQ (keywords)

    alt נמצאה תשובה
        BOT-->>U: תשובה אוטומטית
        U->>BOT: "עדיין לא פתור"
        BOT-->>U: "אפתח קריאת שירות?"
    else לא נמצאה
        BOT-->>U: "לא מצאתי. רוצה שאשלח לאדמין?"
    end

    U->>BOT: "שלח לאדמין" + תיאור
    BOT->>BE: POST /support-tickets {title, description, category, source="chat_widget"}
    BE->>DB: INSERT support_ticket
    BE->>ADMIN: 🔔 notification "קריאה חדשה מ-{user}"
    BE-->>BOT: {ticket_id, ticket_number: "TKT-015"}
    BOT-->>U: "✅ קריאה #TKT-015 נפתחה"

    ADMIN->>BE: POST /support-tickets/{id}/comments {text}
    BE->>U: 🔔 "אדמין הגיב לקריאה #TKT-015"

    ADMIN->>BE: PATCH /support-tickets/{id} {status: "RESOLVED"}
    BE->>U: 🔔 "קריאתך #TKT-015 טופלה ✅"
```
