# Phase 3 — Wave 1.3 Recon: Work Orders write endpoints

**Goal**: extend Wave 1.2's scope strategy from list/detail to the rest of work_orders
write/state-machine endpoints — close any list-vs-detail style gaps that still exist
on `update / approve / reject / cancel / close / delete / scan-equipment / etc.`

**Scope of this recon**: backend only. Frontend untouched (per user direction).
DB unchanged.

---

## 1. Endpoint inventory & current state

### 1.1 Already migrated in Wave 1.2 (don't touch again)

| # | Endpoint | Method | DB perm used | Status |
|---|---|---|---|---|
| 1 | `/work-orders` | GET | `work_orders.read` | ✅ migrated (post-hoc filter for REGION/WORK; SUPPLIER blocked) |
| 2 | `/work-orders/{id}` | GET | `work_orders.read` | ✅ migrated (`AuthorizationService.authorize`, leak closed) |

---

### 1.2 Endpoints to migrate in Wave 1.3 (write & state machine)

Legend for **Current scope**:
- ❌ — `require_permission` only, no per-resource scope check (LEAK candidate)
- 🔒 — also wrapped by `_require_order_coordinator_or_admin` (queue role)
- ✅ — already has scope logic

| # | Endpoint | Method | DB perm | Coord-only? | Current scope on resource | Roles in DB granted | Risk | Action |
|---|---|---|---|---|---|---|---|---|
| 3 | `/work-orders` | POST `create` | `work_orders.create` | NO | ❌ none | only those with `work_orders.create` (today: not seeded — matrix gap) | Med | **Migrate**: validate project scope before create (REGION/AREA/WORK) |
| 4 | `/work-orders/{id}` | PUT/PATCH `update` | `work_orders.update` | NO | ❌ none | ADMIN, COORDINATOR, AREA_MGR, REGION_MGR, WORK_MGR | **HIGH** — AREA_MGR can edit a WO outside their area | **Migrate** |
| 5 | `/work-orders/{id}/approve` | POST/PATCH | `work_orders.approve` | 🔒 YES | ❌ | ADMIN, COORDINATOR, AREA_MGR (DB), REGION_MGR (DB), WORK_MGR (DB) | Low (queue blocks non-coord) but DB grants are misleading | **Migrate (no behavior change)** + flag DB cleanup later |
| 6 | `/work-orders/{id}/reject` | POST/PATCH | `work_orders.approve` | 🔒 YES | ❌ | same as approve | Low (same) | **Migrate (no behavior change)** |
| 7 | `/work-orders/{id}/start` | POST/PATCH | `work_orders.update` | NO | ❌ | ADMIN, COORDINATOR, AREA_MGR, REGION_MGR, WORK_MGR | **HIGH** — WORK_MGR could start a WO not in their assignments | **Migrate** |
| 8 | `/work-orders/{id}/complete` (= `/close`) | POST/PATCH | `work_orders.close` | NO | ❌ | not seeded today | **HIGH** if granted | **Migrate** |
| 9 | `/work-orders/{id}/cancel` | POST | `work_orders.cancel` | NO | ❌ | not seeded today | **HIGH** if granted | **Migrate** |
| 10 | `/work-orders/{id}` | DELETE | `work_orders.delete` | NO | ❌ | ADMIN only (today) | Low (admin global) | **Migrate (defense in depth)** |
| 11 | `/work-orders/{id}/scan-equipment` | POST | `work_orders.read` | NO | ❌ | most roles | **HIGH** — WORK_MGR could scan a WO not in their assignments | **Migrate** |
| 12 | `/work-orders/{id}/confirm-equipment` | POST | `work_orders.update` | NO | ❌ | many | **HIGH** — same | **Migrate** |
| 13 | `/work-orders/{id}/remove-equipment` | POST | `work_orders.update` | NO | ❌ | many | **HIGH** — same | **Migrate** |
| 14 | `/work-orders/{id}/pdf` | GET | `work_orders.read` | NO | ❌ | almost everyone | Med — info disclosure of finance fields | **Migrate** |

### 1.3 Endpoints to LEAVE AS-IS in this wave

