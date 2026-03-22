# Forewise v2.0.0 — Appendices
## Forest Management System | Final Project Book
**Date:** 22.03.2026 | **Author:** nirab96Developer
**Stack:** FastAPI (Python 3.10) + React 18 (TypeScript) + PostgreSQL + Leaflet

---
---

# Appendix A — Code Documentation (3 Core Processes)

---

## Process 1 — Fair Rotation Algorithm (סבב הוגן)

### Name & Purpose
**Fair Rotation Supplier Selection** — An automated algorithm that assigns
suppliers to work orders fairly. The system runs 5 checks per candidate
supplier, selects the one with fewest past assignments, and falls back
through area -> region -> coordinator notification if no match is found.

### Backend — supplier_rotation_service.py

```python
class SupplierRotationService:

    def select_supplier_with_checks(
        self, db, area_id, region_id, equipment_model_id, exclude_ids
    ):
        """
        5-check supplier selection with area -> region -> coordinator fallback.

        Checks per supplier:
        1. Active in area/region (active_area_ids contains project area)
        2. Supplier is_active = True
        3. Has equipment of requested type (supplier_equipment)
        4. Equipment has a license plate (legal requirement)
        5. Equipment status = 'available' (not assigned elsewhere)

        Returns { supplier_id, fallback_level, notify_coordinator }
        """

        def _find_in_scope(scope_filter):
            # Query all active suppliers matching the geographic scope
            query = db.query(Supplier).filter(
                Supplier.is_active == True,       # Check 2: supplier is active
                scope_filter,                     # Check 1: area or region match
            )
            if exclude_ids:                       # Skip previously tried suppliers
                query = query.filter(Supplier.id.notin_(exclude_ids))

            valid = []
            for supplier in query.all():
                # Verify supplier has matching available equipment
                eq_query = db.query(SupplierEquipment).filter(
                    SupplierEquipment.supplier_id == supplier.id,
                    SupplierEquipment.is_active == True,      # Check 3: has equipment
                    SupplierEquipment.license_plate != None,   # Check 4: has license
                    SupplierEquipment.status == 'available',   # Check 5: not in use
                )
                if equipment_model_id:            # Match specific equipment model
                    eq_query = eq_query.filter(
                        SupplierEquipment.equipment_model_id == equipment_model_id
                    )
                if eq_query.first():              # At least one unit available
                    valid.append(supplier)

            if not valid:
                return None

            # Select supplier with fewest total assignments (fairness)
            valid.sort(key=lambda s: s.total_assignments or 0)
            return valid[0]

        # --- Fallback chain ---

        # Level 1: Search within the project's area
        if area_id:
            supplier = _find_in_scope(
                Supplier.active_area_ids.contains([area_id])
            )
            if supplier:
                supplier.total_assignments = (supplier.total_assignments or 0) + 1
                return {"supplier_id": supplier.id, "fallback_level": "area",
                        "notify_coordinator": False}

        # Level 2: Expand search to the entire region
        if region_id:
            supplier = _find_in_scope(
                Supplier.active_region_ids.contains([region_id])
            )
            if supplier:
                supplier.total_assignments = (supplier.total_assignments or 0) + 1
                return {"supplier_id": supplier.id, "fallback_level": "region",
                        "notify_coordinator": False}

        # Level 3: No supplier found — alert coordinator for manual handling
        return {"supplier_id": None, "fallback_level": "none",
                "notify_coordinator": True}
```

```python
    def get_rotation_queue(self, db, area_id, equipment_type_id, limit=10):
        """
        Build a priority-scored queue of suppliers for display in the
        coordinator's dashboard. Higher score = should be selected first.
        """
        # ... filter active suppliers with equipment ...

        # Scoring formula
        score = (
            days_since_last * 10                  # Long wait = high priority
            + (100 / (total_assignments + 1)) * 5 # Few jobs = high priority
            + (rating or 3) * 2                    # Good rating = slight bonus
        )

        queue.sort(key=lambda x: x["priority_score"], reverse=True)
        return queue[:limit]
```

### Backend — work_order_service.py (Integration)

