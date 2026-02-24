# RUNBOOK BACKUP RESTORE

## Backup Policy
- Daily full PostgreSQL backup.
- Pre-release on-demand backup.
- Keep retention according to ops policy.

## Backup Verify
1. Check backup file integrity.
2. Validate restore headers/metadata.

## Restore Drill
1. Restore to staging clone.
2. Validate:
   - auth login works
   - key tables readable
   - critical finance/workflow queries return expected shape

## Emergency Restore
1. Freeze write operations.
2. Restore from approved point.
3. Re-run app health and smoke suite.

