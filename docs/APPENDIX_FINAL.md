# נספחים — מערכת Forewise

---

# נספח א׳ — מסכי מערכת עיקריים

---

## 1. מסך התחברות (Login)

![מסך התחברות](screenshots/login.png)

### תפקיד משתמש
כל המשתמשים — מנהלי מערכת, מנהלי מרחב, מנהלי אזור, מנהלי עבודה, רכזי הזמנות, מנהלות חשבונות.

### מטרה
מסך הכניסה הראשי למערכת. המשתמש מזדהה באמצעות שם משתמש וסיסמה.
המערכת תומכת באימות דו-שלבי (2FA) — לאחר הזנת הסיסמה נשלח קוד חד-פעמי (OTP) למייל,
או לחלופין ניתן להשתמש באימות ביומטרי (WebAuthn) אם הוגדר מראש.

### פעולות עיקריות
- הזנת שם משתמש וסיסמה
- כניסה ביומטרית (אם רשום)
- שכחתי סיסמה — איפוס באמצעות קוד OTP

### הערות
- לאחר 5 ניסיונות כושלים החשבון ננעל אוטומטית ל-15 דקות.
- בסביבת Production, ממשק ה-API (docs/redoc) חסום.

---

## 2. לוח בקרה (Dashboard)

![לוח בקרה](screenshots/dashboard.png)

### תפקיד משתמש
כל תפקיד רואה לוח בקרה מותאם — מנהל מערכת רואה מדדים כלל-מערכתיים, מנהל אזור רואה מדדים תפעוליים, מנהלת חשבונות רואה מדדים כספיים.

### מטרה
תצוגה מרכזית של מצב המערכת בזמן אמת — הזמנות פתוחות, דיווחים ממתינים לאישור,
חריגות תקציב, התראות דחופות ופעולות מהירות.

### פעולות עיקריות
- צפייה ב-KPI מרכזיים (הזמנות פתוחות, דיווחים ממתינים, חריגות תקציב)
- ניווט מהיר לפעולות (יצירת הזמנה, אישור דיווח, צפייה בחשבוניות)
- צפייה בפעילות אחרונה ובהתראות

### הערות
כל KPI מותאם להרשאות — מנהל מרחב רואה רק נתוני המרחב שלו, מנהל אזור רואה רק את האזור שלו.

---

## 3. רשימת פרויקטים / סביבת עבודה

![פרויקטים](screenshots/projects.png)

### תפקיד משתמש
מנהלי אזור, מנהלי עבודה, מנהלי מרחב.

### מטרה
ניהול פרויקטים פעילים — צפייה בסטטוס, תקציב, הזמנות פעילות ודיווחי עבודה.
סביבת העבודה של פרויקט כוללת לשוניות: סקירה כללית, הזמנות עבודה, כלים בפרויקט ומפה.

### פעולות עיקריות
- חיפוש וסינון פרויקטים
- כניסה לסביבת עבודה של פרויקט
- צפייה במפת יער ואזור עבודה (Leaflet + PostGIS)

---

## 4. יצירת הזמנת עבודה

![יצירת הזמנה](screenshots/create_work_order.png)

### תפקיד משתמש
מנהל עבודה, מנהל אזור.

### מטרה
יצירת הזמנה חדשה עבור פרויקט — בחירת סוג ציוד, שיטת הקצאה (סבב הוגן / בחירה ידנית),
תאריכי עבודה ותיאור.

### פעולות עיקריות
- בחירת פרויקט, סוג ציוד, שיטת הקצאה
- הגדרת תאריכי עבודה
- שליחה — ההזמנה נוצרת בסטטוס PENDING

### הערות
המערכת מוודאת שקיים תקציב זמין לפרויקט לפני יצירת ההזמנה.
סוג הכלי (equipment_type) חובה ומאומת מול קטגוריות קיימות במערכת.

---

## 5. ניהול הזמנות — מתאם הזמנות

![ניהול הזמנות](screenshots/orders_management.png)

### תפקיד משתמש
רכז הזמנות (Order Coordinator).

### מטרה
ניהול תור הזמנות — שליחה לספק, מעקב אחר תגובות, אישור סופי.
המתאם שולט בזרימת ההזמנה מרגע היצירה ועד לאישור הסופי.