```python
    def send_to_supplier(self, db, work_order_id):
        """Send work order to supplier — auto-selects via Fair Rotation."""

        if not work_order.supplier_id:
            # Delegate to rotation algorithm
            selected = self._select_supplier_by_rotation(db, work_order)
            work_order.supplier_id = selected

        # Generate time-limited portal token (3 hours)
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=3)
        portal_url = f"https://forewise.co/supplier-portal/{token}"

        work_order.portal_token = token
        work_order.status = "DISTRIBUTING"

        # Send email notification to supplier
        send_email(
            to=supplier.email,
            subject=f"הזמנת עבודה מספר {order_number} - דורש תגובה",
            body=f"לצפייה ואישור/דחייה:\n{portal_url}\n"
                 f"הקישור תקף עד: {expires_at.strftime('%d/%m/%Y %H:%M')}"
        )
```

### Frontend — OrderCoordination.tsx

```tsx
// Coordinator screen — manages all pending work orders
// Polls every 30 seconds for status updates

// Force a specific supplier (bypasses fair rotation)
const handleForceSupplier = async (workOrderId, supplierId, reason) => {
  await api.post(`/work-orders/${workOrderId}/force-supplier`, {
    supplier_id: supplierId,             // Manually chosen supplier
    reason: reason,                      // Requires min 10 chars
    constraint_reason_id: selectedId,    // Why bypassing rotation
  });
};

// Move to next supplier in rotation queue
const handleMoveToNext = async (workOrderId) => {
  await api.post(`/work-orders/${workOrderId}/move-to-next`);
  // System selects next-best supplier automatically
};

// Auto-refresh every 30 seconds
useEffect(() => {
  const interval = setInterval(loadOrders, 30000);
  return () => clearInterval(interval);
}, []);
```

### Database Tables

| Table | Key Fields | Description |
|-------|-----------|-------------|
| `suppliers` | `id`, `name`, `is_active`, `active_area_ids[]`, `active_region_ids[]`, `total_assignments`, `rating` | Supplier registry with geographic service areas |
| `supplier_rotations` | `supplier_id`, `equipment_type_id`, `area_id`, `rotation_position`, `total_assignments`, `last_assignment_date`, `priority_score` | Rotation state per supplier-equipment-area combination |
| `supplier_equipment` | `supplier_id`, `equipment_model_id`, `license_plate`, `status` (`available`/`in_use`), `is_active` | Physical equipment inventory per supplier |
| `work_orders` | `supplier_id`, `status`, `portal_token`, `token_expires_at`, `is_forced_selection`, `constraint_notes` | Work order with supplier assignment and portal state |

### Process Flow
```
1. Work manager creates order → selects "Fair Rotation"
2. System runs 5 checks (active, equipment, license, available)
3. Selects supplier with fewest assignments in area
4. If none found → searches region → if none → alerts coordinator
5. Sends portal link to supplier (3-hour token)
6. Supplier accepts/rejects via portal
7. If rejected → auto-moves to next supplier in queue
```

---

## Process 2 — Work Hours Reporting & Cost Calculation (דיווח שעות)

### Name & Purpose
**Work Hours Reporting and Automatic Cost Calculation** — Field workers
report daily work hours in standard (9h/day fixed) or non-standard
(custom segments with billing percentages) mode. The system automatically
calculates costs using the equipment type's hourly rate, adds overnight
guard fees, and applies 17% VAT.

### Backend — worklog_service.py

