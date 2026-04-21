# נושא 4 — Order Coordinator Screen (מסך מתאם הזמנות)

> **שלב:** Discovery בלבד · אין שינויי קוד.

---

## 1. גישה למסך — `OrderCoordination.tsx`

המסך נטען רק אם המשתמש `isAdmin` או `currentRole === ORDER_COORDINATOR`.
טוען את ההזמנות ב-4 קבוצות סטטוס במקביל ורענון אוטומטי כל 30 שניות.

---

## 2. פעולות זמינות במסך

| פעולה | מתי מוצגת | API | תיאור |
|---|---|---|---|
| **רענן** | תמיד | re-fetch | טעינה מחדש |
| **מחק נבחרים** | אדמין + עם בחירה | `DELETE /work-orders/{id}` | soft delete |
| **צפה בפרטים** | בהרחבה | `navigate(/work-orders/{id})` | ניווט |
| **תעד שיחה** | בהרחבה | `POST /work-order-coordination-logs` | תיעוד "CALL" |
| **שלח לספק (סבב הוגן)** | `status === 'PENDING'` | `POST /work-orders/{id}/send-to-supplier` | מתחיל הפצה |
| **העבר לספק הבא** | `status === 'DISTRIBUTING'` | `POST /work-orders/{id}/move-to-next-supplier` | בוחר הבא בתור |
| **אשר ושלח לביצוע** | `status === 'SUPPLIER_ACCEPTED_PENDING_COORDINATOR'` | `POST /work-orders/{id}/approve` | אישור סופי |
| **בטל הזמנה** | אדמין + לא APPROVED_AND_SENT | `POST /work-orders/{id}/cancel?notes=...` | ביטול |

**לא קיים במסך זה:** דחייה ידנית (`reject`), שליחה מחודשת (`resend`), preview-allocation, override.

---

## 3. כל ה-Endpoints של מתאם

| Endpoint | Permission | Role gate |
|---|---|---|
| `POST /send-to-supplier` | `work_orders.distribute` | ORDER_COORDINATOR / ADMIN |
| `POST /approve` | `work_orders.approve` | ORDER_COORDINATOR / ADMIN |
| `POST /reject` | `work_orders.approve` | ORDER_COORDINATOR / ADMIN |
| `POST /move-to-next-supplier` | `work_orders.update` | ORDER_COORDINATOR / ADMIN |
| `POST /resend-to-supplier` | `work_orders.update` | ORDER_COORDINATOR / ADMIN |
| `POST /cancel` | `work_orders.cancel` | **ללא role gate ייחודי** |
| `POST /preview-allocation` | `work_orders.create` | — |

---

## 4. מתודות Service ופעולות שלהן

### `send_to_supplier`
- מצבי כניסה: `PENDING`, `DISTRIBUTING`, `draft`
- מעבר → `DISTRIBUTING`
- אם אין `supplier_id` → קורא ל-`select_supplier_with_checks` (סבב הוגן)
- יוצר token חדש (תוקף 3 שעות), שולח Email
- מעדכן `SupplierRotation`

### `approve`
- מעבר → `APPROVED_AND_SENT`
- חוסם self-approval (אם `created_by_id == current_user.id`)
- **אין בדיקה ש-`equipment_id` קיים** למרות שה-router-docstring טוען אחרת
- שולח 3 מיילים: לספק (Waze), ליוצר/PM, התראות in-app

### `reject`
- מעבר → `REJECTED`
- משחרר frozen budget מהפרויקט
- מעדכן `update_rotation_after_rejection`

### `cancel`
- מעבר → `CANCELLED`
- משחרר frozen budget

### `move_to_next_supplier`
- אם נמצא הבא → נשאר `DISTRIBUTING`, token חדש
- אם אין → `REJECTED`

### `force_supplier`
- **קיים ב-service אבל אין endpoint!** — רק דרך `is_forced_selection=true` ביצירה.

### `resend_to_supplier`
- **Stub בלבד** — לא מחדש token ולא שולח שוב

---

## 5. State Machine — מעברי סטטוס מותרים

מתוך `app_backend/app/core/enums.py` (`WO_TRANSITIONS`):

| מ- | ל- |
|---|---|
| `PENDING` | `DISTRIBUTING`, `CANCELLED` |
| `DISTRIBUTING` | `DISTRIBUTING` (self), `SUPPLIER_ACCEPTED_PENDING_COORDINATOR`, `REJECTED`, `CANCELLED`, `EXPIRED` |
| `SUPPLIER_ACCEPTED_PENDING_COORDINATOR` | `APPROVED_AND_SENT`, `REJECTED`, `CANCELLED` |
| `APPROVED_AND_SENT` | `COMPLETED`, `CANCELLED`, `STOPPED` |
| Terminal | `COMPLETED`, `REJECTED`, `CANCELLED`, `EXPIRED`, `STOPPED` |

**קריטי:** `IN_PROGRESS` ו-`ACTIVE` משמשים בקוד אבל **לא ב-enum** — drift.

ה-helper `validate_wo_transition()` קיים אבל **לא נקרא מ-routers** — רק מטסטים. אכיפה לא מרכזית.

---

## 6. SupplierRotationService

### מי הספק הבא בתור?
- מסנן ספקים פעילים באזור (area) או region (fallback)
- דורש: ספק פעיל, ציוד פעיל עם רישוי, סטטוס `available`, קטגוריה תואמת
- **בוחר את זה עם `total_assignments` הנמוך ביותר** ← הוגנות

### מתי הסטטיסטיקה מתעדכנת?

| Event | מתי | מתי בקוד |
|---|---|---|
| `update_rotation_after_assignment` | בעת `send_to_supplier` | מעלה `total_assignments`, `rotation_position` |
| `update_rotation_after_rejection` | בעת `reject`, פורטל-reject, expiry | מעלה `rejection_count`, מוריד `priority_score` |
| `update_rotation_after_completion` | בעת `complete_work` (legacy) | מעלה `successful_completions` |

**Bug שזוהה:** `update_rotation_after_rejection` נקרא **אחרי** ש-`_move_to_next_supplier` כבר עדכן `work_order.supplier_id`, אז ייתכן שהוא מעדכן את הספק החדש במקום הדוחה.
