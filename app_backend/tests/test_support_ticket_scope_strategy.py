"""
Phase 3 Wave 3.1.5 — direct unit tests for SupportTicketScopeStrategy.

Pins the role × outcome matrix at the strategy layer so future
regressions get caught immediately. Existing integration tests
(tests/test_support_tickets_permissions.py) keep covering the
router endpoints; these tests cover the strategy itself + the
two `/comments` endpoints which weren't tested for ownership
before this wave.
"""
import asyncio
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.core.authorization import AuthorizationService
from app.core.authorization.scope_strategies import SupportTicketScopeStrategy
from app.routers.support_tickets import (
    add_ticket_comment,
    get_ticket_comments,
    CommentInput,
)


def _user(role_code, *, user_id=1):
    user = MagicMock()
    user.id = user_id
    user.role_id = 1
    user.is_active = True
    user.full_name = f"User {user_id}"
    user.username = f"user_{user_id}"
    user.role = MagicMock()
    user.role.code = role_code
    user.role.permissions = []
    user._permissions = set()
    return user


def _ticket(*, ticket_id=1, owner_id=1, ticket_number="TKT-202604-0001"):
    t = MagicMock()
    t.id = ticket_id
    t.ticket_number = ticket_number
    t.user_id = owner_id
    t.status = "open"
    return t


# ===========================================================================
# Strategy.check() — admin bypass + ownership
# ===========================================================================

class TestStrategyCheck:

    def test_admin_passes_anyones_ticket(self):
        SupportTicketScopeStrategy().check(
            None, _user("ADMIN", user_id=1), _ticket(owner_id=999),
        )

    def test_owner_passes(self):
        for role in ("WORK_MANAGER", "AREA_MANAGER", "REGION_MANAGER",
                     "ORDER_COORDINATOR", "ACCOUNTANT", "SUPPLIER", "FIELD_WORKER"):
            SupportTicketScopeStrategy().check(
                None, _user(role, user_id=42), _ticket(owner_id=42),
            )

    def test_non_owner_403_for_every_non_admin_role(self):
        for role in ("WORK_MANAGER", "AREA_MANAGER", "REGION_MANAGER",
                     "ORDER_COORDINATOR", "ACCOUNTANT", "SUPPLIER", "FIELD_WORKER"):
            with pytest.raises(HTTPException) as exc:
                SupportTicketScopeStrategy().check(
                    None, _user(role, user_id=42), _ticket(owner_id=999),
                )
            assert exc.value.status_code == 403

    def test_super_admin_does_NOT_bypass(self):
        """Pinning current support_tickets behavior: only the literal
        ADMIN code bypasses, NOT SUPER_ADMIN. Diverges from
        NotificationScopeStrategy intentionally — see strategy
        docstring. If product wants SUPER_ADMIN access too, that's a
        deliberate change, not a centralization side-effect."""
        with pytest.raises(HTTPException) as exc:
            SupportTicketScopeStrategy().check(
                None, _user("SUPER_ADMIN", user_id=1), _ticket(owner_id=999),
            )
        assert exc.value.status_code == 403


# ===========================================================================
# Strategy.filter() — admin sees all, others scoped to own
# ===========================================================================

class TestStrategyFilter:

    def test_admin_query_unchanged(self):
        q = MagicMock()
        out = SupportTicketScopeStrategy().filter(None, _user("ADMIN"), q)
        q.filter.assert_not_called()
        assert out is q

    def test_non_admin_filters_by_user_id(self):
        q = MagicMock()
        out = SupportTicketScopeStrategy().filter(
            None, _user("WORK_MANAGER", user_id=42), q,
        )
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

    def test_authorize_routes_to_support_ticket_strategy(self):
        svc = AuthorizationService(_DBStub())
        with pytest.raises(HTTPException) as exc:
            svc.authorize(
                _user("WORK_MANAGER", user_id=42),
                resource=_ticket(owner_id=999),
                resource_type="SupportTicket",
            )
        assert exc.value.status_code == 403

    def test_authorize_admin_passes(self):
        svc = AuthorizationService(_DBStub())
        svc.authorize(
            _user("ADMIN", user_id=1),
            resource=_ticket(owner_id=999),
            resource_type="SupportTicket",
        )

    def test_authorize_owner_passes(self):
        svc = AuthorizationService(_DBStub())
        svc.authorize(
            _user("WORK_MANAGER", user_id=42),
            resource=_ticket(owner_id=42),
            resource_type="SupportTicket",
        )


