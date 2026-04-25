"""
Tests for permission + ownership enforcement on /api/v1/notifications/*.

Phase 2 Wave 7.G — split into two groups:

(1) Five admin mutations gated behind `notifications.manage`
    (ADMIN per Wave 7.A migration):
      POST   /notifications
      POST   /notifications/bulk-action
      POST   /notifications/cleanup
      PUT    /notifications/{id}
      DELETE /notifications/{id}

(2) Four self-service per-id endpoints that now enforce ownership via
    `_check_notification_ownership` BEFORE touching the service layer.
    Owner passes, non-owner gets 403, ADMIN bypasses.
      POST  /notifications/{id}/read
      PATCH /notifications/{id}/read
      (and the unit-level helper itself)
"""
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.routers.notifications import (
    _check_notification_ownership,
    _mark_one_as_read,
    bulk_notification_action,
    cleanup_old_notifications,
    create_notification,
    delete_notification,
    update_notification,
)
from app.schemas.notification import NotificationCreate, NotificationUpdate, NotificationBulkAction


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


def _supplier():
    return _user("SUPPLIER", perms={"equipment.read"})


def _accountant():
    return _user("ACCOUNTANT", perms={"invoices.read"})


def _coordinator():
    return _user("ORDER_COORDINATOR", perms={"work_orders.update"})


def _notification(notif_id: int = 100, owner_id: int = 1):
    n = MagicMock()
    n.id = notif_id
    n.user_id = owner_id
    n.is_read = False
    n.read_at = None
    return n


class _DBStub:
    """Pass-through stub. Service calls are mocked separately."""

    def commit(self):
        pass

    def refresh(self, obj):
        pass

    def query(self, model):
        return self

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return None

    def all(self):
        return []

    def count(self):
        return 0


# ---------------------------------------------------------------------------
# _check_notification_ownership
# ---------------------------------------------------------------------------

class TestCheckOwnership:

    def test_owner_passes(self):
        u = _user("WORK_MANAGER", user_id=42)
        n = _notification(owner_id=42)
        _check_notification_ownership(u, n)

    def test_admin_bypasses_ownership(self):
        u = _admin()
        n = _notification(owner_id=999)  # someone else's
        _check_notification_ownership(u, n)

    def test_super_admin_bypasses(self):
        u = _user("SUPER_ADMIN", user_id=2)
        n = _notification(owner_id=999)
        _check_notification_ownership(u, n)

    def test_non_owner_403(self):
        u = _user("WORK_MANAGER", user_id=42)
        n = _notification(owner_id=999)
        with pytest.raises(HTTPException) as exc:
            _check_notification_ownership(u, n)
        assert exc.value.status_code == 403

    def test_supplier_non_owner_403(self):
        u = _user("SUPPLIER", user_id=42)
        n = _notification(owner_id=999)
        with pytest.raises(HTTPException) as exc:
            _check_notification_ownership(u, n)
        assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# Admin mutations (5)
# ---------------------------------------------------------------------------

class TestCreateNotification:

    def test_admin_passes(self, monkeypatch):
        captured = {}
        monkeypatch.setattr(
            "app.routers.notifications.notification_service.create_notification",
            lambda db, n: captured.setdefault("created", n) or _notification(),
        )
        payload = NotificationCreate(
            user_id=1, title="t", message="m", notification_type="SYSTEM",
        )
        result = create_notification(payload, _DBStub(), _admin())
        assert result is not None

    def test_supplier_blocked_403(self):
        payload = NotificationCreate(
            user_id=1, title="t", message="m", notification_type="SYSTEM",
        )
        with pytest.raises(HTTPException) as exc:
            create_notification(payload, _DBStub(), _supplier())
        assert exc.value.status_code == 403

    def test_coordinator_blocked_403(self):
        payload = NotificationCreate(
            user_id=1, title="t", message="m", notification_type="SYSTEM",
        )
        with pytest.raises(HTTPException) as exc:
            create_notification(payload, _DBStub(), _coordinator())
        assert exc.value.status_code == 403