```python
class WorklogService:

    def _generate_report_number(self, db):
        """Generate sequential report number, displayed as WL-YYYY-XXXX."""
        max_num = db.query(func.max(Worklog.report_number)).scalar() or 0
        return max_num + 1     # e.g. 48 -> displayed as WL-2026-0048

    @staticmethod
    def format_report_number(report_number):
        """Format for display: WL-2026-0047"""
        return f"WL-{datetime.now().year}-{str(report_number).zfill(4)}"

    def _resolve_hourly_rate(self, db, worklog_dict):
        """
        Hourly rate resolution chain:
          1. Work order hourly_rate (if manually set during order creation)
          2. Equipment type default_hourly_rate (from equipment_types table)
          3. 0 (no rate found — will be flagged as unverified)
        """
        wo = db.query(WorkOrder).filter_by(id=wo_id).first()
        if wo and wo.hourly_rate:
            return float(wo.hourly_rate)               # Priority 1

        if wo and wo.equipment_type:
            et = db.query(EquipmentType).filter(
                EquipmentType.name.ilike(wo.equipment_type)
            ).first()
            if et:
                return float(et.default_hourly_rate)   # Priority 2

        return 0                                        # No rate

    def create(self, db, data, current_user_id):
        """Create worklog with automatic cost calculation."""

        report_number = self._generate_report_number(db)

        # Overnight guard handling (NIS 250 per night)
        overnight_total = 0.0
        if includes_guard:
            worklog_dict['is_overnight'] = True
            worklog_dict['overnight_nights'] = 1
            worklog_dict['overnight_rate'] = Decimal('250')
            overnight_total = 250.0

        # Resolve hourly rate from work order or equipment type
        rate = self._resolve_hourly_rate(db, worklog_dict)
        hours = float(worklog_dict.get('work_hours') or 0)

        # Cost formula: (hours x rate) + overnight guard fee
        worklog_dict['cost_before_vat'] = round(
            hours * rate + overnight_total, 2
        )
        worklog_dict['vat_rate'] = 17.0
        worklog_dict['cost_with_vat'] = round(
            worklog_dict['cost_before_vat'] * 1.17, 2
        )

        worklog = Worklog(**worklog_dict)
        db.add(worklog)
        db.commit()
        return worklog
```

### Frontend — WorklogFormUnified.tsx

```tsx
// Two reporting modes: standard and non-standard
const [isNonStandard, setIsNonStandard] = useState(false);

// Standard: 06:30-17:00, 1.5h break = 9 billable hours
// Non-standard: Custom time segments with billing percentages

const ACTIVITY_TYPES = [
  { value: 'work',             label: 'עבודה',           percent: 100 },
  { value: 'rest',             label: 'מנוחה',           percent: 0   },
  { value: 'idle_0',           label: 'בטלה 0%',         percent: 0   },
  { value: 'idle_50',          label: 'בטלה 50%',        percent: 50  },
  { value: 'idle_100',         label: 'בטלה 100%',       percent: 100 },
  { value: 'equipment_change', label: 'החלפת כלים 50%',  percent: 50  },
  { value: 'travel_50',        label: 'נסיעות 50%',      percent: 50  },
  { value: 'travel_100',       label: 'נסיעות 100%',     percent: 100 },
];

// Time segments for non-standard reports
const [segments, setSegments] = useState([
  { id: 1, type: 'work', start_time: '06:30', end_time: '12:00', notes: '' },
]);

// Overnight guard checkbox
const [formData, setFormData] = useState({
  includes_guard: false,    // Adds NIS 250 to cost
  // ...
});

// Offline support — save locally if no network connection
if (!navigator.onLine) {
  await saveOfflineWorklog(payload);
  showToast('הדיווח נשמר במכשיר — יסונכרן כשיחזור חיבור', 'info');
  return;
}
await api.post('/worklogs', payload);
```

### Database Tables

| Table | Key Fields | Description |
|-------|-----------|-------------|
| `worklogs` | `id`, `report_number`, `report_type` (`standard`/`manual`), `work_order_id`, `project_id`, `user_id`, `report_date`, `work_hours`, `hourly_rate_snapshot`, `cost_before_vat`, `cost_with_vat`, `vat_rate`, `is_overnight`, `overnight_nights`, `status` | Individual work hour reports with calculated costs |
| `worklog_segments` | `worklog_id`, `type`, `start_time`, `end_time`, `percent`, `notes` | Time breakdown segments for non-standard reports |
| `equipment_types` | `id`, `name`, `default_hourly_rate`, `overnight_rate` | Equipment pricing configuration |

### Cost Formulas
```
Standard:   work_hours = 9 (fixed: 10.5h shift - 1.5h break)
Non-std:    work_hours = SUM(segment_hours x segment_percent / 100)

cost_before_vat = work_hours x hourly_rate + overnight_nights x 250
cost_with_vat   = cost_before_vat x 1.17
report_number   = WL-{year}-{sequential_id:04d}  (e.g. WL-2026-0048)
```

---

## Process 3 — Budget Freeze & Release (הקפאת תקציב)

### Name & Purpose
**Budget Management — Freeze, Release, and Transfer** — When a work order
is created, the system freezes the estimated cost from the project budget
(`committed_amount`). When the work is completed, the freeze is released
and actual cost moves to `spent_amount`. If budget is insufficient, the
order creation is blocked with an error message.