| # | Endpoint | Method | Why no migration |
|---|---|---|---|
| 15 | `/work-orders/statistics` | GET | Aggregate-only, no row-level identity. Already gated by `work_orders.read`. Defer to a "stats-by-scope" feature wave. |
| 16 | `/work-orders/preview-allocation` | POST | No persisted resource — runs the rotation simulator for a project_id passed in. Coordinator-or-admin perm via `work_orders.create` is enough. |
| 17 | `/work-orders/{id}/restore` | POST | `work_orders.restore` is admin-only by perm matrix; already implicitly admin-global. Adding scope is cosmetic. Track as "nice to have". |
| 18 | `/work-orders/{id}/admin-override-equipment` | POST | Hard-coded `role.code in ('ADMIN','SUPER_ADMIN')`. By definition global. No scope check needed. |
| 19 | `/work-orders/{id}/send-to-supplier` | POST | `_require_order_coordinator_or_admin` already restricts to global roles. They see everything by policy → scope `authorize` would be a no-op. Keep simple. |
| 20 | `/work-orders/{id}/move-to-next-supplier` | POST | Same — coordinator/admin only. |
| 21 | `/work-orders/{id}/resend-to-supplier` | POST | Same. |

---

## 2. Decision matrix per role (write side)

This is the truth-table that the migration must satisfy. Tests will assert each cell.

| Role / Action | update | approve | reject | start | complete | cancel | delete | scan | confirm-eq | remove-eq |
|---|---|---|---|---|---|---|---|---|---|---|
| ADMIN / SUPER_ADMIN | ✅ all | ✅ all | ✅ all | ✅ all | ✅ all | ✅ all | ✅ all | ✅ all | ✅ all | ✅ all |
| ORDER_COORDINATOR | ✅ all | ✅ all | ✅ all | ✅ all | ✅ all | ✅ all | ❌ 403 | ✅ all | ✅ all | ✅ all |
| ACCOUNTANT | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 |
| REGION_MGR | ✅ region | 🔒 403 (queue) | 🔒 403 | ✅ region | ✅ region | ❌ 403 | ❌ 403 | ✅ region | ✅ region | ✅ region |
| AREA_MGR | ✅ area | 🔒 403 (queue) | 🔒 403 | ✅ area | ✅ area | ❌ 403 | ❌ 403 | ✅ area | ✅ area | ✅ area |
| WORK_MGR | ✅ assigned | 🔒 403 (queue) | 🔒 403 | ✅ assigned | ✅ assigned | ❌ 403 | ❌ 403 | ✅ assigned | ✅ assigned | ❌ 403 |
| SUPPLIER | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 (use portal) | ❌ 403 | ❌ 403 |

Notes:
- **🔒 403 (queue)**: existing `_require_order_coordinator_or_admin` blocks them. We keep this.
  Without that wrapper REGION/AREA/WORK_MGR have the perm in DB but the router intent is
  "approval queue is owned by coordinator". Behavior preserved.
- **WORK_MGR + remove-equipment**: today the perm is `work_orders.update`, which WORK_MGR has.
  But removing equipment frees a project's budget — that's a coordinator-only action.
  **Question for product**: does WORK_MGR really get this button? If not — restrict in policy.
  Recommendation: keep with scope (WORK_MGR can do it on **assigned** projects only) and
  flag for product review as a follow-up. Marked `✅ assigned` above for now to match
  current DB grants.
- **scan-equipment for WORK_MGR**: legitimate — they're in the field. Scope = assigned.

---

## 3. Migration pattern (template)

Each migrated endpoint follows the same shape:

```python
# Before:
require_permission(current_user, "work_orders.update")
work_order = work_order_service.update(db, work_order_id, data, current_user_id=...)
```

```python
# After:
work_order = db.query(WorkOrder).filter(
    WorkOrder.id == work_order_id, WorkOrder.deleted_at.is_(None),
).first()
if not work_order:
    raise HTTPException(404, "WorkOrder not found")

AuthorizationService(db).authorize(
    current_user,
    "work_orders.update",
    resource=work_order,
    resource_type="WorkOrder",
)

work_order = work_order_service.update(db, work_order_id, data, current_user_id=...)
```

Key invariants:
- Permission check still runs (RBAC layer of `authorize`).
- Same 403 message, same 404 path.
- Service layer untouched.
- For approve/reject: `_require_order_coordinator_or_admin(current_user)` stays
  **before** the `authorize` call — it's a stricter gate than the strategy and
  the strategy is a no-op for those roles anyway.

