# Rollback Runbook

## Goal
Restore service quickly after a failed deployment while preserving data integrity.

## Scope
- Backend application rollback
- Frontend rollback
- Database migration rollback decision path

## Preconditions
- Last known good release artifact is available.
- Team has deployment access.
- Database backup exists for current release window.

## Procedure

1. Declare incident and freeze new deployments.
2. Identify failed release version (`bad_release`) and previous stable (`good_release`).
3. Roll back application artifacts:
   - Backend: redeploy `good_release` image/code.
   - Frontend: redeploy `good_release` static bundle.
4. Verify service health:
   - `/health`
   - `/api/v1/health`
   - `/api/v1/health/db`
5. Validate critical business paths:
   - auth login
   - dashboard load
   - one read + one write flow
6. Announce status and monitor logs/alerts for 30 minutes.

## Database Rollback Decision

- If failed release includes non-breaking migrations that are backward-compatible:
  - prefer application rollback only.
- If migration is breaking and blocks service:
  - execute approved DB rollback plan (only if downgrade tested).

## Safety Rules
- Never run destructive DB commands without explicit approval.
- Prefer point-in-time restore only if logical rollback cannot recover.

## Post-Rollback

- Open RCA ticket.
- Record exact command history and timestamps.
- Add preventive action for next release gate.

