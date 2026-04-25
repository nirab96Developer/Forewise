# Phase 3 — Wave 3.1 — Policy Engine — Discovery & Proposal

**תאריך**: 2026-04-26
**סטטוס**: discovery + proposal בלבד. **אפס שינויי קוד.** ממתין לאישור.

---

## 1. Discovery — איפה מאכפים היום הרשאות/scope/ownership

### 1.A — Custom auth helpers (8 דפוסים שונים)

| מקור | שם הפונקציה | מה בודק |
|---|---|---|
| `routers/admin.py:21` | `verify_admin(current_user)` | role.code == "ADMIN", זורק 403 |
| `routers/budgets.py:23` | `_check_budget_scope(db, user, budget)` | RBAC + region/area/project + DB query (project_assignments) |
| `routers/notifications.py:14` | `_check_notification_ownership(user, n)` | ADMIN bypass + user_id ownership |
| `routers/supplier_rotations.py:34` | `_check_rotation_scope(user, rotation)` | RBAC + region/area; NULL row hidden |
| `routers/work_orders.py:85` | `_require_order_coordinator_or_admin(user)` | role check |
| `routers/dashboard.py:18` | `_dashboard_view(user)` (Depends helper) | require_permission gate |

**8 helpers, 6 חתימות שונות**, אף אחד לא מחזיר תוצאה אחידה.

### 1.B — Inline `current_user.role.code` checks (24 מקומות)

7 קבצים: `admin.py`, `admin_projects.py`, `auth.py`, `dashboard.py`, `notifications.py`, `project_assignments.py`, `support_tickets.py`. כל אחד עם פטרן שונה (`==`, `!=`, `in (...)`, `not in (...)`).

### 1.C — Scope filtering ב-WHERE (47 שימושים ב-7 קבצים)

`current_user.region_id` / `current_user.area_id` משולבים ישירות ב-SQL queries (filter, group_by) ב:
`budgets.py`, `worklogs.py`, `projects.py`, `dashboard.py`, `activity_logs.py`, `invoices.py`, `work_orders.py`.

### 1.D — Status-based blocking בservice layer (10+ מקומות)

לדוגמה:
```python
if work_order.status not in allowed: raise ...
if equipment.status not in ('available', 'in_use'): raise ...
if db_release.status != "pending": raise ...
```
פזורים ב-`equipment_maintenance_service`, `equipment_service`, `balance_release_service`, `milestone_service`, `work_order_service`.

### 1.E — Ownership checks בDB query (פרויקט שמוקצה)

`ProjectAssignment.user_id == current_user.id` ב-`projects.py:115` ו-`dashboard.py:445`. גם `_check_budget_scope` עושה את אותה queryב-DB.

### בעיות מצטברות

1. **6 helpers שונים** עם חתימות לא אחידות — כל קובץ מחדש את הגלגל.
2. **24 inline checks** של `role.code` — קל לשכוח אחד או לטעות בpatten.
3. **47 scope filters** ב-WHERE — אין שום מקום מרכזי שאומר "לAREA_MANAGER מותר רק area שלו".
4. **10+ status rules** מעורבים בלוגיקה עסקית — אין הפרדה.
5. **2 מקומות שכופלים** את אותה ProjectAssignment query.

---

## 2. מבנה מוצע ל-`AuthorizationService`

### חתימה מרכזית

```python
# app/core/authorization/service.py

from typing import Optional, Any
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.exceptions import ForbiddenException

class AuthorizationService:
    """Single entry point for every permission/scope/ownership/status check.

    Replaces the 8 ad-hoc helpers + 24 inline role checks + 47 inline
    scope filters + 10 status guards scattered across the routers.

    Three-layer model (only the layers you opt into run):
      RBAC   — does the user hold the named permission?
      ABAC   — is the resource within the user's scope/ownership?
      State  — is the resource in a status that allows this action?
    """

    def __init__(self, db: Session):
        self.db = db

    def authorize(
        self,
        user: User,
        action: str,                  # "budgets.read", "work_orders.approve", ...
        resource: Optional[Any] = None,  # SQLAlchemy instance (Budget, WorkOrder, ...)
        context: Optional[dict] = None,  # extra hints (allowed_statuses, target_user_id, ...)
    ) -> None:
        """Raises ForbiddenException if any layer denies. Returns None on pass."""
        ...

    def filter_query(
        self,
        user: User,
        query,                         # SQLAlchemy Query
        resource_type: str,            # "Budget", "WorkOrder", ...
    ):
        """Apply RBAC + scope as WHERE clauses. Returns the narrowed query.
        Replaces the 47 inline `if role: query.filter(...)` blocks."""
        ...
```

### Internal layers

```
authorize()
  ├─ _check_rbac(user, action)
  │     existing require_permission() under the hood
  ├─ _check_scope(user, resource)
  │     dispatches per resource_type:
  │       Budget          → region/area/project (current Wave 5 logic)
  │       WorkOrder       → region/area + assigned_projects
  │       SupplierRotation → region/area (current Wave 7.D logic)
  │       Notification    → user_id ownership
  │       Worklog         → user_id ownership + project scope
  │       Invoice         → area/region scope
  │       SupportTicket   → user_id ownership
  ├─ _check_status(resource, action, context.allowed_statuses)
  │     consolidated state-machine guard
  └─ no return; raises ForbiddenException with structured detail
```

### Scope strategy table (single source of truth)