---

## 4. Tests planned (per migrated endpoint)

For each migrated endpoint:
1. **Happy path** — admin/coordinator can perform action.
2. **In-scope role passes** — REGION_MGR on a same-region WO; AREA_MGR on same-area;
   WORK_MGR on assigned project.
3. **Out-of-scope role 403** — REGION_MGR on different-region; AREA_MGR on different-area;
   WORK_MGR on un-assigned project. **This is the leak-closure test.**
4. **Supplier 403** — defense in depth.
5. **Behavior identity for queue endpoints** — approve/reject by REGION_MGR still 403'd
   by the queue wrapper (no behavior change).

Plus integration tests already covered in Wave 1.2 (`/work-orders/{id}` GET) — no
regression there.

---

## 5. Open questions / decisions for product

| # | Question | Default if no answer |
|---|---|---|
| Q1 | Should REGION_MGR / AREA_MGR be able to approve/reject inside their own region/area? Today blocked by `_require_order_coordinator_or_admin`. DB permissions suggest yes; router says no. | **Default: keep current behavior.** Coordinator/admin only on the approval queue. |
| Q2 | Should WORK_MGR have `remove-equipment` on assigned projects? It releases budget and stops the WO. | **Default: yes (scoped to assigned)** — matches today's DB grant. Flag for review. |
| Q3 | Should WORK_MGR have `cancel` / `complete` (close)? Not in DB today. | **Default: not in this wave.** Don't add new perms here; only enforce existing ones. |
| Q4 | Should SUPPLIER ever hit `/work-orders/*`? | **Default: no, ever.** They go through `/supplier-portal/{token}/...`. Strategy already blocks. |

---

## 6. Performance debt — tracked

**Item**: `routers/work_orders.py:list_work_orders` post-hoc filtering for
REGION_MANAGER / WORK_MANAGER.

- **Today**: `work_order_service.list(db, search)` runs the SQL, returns up to
  page_size rows, then the router filters in Python.
- **Why it's fine now**: ~60 work orders in production. Page size 25.
  Worst case: in-memory filter over a single page.
- **Why it'll bite later**: pagination math is wrong if the post-filter drops rows
  (page 1 might end up with 12 items not 25). At ~10× volume (~600 WOs) the
  page totals will be visibly wrong for non-global roles.
- **Fix**: push the scope filter into `WorkOrderService.list()` via
  `AuthorizationService.filter_query(user, q, "WorkOrder")` so the SQL itself
  joins `Project` and filters. The strategy's `filter()` method is already
  written and tested for this.
- **Trigger**: when total work orders > 200 OR when QA reports a "less than
  page_size items on a non-final page" bug for REGION/WORK_MGR.
- **Recorded in**: `HANDOFF.md` → Performance Debt section (to be added).

---

## 7. Proposed wave breakdown

To keep PRs reviewable:

- **Wave 1.3.a — high-risk write endpoints**: `update / patch`, `start`, `cancel`,
  `close (complete)`, `delete`. ~5 endpoints. ~10 new tests.
- **Wave 1.3.b — equipment endpoints**: `scan-equipment`, `confirm-equipment`,
  `remove-equipment`. 3 endpoints. ~6 new tests.
- **Wave 1.3.c — approval queue (no-behavior-change)**: `approve`, `reject`.
  2 endpoints, mostly defense-in-depth + behavior-identity tests. ~4 tests.
- **Wave 1.3.d — read side**: `pdf`. 1 endpoint. ~2 tests.
- **Wave 1.3.e — create**: `POST /work-orders`. Validate project scope on the
  payload's `project_id`. ~3 tests.

That's 5 sub-waves, but each is small and isolated. Recommend doing 1.3.a first
(biggest win, closes real leaks) and pausing for re-approval before continuing.

---

## 8. Summary

- 11 endpoints to migrate.
- 7 endpoints to leave as-is (with documented justification).
- 0 DB changes.
- 0 frontend changes.
- 0 service-layer changes.
- ~25 new tests across 5 sub-waves.
- 1 performance debt item recorded for future SQL-level pushdown.

Awaiting approval to start with **Wave 1.3.a** (update / start / cancel / close / delete).
