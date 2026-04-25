"""
Tests for ownership + scoping on /api/v1/support-tickets/*.

Phase 2 Wave 7.I — support_tickets is intentionally permission-FREE
(any authenticated user opens a ticket about themselves). The two
security promises this wave locks in:

  1. GET /support-tickets is SCOPED:
       - ADMIN sees every ticket
       - any other authenticated user sees only ticket.user_id == current_user.id

  2. POST /support-tickets and POST /support-tickets/from-widget force
     `user_id = current_user.id` regardless of what the request body
     says. A caller can NEVER open a ticket on behalf of another user.

The single-ticket and PUT endpoints already have the standard
admin-or-owner check; lock that in too.
"""
import asyncio
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.routers.support_tickets import (
    create_support_ticket,
    create_ticket_from_widget,
    get_support_ticket,
    get_support_tickets,
    update_support_ticket,
    StepResult,
    ClientContext,
    WidgetTicketCreate,
)
from app.schemas.support_ticket import (
    SupportTicketCreate, SupportTicketUpdate, TicketType, TicketPriority,
)


def _user(role_code: str, *, user_id: int = 1):
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


def _admin():
    return _user("ADMIN")


def _ticket(ticket_id: int = 1, owner_id: int = 1, ticket_number: str = "TKT-202604-0001"):
    t = MagicMock()
    t.id = ticket_id
    t.ticket_number = ticket_number
    t.user_id = owner_id
    t.title = "test"
    t.description = "test"
    t.status = "open"
    t.priority = "normal"
    t.category = "general"
    t.created_at = datetime.utcnow()
    t.updated_at = datetime.utcnow()
    t.is_active = True
    return t


class _DBStub:
    """Minimal session for support_tickets handlers."""

    def __init__(self, ticket=None, listed_tickets=None):
        self._ticket = ticket
        self._listed = listed_tickets or []
        self._current_model = None
        self.committed = False
        self._added = []

    def query(self, model):
        self._current_model = getattr(model, "__name__", str(model))
        return self

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *a, **kw):
        return self

    def offset(self, *a, **kw):
        return self

    def limit(self, *a, **kw):
        return self

    def join(self, *a, **kw):
        return self

    def first(self):
        if self._current_model == "SupportTicket":
            return self._ticket
        if self._current_model == "User":
            return _user("WORK_MANAGER")
        return None

    def all(self):
        if self._current_model == "SupportTicket":
            return self._listed
        if self._current_model == "User":
            return [_user("ADMIN")]  # for _notify_admins_new_ticket
        return []

    def add(self, obj):
        self._added.append(obj)

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        # Simulate the DB filling in id+ticket_number+timestamps
        if not getattr(obj, "id", None):
            obj.id = 999
        if not getattr(obj, "ticket_number", None):
            obj.ticket_number = "TKT-NEW"
        if not getattr(obj, "created_at", None):
            obj.created_at = datetime.utcnow()

    def scalar(self):
        return 0  # _generate_ticket_number count

    def execute(self, *a, **kw):
        cursor = MagicMock()
        cursor.scalar.return_value = 0
        return cursor


def _bg_tasks():
    bg = MagicMock()
    bg.add_task = MagicMock()
    return bg


# ===========================================================================
# Wave 7.I — GET / scoping
# ===========================================================================

class TestListScoping:

    def test_admin_sees_all(self):
        # Two tickets, owned by different users; admin should see both
        t1 = _ticket(ticket_id=1, owner_id=42)
        t2 = _ticket(ticket_id=2, owner_id=99)
        db = _DBStub(listed_tickets=[t1, t2])
        result = asyncio.run(get_support_tickets(
            skip=0, limit=100, page=1,
            status_filter=None, priority=None, category=None,
            db=db, current_user=_admin(),
        ))
        assert len(result) == 2

    def test_non_admin_query_filters_by_user_id(self, monkeypatch):
        """Verify the QUERY layer applies the user_id filter for non-admin.

        We can't easily inspect the SQLAlchemy WHERE from the stub, but
        we can monkeypatch the filter to capture what gets called.
        """
        captured_filters = []
        original_filter = _DBStub.filter

        def spy_filter(self, *args, **kwargs):
            captured_filters.append(args)
            return original_filter(self, *args, **kwargs)

        monkeypatch.setattr(_DBStub, "filter", spy_filter)

        db = _DBStub(listed_tickets=[])
        u = _user("WORK_MANAGER", user_id=42)
        asyncio.run(get_support_tickets(
            skip=0, limit=100, page=1,
            status_filter=None, priority=None, category=None,
            db=db, current_user=u,
        ))
        # Last filter() call should be the user_id == current_user.id one
        flat = " ".join(str(a) for args in captured_filters for a in args)
        assert "user_id" in flat or "SupportTicket.user_id" in flat


# ===========================================================================
# Wave 7.I — single-ticket admin-or-owner
# ===========================================================================