### פעולות עיקריות
- שליחת הזמנה לספק (יצירת קישור פורטל)
- מעקב אחר תגובת ספק (אישור / דחייה)
- אישור סופי של הזמנה (coordinator-approve)
- מעבר לספק הבא במקרה של דחייה

---

## 6. פורטל ספקים

![פורטל ספקים](screenshots/supplier_portal.png)

### תפקיד משתמש
ספק חיצוני (ללא כניסה למערכת — גישה באמצעות קישור חד-פעמי).

### מטרה
ספק מקבל קישור במייל עם token חד-פעמי (בתוקף 3 שעות).
בפורטל הספק רואה את פרטי ההזמנה ויכול לאשר אותה עם בחירת כלי, או לדחות אותה.

### פעולות עיקריות
- צפייה בפרטי הזמנה (פרויקט, סוג ציוד, תאריכים)
- אישור הזמנה ובחירת כלי (מספר רישוי)
- דחיית הזמנה עם סיבה

### הערות
- קישור שפג תוקפו מציג הודעה ברורה
- לא ניתן לאשר או לדחות פעמיים (מניעת כפילות)
- הפורטל מותאם לנייד

---

## 7. אימות כלי לפי מספר רישוי

![אימות כלי](screenshots/equipment_validation.png)

### תפקיד משתמש
מנהל עבודה (שטח).

### מטרה
אימות שהכלי שהגיע לשטח תואם את ההזמנה — על ידי הזנת מספר רישוי.
המערכת בודקת: הכלי קיים, שייך לספק הנכון, ההזמנה מאושרת.

### פעולות עיקריות
- הזנת מספר רישוי (ראשי) או סריקת QR (משני)
- קבלת תוצאת אימות — תקין / לא תקין עם פירוט
- המשך לדיווח שעות

### הערות
אם הכלי שייך לספק שונה מהספק שאושר בהזמנה — מוצגת אזהרה.
תומך גם בעבודה אופליין (שמירה מקומית וסנכרון בחזרה לחיבור).

---

## 8. דיווח שעות עבודה

![דיווח שעות](screenshots/worklog.png)

### תפקיד משתמש
מנהל עבודה.

### מטרה
דיווח שעות עבודה בשטח — שעת התחלה, שעת סיום, הפסקות, תיאור עבודה.
הדיווח מחושב אוטומטית (שעות נטו, עלות לפי תעריף).

### פעולות עיקריות
- הזנת תאריך, שעות, הפסקות
- תיאור הפעילות
- שליחה לאישור

---

## 9. אישור דיווחים — מנהלת חשבונות

![אישור דיווחים](screenshots/accounting.png)

### תפקיד משתמש
מנהלת חשבונות.

### מטרה
תיבת עבודה כספית — סקירה ואישור דיווחי שעות שהוגשו.
המנהלת רואה את כל הדיווחים הממתינים, עם סינון לפי פרויקט, ספק ותאריך.

### פעולות עיקריות
- סינון דיווחים ממתינים
- צפייה בפירוט דיווח (שעות, עלות, ציוד)
- אישור או דחייה (עם סיבה)

### הערות
מנהלת חשבונות לא יכולה לאשר דיווח שיצרה בעצמה (self-approval blocked).
גישה מוגבלת לאזור שלה בלבד.

---

## 10. חשבוניות

![חשבוניות](screenshots/invoices.png)

### תפקיד משתמש
מנהלת חשבונות, מנהל מערכת.

### מטרה
ניהול מחזור החשבוניות — יצירה מדיווחים מאושרים, אישור, סימון כשולם.
מספר חשבונית נוצר אוטומטית (INV-YYYY-NNNN).

### פעולות עיקריות
- יצירת חשבונית מדיווחים מאושרים
- אישור חשבונית
- סימון כשולם

### הערות
מעבר סטטוס חשבונית נאכף: DRAFT -> APPROVED -> PAID.
לא ניתן לדלג על שלבים.

---
---

# נספח ב׳ — תהליכים עסקיים מרכזיים

---

## תהליך 1: יצירת הזמנת עבודה + שיבוץ ספק

