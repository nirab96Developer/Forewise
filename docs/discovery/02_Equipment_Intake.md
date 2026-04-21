# נושא 2 — Equipment Intake (קליטת כלי בשטח)

> **שלב:** Discovery בלבד · אין שינויי קוד.

---

## 1. מסכים בפועל — שני מסלולים מקבילים בקוד

הקוד **לא אחיד** — יש שני מסלולי קליטה שונים:

| מסך | מה הוא קורא ל-API | האם מבצע את 3 המצבים? |
|---|---|---|
| `pages/Projects/ProjectWorkspaceNew.tsx` (Modal פנימי) | `POST /work-orders/{id}/scan-equipment` ואז confirm/override | ✅ **כן** — זה המסלול הנכון |
| `components/equipment/ScanEquipmentModal.tsx` + `WorkOrderDetail.tsx` | `GET /equipment/by-code/...` ואז `POST /work-orders/{id}/confirm-equipment` ישירות | ❌ **דולג על scan-equipment** — אין בדיקת 3 מצבים |
| `pages/Equipment/EquipmentScan.tsx` (`/equipment/scan`) | `POST /equipment/validate-plate` + `POST /equipment/{id}/scan` | ❌ לא מעדכן Work Order |

**משמעות:** משתמש שיכנס ל-WorkOrderDetail וילחץ "סרוק כלי" יקבל זרימה אחרת ממי שיכנס מ-ProjectWorkspace.

---

## 2. Endpoints שמטפלים בקליטה

| Method | Path | מה עושה | הערות |
|---|---|---|---|
| `POST` | `/api/v1/work-orders/{id}/scan-equipment` | זרימת 3 מצבים | מחזיר 200 בכל המצבים, ה-status בגוף |
| `POST` | `/api/v1/work-orders/{id}/confirm-equipment` | אישור העברת כלי בין פרויקטים | משחרר WO ישן, מעביר אליי |
| `POST` | `/api/v1/work-orders/{id}/admin-override-equipment` | עקיפה של אדמין במצב wrong_type | דורש `reason` |

**הקוד יושב ב-`work_orders.py` עצמו** (שורות 1013-1204) — לא ב-service מופרד. שיבור עיצובי.

---

## 3. שלושת המצבים — מה כתוב בקוד (`work_orders.py:1013-1113`)

### Preconditions לפני המצבים
- WO חייב להיות בסטטוס `APPROVED_AND_SENT`, `IN_PROGRESS` או `ACTIVE` (אחרת 400)
- `license_plate` חייב להיות לא ריק

### מצב A — התאמה מלאה
```
license_plate == expected_plate
↓
status="ok", message="כלי תואם — אומת בהצלחה"
↓ עדכונים: equipment_id, equipment_license_plate, updated_at
↓ אם status היה APPROVED_AND_SENT → status="IN_PROGRESS"
```

### מצב B — אותו סוג, רישוי שונה
```
לא תואם, אך scanned_eq קיים, ו-scanned_type == wo_type
↓ שאילתה: האם הכלי פעיל בפרויקטים אחרים?
↓ status="different_plate", question="האם להעביר?"
↓ מחזיר old_project (אך רק אחד גם אם יש מספר WOs פעילים — לולאה דורסת!)
```

→ אישור בפרונט קורא ל-`/confirm-equipment` שמעביר אליו ומשחרר את ה-WO הישן (`status="STOPPED"`).

### מצב C — סוג שונה / כלי לא קיים
```
לא A ולא B (כולל מצב שהכלי לא קיים בכלל)
↓ status="wrong_type", message="סוג הציוד שנסרק שונה מההזמנה"
↓ אם המשתמש ADMIN/SUPER_ADMIN → admin_can_override=true
```

**אבחנה חשובה:** `wrong_type` יורה גם כשהכלי לא קיים במערכת בכלל — לא רק כשהסוג באמת לא מתאים.

---

## 4. שינויי סטטוס בעת קליטה

| פעולה | מ- | ל- |
|---|---|---|
| `scan-equipment` (מצב A) | `APPROVED_AND_SENT` | `IN_PROGRESS` |
| `scan-equipment` (מצב A) | `IN_PROGRESS`/`ACTIVE` | ללא שינוי |
| `confirm-equipment` | `APPROVED_AND_SENT` | `IN_PROGRESS` |
| `admin-override-equipment` | `APPROVED_AND_SENT` | `IN_PROGRESS` |
| `_release_equipment_from_old_wo` | אחר | `STOPPED` |

**הערה:** ה-router השני (`equipment.py`) משתמש בקבוצת סטטוסים **אחרת** (`ACCEPTED`, `IN_PROGRESS`) — בעיית עקביות.

---

## 5. השוואה לאפיון העסקי שלך

| מה אמרת | מה כתוב בקוד | פער |
|---|---|---|
| התאמה מלאה → IN_PROGRESS | ✅ נכון, מהמצב APPROVED_AND_SENT | אם WO ב-IN_PROGRESS — לא משנה כלום |
| מספר רישוי שונה → אזהרה "להעביר?" | ✅ עובד | מציג רק 1 מהפרויקטים, גם אם יש מספר |
| כלי שונה → לא ניתן, חוזר למתאם | ⚠️ **חלקית** | כתוב `status="wrong_type"` ב-JSON — אבל **לא משנה את סטטוס ה-WO** ולא יוצר התראה למתאם |
| כלי לא יכול להיות פעיל בשני פרויקטים | ✅ נאכף ב-`_release_equipment_from_old_wo` | רק אם משתמשים ב-`scan-equipment` הראשי |

---

## 6. בעיות פתוחות שגיליתי

1. **שני מסלולים שונים בפרונט** (`ProjectWorkspaceNew` עם 3 מצבים, `WorkOrderDetail` בלי) — UX לא עקבי
2. **Type-matching לפי שם טקסטואלי** (`equipment_type` legacy string), לא לפי FK `type_id`
3. **`wrong_type` לא מחזיר את ה-WO לסטטוס מתאם** — נשאר ב-APPROVED_AND_SENT
4. **רק old_project אחד** מוחזר גם אם יש מספר WOs פעילים על אותו כלי
5. **case-sensitive comparison** — `'123-45-678' != '123-45-678 '` (אם יש רווחים)
