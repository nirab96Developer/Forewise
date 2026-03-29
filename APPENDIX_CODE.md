# נספח ב׳ — קוד תהליכים עיקריים (Code Appendix)
## מערכת Forewise — ניהול פרויקטים ויערות

---

# תהליך 1: מחזור חיי הזמנת עבודה (Work Order Lifecycle)
## End-to-End Flow: יצירה → הפצה → אישור ספק → אישור מתאם → סריקת ציוד → דיווח

### א. שם ומטרה
**שם:** Work Order Lifecycle — מחזור חיי הזמנת עבודה
**מטרה:** תהליך זה מייצג את הליבה העסקית של המערכת. הזמנת עבודה עוברת 7 שלבים מרגע יצירתה על ידי מנהל העבודה, דרך הפצה לספקים, אישור מתאם, סריקת ציוד בשטח, ועד דיווח שעות. כל שלב כולל ולידציות, עדכון State Machine, ועדכון תקציבי. התהליך מבטיח שאין עבודה בשטח ללא אישור, ואין דיווח ללא כלי סרוק.

### ב. קוד צד לקוח (Frontend)
📸 *[צילום מסך — Project Workspace עם הזמנה]*

**קבצים:**
- `app_frontend/src/pages/Projects/ProjectWorkspaceNew.tsx` — Workspace ראשי
- `app_frontend/src/pages/WorkOrders/NewWorkOrder.tsx` — טופס יצירה
- `app_frontend/src/pages/Dashboard/OrderCoordinatorDashboard.tsx` — תור מתאם

**קוד Frontend — סריקת ציוד עם 3 תרחישים:**
```
// ScanEquipmentModal — 3 scenarios
// File: ProjectWorkspaceNew.tsx

// Scenario A: Full match → auto-approve
const handleScan = async () => {
  const res = await api.post(
    `/work-orders/${orderId}/scan-equipment`,
    { license_plate: trimmed }
  );
  if (res.data.status === 'ok') {
    // Equipment matched — WO moves to IN_PROGRESS
    onScanned(orderId, trimmed);
  } else if (res.data.status === 'different_plate') {
    // Scenario B: Same type, different plate — ask user
    setPhase('different_plate');
  } else if (res.data.status === 'wrong_type') {
    // Scenario C: Wrong type — block (Admin only override)
    setPhase('wrong_type');
  }
};

// Scenario B: User confirms different plate
const handleConfirmDifferentPlate = async () => {
  await api.post(`/work-orders/${orderId}/confirm-equipment`, {
    equipment_id: scanResult.equipment_id,
  });
  // Equipment transferred from old project,
  // remaining budget released
};

// Scenario C: Admin override for wrong type
const handleAdminOverride = async () => {
  await api.post(`/work-orders/${orderId}/admin-override-equipment`, {
    license_plate: value.trim(),
    reason: adminReason.trim(),
  });
  // Logged in activity_logs as ADMIN_EQUIPMENT_OVERRIDE
};
```

### ג. קוד צד שרת (Backend)

**קבצים:**
- `app_backend/app/services/work_order_service.py` — שירות הזמנות
- `app_backend/app/routers/work_orders.py` — endpoints
- `app_backend/app/services/supplier_rotation_service.py` — סבב הוגן

**State Machine — מעברי סטטוס:**
```
DRAFT → PENDING → DISTRIBUTING → SUPPLIER_ACCEPTED_PENDING_COORDINATOR
→ APPROVED_AND_SENT → IN_PROGRESS → COMPLETED
```

**קוד Backend — scan-equipment endpoint:**
```python
# File: work_orders.py — POST /{work_order_id}/scan-equipment

@router.post("/{work_order_id}/scan-equipment")
def scan_equipment(work_order_id, body, db, current_user):
    """
    Scan equipment QR/license plate and match against work order.
    3 scenarios:
      A) Full match — plate + type match -> auto-approve
      B) Same type, different plate -> return question
      C) Wrong type -> block (only Admin can override)
    """
    wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    scanned_eq = db.query(Equipment).filter(
        Equipment.license_plate == license_plate
    ).first()

    # Scenario A: Full match
    if license_plate == expected_plate:
        wo.equipment_id = scanned_eq.id
        wo.equipment_license_plate = license_plate
        wo.status = "IN_PROGRESS"  # State transition
        return {"status": "ok"}

    # Scenario B: Same type, different plate
    if scanned_eq and scanned_type == wo_type:
        return {
            "status": "different_plate",
            "question": "הכלי שנסרק שונה. האם לשייך?",
            "old_project": old_project_info,
        }

    # Scenario C: Wrong type — BLOCK
    return {
        "status": "wrong_type",
        "admin_can_override": is_admin,
    }
```