### למה התהליך הזה קריטי
בארגון שמנהל עשרות פרויקטים במקביל עם עשרות ספקים, חלוקת עבודה ידנית (טלפונים, וואטסאפ, אקסלים) גורמת לעיכובים, טעויות ואי-הוגנות בחלוקה. תהליך זה מחליף את העבודה הידנית במנגנון אוטומטי: ההזמנה נוצרת, ספק נבחר בהגינות (סבב הוגן), ומקבל קישור מאובטח לאישור — ללא צורך בתיאום ידני.

### איזו בעיה עסקית נפתרת
- ספקים מקבלים הזמנות בצורה שוויונית (Fair Rotation) — לא לפי קשרים אישיים
- מניעת שכחת הזמנות — token בתוקף 3 שעות, לאחר מכן מעבר אוטומטי לספק הבא
- שקיפות מלאה — כל שלב (שליחה, תגובה, אישור) מתועד ומנוטר

### קבצי Frontend
- `app_frontend/src/pages/WorkOrders/NewWorkOrder.tsx` — טופס יצירת הזמנה

### קבצי Backend
- `app_backend/app/services/work_order_service.py` — לוגיקה עסקית
- `app_backend/app/routers/work_orders.py` — API endpoints

### קטע קוד — Backend: יצירת הזמנה

    def create_work_order(self, db, work_order, created_by_id):
        # Generate unique portal token for supplier access
        portal_token = secrets.token_urlsafe(32)

        # Validate equipment type exists in system categories
        equipment_type_name = wo_dict.get("equipment_type")
        cat_row = db.execute(text(
            "SELECT id FROM equipment_categories "
            "WHERE LOWER(name) = LOWER(:n)"
        ), {"n": equipment_type_name}).fetchone()
        if not cat_row:
            raise HTTPException(400, "Equipment type not found")

        # Create work order with PENDING status
        wo_dict['status'] = 'PENDING'
        new_wo = WorkOrder(**wo_dict)
        db.add(new_wo)
        db.commit()
        return new_wo

### קטע קוד — Backend: שליחה לספק (כולל סבב הוגן)

    def send_to_supplier(self, db, work_order_id, current_user_id):
        work_order = self.get_work_order(db, work_order_id)

        # If no supplier assigned — use Fair Rotation algorithm
        if not work_order.supplier_id:
            selected = self._select_supplier_by_rotation(db, work_order)
            if not selected:
                raise ValidationException("No available supplier")
            work_order.supplier_id = selected

        # Generate time-limited portal token (3 hours)
        token = secrets.token_urlsafe(32)
        work_order.portal_token = token
        work_order.portal_expiry = datetime.utcnow() + timedelta(hours=3)
        work_order.status = "DISTRIBUTING"

        # Send branded email with portal link to supplier
        send_email(to=supplier.email, subject="New Work Order",
                   html_body=branded_html)

### זרימה

| שלב | קלט | עיבוד | פלט |
|-----|------|-------|-----|
| 1 | פרטי הזמנה (פרויקט, סוג ציוד) | ולידציה, בדיקת תקציב | הזמנה בסטטוס PENDING |
| 2 | הזמנה + שיטת הקצאה | בחירת ספק (סבב הוגן / ידני) | הזמנה בסטטוס DISTRIBUTING |
| 3 | תגובת ספק (אישור/דחייה) | עדכון סטטוס, שמירת ציוד | SUPPLIER_ACCEPTED_PENDING_COORDINATOR |
| 4 | אישור מתאם | אישור סופי | APPROVED_AND_SENT |

### מסד נתונים

**טבלה: work_orders**

| שדה | סוג | תיאור | קשר |
|-----|------|-------|------|
| id | integer PK | מזהה ייחודי | |
| order_number | integer NOT NULL | מספר הזמנה | |
| project_id | integer | פרויקט | -> projects.id |
| supplier_id | integer | ספק שנבחר | -> suppliers.id |
| equipment_id | integer | כלי שהוצמד | -> equipment.id |
| created_by_id | integer | מי יצר | -> users.id |
| status | varchar | סטטוס (מכונת מצבים) | |
| portal_token | varchar | token לפורטל ספק | |
| portal_expiry | timestamp | תוקף הtoken | |
| allocation_method | varchar | שיטת הקצאה (fair_rotation/forced) | |
| frozen_amount | numeric | סכום מוקפא מתקציב | |
| requested_equipment_model_id | integer | דגם ציוד | -> equipment_models.id |



