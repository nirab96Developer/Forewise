# Phase 3 — Wave 3.1.6 Recon: Worklogs

**Goal**: Map out the worklogs domain before implementation. Identify
ownership/scope checks, gaps between list/detail/actions, propose a
unified policy, and split into reviewable sub-waves.

**Status**: Read-only recon. No code/DB/frontend changes.

---

## 1. Endpoint inventory (18 total)

### 1.1 Read endpoints (8)

| # | Path | Method | Perm | Today's scope | Gap? |
|---|---|---|---|---|---|
| 1 | `/worklogs` (list) | GET | `worklogs.read` | `if user.area_id: filter by area` | **❌ broken**: admin with area gets sliced too; REGION/WORK_MGR get nothing |
| 2 | `/worklogs/my-worklogs` | GET | none | hard `user_id = current_user.id` | ✅ fine (self-service) |
| 3 | `/worklogs/pending-approval` | GET | `worklogs.approve` | none | ❌ no scope — REGION_MGR with the perm sees other regions |
| 4 | `/worklogs/statistics` | GET | `worklogs.read` | none | ❌ no scope — sees all financial stats |
| 5 | `/worklogs/activity-codes` | GET | none (auth only) | n/a (returns ActivityType list) | ✅ fine |
| 6 | `/worklogs/{id}` | GET | `worklogs.read` | `if user.area_id: filter by area` (404 if mismatch) | **❌ same broken filter; SUPPLIER not gated to own** |
| 7 | `/worklogs/by-work-order/{wo_id}` | GET | `worklogs.read` | none | ❌ no scope at all |
| 8 | `/worklogs/{id}/pdf` | GET | `worklogs.read` | none | ❌ info disclosure — `hourly_rate_snapshot`, `cost_with_vat` |

### 1.2 Create endpoints (4)

| # | Path | Method | Perm | Today's scope | Gap? |
|---|---|---|---|---|---|
| 9 | `/worklogs` | POST | `worklogs.create` | none on payload | ❌ no project scope — anyone with the perm can report on any WO |
| 10 | `/worklogs/standard` | POST | `worklogs.create` | none | ❌ same |
| 11 | `/worklogs/manual` | POST | `worklogs.create` | none | ❌ same |
| 12 | `/worklogs/storage` | POST | `worklogs.create` | none | ❌ same |

### 1.3 State / mutate endpoints (6)

| # | Path | Method | Perm | Today's scope | Gap? |
|---|---|---|---|---|---|
| 13 | `/worklogs/{id}` | PUT | `worklogs.update` | none | ❌ no ownership; no scope |
| 14 | `/worklogs/{id}` | DELETE | `worklogs.delete` | none (admin-only by perm grant) | Low risk |
| 15 | `/worklogs/{id}/activate` | POST | `worklogs.restore` | none (admin-only by perm) | Low risk |
| 16 | `/worklogs/{id}/submit` | POST | `worklogs.submit` (owner-bypass) | owner OR `worklogs.submit` perm | ⚠️ owner-bypass logic correct; rest path lacks scope |
| 17 | `/worklogs/{id}/approve` | POST | `worklogs.approve` | none | ❌ no scope — anyone with the perm approves anywhere |
| 18 | `/worklogs/{id}/reject` | POST | `worklogs.approve` (note: NOT `worklogs.reject`) | none | ❌ same — bug-adjacent: `worklogs.reject` perm in DB is unused |

---

## 2. DB permission grants today

```
ACCOUNTANT        | worklogs.read
ADMIN             | worklogs.delete, .read, .read_own, .reject, .submit
AREA_MANAGER      | worklogs.read, .reject
ORDER_COORDINATOR | worklogs.read
REGION_MANAGER    | worklogs.read, .reject
SUPPLIER          | worklogs.read_own, .submit
WORK_MANAGER      | worklogs.read, .reject
```