**קוד Backend — confirm-equipment (העברה בין פרויקטים):**
```python
# File: work_orders.py — POST /{work_order_id}/confirm-equipment

def _release_equipment_from_old_wo(db, equipment, exclude_wo_id, actor_id):
    """
    Release equipment from previous project:
    - Keep already-reported hours (spent stays)
    - Release remaining frozen budget
    - Mark old WO as STOPPED
    """
    for old_wo in old_wos:
        remaining = float(old_wo.remaining_frozen or 0)
        if remaining > 0 and budget:
            budget.committed_amount -= remaining
            budget.remaining_amount = total - committed - spent
        old_wo.remaining_frozen = 0
        old_wo.equipment_id = None
        old_wo.status = "STOPPED"
```

**זרימה:** Frontend שולח license_plate → Backend בודק התאמה → מחזיר תרחיש → Frontend מציג UI מתאים → Backend מעדכן equipment_id + status + budget

### ד. בסיס נתונים

**טבלאות:**
- `work_orders` — הזמנת עבודה (status, equipment_id, equipment_license_plate, frozen_amount, remaining_frozen)
- `equipment` — ציוד (license_plate, equipment_type, supplier_id, assigned_project_id)
- `supplier_invitations` — היסטוריית שליחה לספקים
- `budgets` — תקציב פרויקט (committed_amount, spent_amount, remaining_amount)

**קשרים:**
- work_orders.project_id → projects.id
- work_orders.supplier_id → suppliers.id
- work_orders.equipment_id → equipment.id
- equipment.supplier_id → suppliers.id

📸 *[צילום מסך — DB אחרי סריקת ציוד]*

---

# תהליך 2: תמחור ואישור דיווח + עדכון תקציבי
## Worklog Pricing → Approval → Budget Release → Invoice

### א. שם ומטרה
**שם:** Worklog Pricing & Approval Pipeline
**מטרה:** תהליך זה מבטיח שכל דיווח עבודה מתומחר אוטומטית לפי היררכיית תעריפים (ספק → כלי → סוג ציוד), עובר אישור חשבונאי, ורק אז מקבל תוקף כספי. עם האישור מתעדכן התקציב בזמן אמת. התהליך מונע מניפולציה: הלקוח לא יכול לשלוח תעריף או עלות — הכל מחושב בצד השרת.

### ב. קוד צד לקוח (Frontend)
📸 *[צילום מסך — טופס דיווח + Accountant Inbox]*

**קבצים:**
- `app_frontend/src/pages/WorkLogs/WorklogFormUnified.tsx` — טופס דיווח
- `app_frontend/src/pages/WorkLogs/AccountantInbox.tsx` — אישור דיווחים

**קוד Frontend — שליחת דיווח:**
```
// File: WorklogFormUnified.tsx
const payload = {
  project_id: formData.project_id,
  work_order_id: formData.work_order_id,
  work_date: formData.work_date,
  work_hours: totals.workHours,
  break_hours: totals.restHours,
  includes_guard: overnight,  // Overnight flag
  // NOTE: hourly_rate, cost_before_vat, cost_with_vat
  // are NOT sent — server calculates them
};
```

### ג. קוד צד שרת (Backend)

**קבצים:**
- `app_backend/app/services/worklog_service.py` — שירות דיווחים
- `app_backend/app/services/rate_service.py` — היררכיית תעריפים
- `app_backend/app/routers/worklogs.py` — endpoints

**קוד Backend — חישוב תעריף (Rate Resolution):**
```python
# File: rate_service.py — get_equipment_rate()

def get_equipment_rate(equipment_id, supplier_id, db):
    """
    Rate priority chain:
    1. supplier_equipment.hourly_rate (specific to supplier+equipment)
    2. equipment.hourly_rate (specific to equipment)
    3. equipment_types.hourly_rate (default for equipment type)
    
    overnight_rate: from equipment_types.overnight_rate
    """
    # Priority 1: Supplier-specific rate
    se = db.query(SupplierEquipment).filter(
        SupplierEquipment.equipment_id == equipment_id,
        SupplierEquipment.supplier_id == supplier_id,
    ).first()
    if se and float(se.hourly_rate) > 0:
        return {"hourly_rate": float(se.hourly_rate), "source": "supplier_equipment"}

    # Priority 2: Equipment-level rate
    eq = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if eq.hourly_rate and float(eq.hourly_rate) > 0:
        return {"hourly_rate": float(eq.hourly_rate), "source": "equipment"}

    # Priority 3: Equipment type default
    et = db.query(EquipmentType).filter(EquipmentType.id == eq.equipment_type_id).first()
    if et and float(et.hourly_rate) > 0:
        return {"hourly_rate": float(et.hourly_rate), "source": "equipment_type"}
```

