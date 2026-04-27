# F-1 / F-2 Migration Plan — Permissions Cleanup

**Status**: plan only. Awaiting approval before code changes.

---

## The data we're working with

After querying production:

| Bucket | Count | Examples |
|---|---|---|
| Active lowercase permissions | 134 | `worklogs.read`, `dashboard.view` (which is missing!), … |
| Active **UPPERCASE** permissions | 50 | `WORKLOGS.APPROVE`, `DASHBOARD.VIEW`, `WORK_ORDERS.UPDATE`, … |
| **HAS_TWIN UPPERCASE** (uppercase has a lowercase counterpart) | 15 | `BUDGETS.CREATE` ↔ `budgets.create`, etc. |
| **NO_TWIN UPPERCASE** (uppercase only — no lowercase row) | 35 | `DASHBOARD.VIEW`, `WORKLOGS.APPROVE`, `EQUIPMENT.VIEW`, … |

Roles holding UPPERCASE perms (today, all 7 do):
ACCOUNTANT 13 · ADMIN 50 · AREA_MANAGER 22 · ORDER_COORDINATOR 13 ·
REGION_MANAGER 24 · SUPPLIER 7 · WORK_MANAGER 15

---

## Why F-1 and F-2 split into 2 PRs

If we deactivate every UPPERCASE perm in one PR:
- **35 NO_TWIN UPPERCASE perms have no lowercase replacement**.
- Code paths use the lowercase string (e.g. `_dashboard_view → require_permission("dashboard.view")`). Today they pass thanks to case-insensitive matching against `DASHBOARD.VIEW`.
- After deactivation: **every non-admin role loses dashboard access**, equipment view, projects view, work orders view, etc. ~25+ critical flows break.

Doing it in one PR mixes two concerns:
- **Data hygiene** — no concrete policy change.
- **Policy revocations** — "WORK_MANAGER shouldn't have worklogs.approve" — concrete policy change.

The user spec says "רק לנקות DATA, לא להוסיף הרשאות חדשות". The cleanest read is: do the data cleanup first, **then** make policy revocations as a separate, audited change.

---

## Phase 1 (this PR) — Pure case normalization

### What it does
- For each **HAS_TWIN UPPERCASE** perm (15):
  - Pre-merge: copy any role grants from the uppercase row into the lowercase row (avoiding duplicates).
  - Deactivate the uppercase row (`is_active = false`).
- For each **NO_TWIN UPPERCASE** perm (35):
  - Rename `code` from `UPPERCASE.FORM` → `lowercase.form` in place.
  - All role grants stay attached (no movement needed).

### After Phase 1
- ✅ Zero active UPPERCASE permissions in DB.
- ✅ Zero case-insensitive duplicates.
- ✅ **Every role's effective access is identical** to today (because case-insensitive matching already counted UPPERCASE → lowercase before).
- ✅ PERMISSIONS_MATRIX.md becomes accurate for the first time.
- ✅ F-1 (data hygiene) **CLOSED**.
- ⚠️ F-2 (WORK_MGR can call `/worklogs/X/approve`) **NOT CLOSED** — `WORKLOGS.APPROVE` is now `worklogs.approve` and WORK_MGR still holds it. But it's now visible in the matrix instead of hidden.

### Tests added
1. `permissions.code = LOWER(permissions.code)` for every active row.
2. No two active permissions share `LOWER(code)`.
3. For each role, `set(p.code FOR p IN role.perms)` is unchanged before vs after migration (preserves access).
4. Migration is **idempotent** (running twice is a no-op).

### Risks
- **Low** — preserves effective access exactly. Code paths continue to work.
- The pre-merge step on HAS_TWIN handles the corner case where some role had uppercase but not lowercase. Without pre-merge, that role would lose access.

---

## Phase 2 (separate PR, after Phase 1) — Policy revocations

### What it does (proposal)
For each lowercase perm where the documented policy says "no non-admin role should have it" (per PERMISSIONS_MATRIX.md's `=MISSING_IN_DB` annotations), REVOKE the grant from non-admin roles.

Concrete example for `worklogs.approve`:
```sql
DELETE FROM role_permissions
WHERE permission_id = (SELECT id FROM permissions WHERE code = 'worklogs.approve')
  AND role_id IN (SELECT id FROM roles WHERE code IN
    ('WORK_MANAGER','AREA_MANAGER','REGION_MANAGER','ACCOUNTANT','ORDER_COORDINATOR','SUPPLIER'));
```

### Why a separate PR
- Each revocation is a **policy decision** that needs:
  - Product owner sign-off (does WORK_MGR really not need to approve?)
  - A note in the PR body explaining intent
  - A regression test pinning the new policy
- Lumping 30+ revocations into one PR makes review impossible and risk huge.

### Per-perm proposal (for the Phase 2 PR)
After Phase 1, the lowercase perms involved would be:

| Perm | Currently granted to (non-admin) | Proposed action |
|---|---|---|
| `worklogs.approve` | WORK_MGR, AREA_MGR, REGION_MGR, ACCOUNTANT | Revoke from all (admin-only via require_permission bypass) |
| `worklogs.create` | SUPPLIER, AREA_MGR, REGION_MGR | Keep for SUPPLIER (they create); revoke from others |
| `worklogs.update` | SUPPLIER, AREA_MGR, REGION_MGR | Same |
| `worklogs.view` | many roles | **Keep** (this is the read perm) |
| `work_orders.update` | many | Audit per role |
| `work_orders.delete` | ADMIN only | OK |
| `dashboard.view` | all except SUPPLIER | OK |
| ... | | |

This per-perm decision matrix needs ~half a day of product review. Not part of Phase 1.

---

## Backup plan

Before running Phase 1 migration:
1. `pg_dump` of `permissions` and `role_permissions` tables → timestamped file in `/root/forewise/backups/`.
2. Migration is wrapped in a transaction — full rollback if any assertion fails.
3. Post-migration verification queries embedded in the migration's `assert` block.

---

## Asks for approval (before I write code)

1. **Approve Phase 1 plan?** (case normalization only, preserves effective access, closes F-1)
2. **Approve Phase 2 as a follow-up PR?** (revocations after audit)
3. **Backup approach OK?** (pg_dump to local file)
4. **Test set OK?** (idempotency + case-clean + per-role-set-unchanged + WORK_MGR specific case)

If yes to all four, I'll start coding Phase 1 immediately.
