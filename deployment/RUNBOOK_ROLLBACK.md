# RUNBOOK ROLLBACK

## Goal
Restore stable service after failed deployment.

## Steps
1. Freeze deployments and announce incident.
2. Identify bad release and previous good release.
3. Redeploy backend/frontend to good release.
4. Verify:
   - `/health`
   - `/api/v1/health`
   - `/api/v1/health/db`
5. Validate login + one critical business write flow.
6. Keep heightened monitoring for 30 minutes.

