# RUNBOOK INCIDENT

## Severity
- SEV1: Full outage / severe security risk
- SEV2: Major business flow degraded
- SEV3: Partial degradation

## First 15 Minutes
1. Open incident channel.
2. Assign incident commander.
3. Scope impact (users/modules/env).
4. Freeze deployments.
5. Capture evidence (errors/logs/time window).

## Stabilize
1. Apply safest mitigation (restart/scale/rollback).
2. Verify health endpoints and core flows.
3. Communicate status update every 15 minutes.

## Close
1. Confirm recovery with QA/Product.
2. Publish timeline + root cause.
3. Track corrective actions and owners.

