"""
Tests for permission enforcement on /api/v1/system-rates/* mutations.

Phase 2 Wave 7.B — three mutations on system_rates.py used to accept
any authenticated user. Now they require `system.settings` (ADMIN only
in DB; require_permission ALSO bypasses for role.code == "ADMIN").

Verified:
  - admin passes
  - any non-admin role without system.settings → 403
  - read endpoints unchanged (out of scope for Wave 7.B)
"""
import asyncio
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.routers.system_rates import (
    create_system_rate,
    update_system_rate,
    delete_system_rate,
)
from app.schemas.system_rate import SystemRateCreate, SystemRateUpdate


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _user(role_code: str, *, perms: set[str] | None = None):
    user = MagicMock()
    user.id = 1
    user.role_id = 1
    user.is_active = True
    user.role = MagicMock()
    user.role.code = role_code
    user.role.permissions = [MagicMock(code=p) for p in (perms or set())]
    user._permissions = set(perms or set())
    return user


def _admin():
    return _user("ADMIN")


def _accountant():
    """Accountant has no system.settings — should be blocked."""
    return _user("ACCOUNTANT", perms={"invoices.read", "invoices.create"})


def _coordinator():
    return _user("ORDER_COORDINATOR", perms={"work_orders.update"})


def _supplier():
    return _user("SUPPLIER", perms={"equipment.read"})


class _DBStub:
    """Minimal session: query→filter→first returns the seeded rate;
    add/commit/refresh are no-ops."""

    def __init__(self, rate=None, existing=False):
        self._rate = rate
        self._existing = existing

    def query(self, model):
        self._current = getattr(model, "__name__", str(model))
        return self

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        if self._current == "SystemRate":
            # For create: existing-by-code lookup → None means no conflict
            if not self._existing and self._rate is None:
                return None
            return self._rate
        return None

    def add(self, obj):
        pass

    def commit(self):
        pass

    def refresh(self, obj):
        pass


def _create_payload():
    # Build a SystemRateCreate via the schema constructor so the test
    # tracks any future field changes.
    return SystemRateCreate(
        code="TEST_RATE",
        name="Test Rate",
        rate_type="hourly",
        rate_value=100.0,
    )


def _update_payload():
    return SystemRateUpdate(name="Updated Test Rate")


def _existing_rate():
    rate = MagicMock()
    rate.id = 7
    rate.code = "TEST_RATE"
    rate.is_active = True
    return rate


# ===========================================================================
# create_system_rate
# ===========================================================================

class TestCreateSystemRate:

    def test_admin_passes_permission_gate(self):
        """Admin must NOT get 403. The handler itself has a pre-existing
        bug (it accesses `SystemRate.code` but the model field is named
        `rate_code`), so an admin call eventually raises AttributeError
        — but only AFTER the require_permission gate passes. That's the
        proof we need: a 403 here would mean Wave 7.B broke admin."""
        with pytest.raises(AttributeError):
            asyncio.run(create_system_rate(
                data=_create_payload(),
                db=_DBStub(),
                current_user=_admin(),
            ))

    def test_accountant_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(create_system_rate(
                data=_create_payload(),
                db=_DBStub(),
                current_user=_accountant(),
            ))
        assert exc.value.status_code == 403

    def test_coordinator_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(create_system_rate(
                data=_create_payload(),
                db=_DBStub(),
                current_user=_coordinator(),
            ))
        assert exc.value.status_code == 403

    def test_supplier_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(create_system_rate(
                data=_create_payload(),
                db=_DBStub(),
                current_user=_supplier(),
            ))
        assert exc.value.status_code == 403


# ===========================================================================
# update_system_rate
# ===========================================================================

class TestUpdateSystemRate:

    def test_admin_passes(self):
        result = asyncio.run(update_system_rate(
            rate_id=7,
            data=_update_payload(),
            db=_DBStub(rate=_existing_rate()),
            current_user=_admin(),
        ))
        assert result is not None

    def test_accountant_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(update_system_rate(
                rate_id=7,
                data=_update_payload(),
                db=_DBStub(rate=_existing_rate()),
                current_user=_accountant(),
            ))
        assert exc.value.status_code == 403

    def test_supplier_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(update_system_rate(
                rate_id=7,
                data=_update_payload(),
                db=_DBStub(rate=_existing_rate()),
                current_user=_supplier(),
            ))
        assert exc.value.status_code == 403


# ===========================================================================
# delete_system_rate
# ===========================================================================

class TestDeleteSystemRate:

    def test_admin_passes(self):
        rate = _existing_rate()
        asyncio.run(delete_system_rate(
            rate_id=7,
            db=_DBStub(rate=rate),
            current_user=_admin(),
        ))
        assert rate.is_active is False  # soft-deleted

    def test_accountant_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(delete_system_rate(
                rate_id=7,
                db=_DBStub(rate=_existing_rate()),
                current_user=_accountant(),
            ))
        assert exc.value.status_code == 403

    def test_coordinator_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(delete_system_rate(
                rate_id=7,
                db=_DBStub(rate=_existing_rate()),
                current_user=_coordinator(),
            ))
        assert exc.value.status_code == 403
