"""
Tests for permission enforcement on /api/v1/auth/admin/* endpoints.

Phase 2 Wave 1.A: lock_account, unlock_account, get_security_audit,
get_login_attempts now call require_permission(). This file verifies:
  - admin (ADMIN role.code) passes the check (built-in ADMIN bypass).
  - a real user with the explicit permission passes the check.
  - a user without the permission gets a 403 ForbiddenException.

These tests exercise the route handlers directly with mocked deps so we
don't depend on a running HTTP server or a JWT issuance flow.
"""
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.routers.auth import (
    lock_account,
    unlock_account,
    get_security_audit,
    get_login_attempts,
)


# ---------------------------------------------------------------------------
# User mocks
# ---------------------------------------------------------------------------

def _user(role_code: str, perms: set[str] | None = None):
    """Build a mock user matching what get_current_active_user returns.

    `require_permission` walks `user.role.code` for the ADMIN bypass and
    `user_has_permission(user, perm)` which checks `user._permissions` /
    `user.role.permissions`. We set both to keep the helper happy in
    every code path it might take.
    """
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
    """Accountant has none of the users.{lock,unlock,read} perms."""
    return _user("ACCOUNTANT", perms={"invoices.read", "invoices.create"})


def _supplier():
    """Supplier has nothing relevant."""
    return _user("SUPPLIER", perms=set())


def _user_with(perm: str):
    return _user("REGION_MANAGER", perms={perm})


# ---------------------------------------------------------------------------
# Helpers — mock request payloads for the lock/unlock endpoints
# ---------------------------------------------------------------------------

class _LockReq:
    user_id = 99
    reason = "test"
    duration_hours = 1


class _UnlockReq:
    user_id = 99
    reason = "test"


# ---------------------------------------------------------------------------
# lock_account
# ---------------------------------------------------------------------------

class TestLockAccount:

    def test_admin_bypass(self, monkeypatch):
        # ADMIN should pass require_permission even without users.lock
        monkeypatch.setattr(
            "app.routers.auth.auth_service.lock_account", lambda **kw: True
        )
        monkeypatch.setattr(
            "app.routers.auth.activity_log_service.log_activity",
            lambda **kw: None,
        )
        result = lock_account(_LockReq(), current_user=_admin(), db=MagicMock())
        assert result == {"message": "Account locked successfully"}

    def test_user_with_perm_passes(self, monkeypatch):
        monkeypatch.setattr(
            "app.routers.auth.auth_service.lock_account", lambda **kw: True
        )
        monkeypatch.setattr(
            "app.routers.auth.activity_log_service.log_activity",
            lambda **kw: None,
        )
        result = lock_account(
            _LockReq(),
            current_user=_user_with("users.lock"),
            db=MagicMock(),
        )
        assert result == {"message": "Account locked successfully"}

    def test_accountant_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            lock_account(_LockReq(), current_user=_accountant(), db=MagicMock())
        assert exc.value.status_code == 403

    def test_supplier_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            lock_account(_LockReq(), current_user=_supplier(), db=MagicMock())
        assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# unlock_account
# ---------------------------------------------------------------------------

class TestUnlockAccount:

    def test_admin_bypass(self, monkeypatch):
        monkeypatch.setattr(
            "app.routers.auth.auth_service.unlock_account", lambda **kw: True
        )
        monkeypatch.setattr(
            "app.routers.auth.activity_log_service.log_activity",
            lambda **kw: None,
        )
        result = unlock_account(_UnlockReq(), current_user=_admin(), db=MagicMock())
        assert result == {"message": "Account unlocked successfully"}

    def test_user_with_perm_passes(self, monkeypatch):
        monkeypatch.setattr(
            "app.routers.auth.auth_service.unlock_account", lambda **kw: True
        )
        monkeypatch.setattr(
            "app.routers.auth.activity_log_service.log_activity",
            lambda **kw: None,
        )
        result = unlock_account(
            _UnlockReq(),
            current_user=_user_with("users.unlock"),
            db=MagicMock(),
        )
        assert result == {"message": "Account unlocked successfully"}

    def test_accountant_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            unlock_account(_UnlockReq(), current_user=_accountant(), db=MagicMock())
        assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# get_security_audit
# ---------------------------------------------------------------------------

class TestGetSecurityAudit:

    def test_admin_bypass(self):
        result = get_security_audit(user_id=99, current_user=_admin(), db=MagicMock())
        # stub returns an empty SecurityAuditResponse — only that it doesn't raise
        assert result.user_id == 99

    def test_user_with_perm_passes(self):
        result = get_security_audit(
            user_id=99,
            current_user=_user_with("users.read"),
            db=MagicMock(),
        )
        assert result.user_id == 99

    def test_supplier_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            get_security_audit(user_id=99, current_user=_supplier(), db=MagicMock())
        assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# get_login_attempts
# ---------------------------------------------------------------------------

class TestGetLoginAttempts:

    def test_admin_bypass(self):
        result = get_login_attempts(user_id=99, current_user=_admin(), db=MagicMock())
        assert result.total_attempts == 0

    def test_user_with_perm_passes(self):
        result = get_login_attempts(
            user_id=99,
            current_user=_user_with("users.read"),
            db=MagicMock(),
        )
        assert result.total_attempts == 0

    def test_supplier_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            get_login_attempts(user_id=99, current_user=_supplier(), db=MagicMock())
        assert exc.value.status_code == 403
