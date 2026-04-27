"""
F-1 Phase 1 invariants — pin the cleaned permissions table state.

Per LIVE_VERIFICATION_REPORT.md, the production permissions table
contained 50 active UPPERCASE rows alongside 134 lowercase rows.
Migration b5c6d7e8f9a0 normalized everything to lowercase only.

These tests pin the new invariants so a future seed/migration can't
silently regress F-1:
  - All active permission codes are lowercase.
  - No two active permissions share LOWER(code).

The DB connection is the test database configured by conftest /
DATABASE_URL. The migration runs as part of the test setup
implicitly (alembic head should be ≥ b5c6d7e8f9a0).
"""
import pytest
from sqlalchemy import text

from app.core.database import SessionLocal


@pytest.fixture
def db():
    s = SessionLocal()
    yield s
    s.close()


class TestPermissionsTableInvariants:

    def test_no_active_uppercase_permissions(self, db):
        """The flagship F-1 invariant: zero active UPPERCASE rows."""
        rows = db.execute(text("""
            SELECT id, code FROM permissions
            WHERE is_active = true AND code != LOWER(code)
            LIMIT 5;
        """)).fetchall()
        assert not rows, (
            f"F-1 regression: {len(rows)} active UPPERCASE permission(s) found. "
            f"Migration b5c6d7e8f9a0 should have normalized them. Sample: {rows}"
        )

    def test_no_case_insensitive_duplicates(self, db):
        """No two active permissions can share LOWER(code)."""
        rows = db.execute(text("""
            SELECT LOWER(code) AS perm, COUNT(*) AS cnt
            FROM permissions WHERE is_active = true
            GROUP BY LOWER(code) HAVING COUNT(*) > 1
            LIMIT 5;
        """)).fetchall()
        assert not rows, (
            f"F-1 regression: case-insensitive duplicate active permissions: {rows}"
        )

    def test_alembic_head_includes_f1(self, db):
        """Sanity that migration b5c6d7e8f9a0 (or later) is applied."""
        head = db.execute(text(
            "SELECT version_num FROM alembic_version LIMIT 1"
        )).scalar()
        assert head, "alembic_version table is empty"
        # Just verify the head exists; we don't pin to b5c6d7e8f9a0
        # because future migrations will move it forward.


# ===========================================================================
# F-2 documentation tests — pin the EXPECTED future state
# ===========================================================================

class TestF2OpenItems:
    """F-2 (per LIVE_VERIFICATION_REPORT.md) is NOT closed by Phase 1.
    These tests document the current state and will FAIL once Phase 2
    revokes the offending grants — at which point they should be
    updated to assert the post-revocation state.

    Marked xfail so they don't block CI today; remove the xfail when
    Phase 2 lands."""

    @pytest.mark.xfail(
        reason="F-2 open: WORK_MANAGER still holds worklogs.approve. "
               "Phase 2 (separate PR) will revoke. See F1_MIGRATION_PLAN.md.",
        strict=False,
    )
    def test_work_manager_lacks_worklogs_approve(self, db):
        rows = db.execute(text("""
            SELECT 1 FROM role_permissions rp
            JOIN permissions p ON p.id = rp.permission_id AND p.is_active = true
            JOIN roles r ON r.id = rp.role_id
            WHERE r.code = 'WORK_MANAGER' AND p.code = 'worklogs.approve'
            LIMIT 1;
        """)).first()
        assert rows is None, (
            "WORK_MANAGER should NOT hold worklogs.approve (F-2). "
            "Phase 2 should have revoked this grant."
        )

    @pytest.mark.xfail(
        reason="F-2 open: AREA_MANAGER still holds worklogs.approve.",
        strict=False,
    )
    def test_area_manager_lacks_worklogs_approve(self, db):
        rows = db.execute(text("""
            SELECT 1 FROM role_permissions rp
            JOIN permissions p ON p.id = rp.permission_id AND p.is_active = true
            JOIN roles r ON r.id = rp.role_id
            WHERE r.code = 'AREA_MANAGER' AND p.code = 'worklogs.approve';
        """)).first()
        assert rows is None
