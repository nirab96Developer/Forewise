# Wave 7.F — Recon (extractor-improved matrix)

**Generated**: 2026-04-25
**Status**: recon only, no code changes to routes

## What changed in the extractor

`scripts/audit/extract_routes_with_auth.py` now detects the FastAPI
factory pattern in addition to the inline pattern:

```
# Already detected (inline)
require_permission(current_user, "perm.code")

# Newly detected (factory)
_: bool = Depends(require_permission("perm.code"))
```

## Headline numbers

| | Before Wave 7.F | After Wave 7.F |
|---|---|---|
| 🔴 critical | 78 | **64** |
| 🟡 medium | 33 | 33 |
| 🟢 enforced | 307 | **321** |
| Code perms used | 135 | 144 |
| DB perms | 178 | 184 (+6 from 7.E.1) |

**Net 14 endpoints recategorized** from 🔴 → 🟢 by the extractor fix
alone — most of these were Depends-pattern usages that were already
enforced. No router changes needed for that 14.

## Critical-by-domain after extractor fix

| Domain | 🔴 | Real critical | False positives | Notes |
|---|---|---|---|---|
| auth | 15 | **0** | 15 | All self-service via current_user.id (already audited Wave 1.B/1.C) |
| dashboard | 15 | **0–2** | 13–15 | All scope-filtered by role (region/area). Some have inline admin checks. Decide: lock with `dashboard.view` or accept scope-filter as enforcement. |
| notifications | 9 | **5** | 4 | create / bulk-action / cleanup / PUT-update / DELETE need real perm. read/PATCH-read are self-service. |
| pricing | 4 | **3** | 1 | reports + simulate need `pricing.read` or `budgets.read`. compute-cost is auth-only OK. |
| otp | 3 | **1** | 2 | /cleanup is admin. /send + /verify are LOGIN flow — must stay anonymous. |
| support_tickets | 3 | **1–2** | 1–2 | GET list needs scope; POST create can be auth-only (users open own tickets). |
| journal | 3 | **0** | 3 | All `/users/me/journal*` — self-service per path. |
| activity_types | 2 | **0** | 2 | GET / + GET /{id} — public lookup, intentional. |
| supplier_rotations | 1 | **0** | 1 | PATCH wrapper for PUT — already enforced via wrapper. |
| project_assignments | 1 | **0** | 1 | `/roles/list` — hard-coded enum, auth-only intentional. |
| activity_logs | 1 | **0** | 1 | Has `role_code in ("ADMIN","REGION_MANAGER","AREA_MANAGER")` scoping inside. |
| excel_export | 1 | **0** | 1 | Per-type `require_permission` inside (Phase 0 fix). Extractor missed it. |
| work_order_coordination_logs | 1 | **1?** | 0–1 | POST endpoint — verify ownership/role check. |
| sync | 1 | **1?** | 0–1 | POST /sync/batch — used by mobile, verify it scopes to current_user. |

**Real critical estimate: ~13–17 endpoints**, not 64.

## What truly needs `require_permission` (Wave 7.G+ candidate list)

### Notifications (5)
- `POST /notifications` — `notifications.manage` (admin/system)
- `POST /notifications/bulk-action` — `notifications.manage`
- `POST /notifications/cleanup` — `notifications.manage` (already says "admin only" in docstring)
- `PUT /notifications/{id}` — `notifications.manage` (admin/system mutation)
- `DELETE /notifications/{id}` — owner-or-admin (needs ownership helper)

### Notifications self-service that needs ownership verify (4)
These use `current_user.id` but operate on `{notification_id}`. Need
to verify the notification belongs to the user before mark-as-read /
delete.
- `PATCH /notifications/read-all` — operates on current_user, already safe
- `POST /notifications/read-all` — same
- `PATCH /notifications/{id}/read` — needs ownership check
- `POST /notifications/{id}/read` — needs ownership check

### Pricing (3)
- `GET /pricing/reports/by-project` — `budgets.read` (financial)
- `GET /pricing/reports/by-supplier` — same
- `GET /pricing/simulate-days` — auth-only OK or `budgets.read`

### OTP (1)
- `POST /otp/cleanup` — admin (use existing `system.settings`?)

### Support tickets (1–2)
- `GET /support-tickets` — needs scope (creator-only or admin)
- `POST /support-tickets` + `/from-widget` — auth-only (any user can open)

### Edge cases to verify (3)
- `POST /work-order-coordination-logs` — does it need a coordinator role?
- `POST /sync/batch` — does it scope to current_user.id?
- `GET /dashboard/coordinator-queue` — coordinator-only?

## False positives the extractor could still learn

If a future improvement is desired, these patterns are still missed:

1. **Self-service via current_user.id only** (no user_id input from request)
   — affects all 15 auth endpoints. Low value to detect; the matrix
   would shrink but the actual code is already safe.
2. **Scope-filtering by role** (filter Project.region_id by user.region_id,
   not just user_id) — affects all 15 dashboard endpoints.
3. **Per-type require_permission inside the handler** (excel_export pattern).

## Recommended next wave

**Wave 7.G — notifications enforcement** (5 admin perms + 4 ownership
verifies = 9 endpoints). Largest concentration of real work, all in one
router file. Would need:

1. Decide if `notifications.manage` (already added by Wave 7.A) is the
   right perm for create/bulk-action/cleanup/PUT/DELETE, or split into
   `notifications.create` / `notifications.delete` / `notifications.update`.
2. Add ownership helper for the per-id endpoints (model already has
   `user_id`).
3. Add tests covering admin-passes, owner-passes, non-owner-403,
   no-perm-403.

After 7.G:
- Wave 7.H — pricing reports (3 endpoints, 1 perm decision)
- Wave 7.I — support tickets scoping (2–3 endpoints + scope helper)
- Wave 7.J — small edge cases (otp/cleanup, wo-coord-logs, sync, dashboard
  decision)

Cleanup task (separate, after Wave 7 closes):
- SystemRate.code → rate_code (Wave 7.B handler bug)
- supplier_rotation.equipment_category_id → drop from create payload (Wave 7.D handler bug)

## Output (per request format)

| Metric | Value |
|---|---|
| Critical after extractor fix | **64** (was 78) |
| False positives removed automatically | **14** |
| Truly real critical (manual triage) | **~13–17** |
| Domain with most real work | notifications (9 endpoints) |
| Recommended next wave | **Wave 7.G — notifications** |
