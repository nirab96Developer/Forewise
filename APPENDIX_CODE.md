# נספח ב׳ — קוד תהליכים עיקריים (Code Appendix)
## מערכת Forewise — מצב היישום הנוכחי

---

# תהליך 1: התחברות, 2FA והרשאות
## Login → OTP → Session → Role-based access

### א. שם ומטרה
**שם:** Authentication & Access Flow  
**מטרה:** אימות משתמש פנימי, תמיכה ב־2FA, והקמת session עקבי שממנו כל הפרונט שואב תפקידים והרשאות

### ב. קוד צד לקוח (Frontend)
**קבצים מרכזיים:**
- `app_frontend/src/pages/Login/Login.tsx`
- `app_frontend/src/pages/OTP/OTP.tsx`
- `app_frontend/src/services/otpService.ts`
- `app_frontend/src/utils/permissions.ts`

**עקרונות מימוש:**
- `Login` שולח שם משתמש/אימייל וסיסמה
- אם השרת מחזיר `requires_2fa`, הפרונט שומר מידע זמני ל־OTP ומעביר את המשתמש למסך `/otp`
- `OTP` תומך ב־fallback בין `email`, `username`, ו־`userId` כדי לא להישבר כשההזדהות הראשונית לא התבצעה עם אימייל
- לאחר אימות מוצלח, נבנה `user` object אחיד ב־`localStorage`, וממנו נגזרות הרשאות, תפריט, ניתוב ודשבורד

### ג. קוד צד שרת (Backend)
**קבצים מרכזיים:**
- `app_backend/app/services/auth_service.py`
- `app_backend/app/routers/auth.py`

**עקרונות מימוש:**
- השרת הוא מקור האמת לשאלה האם נדרש 2FA
- השרת מחזיר תפקיד, הרשאות, ונתוני משתמש בפורמט שממנו הפרונט בונה session
- משתמשי `SUPPLIER` אינם אמורים לעבוד דרך האפליקציה הראשית, אלא דרך פורטל ספקים token-based

### ד. בסיס נתונים
**טבלאות עיקריות:**
- `users`
- `roles`
- `permissions`
- `otp_tokens`
- `user_sessions`

---

# תהליך 2: מחזור חיי הזמנת עבודה
## יצירה → בחירת ספק/סבב הוגן → שליחה לספק → אישור ספק → אישור מתאם הזמנות → אימות כלי → ביצוע

### א. שם ומטרה
**שם:** Work Order Lifecycle  
**מטרה:** לנהל הזמנת עבודה משלב הדרישה ועד לביצוע בשטח, תוך שמירה על source of truth בשרת בכל נושא הסטטוסים, הספק, הציוד והעלות

### ב. קוד צד לקוח (Frontend)
**קבצים מרכזיים:**
- `app_frontend/src/pages/Projects/ProjectWorkspaceNew.tsx`
- `app_frontend/src/pages/WorkOrders/NewWorkOrder.tsx`
- `app_frontend/src/pages/WorkOrders/OrderCoordination.tsx`
- `app_frontend/src/pages/SupplierPortal/SupplierPortal.tsx`
- `app_frontend/src/pages/WorkOrders/WorkOrders.tsx`
- `app_frontend/src/pages/WorkOrders/WorkOrderDetail.tsx`

**עקרונות מימוש:**
- `NewWorkOrder` מציג `pricing preview` ו־`allocation preview`, אבל לא שולח יותר שדות כספיים מחושבים לשרת
- מסך תיאום הזמנות מנהל את הזרימה של `PENDING` / `DISTRIBUTING` / `SUPPLIER_ACCEPTED_PENDING_COORDINATOR` / `APPROVED_AND_SENT`
- פורטל הספק עובד דרך token וכולל בחירת כלי זמין מתאים
- אימות כלי בפרויקט מתבצע לפי מספר רישוי, לא לפי זרימת `QR` ייעודית

### ג. קוד צד שרת (Backend)
**קבצים מרכזיים:**
- `app_backend/app/services/work_order_service.py`
- `app_backend/app/routers/work_orders.py`
- `app_backend/app/services/supplier_rotation_service.py`
- `app_backend/app/routers/supplier_portal.py`
- `app_backend/app/core/enums.py`

**State machine עיקרי:**
```text
PENDING
→ DISTRIBUTING
→ SUPPLIER_ACCEPTED_PENDING_COORDINATOR
→ APPROVED_AND_SENT
→ IN_PROGRESS
→ COMPLETED
```

