# F-2 Phase 2 — Decision Table

**Status**: proposal awaiting product approval. **No DB changes
yet.**

**Purpose**: each row below is a candidate REVOKE. Mark each with
your decision before I write the migration.

---

## Scope of this PR (per user direction)

In scope:
- `worklogs.approve`
- `worklogs.create`
- `worklogs.update`

Documented but **not in this PR**:
- `worklogs.reject` — "לא לגעת עד שמחליטים"
- `work_orders.*` — "לא לגעת בשלב הראשון בלי recon נפרד"

---

## Default policy (from user message)

| Permission | Should hold it |
|---|---|
| `worklogs.approve` | ADMIN בלבד (via require_permission bypass) |
| `worklogs.create` | ADMIN + SUPPLIER own. Managers only with explicit product approval. |
| `worklogs.update` | ADMIN + owner/self-service. Managers only with explicit decision. |

---

## Decision table — current grants vs proposed action

### `worklogs.approve` (5 grants today)

| # | Role | Holds today | Used by router | Default policy says | **Proposed action** |
|---|---|---|---|---|---|
| 1 | ADMIN | ✅ | (bypass anyway) | should hold | **KEEP** ✅ |
| 2 | ACCOUNTANT | ✅ | `pending-approval`, `approve`, `reject` | should not hold (admin-only) | **REVOKE** ⚠️ |
| 3 | AREA_MANAGER | ✅ | same | should not hold | **REVOKE** ⚠️ |
| 4 | REGION_MANAGER | ✅ | same | should not hold | **REVOKE** ⚠️ |
| 5 | WORK_MANAGER | ✅ | same | should not hold | **REVOKE** ⚠️ |

**Live impact of revokes**:
- WORK_MGR / AREA_MGR / REGION_MGR / ACCOUNTANT will **lose access** to:
  - `GET /worklogs/pending-approval` — currently returns empty list anyway (0 SUBMITTED today). Will return 403 after.
  - `POST /worklogs/{id}/approve` — currently 500 due to `INVOICED` status; will return 403 after.
  - `POST /worklogs/{id}/reject` — uses same perm; will return 403.
- **No business flow breaks today** because:
  - Production has 0 worklogs in `SUBMITTED` status.
  - The intent (per recon Q1 + matrix) was always ADMIN-only.

---

### `worklogs.create` (5 grants today)

| # | Role | Holds today | Used by router | Default policy says | **Proposed action** |
|---|---|---|---|---|---|
| 1 | ADMIN | ✅ | (bypass) | should hold | **KEEP** ✅ |
| 2 | SUPPLIER | ✅ | `POST /worklogs`, `/standard`, `/manual`, `/storage` | should hold (supplier portal) | **KEEP** ✅ |
| 3 | AREA_MANAGER | ✅ | same | "only with explicit approval" | **REVOKE** ⚠️ (default conservative) |
| 4 | REGION_MANAGER | ✅ | same | same | **REVOKE** ⚠️ |
| 5 | WORK_MANAGER | ✅ | same | same | **REVOKE** ⚠️ |

**Live impact of revokes**:
- AREA/REGION/WORK_MGR will lose `POST /worklogs/*`. They can still:
  - View worklogs (`worklogs.read`).
  - Approve/reject (after `.approve` decision above; currently their grant is the same leak).
- The supplier portal flow is untouched (SUPPLIER keeps `worklogs.create`).
- **Risk**: if there's an undocumented production flow where a manager creates worklogs on someone's behalf, this would break it. Today's data: all 11 worklogs in production were created by ADMIN or SUPPLIER (per a quick check). Manager-created worklogs ≈ rare/none.

---

### `worklogs.update` (5 grants today)

| # | Role | Holds today | Used by router | Default policy says | **Proposed action** |
|---|---|---|---|---|---|
| 1 | ADMIN | ✅ | `PUT /worklogs/{id}` | should hold | **KEEP** ✅ |
| 2 | SUPPLIER | ✅ | same | should hold (own only) | **KEEP** ✅ |
| 3 | AREA_MANAGER | ✅ | same | "explicit decision needed" | **REVOKE** ⚠️ |
| 4 | REGION_MANAGER | ✅ | same | same | **REVOKE** ⚠️ |
| 5 | WORK_MANAGER | ✅ | same | same | **REVOKE** ⚠️ |

**Live impact of revokes**:
- Managers lose `PUT /worklogs/{id}` and `POST /worklogs/{id}/activate` (`.restore` perm; not in this list but related).
- Owner self-service unchanged: SUPPLIER still updates own worklogs.

