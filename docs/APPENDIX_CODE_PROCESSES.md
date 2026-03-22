# נספח קוד — 3 תהליכים מרכזיים | Forewise v2.0.0

**תאריך:** 22.03.2026
**מערכת:** Forewise — מערכת ניהול יערות
**טכנולוגיות:** FastAPI (Python) + React (TypeScript) + PostgreSQL

---

## תהליך 1 — סבב הוגן (Fair Rotation)

### מטרה
מנגנון אוטומטי להקצאת ספקים להזמנות עבודה בצורה הוגנת.
המערכת בוחרת ספק לפי 5 בדיקות: פעיל באזור, פעיל במערכת, יש ציוד מתאים, יש רישוי, וציוד פנוי.
הספק עם הכי פחות הקצאות נבחר ראשון. אם לא נמצא באזור — מחפש במרחב, ואז מתריע למתאם.

### Backend — supplier_rotation_service.py

```python
# Scoring formula — higher score = selected first
# days_waiting x 10 + (100 / assignments+1) x 5 + rating x 2
score = (
    days_since_last * 10                                     # more waiting = higher priority
    + (100 / ((rotation.total_assignments or 0) + 1)) * 5    # fewer jobs = higher priority
    + (float(supplier.rating or 3)) * 2                      # higher rating = slight bonus
)
```

```python
# 5-check supplier selection with area -> region -> coordinator fallback
def select_supplier_with_checks(self, db, area_id, region_id, equipment_model_id, exclude_ids):

    def _find_in_scope(scope_filter):
        # 1. Filter: Supplier.is_active == True + scope (area/region)
        # 2. Filter: exclude previously tried suppliers
        for supplier in query.all():
            eq_query = db.query(SupplierEquipment).filter(
                SupplierEquipment.supplier_id == supplier.id,
                SupplierEquipment.is_active == True,          # Check 3: has equipment
                SupplierEquipment.license_plate != None,       # Check 4: has license plate
                SupplierEquipment.status == 'available',       # Check 5: equipment available
            )
            if equipment_model_id:                             # Match equipment model
                eq_query = eq_query.filter(
                    SupplierEquipment.equipment_model_id == equipment_model_id
                )
            if eq_query.first():
                valid.append(supplier)

        valid.sort(key=lambda s: s.total_assignments or 0)     # Fewest assignments first
        return valid[0]                                         # Winner

    # Fallback chain:
    # 1. Try area_id -> supplier active in project area
    supplier = _find_in_scope(Supplier.active_area_ids.contains([area_id]))
    if supplier: return {"supplier_id": supplier.id, "fallback_level": "area"}

    # 2. Try region_id -> supplier active in project region
    supplier = _find_in_scope(Supplier.active_region_ids.contains([region_id]))
    if supplier: return {"supplier_id": supplier.id, "fallback_level": "region"}

    # 3. No supplier found -> notify coordinator manually
    return {"supplier_id": None, "notify_coordinator": True}
```

### Backend — work_order_service.py (integration)

```python
# Called when work order has no supplier assigned
def send_to_supplier(self, db, work_order_id):
    if not work_order.supplier_id:
        selected = self._select_supplier_by_rotation(db, work_order)
        work_order.supplier_id = selected

    # Generate portal token (valid 3 hours)
    token = secrets.token_urlsafe(32)
    portal_url = f"https://forewise.co/supplier-portal/{token}"
    work_order.status = "DISTRIBUTING"

    # Send email to supplier with portal link
    send_email(to=supplier.email, subject=f"הזמנת עבודה #{order_number}")
```

### Frontend — OrderCoordination.tsx (coordinator screen)

```tsx
// Force supplier assignment (bypasses fair rotation)
const handleForceSupplier = async (workOrderId, supplierId, reason) => {
  await api.post(`/work-orders/${workOrderId}/force-supplier`, {
    supplier_id: supplierId,
    reason: reason,                          // min 10 chars explanation
    constraint_reason_id: selectedReasonId,  // why bypassing rotation
  });
};

// Send to next supplier in rotation
const handleMoveToNext = async (workOrderId) => {
  await api.post(`/work-orders/${workOrderId}/move-to-next`);
};
```

### טבלאות מרכזיות

| טבלה | שדות מרכזיים |
|-------|-------------|
| supplier_rotations | supplier_id, equipment_type_id, area_id, rotation_position, total_assignments, last_assignment_date, priority_score |
| suppliers | id, name, is_active, active_area_ids[], active_region_ids[], total_assignments, rating |
| supplier_equipment | supplier_id, equipment_model_id, license_plate, status, is_active |
| work_orders | supplier_id, status, portal_token, token_expires_at, is_forced_selection |

