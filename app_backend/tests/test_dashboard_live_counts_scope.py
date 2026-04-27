"""
Phase 3 Wave 2.2.f — scope on /dashboard/live-counts.

Closes leak D3 from PHASE3_WAVE22_RECON.md (LOW severity but the
last gap in the dashboard surface). Before this commit, all 17+
counts were global — AREA_MGR saw "system has 315 users".

Three categories, three behaviors:

  ADMIN-ONLY (system-wide aggregates):
    users_active, users_total, roles, permissions,
    regions, areas, locations, rates, tickets_open
    → returned to ADMIN/SUPER_ADMIN/ACCOUNTANT/COORDINATOR;
      0 for scoped roles. Response keys preserved.

  PER-PROJECT (project-scoped):
    projects_active, equipment_total, equipment_in_use,
    suppliers_active, budgets_total, budgets_overrun,
    wo_pending, wo_in_progress, wo_no_status,
    invoices_total, invoices_pending, invoices_paid
    → narrowed by project_id IN scoped_project_ids.

  USER-SCOPED:
    notifications_unread → already user_id-filtered; unchanged.

Approach for tests
------------------
A query-spy stub that returns a configured count for every
.scalar() call AND records which models had a per-project filter
applied. Lets us assert:
  - For admin: counts surface (the spy returns the seeded counts).
  - For scoped roles: ADMIN-only counts are 0; per-project counts
    have the IN-allowed filter applied.
"""
import asyncio
from unittest.mock import MagicMock

import pytest


from app.routers.dashboard import get_live_counts


def _user(role_code, *, perms=None, user_id=1, region_id=None, area_id=None):
    user = MagicMock()
    user.id = user_id
    user.role_id = 1
    user.is_active = True
    user.region_id = region_id
    user.area_id = area_id
    user.role = MagicMock()
    user.role.code = role_code
    user.role.permissions = [MagicMock(code=p) for p in (perms or set())]
    user._permissions = set(perms or set())
    return user


# ---------------------------------------------------------------------------
# Stub
# ---------------------------------------------------------------------------

def _model_name(arg):
    name = getattr(arg, "__name__", None)
    if not name:
        cls = getattr(arg, "class_", None)
        name = getattr(cls, "__name__", None)
    return name or "Unknown"


# When we get a func.count(Model.id) expression, the inner Column's
# .class_ is None (it's been converted to a plain Column ref). Map
# from table name back to model name.
_TABLE_TO_MODEL = {
    "users": "User", "roles": "Role", "permissions": "Permission",
    "regions": "Region", "areas": "Area", "locations": "Location",
    "suppliers": "Supplier", "equipment": "Equipment",
    "projects": "Project", "budgets": "Budget",
    "work_orders": "WorkOrder", "support_tickets": "SupportTicket",
    "project_assignments": "ProjectAssignment",
    "notifications": "Notification",
}


class _CountChain:
    """Per-query chain — records every filter clause and returns
    the configured count on .scalar()."""

    def __init__(self, parent, model_name):
        self._parent = parent
        self._model = model_name

    def __iter__(self):
        return iter([])

    def filter(self, *clauses, **kw):
        for c in clauses:
            try:
                left = getattr(c, "left", None)
                if left is not None:
                    table = getattr(getattr(left, "table", None), "name", None)
                    column = getattr(left, "name", None)
                    if table and column:
                        self._parent.filter_columns.append(f"{table}.{column}")
            except Exception:
                pass
        return self

    def distinct(self):
        return self

    def scalar(self):
        return self._parent._counts.get(self._model, 0)

    def all(self):
        return self._parent._results_for(self._model)


