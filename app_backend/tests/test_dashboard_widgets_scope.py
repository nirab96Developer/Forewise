"""
Phase 3 Wave 2.2.d — scope enforcement on dashboard widget
endpoints that previously returned global lists:

  GET /dashboard/equipment/active
  GET /dashboard/suppliers/active

Closes leak D4 from PHASE3_WAVE22_RECON.md.

Approach
--------
Both endpoints share a helper, `_dashboard_scoped_project_ids`,
which returns:
  - None       → global scope (admin / accountant / coordinator)
  - empty set  → no scope (defense for unknown / blocked roles)
  - set of ids → scope to those project ids

Tests cover the helper directly (mapping each role to the right
scope) plus the endpoint integration (right query shape + response).
"""
import asyncio
from unittest.mock import MagicMock

import pytest

from app.routers.dashboard import (
    _dashboard_scoped_project_ids,
    get_dashboard_active_equipment,
    get_dashboard_active_suppliers,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user(role_code, *, perms=None, user_id=1, region_id=None, area_id=None):
    user = MagicMock()
    user.id = user_id
    user.role_id = 1
    user.is_active = True
    user.region_id = region_id
    user.area_id = area_id
    user.full_name = f"User {user_id}"
    user.username = f"user_{user_id}"
    user.role = MagicMock()
    user.role.code = role_code
    user.role.permissions = [MagicMock(code=p) for p in (perms or set())]
    user._permissions = set(perms or set())
    return user


def _model_name(arg) -> str:
    """Resolve the SQLAlchemy entity referenced by a query argument
    (model class or InstrumentedAttribute) to its model name."""
    name = getattr(arg, "__name__", None)
    if not name:
        cls = getattr(arg, "class_", None)
        name = getattr(cls, "__name__", None)
    return name or "Unknown"


class _Chain:
    """Per-query chain object — preserves its own model identity so
    nested `db.query(...)` calls (e.g. inside a helper) don't pollute
    the parent chain's state.

    Iterability: SQLAlchemy's `Column.in_(subquery)` requires the
    argument to be either a SELECT-like construct or an iterable.
    We make _Chain iterable (yielding nothing) so the suppliers
    endpoint's `Supplier.id.in_(active_supplier_ids)` is accepted
    by SQLAlchemy and produces a normal BinaryExpression that the
    spy can capture."""

    def __init__(self, parent, model_name):
        self._parent = parent
        self._model = model_name

    def __iter__(self):
        return iter([])

    def filter(self, *clauses, **kwargs):
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

    def limit(self, *a, **kw):
        return self

    def all(self):
        return self._parent._results_for(self._model)


class _ScopeDBStub:
    """Stub used by _dashboard_scoped_project_ids tests."""

    def __init__(self, *, project_ids=None, assignments=None):
        self._projects = [(pid,) for pid in (project_ids or [])]
        self._assignments = assignments or []
        self.filter_columns: list[str] = []

    def query(self, *args):
        return _Chain(self, _model_name(args[0]) if args else "Unknown")

    def _results_for(self, model_name):
        if model_name == "Project":
            return self._projects
        if model_name == "ProjectAssignment":
            return self._assignments
        return []


# ===========================================================================
# Helper: _dashboard_scoped_project_ids
# ===========================================================================

class TestScopedProjectIdsHelper:

    def test_admin_global(self):
        assert _dashboard_scoped_project_ids(_ScopeDBStub(), _user("ADMIN")) is None

    def test_super_admin_global(self):
        assert _dashboard_scoped_project_ids(_ScopeDBStub(), _user("SUPER_ADMIN")) is None

    def test_accountant_global(self):
        assert _dashboard_scoped_project_ids(_ScopeDBStub(), _user("ACCOUNTANT")) is None

    def test_coordinator_global(self):
        assert _dashboard_scoped_project_ids(_ScopeDBStub(), _user("ORDER_COORDINATOR")) is None

    def test_region_manager_returns_region_projects(self):
        db = _ScopeDBStub(project_ids=[10, 11, 12])
        result = _dashboard_scoped_project_ids(
            db, _user("REGION_MANAGER", region_id=5),
        )
        assert result == {10, 11, 12}

    def test_region_manager_without_region_id_empty(self):
        db = _ScopeDBStub(project_ids=[10, 11])
        result = _dashboard_scoped_project_ids(
            db, _user("REGION_MANAGER", region_id=None),
        )
        assert result == set()

    def test_area_manager_returns_area_projects(self):
        db = _ScopeDBStub(project_ids=[20, 21])
        result = _dashboard_scoped_project_ids(
            db, _user("AREA_MANAGER", area_id=12),
        )
        assert result == {20, 21}

    def test_work_manager_returns_assigned_projects(self):
        assigns = [
            MagicMock(user_id=7, project_id=30, is_active=True),
            MagicMock(user_id=7, project_id=31, is_active=True),
        ]
        db = _ScopeDBStub(assignments=assigns)
        result = _dashboard_scoped_project_ids(
            db, _user("WORK_MANAGER", user_id=7),
        )
        assert result == {30, 31}

    def test_work_manager_without_assignments_empty(self):
        db = _ScopeDBStub(assignments=[])
        result = _dashboard_scoped_project_ids(
            db, _user("WORK_MANAGER", user_id=7),
        )
        assert result == set()

    def test_supplier_empty(self):
        """Defensive — SUPPLIER is 403'd at dashboard.view in
        production, but if they ever reached here, scope is empty."""
        result = _dashboard_scoped_project_ids(
            _ScopeDBStub(), _user("SUPPLIER"),
        )
        assert result == set()

    def test_field_worker_empty(self):
        result = _dashboard_scoped_project_ids(
            _ScopeDBStub(), _user("FIELD_WORKER"),
        )
        assert result == set()

    def test_unknown_role_empty(self):
        result = _dashboard_scoped_project_ids(
            _ScopeDBStub(), _user("MYSTERY"),
        )
        assert result == set()


# ===========================================================================
# Endpoint: /dashboard/equipment/active
# ===========================================================================

def _equipment(*, eq_id=1, name="Tractor", code="TR-1",
               status="in_use", supplier_id=10,
               assigned_project_id=10):
    e = MagicMock()
    e.id = eq_id
    e.name = name
    e.code = code
    e.status = status
    e.supplier_id = supplier_id
    e.assigned_project_id = assigned_project_id
    return e


class _EquipmentDBStub:
    """Stub that:
      - records every .filter(...) clause for assertion
      - hands back a fixed equipment list on Equipment queries
      - returns the seeded project ids when the helper queries Project.id
      - returns the seeded assignments for ProjectAssignment.

    Uses _Chain so each db.query() gets its own state — prevents
    nested queries from poisoning the outer chain's model identity.
    """

    def __init__(self, *, equipment_list=None,
                 project_ids=None, assignments=None):
        self._equipment = equipment_list or []
        self._projects = [(pid,) for pid in (project_ids or [])]
        self._assignments = assignments or []
        self.filter_columns: list[str] = []

    def query(self, *args):
        return _Chain(self, _model_name(args[0]) if args else "Unknown")

    def _results_for(self, model_name):
        if model_name == "Equipment":
            return self._equipment
        if model_name == "Project":
            return self._projects
        if model_name == "ProjectAssignment":
            return self._assignments
        return []


class TestEquipmentActiveScope:

    def test_admin_no_scope_filter(self):
        eq = [_equipment(eq_id=1), _equipment(eq_id=2)]
        db = _EquipmentDBStub(equipment_list=eq)
        result = asyncio.run(get_dashboard_active_equipment(
            db=db, current_user=_user("ADMIN"), limit=20,
        ))
        assert len(result) == 2
        # No assigned_project_id filter applied for admin
        assert not any(
            "equipment.assigned_project_id" in c for c in db.filter_columns
        )

    def test_accountant_no_scope_filter(self):
        eq = [_equipment(eq_id=1)]
        db = _EquipmentDBStub(equipment_list=eq)
        asyncio.run(get_dashboard_active_equipment(
            db=db,
            current_user=_user("ACCOUNTANT", perms={"dashboard.view"}),
            limit=20,
        ))
        assert not any(
            "equipment.assigned_project_id" in c for c in db.filter_columns
        )

    def test_region_manager_filter_applied(self):
        eq = [_equipment(assigned_project_id=10)]
        db = _EquipmentDBStub(equipment_list=eq, project_ids=[10, 11])
        asyncio.run(get_dashboard_active_equipment(
            db=db,
            current_user=_user("REGION_MANAGER",
                               perms={"dashboard.view"}, region_id=5),
            limit=20,
        ))
        assert any(
            "equipment.assigned_project_id" in c for c in db.filter_columns
        ), f"Expected assigned_project_id filter; got {db.filter_columns}"

    def test_area_manager_filter_applied(self):
        eq = [_equipment(assigned_project_id=20)]
        db = _EquipmentDBStub(equipment_list=eq, project_ids=[20])
        asyncio.run(get_dashboard_active_equipment(
            db=db,
            current_user=_user("AREA_MANAGER",
                               perms={"dashboard.view"}, area_id=12),
            limit=20,
        ))
        assert any(
            "equipment.assigned_project_id" in c for c in db.filter_columns
        )

    def test_work_manager_assigned_filter_applied(self):
        eq = [_equipment(assigned_project_id=30)]
        assigns = [MagicMock(user_id=7, project_id=30, is_active=True)]
        db = _EquipmentDBStub(equipment_list=eq, assignments=assigns)
        asyncio.run(get_dashboard_active_equipment(
            db=db,
            current_user=_user("WORK_MANAGER",
                               perms={"dashboard.view"}, user_id=7),
            limit=20,
        ))
        assert any(
            "equipment.assigned_project_id" in c for c in db.filter_columns
        )

    def test_work_manager_no_assignments_returns_empty(self):
        """Closes the corner case — WORK_MGR with no assignments
        gets an empty list, not the global fleet."""
        db = _EquipmentDBStub(equipment_list=[_equipment()], assignments=[])
        result = asyncio.run(get_dashboard_active_equipment(
            db=db,
            current_user=_user("WORK_MANAGER",
                               perms={"dashboard.view"}, user_id=7),
            limit=20,
        ))
        assert result == []

    def test_supplier_returns_empty(self):
        db = _EquipmentDBStub(equipment_list=[_equipment()])
        result = asyncio.run(get_dashboard_active_equipment(
            db=db,
            current_user=_user("SUPPLIER", perms={"dashboard.view"}),
            limit=20,
        ))
        assert result == []


# ===========================================================================
# Endpoint: /dashboard/suppliers/active
# ===========================================================================

def _supplier(*, sid=1, name="Acme", contact_name="Joe", phone="1111", is_active=True):
    s = MagicMock()
    s.id = sid
    s.name = name
    s.contact_name = contact_name
    s.phone = phone
    s.is_active = is_active
    return s


class _SupplierDBStub:
    """Same shape as _EquipmentDBStub but for suppliers + WorkOrder
    subquery. Uses _Chain like the equipment stub."""

    def __init__(self, *, supplier_list=None,
                 project_ids=None, assignments=None):
        self._suppliers = supplier_list or []
        self._projects = [(pid,) for pid in (project_ids or [])]
        self._assignments = assignments or []
        self.filter_columns: list[str] = []

    def query(self, *args):
        return _Chain(self, _model_name(args[0]) if args else "Unknown")

    def _results_for(self, model_name):
        if model_name == "Supplier":
            return self._suppliers
        if model_name == "Project":
            return self._projects
        if model_name == "ProjectAssignment":
            return self._assignments
        # WorkOrder subquery → empty (filter chain is what we test)
        return []


class TestSuppliersActiveScope:

    def test_admin_no_scope_filter(self):
        sup = [_supplier(sid=1), _supplier(sid=2)]
        db = _SupplierDBStub(supplier_list=sup)
        result = asyncio.run(get_dashboard_active_suppliers(
            db=db, current_user=_user("ADMIN"), limit=20,
        ))
        assert len(result) == 2
        # No supplier-id-in-subquery filter applied for admin
        assert not any("suppliers.id" in c for c in db.filter_columns)

    def test_accountant_no_scope_filter(self):
        sup = [_supplier(sid=1)]
        db = _SupplierDBStub(supplier_list=sup)
        asyncio.run(get_dashboard_active_suppliers(
            db=db,
            current_user=_user("ACCOUNTANT", perms={"dashboard.view"}),
            limit=20,
        ))
        assert not any("suppliers.id" in c for c in db.filter_columns)

    def test_region_manager_filter_applied(self):
        sup = [_supplier(sid=1)]
        db = _SupplierDBStub(supplier_list=sup, project_ids=[10])
        asyncio.run(get_dashboard_active_suppliers(
            db=db,
            current_user=_user("REGION_MANAGER",
                               perms={"dashboard.view"}, region_id=5),
            limit=20,
        ))
        # Supplier.id IN (subquery on WorkOrder)
        assert any("suppliers.id" in c for c in db.filter_columns)

    def test_area_manager_filter_applied(self):
        sup = [_supplier(sid=1)]
        db = _SupplierDBStub(supplier_list=sup, project_ids=[20])
        asyncio.run(get_dashboard_active_suppliers(
            db=db,
            current_user=_user("AREA_MANAGER",
                               perms={"dashboard.view"}, area_id=12),
            limit=20,
        ))
        assert any("suppliers.id" in c for c in db.filter_columns)

    def test_work_manager_no_assignments_returns_empty(self):
        db = _SupplierDBStub(supplier_list=[_supplier()], assignments=[])
        result = asyncio.run(get_dashboard_active_suppliers(
            db=db,
            current_user=_user("WORK_MANAGER",
                               perms={"dashboard.view"}, user_id=7),
            limit=20,
        ))
        assert result == []

    def test_supplier_role_returns_empty(self):
        db = _SupplierDBStub(supplier_list=[_supplier()])
        result = asyncio.run(get_dashboard_active_suppliers(
            db=db,
            current_user=_user("SUPPLIER", perms={"dashboard.view"}),
            limit=20,
        ))
        assert result == []
