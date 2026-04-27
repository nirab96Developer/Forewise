"""
Phase 3 Wave 2.6 — production readiness endpoints.

Tests cover:
  GET /health        — light, returns 200 if app is alive
  GET /version       — build/SHA/environment metadata, no secrets
  GET /health/deep   — app + DB + alembic head + version metadata
                       (200 ok, 503 on DB failure)
"""
from datetime import datetime
import re

import pytest
from fastapi.testclient import TestClient

from app.main import app, APP_VERSION, GIT_SHA, BUILD_TIME


@pytest.fixture
def client():
    return TestClient(app)


# ===========================================================================
# /health — light, unauthenticated
# ===========================================================================

class TestHealthLight:

    def test_returns_200(self, client):
        r = client.get("/health")
        assert r.status_code == 200

    def test_returns_status_ok(self, client):
        r = client.get("/health")
        assert r.json()["status"] == "ok"

    def test_returns_version(self, client):
        r = client.get("/health")
        assert r.json()["version"] == APP_VERSION

    def test_returns_environment(self, client):
        r = client.get("/health")
        assert "environment" in r.json()

    def test_returns_iso_timestamp(self, client):
        r = client.get("/health")
        ts = r.json()["timestamp"]
        # ISO 8601 — round-trip parse
        datetime.fromisoformat(ts)

    def test_no_secrets_leak(self, client):
        """Sanity: response should not contain any of the obvious
        secret-looking field names."""
        body = client.get("/health").json()
        flat = " ".join(str(v).lower() for v in body.values())
        for forbidden in ("password", "secret", "token",
                          "postgresql://", "redis://", "dsn"):
            assert forbidden not in flat, f"Found '{forbidden}' in /health"


# ===========================================================================
# /version
# ===========================================================================

class TestVersionEndpoint:

    def test_returns_200(self, client):
        r = client.get("/version")
        assert r.status_code == 200

    def test_returns_app_version(self, client):
        r = client.get("/version")
        assert r.json()["version"] == APP_VERSION

    def test_returns_git_sha(self, client):
        r = client.get("/version")
        sha = r.json()["git_sha"]
        # Either 'unknown' (no git) or a short SHA (7-40 hex chars)
        assert sha == "unknown" or re.match(r"^[0-9a-f]{7,40}$", sha)

    def test_returns_build_time(self, client):
        r = client.get("/version")
        ts = r.json()["build_time"]
        datetime.fromisoformat(ts)
        # Build time should match the module-load time, not request time
        assert ts == BUILD_TIME

    def test_returns_environment(self, client):
        r = client.get("/version")
        assert "environment" in r.json()

    def test_response_shape_stable(self, client):
        """Pin the exact response key set so a future change can't
        accidentally remove/add fields the frontend or ops dashboard
        depends on."""
        r = client.get("/version")
        keys = set(r.json().keys())
        assert keys == {"version", "git_sha", "build_time", "environment"}

    def test_no_secrets_leak(self, client):
        body = client.get("/version").json()
        flat = " ".join(str(v).lower() for v in body.values())
        for forbidden in ("password", "secret", "postgresql://",
                          "redis://", "dsn", "api_key"):
            assert forbidden not in flat, f"Found '{forbidden}' in /version"


# ===========================================================================
# /health/deep
# ===========================================================================

class TestHealthDeep:

    def test_returns_200_when_db_ok(self, client):
        """Default test DB is up — deep health should be 200."""
        r = client.get("/health/deep")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_includes_version_metadata(self, client):
        body = client.get("/health/deep").json()
        assert body["version"] == APP_VERSION
        assert body["git_sha"] == GIT_SHA
        assert body["build_time"] == BUILD_TIME

    def test_includes_app_check(self, client):
        body = client.get("/health/deep").json()
        assert body["checks"]["app"] == "ok"

    def test_includes_database_check(self, client):
        body = client.get("/health/deep").json()
        assert body["checks"]["database"] == "ok"

    def test_includes_alembic_head(self, client):
        """Migration head should be reported (a known revision string)."""
        body = client.get("/health/deep").json()
        head = body["checks"]["alembic_head"]
        # Either None (alembic table missing — unlikely in test DB)
        # or a non-empty revision string.
        assert head is None or (isinstance(head, str) and len(head) > 0)

    def test_returns_503_when_db_down(self, client, monkeypatch):
        """Force DB failure — expect 503 with status='degraded'."""
        from app import main as main_mod

        def boom():
            raise RuntimeError("simulated db outage")

        # get_db() yields a session; replacing it to raise simulates
        # a connection failure cleanly.
        monkeypatch.setattr(main_mod, "get_db", boom)

        r = client.get("/health/deep")
        assert r.status_code == 503
        body = r.json()
        assert body["status"] == "degraded"
        assert body["checks"]["database"] == "error"
        assert "database_error_type" in body["checks"]
        # Still includes version metadata even on failure
        assert body["version"] == APP_VERSION
        # Still no secrets
        assert "postgresql" not in str(body).lower()
        assert "password" not in str(body).lower()

    def test_response_shape_stable(self, client):
        body = client.get("/health/deep").json()
        top_keys = set(body.keys())
        assert top_keys == {
            "status", "timestamp", "version", "git_sha", "build_time",
            "environment", "checks",
        }
        check_keys = set(body["checks"].keys())
        # alembic_head + app + database always present; error_type
        # only on failure.
        assert {"app", "database", "alembic_head"}.issubset(check_keys)

    def test_no_secrets_leak(self, client):
        body = client.get("/health/deep").json()
        flat = str(body).lower()
        for forbidden in ("password", "postgresql://", "redis://",
                          "dsn", "api_key"):
            assert forbidden not in flat