class TestUpdateNotification:

    def test_admin_passes(self, monkeypatch):
        notif = _notification(owner_id=1)
        monkeypatch.setattr(
            "app.routers.notifications.notification_service.get_notification",
            lambda db, nid: notif,
        )
        update = NotificationUpdate(is_read=True)
        result = update_notification(100, update, _DBStub(), _admin())
        assert result is not None

    def test_accountant_blocked_403(self):
        update = NotificationUpdate(is_read=True)
        with pytest.raises(HTTPException) as exc:
            update_notification(100, update, _DBStub(), _accountant())
        assert exc.value.status_code == 403


class TestBulkAction:

    def test_admin_passes(self, monkeypatch):
        monkeypatch.setattr(
            "app.routers.notifications.notification_service.get_notification",
            lambda db, nid: None,
        )
        payload = NotificationBulkAction(notification_ids=[1, 2], action="mark_read")
        result = bulk_notification_action(payload, _DBStub(), _admin())
        assert "updated_count" in result

    def test_supplier_blocked_403(self):
        payload = NotificationBulkAction(notification_ids=[1, 2], action="mark_read")
        with pytest.raises(HTTPException) as exc:
            bulk_notification_action(payload, _DBStub(), _supplier())
        assert exc.value.status_code == 403


class TestDeleteNotification:

    def test_admin_passes(self, monkeypatch):
        monkeypatch.setattr(
            "app.routers.notifications.notification_service.delete_notification",
            lambda db, notification_id, user_id: True,
        )
        result = delete_notification(100, _DBStub(), _admin())
        assert "deleted" in result["message"].lower()

    def test_supplier_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            delete_notification(100, _DBStub(), _supplier())
        assert exc.value.status_code == 403

    def test_coordinator_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            delete_notification(100, _DBStub(), _coordinator())
        assert exc.value.status_code == 403


class TestCleanupOldNotifications:

    def test_admin_passes(self, monkeypatch):
        monkeypatch.setattr(
            "app.routers.notifications.notification_service.cleanup_old_notifications",
            lambda db, days: 5,
        )
        result = cleanup_old_notifications(30, _DBStub(), _admin())
        assert result["deleted_count"] == 5

    def test_accountant_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            cleanup_old_notifications(30, _DBStub(), _accountant())
        assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# Self-service mark-as-read (ownership)
# ---------------------------------------------------------------------------

class TestMarkOneAsRead:

    def test_owner_passes(self, monkeypatch):
        notif = _notification(owner_id=42)
        monkeypatch.setattr(
            "app.routers.notifications.notification_service.get_notification",
            lambda db, nid: notif,
        )
        monkeypatch.setattr(
            "app.routers.notifications.notification_service.mark_as_read",
            lambda db, notification_id, user_id: notif,
        )
        result = _mark_one_as_read(100, _DBStub(), _user("WORK_MANAGER", user_id=42))
        assert result is notif

    def test_non_owner_403(self, monkeypatch):
        # Notification belongs to user 999; current user is 42.
        notif = _notification(owner_id=999)
        monkeypatch.setattr(
            "app.routers.notifications.notification_service.get_notification",
            lambda db, nid: notif,
        )
        with pytest.raises(HTTPException) as exc:
            _mark_one_as_read(100, _DBStub(), _user("WORK_MANAGER", user_id=42))
        assert exc.value.status_code == 403

    def test_admin_can_mark_anyones_read(self, monkeypatch):
        notif = _notification(owner_id=999)  # someone else
        monkeypatch.setattr(
            "app.routers.notifications.notification_service.get_notification",
            lambda db, nid: notif,
        )
        monkeypatch.setattr(
            "app.routers.notifications.notification_service.mark_as_read",
            lambda db, notification_id, user_id: notif,
        )
        result = _mark_one_as_read(100, _DBStub(), _admin())
        assert result is notif

    def test_missing_returns_404(self, monkeypatch):
        monkeypatch.setattr(
            "app.routers.notifications.notification_service.get_notification",
            lambda db, nid: None,
        )
        with pytest.raises(HTTPException) as exc:
            _mark_one_as_read(100, _DBStub(), _user("WORK_MANAGER", user_id=42))
        assert exc.value.status_code == 404
