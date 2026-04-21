# נושא 5 — Supplier Portal (פורטל ספק)

> **שלב:** Discovery בלבד · אין שינויי קוד.

---

## 1. Endpoints חשופים לספק

מותקן תחת `/api/v1/supplier-portal/`. **ללא JWT** — token-based via URL.

| Method | Path | תיאור |
|---|---|---|
| `GET` | `/{portal_token}` | נתוני ההזמנה + מטה |
| `GET` | `/{portal_token}/available-equipment` | רשימת ציוד של הספק לקטגוריה הנדרשת |
| `POST` | `/{portal_token}/accept` | אישור ההזמנה |
| `POST` | `/{portal_token}/reject` | דחייה |
| `GET` | `/{portal_token}/status` | מצב token (לא נמצא בשימוש בפרונט) |

---

## 2. ולידציות Token

- **Lookup:** `WorkOrder.portal_token == portal_token`
- **תוקף:** בודק 3 שדות (`portal_expiry`, `token_expires_at`, `portal_token_expires`) ו-לוקח את הראשון שאינו null
- **כבר הגיב:** אם `response_received_at` או `supplier_response_at` מאוכלסים → לא תקף לאישור/דחייה
- **סטטוסים מותרים לפעולה:** `PENDING`, `APPROVED`, `sent_to_supplier`, `DISTRIBUTING`

**הערה:** GET ראשי **לא זורק שגיאה** אם token לא תקף — מחזיר flags `already_responded`/`is_expired`.

---

## 3. מה הספק רואה (`SupplierPortal.tsx`)

### Read-only (מ-API)
- מספר הזמנה, כותרת, תיאור, עדיפות, badge "אילוץ"
- פרויקט, אזור/מרחב, תאריכים
- סוג ציוד, שעות מוערכות, תעריף, סכום
- שם הספק
- טיימר מ-`time_remaining_seconds`

### Editable
- **dropdown ציוד** (חובה לאישור) — מ-`available-equipment`
- **textarea הערות** (אופציונלי)
- **dropdown סיבת דחייה** — אופציות **hardcoded** בעברית!

---

## 4. זרימת אישור (Accept)

```
Supplier בוחר Equipment ID
  ↓ (חובה — אחרת alert בפרונט)
POST /accept { equipment_id, license_plate, notes }
  ↓ Backend מנסה לפתור Equipment ב-2 דרכים:
     1. Equipment.id → SupplierEquipment.id
     2. אם רק plate — מחפש לפי plate+supplier; אם לא קיים — יוצר אוטומטית
  ↓ ולידציית קטגוריה (אם requested_equipment_model_id ידוע)
  ↓ מעדכן: equipment_id, equipment_license_plate, supplier_response_at
  ↓ status = SUPPLIER_ACCEPTED_PENDING_COORDINATOR
  ↓ התראה למתאם
```

**גאפ:** Accept handler לא דורש `equipment_id` — UI מאלץ אבל אם לקוח מותאם שלח בלעדיו, יעבור עם `equipment_id=None`.

---

## 5. זרימת דחייה (Reject)

```
Supplier בוחר reason מה-dropdown (hardcoded)
  ↓ POST /reject { notes: "<reason>: <free text>" }
  ↓ ⚠️ אין שליחת reason_id למרות שה-Backend תומך!
  ↓ עדכונים: supplier_response_at, response_received_at
  ↓ אם not is_forced_selection:
     → _move_to_next_supplier (סבב הוגן)
  ↓ אם is_forced_selection:
     → status = REJECTED
  ↓ update_rotation_after_rejection
  ↓ התראות + email למתאם/PM
```

---

## 6. שינויי סטטוס

| Event | סטטוס חדש |
|---|---|
| Accept | `SUPPLIER_ACCEPTED_PENDING_COORDINATOR` |
| Reject (forced) | `REJECTED` |
| Reject (fair, יש הבא בתור) | (ללא שינוי — נשאר `DISTRIBUTING`) |
| Reject (fair, אין הבא) | `REJECTED` |

---

## 7. אבטחה — תצפיות

| נושא | מצב |
|---|---|
| Token חד-פעמי | לא — אבל אחרי מענה ראשון, mutations נחסמות |
| Token guessing | סביר מאוד — `secrets.token_urlsafe(32)`, UNIQUE |
| IDOR | חסום — רק WO עם token תואם נטען |
| Rate limiting | **בפרודקשן בלבד** — 30/60s/IP. **In-memory per worker** — לא מסונכרן בין workers |
| JWT לפורטל | לא נדרש |

---

## 8. בעיות פתוחות שגיליתי

1. **Frontend לא שולח `reason_id`** — `supplier_rejection_reasons` בפועל לא בשימוש בפורטל
2. **רשימת סיבות דחייה hardcoded בפרונט** — לא מסונכרנת עם DB
3. **`_send_order_to_supplier` docstring אומר SMS** — אבל רק email מומש
4. **`update_rotation_after_rejection` עלול לעדכן ספק שגוי** — אחרי `_move_to_next_supplier` עדכן את `supplier_id`
5. **`/status` endpoint לא בשימוש** — קיים בלי קליינט
6. **`accept` ללא `equipment_id`** — אפשרי טכנית, ה-UI מגן
7. **Rate limiter in-memory** — לא יעיל ב-multi-worker production