| Resource | Admin | REGION_MANAGER | AREA_MANAGER | WORK_MANAGER | ACCOUNTANT | COORDINATOR | SUPPLIER |
|---|---|---|---|---|---|---|---|
| Budget | all | region_id match | area_id match | assigned project | area∨region | global | denied |
| WorkOrder | all | region | area | assigned project | global | global | own only |
| SupplierRotation | all | region | area | denied | denied | global | denied |
| Notification | all | own | own | own | own | own | own |
| Worklog | all | region | area | assigned project | global | global | own |
| Invoice | all | region | area | denied | global | denied | own |
| SupportTicket | all | own | own | own | own | own | own |

---

## 3. דוגמה על domain אחד — `budgets`

### לפני (הקוד הנוכחי, שורות 23–86 ב-`budgets.py`)

```python
def _check_budget_scope(db, user, budget):
    if user.role.code in ("ADMIN", "SUPER_ADMIN"): return
    if user.role.code == "REGION_MANAGER":
        if not user.region_id or budget.region_id != user.region_id:
            raise HTTPException(403, "אין הרשאה לתקציב זה")
        return
    # ...50 lines of role-by-role logic...

@router.get("/{budget_id}/detail")
def get_budget_detail(...):
    require_permission(current_user, "budgets.read")     # RBAC
    budget = db.query(Budget).filter(...).first()
    if not budget: raise 404
    _check_budget_scope(db, current_user, budget)        # ABAC
    ...
```

### אחרי (Wave 3.1)

```python
@router.get("/{budget_id}/detail")
def get_budget_detail(...):
    budget = db.query(Budget).filter(...).first()
    if not budget: raise 404
    authz.authorize(current_user, "budgets.read", resource=budget)
    # one call replaces both require_permission + _check_budget_scope
    ...

@router.get("")
def list_budgets(...):
    query = db.query(Budget)
    query = authz.filter_query(current_user, query, "Budget")
    # one call replaces inline `if role == "REGION_MANAGER": query.filter(...)`
    ...
```

`_check_budget_scope` נמחק. הלוגיקה הוזזה ל-`AuthorizationService._check_scope_budget`.

### למה דווקא budgets ראשון?
1. כבר יש לו את ה-helper הכי שלם (`_check_budget_scope` עם כל 6 התפקידים).
2. tests מקיפים מ-Wave 5 (27 cases) — מהווים safety net לrefactor.
3. Domain מבודד יחסית — אם נשבר, לא קורס שאר המערכת.

---

## 4. סיכונים

### גבוה
- **ביצועים** — כל endpoint יקבל קריאה נוספת ל-DB מ-`_check_scope` עבור WORK_MANAGER (lookup ב-`project_assignments`). פתרון: cache ל-request scope, או JOIN בquery.
- **403 לא תואם לbug חבוי** — אם ה-scope policy החדש הדוק יותר (או רופף יותר) מהקיים, frontend יראה behavior אחר. **mitigation**: מקדישים test מקיף שמוודא identity לWave 5 התנהגות לפני שמרחיבים.

### בינוני
- **שינוי signature ב-helpers** — אם מוחקים `_check_budget_scope` בלי לבדוק שאין caller אחר, נשבר.
- **DI complexity** — `AuthorizationService(db)` דורש `Depends(get_db)` בכל handler.

### נמוך
- **Logging extra noise** — כל call ל-authorize יכול ליצור שורה ב-audit log. צריך rate limiting.

---

## 5. איך נבדוק

### 5.A — לפני refactor: snapshot tests
1. לרשום את כל ה-403/200 הקיימים על budgets endpoints (להריץ pytest, לשמור).
2. אחרי refactor: לוודא שאותם 27 tests של Wave 5 עוברים זהה.

### 5.B — Behavior-identity tests
לכל role × budget combination בWave 5:
- **לפני**: תוצאת `_check_budget_scope(user, budget)` (raise/None).
- **אחרי**: תוצאת `authz.authorize(user, "budgets.read", budget)` (raise/None).
- חייבים להיות זהים.

### 5.C — Performance tests
- baseline: זמן ממוצע של 100 קריאות ל-`/budgets/{id}/detail` עם WORK_MANAGER.
- אחרי refactor: ≤110% מהbaseline (10% רגרסיה מותרת לתוספת DB query).

### 5.D — Integration tests
לרוץ את ה-CI subset המלא (370 tests) — חייב לעבור ירוק.

---

## 6. סדר ביצוע מוצע (אם תאשר)

1. **Discovery commit** (קובץ זה) — תיעוד בלבד.
2. **Skeleton** — `app/core/authorization/{__init__.py, service.py, scope_strategies.py}` עם interface ו-NotImplementedError. אפס שינוי בrouters.
3. **Budget strategy** — מימוש `_check_scope_budget` + `_filter_query_budget` שמשכפלים מ-`_check_budget_scope`. tests מאמתים identity.
4. **Refactor budgets.py** — להחליף `require_permission + _check_budget_scope` ב-`authz.authorize`. tests עוברים. למחוק `_check_budget_scope`.
5. **Smoke + commit + CI ירוק**.
6. רק אז להרחיב לdomain הבא (work_orders / supplier_rotations).

---

## 7. מה לא נעשה ב-Wave 3.1

- ❌ לא נכתוב את ה-AuthorizationService לכל ה-domains. רק budgets.
- ❌ לא נמחק את 7 ה-helpers האחרים (`verify_admin`, `_check_notification_ownership`, וכו'). הם נשארים עד שWave 3.1.X (X=2,3,4...) יחליף כל אחד בנפרד.
- ❌ לא נשנה את `require_permission` עצמו — נעטוף, לא נחליף.
- ❌ לא נוסיף ABAC ל-status rules בservice layer (זה Wave נפרד).

---

## ממתין להחלטה

מאשר? יש שינויים לproposal לפני שמתחילים?