---

## תהליך 2 — דיווח שעות + חישוב עלות

### מטרה
תהליך דיווח שעות עבודה ע"י מנהל עבודה בשטח.
שני סוגים: דיווח **תקן** (9 שעות ליום, בלוק אחד) ודיווח **לא תקן** (סגמנטים עם אחוזי תשלום).
המערכת מחשבת עלות אוטומטית: שעות x תעריף + לינה, כולל מע"מ 17%.

### Backend — worklog_service.py

```python
# Report number — sequential, displayed as WL-YYYY-XXXX
def _generate_report_number(self, db):
    max_num = db.query(func.max(Worklog.report_number)).scalar() or 0
    return max_num + 1   # e.g. 48 -> displayed as WL-2026-0048

# Rate resolution chain:
# 1. Work order hourly_rate (manual input)
# 2. Equipment type default_hourly_rate (from equipment_types table)
# 3. 0 (no rate)
def _resolve_hourly_rate(self, db, worklog_dict):
    wo = db.query(WorkOrder).filter_by(id=wo_id).first()
    if wo and wo.hourly_rate:
        return float(wo.hourly_rate)                 # Priority 1: WO rate
    if wo and wo.equipment_type:
        et = db.query(EquipmentType).filter(name=wo.equipment_type).first()
        if et: return float(et.default_hourly_rate)  # Priority 2: type rate
    return 0

# Cost calculation during creation
def create(self, db, data, current_user_id):
    # Overnight guard
    overnight_total = 0.0
    if includes_guard:
        worklog_dict['is_overnight'] = True
        worklog_dict['overnight_nights'] = 1
        overnight_total = 250.0     # NIS 250 per night

    # Cost = (hours x rate) + overnight
    rate = self._resolve_hourly_rate(db, worklog_dict)
    hours = float(worklog_dict['work_hours'])

    worklog_dict['cost_before_vat'] = round(hours * rate + overnight_total, 2)
    worklog_dict['cost_with_vat']   = round(cost_before_vat * 1.17, 2)
```

### Frontend — WorklogFormUnified.tsx

```tsx
// Two modes: standard and non-standard
const [isNonStandard, setIsNonStandard] = useState(false);

// Non-standard activity types with billing percentages
const ACTIVITY_TYPES = [
  { value: 'work',             label: 'עבודה',           percent: 100 },
  { value: 'rest',             label: 'מנוחה',           percent: 0   },
  { value: 'idle_50',          label: 'בטלה 50%',        percent: 50  },
  { value: 'idle_100',         label: 'בטלה 100%',       percent: 100 },
  { value: 'equipment_change', label: 'החלפת כלים 50%',  percent: 50  },
  { value: 'travel_50',        label: 'נסיעות 50%',      percent: 50  },
];

// Submit payload
const payload = {
  work_order_id,
  project_id: selectedProject.id,
  work_date: formData.work_date,
  work_hours: totalHours,           // 9 for standard, calculated for non-standard
  includes_guard: formData.includes_guard,
  report_type: isNonStandard ? 'manual' : 'standard',
  segments: isNonStandard ? segments : undefined,
};

// Offline support
if (!navigator.onLine) {
  await saveOfflineWorklog(payload);  // Saved to IndexedDB, synced later
  return;
}
await api.post('/worklogs', payload);
```

### טבלאות מרכזיות

| טבלה | שדות מרכזיים |
|-------|-------------|
| worklogs | id, report_number, report_type, work_order_id, project_id, user_id, report_date, work_hours, hourly_rate_snapshot, cost_before_vat, cost_with_vat, vat_rate, is_overnight, overnight_nights, status |
| worklog_segments | worklog_id, type, start_time, end_time, percent, notes |
| equipment_types | id, name, default_hourly_rate, overnight_rate |

### נוסחאות

```
תקן:     work_hours = 9 (קבוע)
לא תקן:  work_hours = sum(segment_hours x segment_percent / 100)

cost_before_vat = work_hours x hourly_rate + overnight_nights x 250
cost_with_vat   = cost_before_vat x 1.17
```

---

## תהליך 3 — הקפאת תקציב + שחרור

### מטרה
כשנפתחת הזמנת עבודה, המערכת מקפיאה סכום מתקציב הפרויקט (committed_amount).
כשההזמנה נסגרת, ההקפאה משוחררת והעלות בפועל עוברת ל-spent_amount.
אם אין מספיק תקציב — ההזמנה נחסמת עם הודעת שגיאה.