class _CountDBStub:
    """Tracks which models had counts queried. The ADMIN flow runs
    db.query(func.count(Model.id)) for each — we recognize Model
    via its __name__.

    Per-project flow adds .filter(Model.project_id IN allowed). The
    spy records every filter clause's column name."""

    def __init__(self, *, counts=None, project_ids=None, assignments=None):
        # Map model __name__ → count to return for that model
        self._counts = counts or {}
        self._projects = [(pid,) for pid in (project_ids or [])]
        self._assignments = assignments or []
        self.filter_columns: list[str] = []
        self.execute_calls: list[str] = []

    def query(self, *args):
        """Recognize:
          - db.query(func.count(Model.id))   → Function with .clauses
                                                 (column's class_ is None
                                                 here — use .table.name
                                                 + _TABLE_TO_MODEL)
          - db.query(Project.id) etc.        → InstrumentedAttribute
          - db.query(Model)                  → class
        """
        first = args[0] if args else None
        # SQLAlchemy func.count(X.id) — find the column inside ClauseList
        clauses = getattr(first, "clauses", None)
        if clauses is not None:
            try:
                for inner in clauses:
                    table_name = getattr(
                        getattr(inner, "table", None), "name", None
                    )
                    if table_name and table_name in _TABLE_TO_MODEL:
                        return _CountChain(self, _TABLE_TO_MODEL[table_name])
                    cls = getattr(inner, "class_", None)
                    name = getattr(cls, "__name__", None)
                    if name:
                        return _CountChain(self, name)
            except Exception:
                pass
        return _CountChain(self, _model_name(first))

    def execute(self, sql, params=None):
        """Match raw SQL queries by content. Used for:
          - notifications_unread  (always returns 0 here)
          - rates                 (admin-only)
          - invoices_*            (per-scope)
        """
        sql_str = str(sql).lower()
        self.execute_calls.append(sql_str)
        cursor = MagicMock()
        # Return small fixed numbers per query type
        if "notifications" in sql_str:
            cursor.scalar.return_value = 0
        elif "system_rates" in sql_str:
            cursor.scalar.return_value = 7  # admin sees rates
        elif "invoices" in sql_str:
            cursor.scalar.return_value = 3
        else:
            cursor.scalar.return_value = 0
        return cursor

    def _results_for(self, model_name):
        if model_name == "Project":
            return self._projects
        if model_name == "ProjectAssignment":
            return self._assignments
        return []


def _stub(*, project_ids=None, assignments=None):
    """Default count stub — every model returns its position-based
    count so we can distinguish them in assertions."""
    return _CountDBStub(
        counts={
            "User": 100, "Role": 5, "Permission": 50,
            "Region": 3, "Area": 12, "Location": 50,
            "Supplier": 45, "Equipment": 80,
            "Project": 25, "Budget": 18, "WorkOrder": 30,
            "SupportTicket": 4,
        },
        project_ids=project_ids or [],
        assignments=assignments or [],
    )


# ===========================================================================
# Admin / global roles — all counts present
# ===========================================================================

class TestLiveCountsGlobalRoles:

    def _call(self, user, db=None):
        return asyncio.run(get_live_counts(
            db=db or _stub(), current_user=user,
        ))

    def test_admin_sees_all_counts(self):
        result = self._call(_user("ADMIN"))
        # Admin-only counts should be non-zero (the stub returns 100)
        assert result["users_total"] == 100
        assert result["users_active"] == 100
        assert result["regions"] == 3
        assert result["areas"] == 12
        assert result["locations"] == 50
        assert result["roles"] == 5
        assert result["permissions"] == 50
        assert result["tickets_open"] == 4
        assert result["rates"] == 7
        # Per-project counts also present
        assert result["projects_active"] == 25
        assert result["equipment_total"] == 80

    def test_super_admin_sees_all_counts(self):
        result = self._call(_user("SUPER_ADMIN"))
        assert result["users_total"] == 100
        assert result["regions"] == 3

    def test_accountant_sees_all_counts(self):
        result = self._call(_user("ACCOUNTANT"))
        assert result["users_total"] == 100
        assert result["regions"] == 3
        assert result["projects_active"] == 25

    def test_coordinator_sees_all_counts(self):
        result = self._call(_user("ORDER_COORDINATOR"))
        assert result["users_total"] == 100


# ===========================================================================
# Scoped roles — admin-only counts blanked, per-project filtered
# ===========================================================================