class TestSingleTicketAccess:

    def test_owner_can_read(self):
        t = _ticket(owner_id=42)
        db = _DBStub(ticket=t)
        result = asyncio.run(get_support_ticket(
            ticket_id=1, db=db, current_user=_user("WORK_MANAGER", user_id=42),
        ))
        assert result is t

    def test_admin_can_read_others(self):
        t = _ticket(owner_id=999)
        db = _DBStub(ticket=t)
        result = asyncio.run(get_support_ticket(
            ticket_id=1, db=db, current_user=_admin(),
        ))
        assert result is t

    def test_non_owner_403(self):
        t = _ticket(owner_id=999)
        db = _DBStub(ticket=t)
        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_support_ticket(
                ticket_id=1, db=db, current_user=_user("WORK_MANAGER", user_id=42),
            ))
        assert exc.value.status_code == 403

    def test_missing_404(self):
        db = _DBStub(ticket=None)
        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_support_ticket(
                ticket_id=999, db=db, current_user=_admin(),
            ))
        assert exc.value.status_code == 404


# ===========================================================================
# Wave 7.I — POST forces user_id from current_user
# ===========================================================================

class TestCreateForcesUserId:

    def test_create_uses_current_user_id_even_when_body_says_otherwise(self, monkeypatch):
        """Critical: caller sends user_id=999 in body; ticket must be
        created with user_id == current_user.id (42), not 999."""
        # Stub out activity logger + notification helpers
        monkeypatch.setattr(
            "app.routers.support_tickets.log_support_ticket_created",
            lambda **kw: None,
        )
        monkeypatch.setattr(
            "app.routers.support_tickets._notify_admins_new_ticket",
            lambda *a, **kw: None,
        )

        db = _DBStub()
        bg = _bg_tasks()
        owner = _user("WORK_MANAGER", user_id=42)
        body = SupportTicketCreate(
            user_id=999,  # caller tries to spoof
            title="t",
            description="d",
            type=TicketType.OTHER,
            priority=TicketPriority.NORMAL,
        )
        asyncio.run(create_support_ticket(
            ticket=body, background_tasks=bg, db=db, current_user=owner,
        ))
        # Inspect what was added
        assert len(db._added) == 1
        new_ticket = db._added[0]
        assert new_ticket.user_id == 42, (
            f"Expected user_id=42 (current_user), got {new_ticket.user_id}. "
            "Body field user_id MUST NOT be honored."
        )
        assert new_ticket.created_by_id == 42

    def test_create_omitting_user_id_works(self, monkeypatch):
        """Wave 7.I made user_id Optional in the schema. A caller that
        omits it entirely must still get a ticket created for themselves."""
        monkeypatch.setattr(
            "app.routers.support_tickets.log_support_ticket_created",
            lambda **kw: None,
        )
        monkeypatch.setattr(
            "app.routers.support_tickets._notify_admins_new_ticket",
            lambda *a, **kw: None,
        )

        db = _DBStub()
        bg = _bg_tasks()
        owner = _user("WORK_MANAGER", user_id=42)
        body = SupportTicketCreate(
            title="t",
            description="d",
            type=TicketType.OTHER,
            priority=TicketPriority.NORMAL,
        )
        asyncio.run(create_support_ticket(
            ticket=body, background_tasks=bg, db=db, current_user=owner,
        ))
        assert db._added[0].user_id == 42


# ===========================================================================
# Wave 7.I — widget endpoint also forces user_id
# ===========================================================================

class TestWidgetCreateForcesUserId:

    def test_widget_ignores_userId_in_payload(self, monkeypatch):
        monkeypatch.setattr(
            "app.routers.support_tickets.log_support_ticket_created",
            lambda **kw: None,
        )
        monkeypatch.setattr(
            "app.routers.support_tickets._notify_admins_new_ticket",
            lambda *a, **kw: None,
        )

        db = _DBStub()
        bg = _bg_tasks()
        owner = _user("WORK_MANAGER", user_id=42)
        widget_payload = WidgetTicketCreate(
            userId="999",  # caller tries to spoof
            userName="Imposter",
            userRole="ADMIN",
            currentRoute="/some-page",
            category="GENERAL",
            stepsWalked=[],
            userMessage="help",
            clientContext=ClientContext(
                url="http://x", browser="ua", resolution="1080p", timestamp="now",
            ),
        )
        asyncio.run(create_ticket_from_widget(
            data=widget_payload, background_tasks=bg, db=db, current_user=owner,
        ))
        assert len(db._added) == 1
        assert db._added[0].user_id == 42


# ===========================================================================
# Wave 7.I — PUT (update) admin-or-owner
# ===========================================================================

class TestUpdateAccess:

    def test_owner_can_update(self):
        t = _ticket(owner_id=42)
        db = _DBStub(ticket=t)
        result = asyncio.run(update_support_ticket(
            ticket_id=1,
            ticket=SupportTicketUpdate(title="updated"),
            db=db,
            current_user=_user("WORK_MANAGER", user_id=42),
        ))
        assert result is t

    def test_admin_can_update_others(self):
        t = _ticket(owner_id=999)
        db = _DBStub(ticket=t)
        result = asyncio.run(update_support_ticket(
            ticket_id=1,
            ticket=SupportTicketUpdate(status="resolved"),
            db=db,
            current_user=_admin(),
        ))
        assert result is t

    def test_non_owner_403(self):
        t = _ticket(owner_id=999)
        db = _DBStub(ticket=t)
        with pytest.raises(HTTPException) as exc:
            asyncio.run(update_support_ticket(
                ticket_id=1,
                ticket=SupportTicketUpdate(title="hijack"),
                db=db,
                current_user=_user("WORK_MANAGER", user_id=42),
            ))
        assert exc.value.status_code == 403