### Backend — budget_service.py

```python
def freeze_budget_for_work_order(project_id, work_order_id, amount, db):
    """
    Called when a work order is created.
    Freezes estimated cost from the project's budget.
    Raises ValueError if insufficient budget.
    """
    budget = db.query(Budget).filter(
        Budget.project_id == project_id,
        Budget.is_active == True,
        Budget.deleted_at.is_(None),
    ).first()

    if not budget:
        raise ValueError("אין תקציב פעיל לפרויקט")

    # Calculate available budget
    committed = float(budget.committed_amount or 0)  # Already frozen
    spent     = float(budget.spent_amount or 0)       # Already used
    total     = float(budget.total_amount or 0)       # Total allocation
    available = total - committed - spent              # What's left

    # Block if insufficient
    if available < amount:
        raise ValueError(
            f"אין מספיק תקציב. זמין: {available:,.0f}, נדרש: {amount:,.0f}"
        )

    # Freeze: increase committed, decrease remaining
    budget.committed_amount = committed + amount
    budget.remaining_amount = total - budget.committed_amount - spent

    # Record freeze amount on the work order itself
    wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if wo:
        wo.frozen_amount = amount       # How much was frozen
        wo.remaining_frozen = amount    # Decreases as work is done

    db.commit()


def release_budget_freeze(work_order_id, actual_amount, db):
    """
    Called when a work order is closed/completed.
    Releases the freeze and records actual cost as spent.
    """
    wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not wo or not wo.project_id:
        return

    budget = db.query(Budget).filter(
        Budget.project_id == wo.project_id,
        Budget.is_active == True,
    ).first()
    if not budget:
        return

    frozen = float(wo.frozen_amount or 0)

    # Release frozen amount, record actual spend
    budget.committed_amount = max(0, float(budget.committed_amount or 0) - frozen)
    budget.spent_amount = float(budget.spent_amount or 0) + actual_amount
    budget.remaining_amount = (
        float(budget.total_amount or 0)
        - float(budget.committed_amount)
        - float(budget.spent_amount)
    )

    wo.frozen_amount = 0     # Clear the freeze
    db.commit()
```

### Backend — work_order_service.py (Budget Validation)

```python
    def create_work_order(self, db, work_order, created_by_id):
        """Create work order with budget validation and freeze."""

        # Estimate cost BEFORE creating the order
        estimated_cost = (
            float(estimated_hours) * hourly_rate
            + overnight_nights * 250
        )

        # Check budget availability
        available = total - committed - spent
        if estimated_cost > available:
            raise HTTPException(
                status_code=400,
                detail=f"אין תקציב מספיק. "
                       f"עלות משוערת: {estimated_cost:,.0f}, "
                       f"יתרה זמינה: {available:,.0f}"
            )

        # Create the work order ...
        db.add(db_work_order)
        db.commit()

        # Freeze budget AFTER successful creation
        freeze_budget_for_work_order(
            project_id, db_work_order.id, freeze_amount, db
        )
```

### Frontend — NewWorkOrder.tsx (Cost Estimate)

```tsx
const BILLABLE_HOURS_PER_DAY = 9;       // 10.5h shift - 1.5h break
const OVERNIGHT_NIGHT_RATE   = 250;      // NIS 250 per overnight

// Real-time cost calculation as user fills the form
const totalHours      = workDays * BILLABLE_HOURS_PER_DAY;     // 3 x 9 = 27h
const overnightNights = hasOvernight ? workDays - 1 : 0;       // 3 days = 2 nights
const hoursCost       = totalHours * hourlyRate;                // 27 x 150 = 4,050
const overnightCost   = overnightNights * OVERNIGHT_NIGHT_RATE; // 2 x 250 = 500
const totalAmount     = hoursCost + overnightCost;              // = 4,550

// Displayed in a cost estimate card on the form
// Submitted as frozen_amount to lock from project budget
const workOrderData = {
  frozen_amount: totalAmount,       // Locked from budget
  total_amount: totalAmount,        // Total estimate
  days: workDays,
  has_overnight: true,
  overnight_nights: overnightNights,
  estimated_hours: totalHours,
  hourly_rate: hourlyRate,
};
```