Notable holes:
- **No one has `worklogs.approve` in DB.** ADMIN bypasses `require_permission`, so only ADMIN actually approves. AREA/REGION/WORK_MGR have `worklogs.reject` but the reject endpoint asks for `worklogs.approve`.
- **No one has `worklogs.create` / `worklogs.update`.** Same deal — ADMIN-only via bypass. But the field-team flows go through `my-worklogs` + supplier portal, not the central perm matrix.

This implies: today's reality is "ADMIN does everything; suppliers create/submit their own; everything else is shaky."

---

## 3. Today's three big leaks

### Leak A — list / detail policy mismatch (same shape as WorkOrder Wave 1.2)

```python
if current_user.area_id is not None:
    search.area_id = current_user.area_id          # in list
    query = query.where(Project.area_id == ...)    # in detail
```

This filter applies to **any** user with `area_id`, including admin who happens to be assigned to one. REGION_MANAGER (often `area_id=NULL`, `region_id=N`) gets no narrowing in code → sees everything. WORK_MANAGER same. The list shows what the area filter dictates, the detail shows the same area filter, but neither matches the real intent ("region for region manager", "assigned for work manager").

Identical to WorkOrder pre-Wave 1.2.

### Leak B — approve / reject scope wide open

```python
require_permission(current_user, "worklogs.approve")
# ... no scope check at all ...
worklog_service.approve(...)
```