**עקרונות מימוש נוכחיים:**
- השרת גוזר את `hourly_rate`, `total_amount`, ו־`frozen_amount` בעת יצירת הזמנה
- השרת בוחר ספק לפי סבב הוגן או אילוץ ספק מתועד
- פורטל הספק מאשר רק עם כלי ששייך לספק, מתאים לקטגוריה הנדרשת, ואינו תפוס להזמנה פעילה אחרת
- אישור סופי של הזמנה מתבצע ע"י מתאם הזמנות/Admin ומקדם את ההזמנה ל־`APPROVED_AND_SENT`
- רק לאחר אימות כלי תקין ניתן להתקדם לביצוע בפועל

### ד. בסיס נתונים
**טבלאות עיקריות:**
- `work_orders`
- `equipment`
- `supplier_rotations`
- `supplier_invitations`
- `budgets`

**שדות מרכזיים ב־`work_orders`:**
- `status`
- `supplier_id`
- `equipment_id`
- `equipment_license_plate`
- `requested_equipment_model_id`
- `hourly_rate`
- `total_amount`
- `frozen_amount`
- `remaining_frozen`
- `portal_token`
- `portal_expiry`

---

# תהליך 3: תמחור ודיווחי עבודה
## Worklog creation → server pricing → accountant approval → budget update

### א. שם ומטרה
**שם:** Worklog Pricing & Approval Pipeline  
**מטרה:** להבטיח שכל דיווח עבודה יתומחר לפי הלוגיקה העסקית בצד השרת, יאושר רק אם ההזמנה תקינה, וישפיע נכון על התקציב

### ב. קוד צד לקוח (Frontend)
**קבצים מרכזיים:**
- `app_frontend/src/pages/WorkLogs/WorklogFormUnified.tsx`
- `app_frontend/src/pages/WorkLogs/AccountantInbox.tsx`

**עקרונות מימוש:**
- הפרונט שולח נתוני עבודה בלבד, ולא שדות כספיים מחושבים
- קודי פעילות נטענים מהשרת דרך `activity-codes`
- הדיווח קשור להזמנת עבודה קיימת ולפרויקט קיים

### ג. קוד צד שרת (Backend)
**קבצים מרכזיים:**
- `app_backend/app/services/worklog_service.py`
- `app_backend/app/services/rate_service.py`
- `app_backend/app/routers/worklogs.py`

**עקרונות מימוש:**
- `worklog_service.create()` חוסם דיווח אם ההזמנה אינה בסטטוס שמאפשר עבודה
- נדרש כלי משויך/מאומת להזמנה לפני דיווח
- שדות client-side לא בטוחים כמו `hourly_rate_snapshot`, `cost_before_vat`, `cost_with_vat`, `vat_rate` מנוקים מה־payload
- התמחור מחושב בשרת דרך `resolve_supplier_pricing(...)`
- `vat_rate` הפעיל בקוד הוא `0.18`

**אישור דיווח:**
- אישור חשבונאי מקדם את הדיווח ל־`APPROVED`
- התקציב משתנה באותו רגע: committed יורד, spent עולה, remaining מתעדכן
- אם הוזמנה מסגרת עבודה שנוצלה במלואה, ההזמנה יכולה לעבור ל־`COMPLETED`

### ד. בסיס נתונים
**טבלאות עיקריות:**
- `worklogs`
- `work_orders`
- `budgets`
- `equipment_types`
- `equipment`
- `supplier_equipment` (לתאימות ותמחור היסטורי/מסייע)

**שדות מרכזיים ב־`worklogs`:**
- `hourly_rate_snapshot`
- `cost_before_vat`
- `cost_with_vat`
- `vat_rate`
- `status`
- `activity_type_id`

---

# תהליך 4: סבב הוגן, ציוד ספקים וסנכרון נתונים
## Rotation + supplier equipment truth + equipment shadow sync

### א. שם ומטרה
**שם:** Supplier Allocation & Equipment Sync  
**מטרה:** לחבר בין בחירת ספק, זמינות ציוד, תמחור, ונתוני ציוד אמיתיים כך שלא יהיו כמה "אמיתות" שונות בין פרונט, בקאנד ו־DB

### ב. קוד צד לקוח (Frontend)
**קבצים מרכזיים:**
- `app_frontend/src/pages/WorkOrders/NewWorkOrder.tsx`
- `app_frontend/src/pages/Settings/FairRotation.tsx`
- `app_frontend/src/pages/SupplierPortal/SupplierPortal.tsx`
- `app_frontend/src/services/equipmentTypeService.ts`

**עקרונות מימוש:**
- פריוויו בחירת ספק ותמחור נטען מהשרת
- פורטל הספק מציג רק ציוד זמין עם מספר רישוי
- הפרונט אינו מחליט לבד מי הספק "הנכון" או מה המחיר "האמיתי"

### ג. קוד צד שרת (Backend)
**קבצים מרכזיים:**
- `app_backend/app/services/supplier_rotation_service.py`
- `app_backend/app/services/equipment_service.py`
- `app_backend/app/services/rate_service.py`
- `app_backend/app/routers/supplier_portal.py`
- `app_backend/app/scripts/sync_supplier_equipment_from_equipment.py`