### Database Tables

| Table | Key Fields | Description |
|-------|-----------|-------------|
| `budgets` | `id`, `project_id`, `total_amount`, `committed_amount` (frozen), `spent_amount` (actual), `remaining_amount`, `fiscal_year`, `status` | Project budget with three-tier tracking |
| `work_orders` | `frozen_amount`, `remaining_frozen`, `total_amount`, `estimated_hours`, `hourly_rate` | Freeze state per work order |
| `budget_transfers` | `from_budget_id`, `to_budget_id`, `amount`, `status` (PENDING/APPROVED/REJECTED), `requested_by`, `approved_by` | Budget reallocation requests |

### Budget Flow Diagram
```
 Project Budget (budgets table)

  total_amount = 100,000
  |-- committed_amount (frozen)  = 15,000   <- Open work orders
  |-- spent_amount (actual)      = 35,000   <- Completed work orders
  +-- remaining_amount (free)    = 50,000   <- total - committed - spent

  [New order created: 4,550]
   -> committed += 4,550  |  remaining -= 4,550

  [Order completed, actual cost: 4,200]
   -> committed -= 4,550  |  spent += 4,200  |  remaining += 350
                                               (saved 350)

  [Order cancelled]
   -> committed -= 4,550  |  remaining += 4,550
                             (fully returned)
```

---
---

# Appendix B — UI Guide (15 Screens)

---

## Screen 1 — Work Manager Dashboard (דשבורד מנהל עבודה)

| Field | Value |
|-------|-------|
| **User role** | Work Manager (מנהל עבודה) |
| **Route** | `/` |
| **Purpose** | Central hub showing the work manager's daily overview — assigned projects, active work orders, recent hour reports, and quick actions. |
| **What the user does** | 1. Views KPI cards (projects, hours this week, pending orders). 2. Clicks a project card to enter its workspace. 3. Uses quick-action buttons (new order, report hours, scan equipment). 4. Reviews recent activity feed. |
| **Key elements** | Stat cards (projects, hours, orders), project list, quick-action buttons, activity feed, notification bell |

---

## Screen 2 — Projects List (רשימת פרויקטים)

| Field | Value |
|-------|-------|
| **User role** | All roles (filtered by permissions) |
| **Route** | `/projects` |
| **Purpose** | Browse and search all accessible projects. Work managers see only assigned projects by default ("שלי" toggle). |
| **What the user does** | 1. Searches by project name/code. 2. Filters by status (active/completed). 3. Toggles "שלי" to show only assigned projects. 4. Clicks a project card to open its workspace. 5. Exports project list to Excel. |
| **Key elements** | Search input, status filter, "שלי" toggle, project cards (name, code, region, budget %), "פרויקט חדש" button (admin), Excel export |

---

## Screen 3 — Project Workspace (סביבת עבודה — סקירה)

| Field | Value |
|-------|-------|
| **User role** | Work Manager / Area Manager / Admin |
| **Route** | `/projects/:code/workspace` |
| **Purpose** | Single-project command center with tabs: Overview, Map, Work Orders, Work Logs, Budget, Documents, Activity. |
| **What the user does** | 1. Views project overview (budget utilization %, active orders, reported hours). 2. Switches tabs to manage orders, logs, budget. 3. Creates new work order or hour report from within the project. 4. Views project location on embedded map. |
| **Key elements** | Tab bar (overview/map/orders/worklogs/budget/docs/activity), budget progress bar, stat cards, work order list, worklog list, map with project polygon |

---

## Screen 4 — New Work Order Form (דרישת כלים חדשה)

| Field | Value |
|-------|-------|
| **User role** | Work Manager |
| **Route** | `/projects/:code/workspace/work-orders/new` |
| **Purpose** | Create a new equipment request for a project. Calculates cost estimate in real-time and validates against project budget before submission. |
| **What the user does** | 1. Selects equipment type from dropdown. 2. Sets number of work days (hours auto-calculated: days x 9). 3. Sets start date (end date auto-calculated). 4. Toggles overnight guard (adds NIS 250/night). 5. Chooses allocation method (fair rotation / manual supplier selection). 6. Reviews cost estimate card. 7. Submits — system validates budget and freezes amount. |
| **Key elements** | Project selector (locked if from project context), equipment type dropdown, work days input, start date, hourly rate, overnight checkbox, allocation method (fair rotation / manual), cost estimate card (hours cost + overnight cost + total), submit button |

