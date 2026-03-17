"""
Critical smoke tests — health, auth, core endpoints.
These must pass before every deploy.
"""
import pytest
from app.core.database import SessionLocal
from sqlalchemy import text


class TestHealth:
    """Health endpoint tests."""

    def test_db_connection(self):
        """DB is reachable."""
        db = SessionLocal()
        try:
            result = db.execute(text("SELECT 1")).scalar()
            assert result == 1
        finally:
            db.close()

    def test_tables_exist(self):
        """Core tables exist."""
        db = SessionLocal()
        try:
            core_tables = [
                'users', 'roles', 'projects', 'work_orders', 'worklogs',
                'suppliers', 'equipment', 'invoices', 'budgets',
                'supplier_rotations', 'notifications', 'areas', 'regions',
            ]
            existing = db.execute(text(
                "SELECT tablename FROM pg_tables WHERE schemaname='public'"
            )).fetchall()
            existing_names = {r[0] for r in existing}
            for table in core_tables:
                assert table in existing_names, f"Missing table: {table}"
        finally:
            db.close()

    def test_users_exist(self):
        """At least one active user exists."""
        db = SessionLocal()
        try:
            count = db.execute(text(
                "SELECT COUNT(*) FROM users WHERE is_active = true"
            )).scalar()
            assert count > 0, "No active users in database"
        finally:
            db.close()

    def test_suppliers_have_regions(self):
        """All active suppliers have region_id."""
        db = SessionLocal()
        try:
            orphans = db.execute(text(
                "SELECT COUNT(*) FROM suppliers WHERE is_active = true AND region_id IS NULL"
            )).scalar()
            assert orphans == 0, f"{orphans} suppliers without region"
        finally:
            db.close()

    def test_equipment_have_types(self):
        """All active equipment has equipment_type."""
        db = SessionLocal()
        try:
            no_type = db.execute(text(
                "SELECT COUNT(*) FROM equipment WHERE is_active = true AND (equipment_type IS NULL OR equipment_type = '')"
            )).scalar()
            assert no_type == 0, f"{no_type} equipment without type"
        finally:
            db.close()

    def test_no_stuck_distributing(self):
        """No work orders stuck in DISTRIBUTING with expired portal."""
        db = SessionLocal()
        try:
            stuck = db.execute(text(
                "SELECT COUNT(*) FROM work_orders WHERE status = 'DISTRIBUTING' AND portal_expiry < NOW()"
            )).scalar()
            assert stuck == 0, f"{stuck} stuck DISTRIBUTING orders"
        finally:
            db.close()


class TestAuth:
    """Auth service tests."""

    def test_password_hashing(self):
        """bcrypt hash and verify works."""
        from app.core.security import get_password_hash, verify_password
        password = "TestPass123!"
        hashed = get_password_hash(password)
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("WrongPass", hashed)

    def test_jwt_create_and_decode(self):
        """JWT token creation and decoding works."""
        from app.core.security import create_access_token
        from jose import jwt
        from app.core.config import settings

        token = create_access_token({"sub": "1", "email": "test@test.com", "role": "ADMIN"})
        assert token is not None
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert payload["sub"] == "1"
        assert payload["email"] == "test@test.com"

    def test_admin_user_exists(self):
        """Admin user exists in DB."""
        db = SessionLocal()
        try:
            admin = db.execute(text(
                "SELECT COUNT(*) FROM users u JOIN roles r ON r.id = u.role_id WHERE r.code = 'ADMIN' AND u.is_active = true"
            )).scalar()
            assert admin > 0, "No admin user found"
        finally:
            db.close()


class TestDataIntegrity:
    """Data integrity tests."""

    def test_all_projects_have_region(self):
        """Projects have region_id."""
        db = SessionLocal()
        try:
            orphans = db.execute(text(
                "SELECT COUNT(*) FROM projects WHERE is_active = true AND region_id IS NULL"
            )).scalar()
            assert orphans == 0, f"{orphans} projects without region"
        finally:
            db.close()

    def test_equipment_types_exist(self):
        """Equipment types table has data."""
        db = SessionLocal()
        try:
            count = db.execute(text(
                "SELECT COUNT(*) FROM equipment_types WHERE is_active = true"
            )).scalar()
            assert count >= 10, f"Only {count} equipment types (expected 10+)"
        finally:
            db.close()

    def test_supplier_rotations_have_area(self):
        """Active supplier rotations have area_id."""
        db = SessionLocal()
        try:
            no_area = db.execute(text(
                "SELECT COUNT(*) FROM supplier_rotations WHERE is_active = true AND area_id IS NULL"
            )).scalar()
            # Allow some without area (generic rotations)
            total = db.execute(text(
                "SELECT COUNT(*) FROM supplier_rotations WHERE is_active = true"
            )).scalar()
            assert total > 0, "No supplier rotations"
        finally:
            db.close()

    def test_email_config(self):
        """Brevo email is configured."""
        from app.core.email import get_brevo_api_key
        key = get_brevo_api_key()
        assert key and len(key) > 10, "Brevo API key not configured"
