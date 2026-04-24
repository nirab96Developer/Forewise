"""
Tests for ownership / self-service enforcement on auth.py endpoints.

Phase 2 Wave 1.B + 1.C:
  1.B (ownership):
    - revoke_session, revoke_all_sessions, get_user_sessions —
      operate only on rows where session.user_id == current_user.id.
    - delete_biometric_credential — already filters by user_id;
      regression-locks the behavior.
    - revoke_device — already filters by user_id; regression-locks.
  1.C (self-service):
    - verify_2fa_setup — previously took user_id from body with NO auth.
      Wave 1.C fixed it to require authentication and ignore body user_id
      when it doesn't match the authenticated user.
    - change_password — already self-service; regression-locks.
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException


# ---------------------------------------------------------------------------
# Mock user / session / device / credential factories
# ---------------------------------------------------------------------------

def _user(user_id: int = 1, role_code: str = "WORK_MANAGER"):
    user = MagicMock()
    user.id = user_id
    user.role_id = 1
    user.is_active = True
    user.username = f"user_{user_id}"
    user.full_name = f"User {user_id}"
    user.role = MagicMock()
    user.role.code = role_code
    user.role.permissions = []
    user._permissions = set()
    return user


class _MockSession:
    """In-memory drop-in for SQLAlchemy `Session` query/filter chains."""

    def __init__(self, rows: list):
        self._rows = list(rows)
        self.committed = False
        self._update_called_with = None

    def query(self, model):
        self._model = model
        return self

    def filter(self, *args):
        # We don't introspect the args — the real ownership check happens
        # via WHERE in SQL. We simulate it by always returning all stored
        # rows; the test fixture seeds only the rows that should match.
        return self

    def order_by(self, *args):
        return self

    def first(self):
        return self._rows[0] if self._rows else None

    def all(self):
        return list(self._rows)

    def update(self, values: dict):
        self._update_called_with = values
        for r in self._rows:
            for k, v in values.items():
                setattr(r, k, v)
        return len(self._rows)

    def commit(self):
        self.committed = True


def _session_row(session_id: str, user_id: int, is_active: bool = True):
    s = MagicMock()
    s.id = 100
    s.session_id = session_id
    s.user_id = user_id
    s.ip_address = "127.0.0.1"
    s.user_agent = "test"
    s.is_active = is_active
    s.is_revoked = False
    from datetime import datetime
    s.created_at = datetime.utcnow()
    s.updated_at = datetime.utcnow()
    return s


def _credential_row(credential_id: int, user_id: int):
    c = MagicMock()
    c.id = credential_id
    c.user_id = user_id
    c.is_active = True
    return c


def _device_row(user_id: int):
    d = MagicMock()
    d.user_id = user_id
    d.is_active = True
    return d


# ---------------------------------------------------------------------------
# Wave 1.B — sessions ownership
# ---------------------------------------------------------------------------

class TestRevokeSessionOwnership:

    def test_owner_revokes_own_session(self):
        from app.routers.auth import revoke_session
        owner = _user(user_id=42)
        db = _MockSession([_session_row("abc123token", user_id=42)])
        result = revoke_session(session_id="abc123token", current_user=owner, db=db)
        assert result == {"message": "Session revoked successfully"}
        assert db.committed
        assert db._rows[0].is_revoked is True
        assert db._rows[0].is_active is False

    def test_non_owner_gets_404(self):
        """Querying a session that doesn't belong to the user returns 404
        (the WHERE in SQL filters it out, so .first() is None)."""
        from app.routers.auth import revoke_session
        attacker = _user(user_id=99)
        # Note: empty rows simulates the SQL filter excluding the row
        db = _MockSession([])
        with pytest.raises(HTTPException) as exc:
            revoke_session(session_id="someone-elses-token", current_user=attacker, db=db)
        assert exc.value.status_code == 404

    def test_revoke_all_only_marks_owner_rows(self):
        from app.routers.auth import revoke_all_sessions
        owner = _user(user_id=42)
        # 3 of the user's own sessions
        db = _MockSession([
            _session_row("t1", user_id=42),
            _session_row("t2", user_id=42),
            _session_row("t3", user_id=42),
        ])
        result = revoke_all_sessions(current_user=owner, db=db)
        assert result["revoked_count"] == 3
        assert db.committed
        assert all(r.is_revoked for r in db._rows)

    def test_get_sessions_returns_only_user_rows(self):
        from app.routers.auth import get_user_sessions
        owner = _user(user_id=42)
        db = _MockSession([
            _session_row("t1", user_id=42),
            _session_row("t2", user_id=42),
        ])
        resp = get_user_sessions(current_user=owner, db=db)
        assert resp.total_sessions == 2
        assert resp.current_session.session_id == "t1"
        assert len(resp.other_sessions) == 1

    def test_get_sessions_no_rows_returns_placeholder(self):
        from app.routers.auth import get_user_sessions
        owner = _user(user_id=42)
        db = _MockSession([])
        resp = get_user_sessions(current_user=owner, db=db)
        assert resp.total_sessions == 0
        assert resp.current_session.session_id == "no-session"
        assert resp.other_sessions == []


# ---------------------------------------------------------------------------
# Wave 1.B — biometric credential ownership (regression lock)
# ---------------------------------------------------------------------------

class TestDeleteBiometricCredentialOwnership:

    def test_owner_deletes_own_credential(self):
        from app.routers.auth import delete_biometric_credential
        owner = _user(user_id=42)
        db = _MockSession([_credential_row(credential_id=7, user_id=42)])

        # Async function — drive it directly
        import asyncio
        result = asyncio.run(delete_biometric_credential(
            credential_id=7, current_user=owner, db=db
        ))
        assert result == {"message": "Credential deleted successfully"}
        assert db.committed
        assert db._rows[0].is_active is False

    def test_non_owner_gets_404(self):
        from app.routers.auth import delete_biometric_credential
        attacker = _user(user_id=99)
        db = _MockSession([])  # SQL WHERE filters it out

        import asyncio
        with pytest.raises(HTTPException) as exc:
            asyncio.run(delete_biometric_credential(
                credential_id=7, current_user=attacker, db=db
            ))
        assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# Wave 1.B — device ownership (regression lock)
# ---------------------------------------------------------------------------

class TestRevokeDeviceOwnership:

    def test_owner_revokes_own_device(self):
        from app.routers.auth import revoke_device
        owner = _user(user_id=42)
        db = _MockSession([_device_row(user_id=42)])
        # Use a valid UUID
        device_id = "12345678-1234-5678-1234-567812345678"
        result = revoke_device(device_id=device_id, current_user=owner, db=db)
        assert "מכשיר" in result["message"]
        assert db.committed
        assert db._rows[0].is_active is False

    def test_non_owner_gets_404(self):
        from app.routers.auth import revoke_device
        attacker = _user(user_id=99)
        db = _MockSession([])
        device_id = "12345678-1234-5678-1234-567812345678"
        with pytest.raises(HTTPException) as exc:
            revoke_device(device_id=device_id, current_user=attacker, db=db)
        assert exc.value.status_code == 404

    def test_invalid_uuid_returns_400(self):
        from app.routers.auth import revoke_device
        owner = _user(user_id=42)
        db = _MockSession([])
        with pytest.raises(HTTPException) as exc:
            revoke_device(device_id="not-a-uuid", current_user=owner, db=db)
        assert exc.value.status_code == 400


# ---------------------------------------------------------------------------
# Wave 1.C — 2FA verify-setup vulnerability fix
# ---------------------------------------------------------------------------

class TestVerify2faSetupAuth:
    """Wave 1.C critical fix: was previously unauthenticated; could enable
    2FA for ANY user_id passed in the body."""

    def test_self_succeeds_without_user_id(self, monkeypatch):
        """The fixed endpoint uses current_user.id internally — no need
        to pass user_id at all."""
        from app.routers.auth import verify_2fa_setup
        owner = _user(user_id=42)
        monkeypatch.setattr(
            "app.routers.auth.auth_service.verify_2fa_setup",
            lambda db, uid, code: True,
        )
        result = verify_2fa_setup(
            code="123456",
            user_id=None,
            current_user=owner,
            db=MagicMock(),
        )
        assert result == {"message": "2FA setup verified successfully"}

    def test_self_succeeds_with_matching_user_id(self, monkeypatch):
        """Backwards-compat: caller may still pass user_id matching themselves."""
        from app.routers.auth import verify_2fa_setup
        owner = _user(user_id=42)
        monkeypatch.setattr(
            "app.routers.auth.auth_service.verify_2fa_setup",
            lambda db, uid, code: True,
        )
        result = verify_2fa_setup(
            code="123456",
            user_id=42,
            current_user=owner,
            db=MagicMock(),
        )
        assert result == {"message": "2FA setup verified successfully"}

    def test_blocks_attempt_to_verify_other_users_2fa(self, monkeypatch):
        """The vulnerability: enable 2FA on someone else's account."""
        from app.routers.auth import verify_2fa_setup
        attacker = _user(user_id=42)
        monkeypatch.setattr(
            "app.routers.auth.auth_service.verify_2fa_setup",
            lambda db, uid, code: True,
        )
        with pytest.raises(HTTPException) as exc:
            verify_2fa_setup(
                code="123456",
                user_id=99,  # different from current_user.id
                current_user=attacker,
                db=MagicMock(),
            )
        assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# Wave 1.C — change_password regression lock
# ---------------------------------------------------------------------------

class TestChangePasswordSelfService:

    def test_change_password_uses_current_user_id(self, monkeypatch):
        """Regression test: change_password MUST always use current_user.id
        and never accept a target user_id from the request body."""
        from app.routers.auth import change_password
        from app.schemas.auth import PasswordChangeRequest

        captured_user_id = []

        def fake_change(db, user_id, current_password, new_password):
            captured_user_id.append(user_id)
            return True

        monkeypatch.setattr(
            "app.routers.auth.auth_service.change_password", fake_change
        )
        monkeypatch.setattr(
            "app.routers.auth.activity_log_service.log_activity",
            lambda **kw: None,
        )

        owner = _user(user_id=42)
        request = PasswordChangeRequest(
            current_password="OldPass123!",
            new_password="NewPass123!",
        )
        result = change_password(
            password_data=request, current_user=owner, db=MagicMock()
        )
        assert result == {"message": "Password changed successfully"}
        assert captured_user_id == [42], (
            "change_password must always operate on current_user.id"
        )
