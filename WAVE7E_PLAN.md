# Wave 7.E — project_assignments Recon

**Generated**: 2026-04-24
**Status**: recon only, awaiting sign-off before any fix

## Surprise finding

The 12 endpoints flagged 🔴 in the matrix are mostly **false positives** —
my extractor only matches inline `require_permission(current_user, "...")`
calls, but `project_assignments.py` uses the FastAPI factory pattern:

```python
@router.put("/{assignment_id}")
def update_assignment(
    ...,
    _: bool = Depends(require_permission("project_assignments.update")),
):
```

That **is** real enforcement — the dependency raises 403 before the handler
runs. So 11 of 12 endpoints are technically already "gated".

## The real bug

**Six** of the permission codes the code calls are **missing from the
DB**:

```
project_assignments.update
project_assignments.complete
project_assignments.transfer
project_assignments.bulk_assign
project_assignments.check_availability
project_assignments.check_conflicts
```

ADMIN bypasses `require_permission` regardless of what's in the DB, so
admin-driven calls work today. Any other role hits a "permission not in
DB" → 403 forever. This is a **silent broken-flow** issue: the moment a
non-admin manager tries to update or complete an assignment, they get
403 with no actionable message.

## Full endpoint table

| # | Method + Path | Code uses | DB has it? | Roles assigned (DB) | UI |
|---|---|---|---|---|---|
| 1 | `GET /project-assignments` | `project_assignments.read` | ✅ | ADMIN, AREA_MANAGER, REGION_MANAGER, WORK_MANAGER | no |
| 2 | `GET /project-assignments/my-assignments` | self-service (current_user.id) | n/a | any auth user, own data only | no |
| 3 | `GET /project-assignments/{id}` | `project_assignments.read` | ✅ | (same as #1) | no |
| 4 | `POST /project-assignments/` | `project_assignments.create` | ✅ | ADMIN, AREA_MANAGER, REGION_MANAGER | yes |
| 5 | `PUT /project-assignments/{id}` | `project_assignments.update` | ❌ **MISSING** | only ADMIN works (bypass) | no |
| 6 | `DELETE /project-assignments/{id}` | `project_assignments.delete` | ✅ | ADMIN, REGION_MANAGER | yes |
| 7 | `PUT /project-assignments/{id}/complete` | `project_assignments.complete` | ❌ **MISSING** | only ADMIN | no |
| 8 | `POST /project-assignments/transfer` | `project_assignments.transfer` | ❌ **MISSING** | only ADMIN | no |
| 9 | `GET /project-assignments/availability/check` | `project_assignments.check_availability` | ❌ **MISSING** | only ADMIN | yes |
| 10 | `GET /project-assignments/conflicts/check` | `project_assignments.check_conflicts` | ❌ **MISSING** | only ADMIN | no |
| 11 | `GET /project-assignments/roles/list` | none (hard-coded enum) | n/a | any auth user — non-sensitive | yes |
| 12 | `POST /project-assignments/project/{id}/bulk-assign` | `project_assignments.bulk_assign` | ❌ **MISSING** | only ADMIN | yes |

## Proposed Wave 7.E.1 — DATA MIGRATION ONLY

Add the six missing perms and assign them per the matrix below. **No
router changes** in this step. Pattern matches Wave 7.A.

| Permission | Roles |
|---|---|
| `project_assignments.update` | ADMIN, REGION_MANAGER (mirror existing `delete`) |
| `project_assignments.complete` | ADMIN, REGION_MANAGER, AREA_MANAGER, WORK_MANAGER |
| `project_assignments.transfer` | ADMIN, REGION_MANAGER (org-wide moves) |
| `project_assignments.bulk_assign` | ADMIN, REGION_MANAGER |
| `project_assignments.check_availability` | ADMIN, REGION_MANAGER, AREA_MANAGER |
| `project_assignments.check_conflicts` | ADMIN, REGION_MANAGER, AREA_MANAGER |

After this migration:
- Every existing `Depends(require_permission(...))` call in the router
  resolves against a real DB row.
- WORK_MANAGER can now actually mark their own project assignment as
  complete (currently 403'd).
- AREA_MANAGER can run availability/conflicts checks (currently 403'd).
- REGION_MANAGER can update/transfer/bulk-assign (currently 403'd).
- The whole thing flips on without a single router edit.

## Proposed Wave 7.E.2 — `/roles/list` decision

Currently authenticated-only. Three options:
1. Leave as-is (it's a static enum, no info leak).
2. Add `Depends(require_permission("project_assignments.read"))`.
3. Make it fully public.

Recommendation: option 1 (no change). `/roles/list` returns 6
hard-coded strings, identical for every caller; locking it down adds
friction without security value.

## NOT in scope for Wave 7.E

- Scope filtering per region/area on `GET /` (currently returns all
  assignments to anyone with `read`). Would be Wave 7.E.3 if needed.
- The pre-existing Wave 7.B (`SystemRate.code`) and Wave 7.D
  (`equipment_category_id`) bugs — separate cleanup task after Wave 7.

## Tests to add (Wave 7.E.1)

- ADMIN, REGION_MANAGER, AREA_MANAGER pass each newly-permitted action.
- A role NOT in the matrix (e.g., SUPPLIER) still gets 403.
- DB query verifies the 6 perms exist with the expected role assignments.

If approved, the migration revision id will be `f2a3b4c5d6e7`
(continues the e1f2a3b4c5d6 chain).