If product later grants `worklogs.approve` to an AREA_MANAGER (the perm exists in DB; just isn't currently assigned), they could approve a worklog in another region. Same for reject.

### Leak C — PDF + statistics info disclosure

`/worklogs/{id}/pdf` and `/worklogs/statistics` are gated only by `worklogs.read`. Both expose financial fields:
- PDF: `hourly_rate_snapshot`, `cost_before_vat`, `cost_with_vat`, `paid_hours`, `overnight_total`, supplier email.
- Stats: aggregates across whatever the caller can theoretically see — but the endpoint doesn't check that.

Anyone with `worklogs.read` (ACCOUNTANT, AREA_MGR, REGION_MGR, ORDER_COORDINATOR, WORK_MGR, ADMIN) can pull a PDF for any worklog by guessing the ID.

---

## 4. Proposed unified scope policy

A `WorklogScopeStrategy` mirroring the WorkOrder pattern:

| Role / Action | List | Detail | PDF | Submit | Approve/Reject | Create | Update | Delete |
|---|---|---|---|---|---|---|---|---|
| ADMIN, SUPER_ADMIN | all | all | all | all | all | all | all | all |
| ORDER_COORDINATOR | all (read) | all | all | own | ❌ 403 (queue) | ❌ 403 | own | ❌ |
| ACCOUNTANT | all (read-only) | all | all | ❌ | ❌ | ❌ | ❌ | ❌ |
| REGION_MANAGER | by region | by region | by region | own | by region | by region | own | ❌ |
| AREA_MANAGER | by area | by area | by area | own | by area | by area | own | ❌ |
| WORK_MANAGER | by assigned | by assigned | by assigned | own | by assigned | by assigned | own | ❌ |
| SUPPLIER | own (user_id) | own | own | own | ❌ | own | own | ❌ |
| FIELD_WORKER | own | own | own | own | ❌ | own | own | ❌ |

Where:
- **own** = `worklog.user_id == current_user.id`.
- **by region** = `worklog.project.region_id == user.region_id`.
- **by area** = `worklog.project.area_id == user.area_id`.
- **by assigned** = `worklog.project_id ∈ user's active project_assignments`.

Mirrors the WorkOrder strategy intentionally. Frontend filtering is unchanged — what users see in the list will match what they can open in detail (closes Leak A).

---

## 5. Open product questions

### Q1 — Should AREA/REGION_MANAGER actually approve/reject?
Today they have `worklogs.reject` in DB but the router checks `worklogs.approve`. So in practice they can't.
- **Default for the wave**: keep current behavior — only ADMIN approves/rejects (via bypass). AREA/REGION/WORK_MGR get the strategy gate but the perm gate keeps them out. This is the "defense-in-depth" pattern.
- **Alternative**: allow them in their own scope (more useful for product, but a new behavior).
- **Recommendation**: stick with default. If product wants delegation, that's a separate change.

### Q2 — SUPPLIER scope by user_id or by supplier_id?
A supplier organization can have multiple users (drivers). Today's `worklogs.read_own` pattern is by `user_id` only — so a supplier with 5 drivers can NOT see consolidated reports across them via the API.
- **Default for the wave**: by `user_id` (matches today's `read_own` semantics).
- **Note for product**: if "supplier sees all org's worklogs" is desired, that needs a `worklog.supplier_id == user.supplier_id` rule and a `user.supplier_id` field.
- **Recommendation**: stay with user_id; flag the org-wide question for separate product review.

### Q3 — Order coordinator's worklog access
ORDER_COORDINATOR has `worklogs.read` (all read), no submit/approve/reject. This matches their dispatch role: see everything, mutate via WorkOrder rather than directly.
- **Default**: confirm "global read, no write."

### Q4 — Existing `search.area_id = current_user.area_id` shortcut
The strategy replaces this. **Behavior changes** for users whose `area_id` is set but who shouldn't be area-scoped (e.g. ADMIN with an assigned area). They go from "narrow to my area" to "see everything" (admin) or "see my full region" (region manager).
- This is a deliberate fix of Leak A.
- **Recommendation**: document in the migration commit; tests assert each role × action.

### Q5 — `worklogs.approve` perm not granted to anyone
Should we seed it for ADMIN explicitly? Today admin works via `require_permission` bypass, but it's confusing.
- **Default for this wave**: don't touch DB (per user direction).
- **Follow-up**: a separate "worklog perms cleanup" wave could rationalize this.

### Q6 — Submit endpoint owner-bypass
`if worklog.user_id != current_user.id: require_permission(... "worklogs.submit")`.
This is correct: owner always submits; non-owner needs the perm. The strategy can mirror this with a `submit_check()` or a context flag — either works.
- **Recommendation**: keep the inline owner-check; add `authorize()` as a defense-in-depth layer for non-owners.

---

## 6. Sub-wave proposal

Worklog has more endpoints (18) and more sensitive paths (financials, approval queue, PDF, scan-gating) than WorkOrder. Split into 4 reviewable sub-waves:

### **Wave 3.1.6.a — Read side + leak A** (highest value)
- `WorklogScopeStrategy` skeleton.
- Migrate: `GET /worklogs`, `GET /{id}`, `GET /by-work-order/{wo_id}`, `GET /pdf`, `GET /statistics`, `GET /pending-approval`, `GET /my-worklogs`.
- Replaces the buggy `area_id` shortcut. Closes Leak A + Leak C (PDF disclosure).
- ~7 endpoints, ~25 tests.

### **Wave 3.1.6.b — Approve / reject defense-in-depth** (Leak B)
- Migrate: `POST /{id}/approve`, `POST /{id}/reject`.
- Add scope check on top of the existing perm gate. No behavior change today (only ADMIN actually has the perm).
- 2 endpoints, ~10 tests.

### **Wave 3.1.6.c — Submit + state mutations**
- Migrate: `POST /{id}/submit` (preserve owner-bypass), `PUT /{id}`, `DELETE /{id}`, `POST /{id}/activate`.
- Owner-or-admin pattern. Preserve the scan-gate business logic untouched.
- 4 endpoints, ~12 tests.

### **Wave 3.1.6.d — Create-time scope via ProjectScopeStrategy**
- Migrate: `POST /worklogs`, `/standard`, `/manual`, `/storage`.
- Reuse the existing `ProjectScopeStrategy` (already in `STRATEGIES["Project"]` since Wave 1.3.e) on `data.work_order_id → wo.project_id` or `data.project_id`.
- 4 endpoints, ~10 tests.

**Total estimate**: 4 commits, ~57 new tests, 0 DB changes, 0 frontend changes.

---

## 7. Strategy outline (Worklog)

```python
class WorklogScopeStrategy:
    """
    Worklog scope (Phase 3 Wave 3.1.6).

    Two dimensions of scope:
      A. Ownership — worklog.user_id == user.id (SUPPLIER, FIELD_WORKER)
      B. Project   — worklog.project's region/area/assignment matches user

    Roles:
      ADMIN / SUPER_ADMIN / ORDER_COORDINATOR / ACCOUNTANT → all (read-only
                                                              for ACCOUNTANT
                                                              by perm conv.)
      REGION_MANAGER  → worklog.project.region_id == user.region_id
      AREA_MANAGER    → worklog.project.area_id   == user.area_id
      WORK_MANAGER    → worklog.project_id ∈ assigned projects
      SUPPLIER        → worklog.user_id == user.id
      FIELD_WORKER    → worklog.user_id == user.id
    """

    DETAIL = "אין הרשאה לדיווח זה"

    GLOBAL_ROLES = ("ADMIN", "SUPER_ADMIN", "ORDER_COORDINATOR", "ACCOUNTANT")
    OWN_ONLY_ROLES = ("SUPPLIER", "FIELD_WORKER")

    def _project_for(self, db, worklog):
        # If worklog has direct project_id, use it. Else look up via WO.
        ...

    def check(self, db, user, worklog):
        code = (user.role.code if user.role else "").upper()
        if code in self.GLOBAL_ROLES:
            return
        if code in self.OWN_ONLY_ROLES:
            if worklog.user_id != user.id:
                raise _FORBIDDEN(self.DETAIL)
            return
        # REGION/AREA/WORK_MGR — project-based
        ...

    def filter(self, db, user, query):
        # JOIN Project + filter by region/area/assignment
        # OWN_ONLY_ROLES → filter by user_id
        ...
```

Same structure as `WorkOrderScopeStrategy` with the addition of an
"own only" branch for suppliers/field workers.

---

## 8. Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | Silent behavior change for users with `area_id` set who shouldn't be area-scoped (admin, region_mgr) | Pin in commit message; tests assert each role explicitly |
| R2 | SUPPLIER currently sees own via `read_own` perm; need to make sure the strategy + perm gate work together (perm-only for `my-worklogs` endpoint, scope for everything else) | `my-worklogs` keeps its hard `user_id = current_user.id`; doesn't go through strategy |
| R3 | scan-gate validation in `/submit` is complex (~50 lines); easy to break | Don't touch business logic; only inject `authorize()` after the worklog fetch |
| R4 | PDF generation is a background-friendly operation; HTTPException(403) must propagate cleanly | Same pattern as WO PDF (Wave 1.3.d): fetch+authorize OUTSIDE try block |
| R5 | Service layer's `list()` doesn't apply scope; we'll likely use post-hoc filter (same Performance Debt as WO list — PD-1) | Document a PD-2 entry in HANDOFF.md if applicable |

---

## 9. Performance debt — projected (PD-2 candidate)

If we apply post-hoc Python filtering in `list_worklogs` for REGION/WORK_MGR (mirroring WO's approach), pagination math will be wrong on non-final pages once worklog count grows.

- Today: ~unknown count; let's check actual DB volume before deciding.
- Fix path: push scope into `WorklogService.list()` via `AuthorizationService.filter_query` (already a thing).

Will measure in 3.1.6.a; record in HANDOFF only if real.

---

## 10. Summary

- **18 endpoints** across read/create/state/mutate.
- **3 real leaks**: list-vs-detail mismatch, approve/reject wide-open, PDF+stats info disclosure.
- **6 product questions** with safe defaults documented.
- **4 sub-waves** proposed, totaling ~57 tests, 0 DB/FE changes.
- **1 new strategy** (`WorklogScopeStrategy`) reusing the WorkOrder pattern + adding an "own only" branch for SUPPLIER / FIELD_WORKER.

Awaiting approval to start with **Wave 3.1.6.a** (read side, biggest value).