---

## תהליך 2: אימות כלי לפי מספר רישוי

### למה התהליך הזה קריטי
בשטח, ספק עלול לשלוח כלי שונה מהכלי שאושר — כלי קטן יותר, כלי שלא שייך לספק, או כלי שכבר מוקצה לפרויקט אחר. ללא מנגנון אימות, הארגון משלם עבור ציוד שלא תואם את ההזמנה. מנגנון האימות מונע הפסדים כספיים ומבטיח שהכלי שמגיע לשטח הוא בדיוק הכלי שאושר.

### איזו בעיה עסקית נפתרת
- **מניעת זיוף/החלפה** — אימות שמספר הרישוי שייך לספק שאושר בהזמנה
- **מניעת הקצאה כפולה** — כלי שכבר מוקצה לפרויקט אחר יזוהה
- **בקרת סטטוס** — לא ניתן לאמת כלי אם ההזמנה לא מאושרת (APPROVED_AND_SENT)
- **אזהרות מפורטות** — במקרה של אי-התאמה, המערכת מציגה בדיוק מה לא תואם

### קבצי Frontend
- `app_frontend/src/pages/Equipment/EquipmentScan.tsx` — מסך אימות כלי

### קבצי Backend
- `app_backend/app/routers/equipment.py` — endpoint אימות

### קטע קוד — Backend: אימות מספר רישוי

    @router.post("/validate-plate")
    def validate_license_plate(body, db, current_user):
        plate = body.get("license_plate").strip()
        wo_id = body.get("work_order_id")

        # Search in equipment table, then supplier_equipment
        eq = db.query(Equipment).filter(
            Equipment.license_plate == plate,
            Equipment.is_active == True
        ).first()
        if not eq:
            se = db.query(SupplierEquipment).filter(
                SupplierEquipment.license_plate == plate
            ).first()
        if not eq and not se:
            raise HTTPException(404, "Equipment not found")

        # Cross-validate against the approved work order
        if wo_id:
            wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()

            # Rule 1: WO must be in APPROVED_AND_SENT status
            if wo.status != "APPROVED_AND_SENT":
                result["valid"] = False
                result["warnings"].append("Work order not approved")

            # Rule 2: Equipment must belong to the approved supplier
            if supplier_id != wo.supplier_id:
                result["valid"] = False
                result["warnings"].append("Equipment belongs to different supplier")

        return result  # { valid, equipment_name, supplier_name, warnings }

### קטע קוד — Frontend: מסך אימות

    const validatePlate = async (plate: string) => {
      // POST to validation endpoint with plate + work order context
      const res = await api.post('/equipment/validate-plate', {
        license_plate: plate,
        work_order_id: woIdParam ? parseInt(woIdParam) : undefined,
      });

      setValidation(res.data);
      if (res.data.valid) {
        registerScan(res.data.equipment_id, plate);
      }
    };

### זרימה

| שלב | קלט | עיבוד | פלט |
|-----|------|-------|-----|
| 1 | מספר רישוי | חיפוש ב-equipment + supplier_equipment | כלי נמצא / לא נמצא |
| 2 | כלי + הזמנה | בדיקת סטטוס הזמנה + התאמת ספק | valid: true/false + warnings |
| 3 | אימות מוצלח | רישום סריקה ב-equipment_scans | מעבר לדיווח שעות |

### מסד נתונים

**טבלה: equipment**

| שדה | סוג | תיאור | קשר |
|-----|------|-------|------|
| id | integer PK | מזהה ייחודי | |
| license_plate | varchar | מספר רישוי | |
| supplier_id | integer | ספק בעלים | -> suppliers.id |
| equipment_type_id | integer | סוג ציוד | -> equipment_types.id |
| is_active | boolean | פעיל | |

**טבלה: supplier_equipment**

| שדה | סוג | תיאור | קשר |
|-----|------|-------|------|
| id | integer PK | מזהה | |
| supplier_id | integer | ספק | |
| license_plate | varchar | מספר רישוי | |
| hourly_rate | numeric | תעריף שעתי | |
| equipment_model_id | integer | דגם | -> equipment_models.id |

**טבלה: equipment_scans**