---

## Screen 5 — Work Order Detail (פרטי הזמנת עבודה)

| Field | Value |
|-------|-------|
| **User role** | Work Manager / Coordinator / Admin |
| **Route** | `/work-orders/:id` |
| **Purpose** | View complete work order details in a print-ready format. Shows project, supplier, equipment, dates, costs, and status. |
| **What the user does** | 1. Views order details table (project, supplier, dates, rate, frozen amount). 2. Prints or saves as PDF. 3. Reports hours against this order. 4. Edits or deletes the order. 5. Removes equipment (releases frozen budget). |
| **Key elements** | Green header with order number, status badge (Hebrew), detail table (13 rows), Print/PDF button, Report Hours button, Edit button, Delete button (with confirmation modal showing frozen amount) |

---

## Screen 6 — Standard Work Hours Report (דיווח שעות — תקן)

| Field | Value |
|-------|-------|
| **User role** | Work Manager / Field Worker |
| **Route** | `/work-orders/:id/report-hours` |
| **Purpose** | Report a standard 9-hour work day. Auto-linked to the work order and project. Supports offline submission. |
| **What the user does** | 1. Selects work date. 2. Confirms standard hours (9h). 3. Optionally checks "overnight guard" (adds NIS 250). 4. Adds notes. 5. Submits — system calculates cost automatically. |
| **Key elements** | Date picker, standard/non-standard toggle (green/orange), overnight checkbox, notes field, submit button. Offline: saved to IndexedDB if no network. |

---

## Screen 7 — Non-Standard Work Hours Report (דיווח שעות — לא תקן)

| Field | Value |
|-------|-------|
| **User role** | Work Manager |
| **Route** | `/work-orders/:id/report-hours` (non-standard toggle) |
| **Purpose** | Report work hours with detailed time segments and variable billing percentages. Used for irregular work days. |
| **What the user does** | 1. Toggles to "לא תקן" mode. 2. Adds time segments with activity type (work 100%, idle 50%, travel, etc.). 3. Sets start/end time for each segment. 4. Provides non-standard reason (required). 5. Submits. |
| **Key elements** | Segment list (add/remove), activity type dropdown (8 types with % rates), time inputs per segment, reason field (mandatory), billable hours calculation |

---

## Screen 8 — Equipment QR Scan (סריקת ציוד)

| Field | Value |
|-------|-------|
| **User role** | Work Manager / Field Worker |
| **Route** | `/equipment/scan` |
| **Purpose** | Scan equipment QR code in the field to identify and register equipment presence. Supports camera scanning and manual code entry. |
| **What the user does** | 1. Switches between camera/manual mode. 2. Points camera at QR code on equipment. 3. System identifies equipment (name, type, supplier, rate). 4. Continues to report hours for the identified equipment. |
| **Key elements** | Camera/Manual toggle, QR scanner (html5-qrcode), manual input field, equipment result card (name, supplier, type, hourly rate), "Continue to report hours" button, recent scans list |

---

## Screen 9 — Order Coordination (תיאום הזמנות)

| Field | Value |
|-------|-------|
| **User role** | Order Coordinator (מתאם הזמנות) |
| **Route** | `/order-coordination` |
| **Purpose** | Central management screen for all work orders requiring coordinator action. Shows orders grouped by status with real-time polling (30s refresh). |
| **What the user does** | 1. Views stat cards (total, pending, distributing, supplier-accepted). 2. Filters by status, equipment type, or search text. 3. Approves orders and sends to suppliers. 4. Forces specific supplier with constraint reason. 5. Moves rejected orders to next supplier in queue. 6. Bulk-deletes orders (admin only). |
| **Key elements** | Status stat cards (clickable filters), search bar, status filter chips, order cards with actions (approve/reject/send/move-to-next/force-supplier), constraint reason modal, 30s auto-refresh |

---

## Screen 10 — Accountant Inbox (תיבת אישורים — חשבונאית)

