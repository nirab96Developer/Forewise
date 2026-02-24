# RUNBOOK DEPLOY

## Pre-Deploy
1. Confirm branch/tag and release notes.
2. Ensure DB backup exists.
3. Confirm env vars/secrets availability.

## Deploy
1. Build frontend artifact.
2. Start/refresh stack with `deployment/docker-compose.prod.yml`.
3. Run Alembic migrations to `head`.

## Verification
1. Check `/health`, `/api/v1/health`, `/api/v1/health/db`.
2. Smoke test:
   - login
   - dashboard
   - one work-order flow
   - one finance flow

## Post-Deploy
1. Monitor logs/errors.
2. Mark release as successful.