**קוד Backend — יצירת דיווח עם ולידציות:**
```python
# File: worklog_service.py — create()

def create(self, db, data, current_user_id):
    # RULE 1: work_order_id is mandatory
    # RULE 2: project_id must exist on WO
    # RULE 3: WO must be APPROVED_AND_SENT / IN_PROGRESS / ACTIVE
    # RULE 4: Equipment must be scanned (license_plate on WO)
    # RULE 5: Equipment type mismatch — BLOCK (Admin only)
    # RULE 6: One worklog per day + WO

    # Strip unsafe client fields (prevent manipulation)
    for unsafe_field in ('hourly_rate_snapshot', 'cost_before_vat',
                         'cost_with_vat', 'vat_rate'):
        worklog_dict.pop(unsafe_field, None)

    # Server-side pricing
    rate = self._resolve_hourly_rate(db, worklog_dict)
    worklog_dict['hourly_rate_snapshot'] = rate
    worklog_dict['cost_before_vat'] = hours * rate + overnight_total
    worklog_dict['cost_with_vat'] = cost_before_vat * 1.18
```

**קוד Backend — אישור דיווח + עדכון תקציב:**
```python
# File: worklog_service.py — approve()

def approve(self, db, worklog_id, current_user_id):
    # Self-approval block
    if worklog.user_id == current_user_id:
        raise ValidationException("לא ניתן לאשר דיווח שנוצר על ידך")

    worklog.status = 'APPROVED'
    worklog.approved_by_user_id = current_user_id

    # Budget update — CRITICAL financial moment
    cost = float(worklog.cost_before_vat)
    release = min(cost, float(wo.remaining_frozen))
    budget.committed_amount -= release     # Frozen → released
    budget.spent_amount += cost            # Now counted as spent
    budget.remaining_amount = total - committed - spent
    wo.remaining_frozen -= release

    # Auto-complete WO when all budget consumed
    if wo.remaining_frozen <= 0:
        wo.status = 'COMPLETED'
        equipment.assigned_project_id = None  # Free equipment
```

**זרימה:** מנהל עבודה יוצר דיווח → Server מחשב תעריף + עלות → דיווח PENDING → Submit → SUBMITTED → חשבונאית מאשרת → APPROVED → תקציב מתעדכן → אם נגמר → WO COMPLETED

### ד. בסיס נתונים

**טבלאות:**
- `worklogs` — דיווח (work_hours, hourly_rate_snapshot, cost_before_vat, cost_with_vat, vat_rate, status, approved_by_user_id)
- `budgets` — תקציב (total_amount, committed_amount, spent_amount, remaining_amount)
- `supplier_equipment` — תעריף ספק-ציוד (hourly_rate)
- `equipment_types` — תעריף ברירת מחדל (hourly_rate, overnight_rate)

**שדות מרכזיים ב-worklogs:**
- hourly_rate_snapshot: תעריף שנקבע ברגע היצירה (snapshot)
- cost_before_vat: שעות × תעריף + לינה
- cost_with_vat: לפני מע"מ × 1.18
- vat_rate: 0.18 (קבוע)

📸 *[צילום מסך — DB אחרי אישור דיווח]*

---

# תהליך 3: אלגוריתם סבב הוגן + אילוץ ספק
## Fair Rotation Algorithm + Supplier Constraint Override

### א. שם ומטרה
**שם:** Fair Rotation — אלגוריתם סבב הוגן לחלוקת ספקים
**מטרה:** האלגוריתם מבטיח חלוקה הוגנת של הזמנות עבודה בין ספקים. הוא מתחשב במספר הזמנות קודמות, ימים מאז הזמנה אחרונה, דחיות, ואזור שירות. כאשר נדרש אילוץ ספק (בחירה ידנית), המערכת דורשת סיבה מתועדת ומעדכנת את הסבב בהתאם. זה מונע העדפת ספקים ומבטיח שקיפות.

### ב. קוד צד לקוח (Frontend)
📸 *[צילום מסך — סבב הוגן + אילוץ ספק]*

**קבצים:**
- `app_frontend/src/pages/Settings/FairRotation.tsx` — מסך סבב הוגן
- `app_frontend/src/pages/WorkOrders/NewWorkOrder.tsx` — בחירת ספק

### ג. קוד צד שרת (Backend)

**קבצים:**
- `app_backend/app/services/supplier_rotation_service.py` — אלגוריתם סבב
- `app_backend/app/services/work_order_service.py` — שליחה לספק
- `app_backend/app/routers/work_orders.py` — endpoints