class TestLiveCountsScopedRoles:
    """For REGION/AREA/WORK manager:
      - admin-only counts MUST be 0 (no system info leakage)
      - per-project counts MUST be filtered by project_id IN allowed
      - response shape (keys) MUST stay identical
    """

    def _call(self, user, db):
        return asyncio.run(get_live_counts(db=db, current_user=user))

    def test_region_manager_admin_counts_blanked(self):
        db = _stub(project_ids=[10, 11])
        result = self._call(
            _user("REGION_MANAGER", region_id=5), db,
        )
        # ADMIN-ONLY counts are zero for scoped roles
        assert result["users_total"] == 0
        assert result["users_active"] == 0
        assert result["regions"] == 0
        assert result["areas"] == 0
        assert result["locations"] == 0
        assert result["roles"] == 0
        assert result["permissions"] == 0
        assert result["tickets_open"] == 0
        assert result["rates"] == 0

    def test_region_manager_per_project_filter_applied(self):
        db = _stub(project_ids=[10, 11])
        self._call(_user("REGION_MANAGER", region_id=5), db)
        # Per-project counts must add a project_id IN filter
        # (we can see it in the spy's filter_columns)
        cols = db.filter_columns
        assert any("projects.id" in c for c in cols), \
            f"Expected projects.id filter; got {cols}"
        assert any("equipment.assigned_project_id" in c for c in cols), \
            f"Expected equipment.assigned_project_id filter; got {cols}"
        assert any("budgets.project_id" in c for c in cols), \
            f"Expected budgets.project_id filter; got {cols}"
        assert any("work_orders.project_id" in c for c in cols), \
            f"Expected work_orders.project_id filter; got {cols}"

    def test_area_manager_admin_counts_blanked(self):
        db = _stub(project_ids=[20, 21])
        result = self._call(
            _user("AREA_MANAGER", area_id=12), db,
        )
        assert result["users_total"] == 0
        assert result["regions"] == 0

    def test_work_manager_with_assignments_sees_scoped_counts(self):
        assigns = [
            MagicMock(user_id=7, project_id=30, is_active=True),
        ]
        db = _stub(assignments=assigns)
        result = self._call(
            _user("WORK_MANAGER", user_id=7), db,
        )
        # Admin-only: 0
        assert result["users_total"] == 0
        # Per-project: filter applied → counts come from stub
        assert any(
            "work_orders.project_id" in c for c in db.filter_columns
        )

    def test_work_manager_no_assignments_zeros_per_project(self):
        """Empty scope (no assignments) → all per-project counts = 0
        and no IN filter applied (fast path)."""
        db = _stub(assignments=[])
        result = self._call(
            _user("WORK_MANAGER", user_id=7), db,
        )
        assert result["projects_active"] == 0
        assert result["equipment_total"] == 0
        assert result["budgets_total"] == 0
        assert result["wo_pending"] == 0
        assert result["users_total"] == 0  # admin-only → 0


# ===========================================================================
# Response shape — keys preserved across all roles
# ===========================================================================

class TestLiveCountsResponseShape:
    """Frontend-stability check: every role MUST receive every key,
    even if some are 0. Keys must NOT be added or removed across
    roles."""

    EXPECTED_KEYS = {
        # admin-only
        "users_active", "users_total", "roles", "permissions",
        "regions", "areas", "locations", "rates", "tickets_open",
        # per-project
        "projects_active", "equipment_total", "equipment_in_use",
        "suppliers_active", "budgets_total", "budgets_overrun",
        "wo_pending", "wo_in_progress", "wo_no_status",
        "invoices_total", "invoices_pending", "invoices_paid",
        # user-scoped
        "notifications_unread",
    }

    @pytest.mark.parametrize("role", [
        "ADMIN", "SUPER_ADMIN", "ACCOUNTANT", "ORDER_COORDINATOR",
        "REGION_MANAGER", "AREA_MANAGER", "WORK_MANAGER",
    ])
    def test_all_keys_present_for_each_role(self, role):
        db = _stub(project_ids=[10], assignments=[
            MagicMock(user_id=1, project_id=10, is_active=True),
        ])
        kwargs = {}
        if role == "REGION_MANAGER":
            kwargs["region_id"] = 5
        elif role == "AREA_MANAGER":
            kwargs["area_id"] = 12
        result = asyncio.run(get_live_counts(
            db=db, current_user=_user(role, **kwargs),
        ))
        missing = self.EXPECTED_KEYS - set(result.keys())
        extra = set(result.keys()) - self.EXPECTED_KEYS
        assert not missing, f"Missing keys for {role}: {missing}"
        assert not extra, f"Unexpected keys for {role}: {extra}"


# ===========================================================================
# Suppliers active — special case (computed via WorkOrder JOIN)
# ===========================================================================

class TestSuppliersActiveCount:

    def test_admin_global_count(self):
        db = _stub()
        result = asyncio.run(get_live_counts(
            db=db, current_user=_user("ADMIN"),
        ))
        # Admin path: simple Supplier.is_active count → 45
        assert result["suppliers_active"] == 45

    def test_region_manager_filtered_via_workorder_subquery(self):
        db = _stub(project_ids=[10])
        asyncio.run(get_live_counts(
            db=db, current_user=_user("REGION_MANAGER", region_id=5),
        ))
        # Filter chain should include suppliers.id (the IN-subquery)
        cols = db.filter_columns
        assert any("suppliers.id" in c for c in cols), \
            f"Expected suppliers.id IN filter; got {cols}"