| Field | Value |
|-------|-------|
| **User role** | Accountant (מנהלת חשבונות) |
| **Route** | `/accountant-inbox` |
| **Purpose** | Review and approve/reject submitted work hour reports. Generate monthly invoices per supplier. |
| **What the user does** | 1. Views all submitted worklogs pending approval. 2. Approves or rejects individual reports. 3. Reviews cost calculations (hours x rate + VAT). 4. Generates monthly invoice (selects project, supplier, month). 5. Exports to Excel. |
| **Key elements** | Worklog list with status badges (submitted/approved/invoiced/rejected), approve/reject buttons per item, monthly invoice generator modal (project + supplier + month selectors), export buttons |

---

## Screen 11 — Pricing Reports (דוחות תמחור)

| Field | Value |
|-------|-------|
| **User role** | Accountant / Admin / Area Manager |
| **Route** | `/reports/pricing` |
| **Purpose** | Financial reporting dashboard showing cost breakdown by project, supplier, or equipment type. Supports date filtering and export. |
| **What the user does** | 1. Switches between report views (by project / by supplier / by equipment type). 2. Filters by date range and worklog status. 3. Expands project rows to see individual worklog details. 4. Exports to CSV, PDF, or Excel. |
| **Key elements** | Report type tabs (3), date range filters, status filter, summary cards (total reports, hours, cost before VAT, cost with VAT), expandable data table, export buttons (CSV/PDF/Excel), unverified rate warning banner |

---

## Screen 12 — Supplier Portal (פורטל ספק)

| Field | Value |
|-------|-------|
| **User role** | External Supplier (no login required) |
| **Route** | `/supplier-portal/:token` |
| **Purpose** | External landing page where suppliers view work order details and accept or reject assignments. Accessed via unique time-limited link (3 hours). |
| **What the user does** | 1. Opens link received by email/SMS. 2. Views order details (equipment type, dates, location, rate). 3. Selects available equipment and enters license plate. 4. Accepts the order (with equipment selection) or rejects with reason. 5. Views Waze/Google Maps navigation to work site. |
| **Key elements** | Order details card, equipment selection dropdown, license plate input, accept button (green), reject button (red) with reason field, countdown timer (3 hours), Waze/Google Maps links, no authentication required |

---

## Screen 13 — User Management (ניהול משתמשים)

| Field | Value |
|-------|-------|
| **User role** | Admin |
| **Route** | `/settings/admin/users` |
| **Purpose** | Create, edit, and manage system users. Assign roles, regions, and areas. |
| **What the user does** | 1. Views user list with role and status. 2. Creates new user (name, email, phone, role, region, area). 3. Edits user details and role assignments. 4. Activates/deactivates users. |
| **Key elements** | User cards/list, search, "New User" button, role assignment dropdown, region/area assignment, active/inactive toggle |

---

## Screen 14 — Roles & Permissions (תפקידים והרשאות)

| Field | Value |
|-------|-------|
| **User role** | Admin |
| **Route** | `/settings/admin/roles` |
| **Purpose** | Define system roles and assign granular permissions per role. Each permission controls access to specific features. |
| **What the user does** | 1. Views roles table (code, name, permissions count, user count). 2. Creates/edits a role with name and description. 3. Toggles individual permissions per role (grouped by category). 4. Deletes unused roles. |
| **Key elements** | Roles tab / Permissions tab, roles table (code, name, description, permissions count, user count, status), permission categories (projects, work orders, worklogs, suppliers, users, reports, settings), checkbox toggles per permission |

---

## Screen 15 — System Settings (הגדרות מערכת)

| Field | Value |
|-------|-------|
| **User role** | Admin |
| **Route** | `/settings` |
| **Purpose** | Central settings hub with categorized navigation to all administrative functions. Shows live counts (users, suppliers, equipment, etc.). |
| **What the user does** | 1. Expands setting categories (Users, Suppliers, Budgets, Organization, Reports). 2. Clicks specific setting to navigate (e.g., "Manage Users" → `/settings/admin/users`). 3. Views live count badges showing current totals. |
| **Key elements** | Expandable category cards (Users & Permissions, Suppliers & Equipment, Budgets & Finance, Organization, Reports), child navigation items with live count badges, icons per category |

---
---

*Forewise v2.0.0 — Final Project Appendices | Generated 22.03.2026*
*Author: nirab96Developer | Stack: FastAPI + React + PostgreSQL + Leaflet*