**קוד Backend — אלגוריתם הסבב:**
```python
# File: supplier_rotation_service.py — get_rotation_queue()

def get_rotation_queue(self, db, area_id, equipment_type_id, limit=10):
    """
    Priority scoring algorithm:
    - Base score from rotation_position
    - Bonus for days waiting (more days = higher priority)
    - Penalty for rejections (-10 per rejection)
    - Filter: only suppliers with active equipment + license plate
    """
    results = (
        db.query(Supplier, SupplierRotation)
        .join(SupplierRotation)
        .filter(
            SupplierRotation.is_active == True,
            SupplierRotation.is_available != False,
        )
    )
    if area_id:
        results = results.filter(SupplierRotation.area_id == area_id)
    if equipment_type_id:
        results = results.filter(
            SupplierRotation.equipment_type_id == equipment_type_id
        )

    queue = []
    for supplier, rotation in results:
        # Verify supplier actually has equipment with license plate
        eq_check = db.query(Equipment).filter(
            Equipment.supplier_id == supplier.id,
            Equipment.is_active == True,
            Equipment.license_plate != None,
        )
        if equipment_type_id:
            eq_check = eq_check.filter(Equipment.type_id == equipment_type_id)
        if not eq_check.first():
            continue  # Skip suppliers without valid equipment

        days_since_last = 999
        if rotation.last_assignment_date:
            days_since_last = (date.today() - rotation.last_assignment_date).days

        # Priority score calculation
        priority_score = (
            (rotation.priority_score or 50)
            + days_since_last * 2      # Waiting bonus
            - (rotation.rejection_count or 0) * 10  # Rejection penalty
        )
        queue.append({
            "supplier_id": supplier.id,
            "supplier_name": supplier.name,
            "days_waiting": days_since_last,
            "total_assignments": rotation.total_assignments or 0,
            "rejection_count": rotation.rejection_count or 0,
            "priority_score": priority_score,
        })

    # Sort by priority score (highest first = most deserving)
    queue.sort(key=lambda x: x["priority_score"], reverse=True)
    return queue[:limit]
```

**קוד Backend — עדכון סבב אחרי הקצאה:**
```python
# File: supplier_rotation_service.py

def update_rotation_after_assignment(self, db, supplier_id, equipment_type_id, area_id):
    """Push supplier to back of queue after assignment."""
    rotation.last_assignment_date = date.today()
    rotation.total_assignments += 1
    rotation.is_available = False  # Busy
    rotation.priority_score = max(0, rotation.priority_score - 20)

def update_rotation_after_rejection(self, db, supplier_id, equipment_type_id):
    """Penalize supplier who rejected."""
    rotation.rejection_count += 1
    rotation.priority_score = max(0, rotation.priority_score - 10)

def update_rotation_after_completion(self, db, supplier_id, equipment_type_id):
    """Reward supplier who completed successfully."""
    rotation.successful_completions += 1
    rotation.is_available = True   # Free again
    rotation.priority_score += 15  # Completion bonus
```

**קוד Backend — אילוץ ספק (Force Supplier):**
```python
# File: work_order_service.py — force_supplier()

def force_supplier(self, db, work_order_id, supplier_id, reason, user_id):
    """
    Admin/coordinator forces a specific supplier.
    - Reason is MANDATORY (audit trail)
    - Supplier must have matching equipment type
    - Rotation is updated to push forced supplier to back
    """
    if not reason or not reason.strip():
        raise HTTPException(400, "Reason required for forced selection")

    wo.supplier_id = supplier_id
    wo.is_forced_selection = True
    wo.constraint_notes = reason

    # Update rotation — push to back of queue
    rotation_service.enforce_rotation(db, supplier_id, wo.equipment_type_id)
```

**זרימה:** הזמנה חדשה → אלגוריתם בוחר ספק (highest priority_score) → שליחה לספק → אם דוחה: penalty + ספק הבא → אם מאשר: bonus + available=false → אחרי השלמה: completion bonus + available=true

### ד. בסיס נתונים

**טבלאות:**
- `supplier_rotations` — סבב הוגן (supplier_id, equipment_type_id, area_id, priority_score, total_assignments, rejection_count, last_assignment_date, is_available)
- `supplier_invitations` — היסטוריית הזמנות לספקים (supplier_id, work_order_id, status, response_notes)
- `supplier_constraints` — אילוצי ספק (work_order_id, supplier_id, reason, created_by)

**שדות מרכזיים ב-supplier_rotations:**
- priority_score: ניקוד עדיפות (גבוה = בתור ראשון)
- total_assignments: סה"כ הקצאות
- rejection_count: סה"כ דחיות
- is_available: האם פנוי לעבודה
- last_assignment_date: תאריך הקצאה אחרונה

**קשרים:**
- supplier_rotations.supplier_id → suppliers.id
- supplier_rotations.equipment_type_id → equipment_types.id
- supplier_rotations.area_id → areas.id

📸 *[צילום מסך — DB אחרי סבב הוגן]*