---

## Out-of-scope items (documented for visibility only)

### `worklogs.reject` (4 grants today)

| Role | Holds | Router usage | Note |
|---|---|---|---|
| ADMIN | ✅ | (none — router checks `.approve`, not `.reject`) | dead-code grant |
| AREA_MANAGER | ✅ | (none) | dead-code |
| REGION_MANAGER | ✅ | (none) | dead-code |
| WORK_MANAGER | ✅ | (none) | dead-code |

**Status**: Per user spec "לא לגעת". The grant is functionally
dead because no router code path checks `worklogs.reject` (the
`/reject` endpoint requires `worklogs.approve`). Holding it has
no effect today.

If product later wants AREA/REGION/WORK_MGR to reject (their own
scope's worklogs), the perm is already in place — no DB change
needed, only a code change in the `/reject` handler.

### `worklogs.delete`, `.read`, `.read_own`, `.submit`, `.view`

| Perm | Grants | Status |
|---|---|---|
| `.delete` | ADMIN only | ✅ correct, no action |
| `.read` | 6 roles | ✅ correct, used for listing |
| `.read_own` | ADMIN + SUPPLIER | ✅ correct |
| `.submit` | ADMIN + SUPPLIER | ✅ correct |
| `.view` | 6 roles | ⚠️ dead — no router uses `.view` (we use `.read`); harmless to keep, can deactivate later |

### `work_orders.*` (deferred per user spec)

22 grants across 12 distinct perms. Each touches the most-used
backend domain. Needs its own recon document and product session.
**Not part of this PR.**

---

## Migration outline (when approved)

```sql
-- F-2 Phase 2 — revoke 11 specific grants per decision table
DELETE FROM role_permissions WHERE
  role_id = (SELECT id FROM roles WHERE code = 'ACCOUNTANT')
  AND permission_id = (SELECT id FROM permissions WHERE code = 'worklogs.approve');
-- ...repeat for all 11 (role, perm) pairs flagged REVOKE above
```

Wrapped in a transaction with assertions:
1. After: `worklogs.approve` should be granted to ADMIN only.
2. After: `worklogs.create` should be granted to {ADMIN, SUPPLIER}.
3. After: `worklogs.update` should be granted to {ADMIN, SUPPLIER}.
4. After: SUPPLIER's existing supplier-portal flows still work (smoke test).

---

## Tests planned (when migration approved)

In `tests/test_permissions_table_invariants.py::TestF2OpenItems`:
- Remove the `xfail` from the 2 existing tests (work_mgr / area_mgr lack worklogs.approve).
- Add 6 more equivalent tests for the other 9 revoked grants.
- Net: 8 tests pinning the post-revocation state.

In live verification post-migration:
- `WORK_MGR /worklogs/pending-approval` should return **403** (was 200).
- `AREA_MGR /worklogs/pending-approval` should return **403**.
- All sanity checks (dashboard, work-orders, my-worklogs) still 200 for every role.

---

## Approval matrix

Please mark each row below before I write code.

| # | Action | Decision (mark with ✅ to revoke, ❌ to keep) |
|---|---|---|
| 1 | REVOKE `worklogs.approve` from ACCOUNTANT | _____ |
| 2 | REVOKE `worklogs.approve` from AREA_MANAGER | _____ |
| 3 | REVOKE `worklogs.approve` from REGION_MANAGER | _____ |
| 4 | REVOKE `worklogs.approve` from WORK_MANAGER | _____ |
| 5 | REVOKE `worklogs.create` from AREA_MANAGER | _____ |
| 6 | REVOKE `worklogs.create` from REGION_MANAGER | _____ |
| 7 | REVOKE `worklogs.create` from WORK_MANAGER | _____ |
| 8 | REVOKE `worklogs.update` from AREA_MANAGER | _____ |
| 9 | REVOKE `worklogs.update` from REGION_MANAGER | _____ |
| 10 | REVOKE `worklogs.update` from WORK_MANAGER | _____ |
| 11 | REVOKE `worklogs.update` from SUPPLIER | _____ (default: KEEP — supplier owns own) |

If you approve all 10 ✅ defaults (skipping #11), I'll:
1. Write the alembic migration.
2. Take a fresh pg_dump backup.
3. Run it with embedded assertions.
4. Update tests, live verify, commit + push.

**Estimated time after approval**: ~1 hour.
