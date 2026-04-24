"""
Tests for permission enforcement on /api/v1/equipment/{id}/{scan,release}.

Phase 2 Wave 6 — these two endpoints used to accept any authenticated
user (incl. ACCOUNTANT, anyone with a valid token) and silently mutate
state:
  - scan_equipment writes an equipment_scans row and can flip a WO from
    ACCEPTED → IN_PROGRESS.
  - release_equipment marks a WO as COMPLETED and sets equipment status
    back to "available".

Wave 6 added:
  - require_permission(current_user, "equipment.read") on /scan
    (suppliers DO need to scan in field, so equipment.read which they
    have is the right gate; ACCOUNTANT etc. get 403).
  - require_permission(current_user, "work_orders.update") on /release
    (suppliers must NOT be able to mark their own WOs as completed —
    only managers/coordinator/admin).

These tests exercise the route handlers directly with mocked deps so we
don't depend on a running HTTP server or full DB.
"""
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.routers.equipment import scan_equipment, release_equipment


def _user(role_code: str, *, perms: set[str] | None = None, user_id: int = 1):
    user = MagicMock()
    user.id = user_id
    user.role_id = 1
    user.is_active = True
    user.role = MagicMock()
    user.role.code = role_code
    user.role.permissions = [MagicMock(code=p) for p in (perms or set())]
    user._permissions = set(perms or set())
    return user


def _admin():
    return _user("ADMIN")


def _supplier_with_eq_read():
    """Supplier in DB has equipment.read but NOT work_orders.update —
    matches production data."""
    return _user("SUPPLIER", perms={"equipment.read", "work_orders.read_own"})


def _supplier_no_perms():
    return _user("SUPPLIER", perms=set())


def _accountant():
    """Accountant has work_orders.read but neither equipment.read nor
    work_orders.update — should be blocked from both endpoints."""
    return _user("ACCOUNTANT", perms={"work_orders.read", "invoices.read"})


def _coordinator():
    return _user(
        "ORDER_COORDINATOR",
        perms={"equipment.read", "work_orders.update", "work_orders.read"},
    )


# ---------------------------------------------------------------------------
# Mock equipment + DB
# ---------------------------------------------------------------------------

def _equipment(equipment_id: int = 7):
    eq = MagicMock()
    eq.id = equipment_id
    eq.code = "EQ-007"
    eq.status = "in_use"
    return eq


class _DB:
    """Minimal DB stub. equipment query returns the seeded equipment;
    everything else returns None / empty."""

    def __init__(self, equipment=None):
        self._equipment = equipment
        self._committed = False
        self._executed = []

    def query(self, model):
        self._current = getattr(model, "__name__", str(model))
        return self

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        if self._current == "Equipment":
            return self._equipment
        return None

    def all(self):
        return []

    def execute(self, statement, params=None):
        self._executed.append((statement, params))
        cursor = MagicMock()
        cursor.fetchall.return_value = []
        return cursor

    def commit(self):
        self._committed = True


# ===========================================================================
# scan_equipment
# ===========================================================================

class TestScanEquipmentPermission:

    def test_admin_passes(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.activity_logger.log_equipment_scanned",
            lambda **kw: None,
        )
        result = scan_equipment(
            equipment_id=7,
            db=_DB(equipment=_equipment()),
            current_user=_admin(),
        )
        assert result["success"] is True

    def test_supplier_with_equipment_read_passes(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.activity_logger.log_equipment_scanned",
            lambda **kw: None,
        )
        result = scan_equipment(
            equipment_id=7,
            db=_DB(equipment=_equipment()),
            current_user=_supplier_with_eq_read(),
        )
        assert result["success"] is True

    def test_supplier_without_equipment_read_403(self):
        with pytest.raises(HTTPException) as exc:
            scan_equipment(
                equipment_id=7,
                db=_DB(equipment=_equipment()),
                current_user=_supplier_no_perms(),
            )
        assert exc.value.status_code == 403

    def test_accountant_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            scan_equipment(
                equipment_id=7,
                db=_DB(equipment=_equipment()),
                current_user=_accountant(),
            )
        assert exc.value.status_code == 403


# ===========================================================================
# release_equipment
# ===========================================================================

class TestReleaseEquipmentPermission:

    def test_admin_passes(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.activity_logger._log",
            lambda **kw: None,
        )
        result = release_equipment(
            equipment_id=7,
            db=_DB(equipment=_equipment()),
            current_user=_admin(),
            work_order_id=None,
        )
        assert result["success"] is True
        assert result["new_status"] == "available"

    def test_coordinator_passes(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.activity_logger._log",
            lambda **kw: None,
        )
        result = release_equipment(
            equipment_id=7,
            db=_DB(equipment=_equipment()),
            current_user=_coordinator(),
            work_order_id=None,
        )
        assert result["success"] is True

    def test_supplier_blocked_403(self):
        """Suppliers must NOT be able to mark their own WO as completed
        and free equipment — that's the coordinator's job."""
        with pytest.raises(HTTPException) as exc:
            release_equipment(
                equipment_id=7,
                db=_DB(equipment=_equipment()),
                current_user=_supplier_with_eq_read(),
                work_order_id=None,
            )
        assert exc.value.status_code == 403

    def test_accountant_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            release_equipment(
                equipment_id=7,
                db=_DB(equipment=_equipment()),
                current_user=_accountant(),
                work_order_id=None,
            )
        assert exc.value.status_code == 403