**עקרונות מימוש:**
- סבב הוגן בודק ספקים שיש להם ציוד פעיל מתאים עם `license_plate`
- תמחור נשען על שילוב של `equipment`, `supplier_equipment`, ו־`equipment_types`
- `equipment_service` מסנכרן shadow records בין `equipment` ל־`supplier_equipment`
- קיים data-fix script ליישור נתונים ישנים בבסיס הנתונים

### ד. בסיס נתונים
**טבלאות עיקריות:**
- `equipment`
- `supplier_equipment`
- `suppliers`
- `equipment_types`
- `equipment_models`
- `supplier_rotations`

**הערה ארכיטקטונית:**
- מקור האמת התפעולי עבר בעיקר ל־`equipment`
- `supplier_equipment` עדיין קיים ומשמש לצורכי תאימות, תמחור וחלק מהמסכים, ולכן נדרש סנכרון קבוע

---

# תהליך 5: חשבוניות
## Approved worklogs → invoice items → invoice detail → PDF / send / paid

### א. שם ומטרה
**שם:** Invoice Flow  
**מטרה:** לייצר, להציג ולנהל חשבוניות מתוך נתוני עבודה מאושרים, עם פירוט, PDF, סטטוסים ותשלום

### ב. קוד צד לקוח (Frontend)
**קבצים מרכזיים:**
- `app_frontend/src/pages/Invoices/Invoices.tsx`
- `app_frontend/src/pages/Invoices/InvoiceDetail.tsx`

**עקרונות מימוש:**
- רשימת חשבוניות נשענת על הנתונים כפי שהשרת מחזיר, בלי תיקוני `work_order_id` מקומיים
- מסך פרטי חשבונית מציג itemized data, PDF, שליחה לספק וסימון כשולם
- ה־UI תומך בסטטוס `SENT`

### ג. קוד צד שרת (Backend)
**קבצים מרכזיים:**
- `app_backend/app/routers/invoices.py`
- `app_backend/app/services/invoice_service.py`
- `app_backend/app/services/pdf_documents.py`

**עקרונות מימוש:**
- `/invoices/{id}/items` מחזיר גם פרטי ספק, פרויקט ופריטי חשבונית
- סימון כשולם מעדכן `paid_amount` ו־`status = PAID`
- PDF החשבונית נבנה בשרת
- מע"מ המערכת בחשבוניות ובדיווחים מיושר ל־`18%`

### ד. בסיס נתונים
**טבלאות עיקריות:**
- `invoices`
- `invoice_items`
- `invoice_payments`
- `worklogs`

**שדות מרכזיים ב־`invoices`:**
- `invoice_number`
- `subtotal`
- `tax_amount`
- `total_amount`
- `paid_amount`
- `status`
- `supplier_id`
- `project_id`

---

# תהליך 6: יכולות אופליין וביומטריה
## PWA / IndexedDB queue / WebAuthn

### א. שם ומטרה
**שם:** Offline & Secure Access Flow  
**מטרה:** לשפר שימוש בשטח בתנאי קישוריות משתנים, ולאפשר גישה מאובטחת ונוחה באמצעות ביומטריה בדפדפנים נתמכים

### ב. קוד צד לקוח (Frontend)
**קבצים מרכזיים:**
- `app_frontend/src/hooks/useOfflineSync.ts`
- `app_frontend/src/utils/offlineStorage.ts`
- `app_frontend/src/pages/PendingSync/PendingSync.tsx`
- `app_frontend/src/services/biometricService.ts`
- `app_frontend/src/main.tsx`
- `app_frontend/vite.config.ts`

**עקרונות מימוש:**
- תור אופליין אחיד מבוסס `IndexedDB`
- סנכרון אוטומטי כשחוזרים לאינטרנט
- התקנה כ־PWA דרך `vite-plugin-pwa`
- רישום ואימות ביומטרי דרך `WebAuthn`

### ג. קוד צד שרת (Backend)
**קבצים מרכזיים:**
- `app_backend/app/routers/auth.py`
- `app_backend/app/models/biometric_credential.py`
- `app_backend/app/models/otp_token.py`

**עקרונות מימוש:**
- `OTP` עובד בזרימת כניסה מלאה
- `WebAuthn` עובד בזרימות `register begin/complete` ו־`login begin/complete`
- אתגרי `WebAuthn` נשמרים ב־DB ולא רק בזיכרון process, כדי לעבוד נכון גם ב־multi-worker

### ד. סטטוס נוכחי
- אופליין חלקי אמיתי נבדק
- `PWA` נבנה ומייצר `service worker`
- `OTP` ו־`WebAuthn` נבדקו בפועל