| שדה | סוג | תיאור | קשר |
|-----|------|-------|------|
| id | integer PK | מזהה | |
| equipment_id | integer NOT NULL | כלי שנסרק | -> equipment.id |
| work_order_id | integer | הזמנת עבודה | -> work_orders.id |
| scanned_by | integer NOT NULL | מי סרק | -> users.id |
| scan_type | varchar NOT NULL | סוג סריקה (plate_validation) | |
| scan_timestamp | timestamp NOT NULL | זמן סריקה | |
| is_valid | boolean | תוצאת אימות | |



---

## תהליך 3: דיווח שעות -> אישור -> חשבונית

### למה התהליך הזה קריטי
זהו התהליך שבו כסף עובר ידיים. ללא בקרה הדוקה, ספק יכול לדווח שעות מנופחות, מנהל עבודה יכול לאשר דיווח של עצמו, וחשבוניות יכולות להיווצר ללא אישור מוסמך. תהליך זה מבטיח שכל שקל שמשולם עבר: (1) דיווח מסודר, (2) אישור מנהלת חשבונות מוסמכת, ו-(3) יצירת חשבונית רשמית — ללא אפשרות לדלג על שלבים.

### איזו בעיה עסקית נפתרת
- **מניעת self-approval** — מנהל עבודה לא יכול לאשר דיווח שיצר בעצמו
- **הפרדת סמכויות** — רק מנהלת חשבונות באזור הנכון יכולה לאשר
- **מכונת מצבים קשיחה** — חשבונית חייבת לעבור DRAFT -> APPROVED -> PAID, ללא דילוגים
- **עדכון תקציב אוטומטי** — בכל אישור דיווח, הסכום מתעדכן בתקציב הפרויקט
- **מניעת כפילות** — לא ניתן ליצור חשבונית מדיווח שכבר חויב

### קבצי Frontend
- `app_frontend/src/pages/WorkLogs/WorklogFormUnified.tsx` — טופס דיווח
- `app_frontend/src/pages/WorkLogs/AccountantInbox.tsx` — תיבת אישור חשבונאית

### קבצי Backend
- `app_backend/app/services/worklog_service.py` — דיווח + אישור
- `app_backend/app/services/invoice_service.py` — יצירת חשבונית

### קטע קוד — Backend: יצירת דיווח שעות

    def create(self, db, data, current_user_id):
        # Validate: work order must exist and be approved
        wo = db.query(WorkOrder).filter_by(id=data.work_order_id).first()
        if not wo:
            raise ValidationException("Work order not found")

        # Derive project and supplier from the work order
        project_id = data.project_id or wo.project_id
        supplier_id = data.supplier_id or wo.supplier_id

        # Calculate costs: hours * hourly rate + VAT
        worklog_dict['hourly_rate_snapshot'] = hourly_rate
        worklog_dict['cost_before_vat'] = work_hours * hourly_rate
        worklog_dict['cost_with_vat'] = cost_before_vat * Decimal('1.17')
        worklog_dict['status'] = 'PENDING'

        worklog = Worklog(**worklog_dict)
        db.add(worklog)
        db.commit()

### קטע קוד — Backend: אישור דיווח + עדכון תקציב

    def approve(self, db, worklog_id, current_user_id):
        worklog = self.get_by_id(db, worklog_id)

        # Set approval metadata
        worklog.status = 'APPROVED'
        worklog.approved_by_user_id = current_user_id
        worklog.approved_at = datetime.utcnow()
        db.commit()

        # Financial side-effect: update project budget
        if worklog.work_order_id:
            wo = db.query(WorkOrder).filter_by(id=worklog.work_order_id).first()
            if wo and wo.project_id:
                cost = float(worklog.work_hours) * float(worklog.hourly_rate_snapshot)
                budget = db.query(Budget).filter_by(project_id=wo.project_id).first()
                if budget:
                    budget.spent_amount += Decimal(str(cost))  # atomic budget update
                    db.commit()