### Backend — budget_service.py

```python
# FREEZE — called when work order is created
def freeze_budget_for_work_order(project_id, work_order_id, amount, db):
    budget = db.query(Budget).filter(
        Budget.project_id == project_id,
        Budget.is_active == True,
    ).first()

    # available = total - committed - spent
    committed = float(budget.committed_amount or 0)
    spent     = float(budget.spent_amount or 0)
    total     = float(budget.total_amount or 0)
    available = total - committed - spent

    if available < amount:
        raise ValueError(f"אין מספיק תקציב. זמין: {available}, נדרש: {amount}")

    # Freeze: add to committed, reduce remaining
    budget.committed_amount = committed + amount
    budget.remaining_amount = total - budget.committed_amount - spent

    # Store freeze on work order
    wo.frozen_amount = amount
    wo.remaining_frozen = amount
```

```python
# RELEASE — called when work order is closed/completed
def release_budget_freeze(work_order_id, actual_amount, db):
    frozen = float(wo.frozen_amount or 0)

    budget.committed_amount = max(0, committed - frozen)  # Unfreeze
    budget.spent_amount     = spent + actual_amount        # Record actual
    budget.remaining_amount = total - committed - spent    # Recalculate

    wo.frozen_amount = 0                                   # Clear
```

```python
# TRANSFER — budget reallocation between projects
def request_budget_transfer(from_budget_id, to_budget_id, amount, reason, db):
    transfer = BudgetTransfer(status="PENDING")  # Requires area manager approval

def approve_budget_transfer(transfer_id, approved_amount, db):
    from_b.total_amount -= approved_amount       # Deduct from source
    to_b.total_amount   += approved_amount       # Add to destination
    transfer.status = "APPROVED"
```

### Backend — work_order_service.py (budget validation)

```python
# In create_work_order() — validate BEFORE creating
estimated_cost = float(estimated_hours) * hourly_rate + overnight_nights * 250

available = total - committed - spent
if estimated_cost > available:
    raise HTTPException(400,
        f"אין תקציב מספיק. עלות: {estimated_cost}, יתרה: {available}"
    )

# After creation -> freeze budget
freeze_budget_for_work_order(project_id, work_order_id, freeze_amount, db)
```

### Frontend — NewWorkOrder.tsx (cost estimate)

```tsx
const BILLABLE_HOURS_PER_DAY = 9;        // 10.5h shift - 1.5h break = 9h billed
const OVERNIGHT_NIGHT_RATE   = 250;       // NIS 250 per overnight

const totalHours     = workDays * BILLABLE_HOURS_PER_DAY;     // 3 days x 9 = 27h
const overnightNights = hasOvernight ? workDays - 1 : 0;      // 3 days = 2 nights
const hoursCost      = totalHours * hourlyRate;                // 27 x 150 = 4,050
const overnightCost  = overnightNights * OVERNIGHT_NIGHT_RATE; // 2 x 250 = 500
const totalAmount    = hoursCost + overnightCost;              // 4,550

// Submitted as frozen_amount to lock budget
{ frozen_amount: totalAmount, total_amount: totalAmount, days: workDays, ... }
```

### טבלאות מרכזיות

| טבלה | שדות מרכזיים |
|-------|-------------|
| budgets | id, project_id, total_amount, committed_amount (frozen), spent_amount (actual), remaining_amount, fiscal_year |
| work_orders | frozen_amount, remaining_frozen, total_amount, estimated_hours, hourly_rate |
| budget_transfers | from_budget_id, to_budget_id, amount, status (PENDING/APPROVED/REJECTED) |

### תרשים זרימת תקציב

```
 תקציב פרויקט (budgets)

  total_amount = 100,000
  |-- committed_amount (מוקפא) = 15,000  <-- הזמנות פתוחות
  |-- spent_amount (בוצע)      = 35,000  <-- הזמנות שנסגרו
  +-- remaining_amount (זמין)  = 50,000  <-- total - committed - spent

  [הזמנה חדשה 4,550]
   -> committed += 4,550  |  remaining -= 4,550

  [הזמנה נסגרה, עלות בפועל 4,200]
   -> committed -= 4,550  |  spent += 4,200  |  remaining += 350
                                               (חיסכון 350)
```

---

*Forewise v2.0.0 — Code Appendix | Generated 22.03.2026*
