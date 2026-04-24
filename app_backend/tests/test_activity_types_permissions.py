"""
Tests for permission enforcement on /api/v1/activity-types mutations.

Phase 2 Wave 7.C — three mutations on activity_types.py used to have
NO authentication at all (not even get_current_active_user). Anyone on
the internet could insert/edit/soft-delete activity_types rows that
worklogs reference. Now ADMIN-only via:
  - activity_types.create
  - activity_types.update
  - activity_types.delete
(All three permissions seeded by Wave 7.A migration e1f2a3b4c5d6.)

Read endpoints (GET / and GET /{id}) are intentionally untouched in
this wave — they're a lookup table; tightening them is a separate
decision.
"""
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.routers.activity_types import (
    ActivityTypeCreate,
    create_activity_type,
    update_activity_type,
    delete_activity_type,
)


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


def _coordinator():
    return _user("ORDER_COORDINATOR", perms={"work_orders.update"})


def _supplier():
    return _user("SUPPLIER", perms={"equipment.read"})


def _accountant():
    return _user("ACCOUNTANT", perms={"invoices.read"})


class _DBStub:
    def __init__(self, existing=None):
        self._existing = existing

    def query(self, model):
        return self

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._existing

    def add(self, obj):
        pass

    def commit(self):
        pass

    def refresh(self, obj):
        pass


def _payload():
    return ActivityTypeCreate(
        code="TEST_TYPE",
        name="Test Type",
        description="for tests",
        category="general",
    )


def _existing():
    obj = MagicMock()
    obj.id = 7
    obj.code = "TEST_TYPE"
    obj.is_active = True
    return obj


# ===========================================================================
# create_activity_type
# ===========================================================================

class TestCreateActivityType:

    def test_admin_passes(self):
        # No existing row → handler proceeds to create
        result = create_activity_type(
            data=_payload(),
            db=_DBStub(existing=None),
            current_user=_admin(),
        )
        assert result is not None

    def test_coordinator_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            create_activity_type(
                data=_payload(),
                db=_DBStub(existing=None),
                current_user=_coordinator(),
            )
        assert exc.value.status_code == 403

    def test_supplier_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            create_activity_type(
                data=_payload(),
                db=_DBStub(existing=None),
                current_user=_supplier(),
            )
        assert exc.value.status_code == 403

    def test_accountant_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            create_activity_type(
                data=_payload(),
                db=_DBStub(existing=None),
                current_user=_accountant(),
            )
        assert exc.value.status_code == 403


# ===========================================================================
# update_activity_type
# ===========================================================================

class TestUpdateActivityType:

    def test_admin_passes(self):
        result = update_activity_type(
            activity_type_id=7,
            data=_payload(),
            db=_DBStub(existing=_existing()),
            current_user=_admin(),
        )
        assert result is not None

    def test_supplier_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            update_activity_type(
                activity_type_id=7,
                data=_payload(),
                db=_DBStub(existing=_existing()),
                current_user=_supplier(),
            )
        assert exc.value.status_code == 403

    def test_coordinator_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            update_activity_type(
                activity_type_id=7,
                data=_payload(),
                db=_DBStub(existing=_existing()),
                current_user=_coordinator(),
            )
        assert exc.value.status_code == 403


# ===========================================================================
# delete_activity_type
# ===========================================================================

class TestDeleteActivityType:

    def test_admin_passes(self):
        obj = _existing()
        result = delete_activity_type(
            activity_type_id=7,
            db=_DBStub(existing=obj),
            current_user=_admin(),
        )
        assert obj.is_active is False  # soft-deleted
        assert "בוטל" in result["message"]

    def test_supplier_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            delete_activity_type(
                activity_type_id=7,
                db=_DBStub(existing=_existing()),
                current_user=_supplier(),
            )
        assert exc.value.status_code == 403

    def test_accountant_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            delete_activity_type(
                activity_type_id=7,
                db=_DBStub(existing=_existing()),
                current_user=_accountant(),
            )
        assert exc.value.status_code == 403
