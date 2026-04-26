"""
Phase 3 Wave 3.1.4 — direct unit tests for NotificationScopeStrategy.

Notifications are pure-ownership: no region/area/project, just
`notification.user_id == user.id` with admin bypass. The legacy
helper `_check_notification_ownership` now delegates here, so the
behavior pinned by tests/test_notifications_permissions.py
TestCheckOwnership keeps the helper covered. These tests pin the
strategy itself + the AuthorizationService wiring so future
changes to either layer get caught immediately.
"""
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.core.authorization import AuthorizationService
from app.core.authorization.scope_strategies import NotificationScopeStrategy


def _user(role_code, *, user_id=1, perms=None):
    user = MagicMock()
    user.id = user_id
    user.role_id = 1
    user.is_active = True
    user.role = MagicMock()
    user.role.code = role_code
    user.role.permissions = [MagicMock(code=p) for p in (perms or set())]
    user._permissions = set(perms or set())
    return user


def _notif(*, owner_id=1, notif_id=100):
    n = MagicMock()
    n.id = notif_id
    n.user_id = owner_id
    return n


# ===========================================================================
# Strategy.check() — admin bypass
# ===========================================================================

class TestStrategyAdminBypass:

    def test_admin_can_access_anyones_notification(self):
        NotificationScopeStrategy().check(
            None, _user("ADMIN", user_id=1), _notif(owner_id=999),
        )

    def test_super_admin_can_access_anyones_notification(self):
        NotificationScopeStrategy().check(
            None, _user("SUPER_ADMIN", user_id=2), _notif(owner_id=999),
        )

    def test_admin_can_access_own_notification(self):
        NotificationScopeStrategy().check(
            None, _user("ADMIN", user_id=42), _notif(owner_id=42),
        )


# ===========================================================================
# Strategy.check() — ownership for everyone else
# ===========================================================================

class TestStrategyOwnership:

    def test_owner_passes(self):
        for role in ("WORK_MANAGER", "AREA_MANAGER", "REGION_MANAGER",
                     "ORDER_COORDINATOR", "ACCOUNTANT", "SUPPLIER", "FIELD_WORKER"):
            NotificationScopeStrategy().check(
                None, _user(role, user_id=42), _notif(owner_id=42),
            )

    def test_non_owner_403_for_every_non_admin_role(self):
        for role in ("WORK_MANAGER", "AREA_MANAGER", "REGION_MANAGER",
                     "ORDER_COORDINATOR", "ACCOUNTANT", "SUPPLIER", "FIELD_WORKER"):
            with pytest.raises(HTTPException) as exc:
                NotificationScopeStrategy().check(
                    None, _user(role, user_id=42), _notif(owner_id=999),
                )
            assert exc.value.status_code == 403


# ===========================================================================
# Strategy.filter() — pure ownership filter on Notification queries
# ===========================================================================

class TestStrategyFilter:

    def test_filter_applies_user_id_predicate_for_non_admin(self):
        # filter() returns query.filter(Notification.user_id == user.id);
        # using a MagicMock query lets us verify .filter() was called.
        q = MagicMock()
        out = NotificationScopeStrategy().filter(None, _user("WORK_MANAGER", user_id=42), q)
        q.filter.assert_called_once()
        assert out is q.filter.return_value

    def test_filter_also_applies_for_admin(self):
        """My-notifications listings are personal even for admin —
        admin sees their own bell at /my, not the global firehose."""
        q = MagicMock()
        out = NotificationScopeStrategy().filter(None, _user("ADMIN", user_id=1), q)
        q.filter.assert_called_once()
        assert out is q.filter.return_value


# ===========================================================================
# AuthorizationService wiring
# ===========================================================================

class _DBStub:
    def query(self, *a, **kw):
        return self

    def filter(self, *a, **kw):
        return self

    def first(self):
        return None


class TestServiceWiring:

    def test_authorize_routes_to_notification_strategy_via_resource_type(self):
        svc = AuthorizationService(_DBStub())
        with pytest.raises(HTTPException) as exc:
            svc.authorize(
                _user("WORK_MANAGER", user_id=42),
                resource=_notif(owner_id=999),
                resource_type="Notification",
            )
        assert exc.value.status_code == 403

    def test_authorize_admin_bypasses_via_service(self):
        svc = AuthorizationService(_DBStub())
        svc.authorize(
            _user("ADMIN", user_id=1),
            resource=_notif(owner_id=999),
            resource_type="Notification",
        )

    def test_authorize_owner_passes_via_service(self):
        svc = AuthorizationService(_DBStub())
        svc.authorize(
            _user("WORK_MANAGER", user_id=42),
            resource=_notif(owner_id=42),
            resource_type="Notification",
        )


# ===========================================================================
# Backwards-compat: the legacy helper still works after migration
# ===========================================================================

class TestLegacyHelperDelegation:

    def test_helper_still_callable_with_two_args(self):
        """The router's _check_notification_ownership now delegates
        to the strategy. Confirm the public signature is unchanged so
        no other call sites break."""
        from app.routers.notifications import _check_notification_ownership
        # Signature: (user, notification) — no db arg.
        _check_notification_ownership(_user("ADMIN", user_id=1), _notif(owner_id=999))

    def test_helper_raises_403_for_non_owner(self):
        from app.routers.notifications import _check_notification_ownership
        with pytest.raises(HTTPException) as exc:
            _check_notification_ownership(
                _user("WORK_MANAGER", user_id=42),
                _notif(owner_id=999),
            )
        assert exc.value.status_code == 403