### קטע קוד — Backend: יצירת חשבונית

    def create(self, db, data, current_user_id):
        # Auto-generate sequential invoice number
        year = datetime.now().year
        last = db.query(Invoice).filter(
            Invoice.invoice_number.like(f"INV-{year}-%")
        ).order_by(Invoice.id.desc()).first()
        seq = int(last.invoice_number.split('-')[-1]) + 1 if last else 1
        invoice_dict['invoice_number'] = f"INV-{year}-{seq:04d}"

        # Auto-calculate VAT (17%) and due date (+30 days)
        total = invoice_dict['total_amount']
        invoice_dict['subtotal'] = total / Decimal('1.17')
        invoice_dict['tax_amount'] = total - invoice_dict['subtotal']
        invoice_dict['due_date'] = invoice_dict['issue_date'] + timedelta(days=30)
        invoice_dict['status'] = 'DRAFT'

        invoice = Invoice(**invoice_dict)
        db.add(invoice)
        db.commit()

### זרימה

| שלב | שחקן | פעולה | סטטוס | השפעה כספית |
|-----|-------|-------|-------|-------------|
| 1 | מנהל עבודה | יוצר דיווח שעות | PENDING | אין |
| 2 | מנהל עבודה | שולח לאישור | SUBMITTED | אין |
| 3 | מנהלת חשבונות | מאשרת | APPROVED | budget.spent_amount += cost |
| 4 | מנהלת חשבונות | דוחה (אם יש בעיה) | REJECTED | אין |
| 5 | מנהל מערכת | יוצר חשבונית | DRAFT | חשבונית עם מע"מ + מספר סידורי |
| 6 | מנהלת חשבונות | מאשרת חשבונית | APPROVED | |
| 7 | מנהלת חשבונות | מסמנת כשולם | PAID | סיום מחזור כספי |

### מסד נתונים

**טבלה: worklogs**

| שדה | סוג | תיאור | קשר |
|-----|------|-------|------|
| id | integer PK | מזהה | |
| work_order_id | integer | הזמנת עבודה | -> work_orders.id |
| project_id | integer | פרויקט | -> projects.id |
| user_id | integer | מדווח | -> users.id |
| report_date | date | תאריך דיווח | |
| work_hours | numeric | שעות עבודה | |
| break_hours | numeric | שעות הפסקה | |
| hourly_rate_snapshot | numeric | תעריף (צילום מרגע הדיווח) | |
| cost_before_vat | numeric | עלות לפני מע"מ | |
| cost_with_vat | numeric | עלות כולל מע"מ | |
| status | varchar | סטטוס (PENDING->SUBMITTED->APPROVED) | |
| approved_by_user_id | integer | מאשר | |
| approved_at | timestamp | זמן אישור | |

**טבלה: invoices**

| שדה | סוג | תיאור | קשר |
|-----|------|-------|------|
| id | integer PK | מזהה | |
| invoice_number | varchar NOT NULL | מספר חשבונית (INV-YYYY-NNNN) | |
| supplier_id | integer NOT NULL | ספק | |
| project_id | integer | פרויקט | |
| subtotal | numeric NOT NULL | סכום לפני מע"מ | |
| tax_amount | numeric NOT NULL | מע"מ (17%) | |
| total_amount | numeric NOT NULL | סכום כולל | |
| paid_amount | numeric | סכום ששולם | |
| status | varchar NOT NULL | סטטוס (DRAFT->APPROVED->PAID) | |
| issue_date | date NOT NULL | תאריך הפקה | |
| due_date | date NOT NULL | תאריך פירעון | |

**טבלה: budgets**

| שדה | סוג | תיאור | קשר |
|-----|------|-------|------|
| id | integer PK | מזהה | |
| project_id | integer | פרויקט | |
| total_amount | numeric | תקציב כולל | |
| committed_amount | numeric | סכום מוקפא (הזמנות פתוחות) | |
| spent_amount | numeric | סכום שנוצל (דיווחים מאושרים) | |
| remaining_amount | numeric | יתרה זמינה | |



---

## סיכום טכנולוגי

| שכבה | טכנולוגיה |
|------|-----------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Backend | FastAPI (Python), SQLAlchemy ORM |
| Database | PostgreSQL 16 + PostGIS |
| Authentication | JWT + OTP (email) + WebAuthn (biometric) |
| Maps | Leaflet + PostGIS spatial queries |
| Deployment | Gunicorn, systemd, Nginx, GitHub Actions CI/CD |
| Monitoring | Sentry (error tracking), Loguru (structured logging) |