# ===========================================================================
# Coverage for the /comments endpoints — not pinned in the legacy
# permission tests but they share the same ownership rule and now
# go through the same strategy.
# ===========================================================================

class _CommentsDBStub:
    """Hands back a seeded ticket and an empty comments list."""

    def __init__(self, ticket=None, comments=None):
        self._ticket = ticket
        self._comments = comments or []
        self._current_model = None
        self.added = []
        self.committed = False

    def query(self, model):
        self._current_model = getattr(model, "__name__", str(model))
        return self

    def filter(self, *a, **kw):
        return self

    def order_by(self, *a, **kw):
        return self

    def all(self):
        if self._current_model == "SupportTicketComment":
            return self._comments
        return []

    def first(self):
        if self._current_model == "SupportTicket":
            return self._ticket
        return None

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        if not getattr(obj, "id", None):
            obj.id = 999


class TestCommentsScope:

    def test_owner_can_read_comments(self, monkeypatch):
        t = _ticket(owner_id=42)
        db = _CommentsDBStub(ticket=t)
        result = asyncio.run(get_ticket_comments(
            ticket_id=1, db=db, current_user=_user("WORK_MANAGER", user_id=42),
        ))
        assert result == []

    def test_admin_can_read_anyones_comments(self, monkeypatch):
        t = _ticket(owner_id=999)
        db = _CommentsDBStub(ticket=t)
        result = asyncio.run(get_ticket_comments(
            ticket_id=1, db=db, current_user=_user("ADMIN", user_id=1),
        ))
        assert result == []

    def test_non_owner_blocked_from_reading_comments_403(self):
        t = _ticket(owner_id=999)
        db = _CommentsDBStub(ticket=t)
        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_ticket_comments(
                ticket_id=1, db=db, current_user=_user("WORK_MANAGER", user_id=42),
            ))
        assert exc.value.status_code == 403

    def test_owner_can_add_comment(self, monkeypatch):
        t = _ticket(owner_id=42)
        db = _CommentsDBStub(ticket=t)
        monkeypatch.setattr(
            "app.routers.support_tickets.log_support_ticket_replied",
            lambda **kw: None,
        )
        monkeypatch.setattr(
            "app.routers.support_tickets.log_support_ticket_status_changed",
            lambda **kw: None,
        )
        result = asyncio.run(add_ticket_comment(
            ticket_id=1,
            comment=CommentInput(content="hello"),
            db=db,
            current_user=_user("WORK_MANAGER", user_id=42),
        ))
        assert result["user_id"] == 42

    def test_non_owner_blocked_from_adding_comment_403(self):
        t = _ticket(owner_id=999)
        db = _CommentsDBStub(ticket=t)
        with pytest.raises(HTTPException) as exc:
            asyncio.run(add_ticket_comment(
                ticket_id=1,
                comment=CommentInput(content="hijack"),
                db=db,
                current_user=_user("WORK_MANAGER", user_id=42),
            ))
        assert exc.value.status_code == 403

    def test_missing_ticket_returns_404_for_comments_get(self):
        db = _CommentsDBStub(ticket=None)
        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_ticket_comments(
                ticket_id=999, db=db, current_user=_user("ADMIN"),
            ))
        assert exc.value.status_code == 404

    def test_missing_ticket_returns_404_for_comments_post(self):
        db = _CommentsDBStub(ticket=None)
        with pytest.raises(HTTPException) as exc:
            asyncio.run(add_ticket_comment(
                ticket_id=999,
                comment=CommentInput(content="x"),
                db=db,
                current_user=_user("ADMIN"),
            ))
        assert exc.value.status_code == 404
