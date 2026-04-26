# Phase 3 — Wave 2.2 Recon: Dashboard Scope Audit

**Goal**: Read each of the 23 endpoints in `routers/dashboard.py` (1650 lines)
and classify their scope behavior. Identify the real leaks and propose
ordered sub-waves to close them.

**Status**: Read-only audit. No code/DB/frontend changes.

---

## 0. Global gate (the good news)

Every dashboard endpoint depends on `_dashboard_view`, which calls
`require_permission(current_user, "dashboard.view")`. Per migration
`a3b4c5d6e7f8`, **SUPPLIER does NOT hold this perm**, so all leaks
below are scoped to authenticated **non-supplier** users:
ADMIN / SUPER_ADMIN / REGION_MGR / AREA_MGR / WORK_MGR /
ORDER_COORDINATOR / ACCOUNTANT / FIELD_WORKER.

This means the audit is about **scope leakage between authorized
roles** (e.g. AREA_MGR seeing system-wide totals), not about
external attackers. Severity is calibrated accordingly.

---

## 1. Endpoint inventory & classification

Legend:
- ✅ properly scoped per role/region/area
- ⚠️ partial — some queries scoped, some not
- ❌ no scope — global data returned regardless of caller

| # | Path | Status | Intended audience | Notes |
|---|---|---|---|---|
| 1  | `GET /my-tasks` | ✅ | all roles | Delegates to `PendingTasksEngine.get_my_tasks(role, region_id, area_id)`. Engine handles scope. |
| 2  | `GET /summary` | ⚠️ | all roles | Project/Budget scoped; entity counts (users, regions, equipment, invoices, hours) GLOBAL. |
| 3  | `GET /admin-overview` | ✅ | ADMIN only | Explicit `if not ADMIN/SUPER_ADMIN: 403`. All queries global by design. |
| 4  | `GET /map` | ⚠️ | all roles | REGION_MGR/AREA_MGR scoped; everyone else (incl. WORK_MGR, COORDINATOR, ACCOUNTANT) falls through to global. |
| 5  | `GET /projects` | ✅ | all roles | Properly scoped: WORK_MGR/FIELD_WORKER via ProjectAssignment OR manager_id; REGION/AREA by region_id/area_id. |
| 6  | `GET /alerts` | ⚠️ + 🐞 | all roles | Budget-overrun query scopes via `Project.region_id` filter on a `Budget` query without a JOIN — **SQL bug**. Pending-WO count not scoped. |
| 7  | `GET /statistics` | ⚠️ | all roles | Projects scoped; monthly_trend not scoped. |
| 8  | `GET /live-counts` | ❌ | all roles | 17+ counts, ALL global. AREA_MGR sees system-wide totals. |
| 9  | `GET /financial-summary` | ⚠️ | all roles | Budgets scoped by region/area; invoice stats GLOBAL. |
| 10 | `GET /stats` | ⚠️ | all roles | Alias for `/summary` — inherits its issues. |
| 11 | `GET /activity` | ⚠️ | all roles | `user_id == self.id` filter for non-admin. REGION/AREA_MGR see only own activity, not their scope's — inconsistent with `/activity-logs/`. |
| 12 | `GET /hours` | ⚠️ | all roles | Same `user_id == self.id` for non-admin. REGION/AREA_MGR can't see scope's hours. |
| 13 | `GET /equipment/active` | ❌ | all roles | No scope at all. Equipment list across all projects/suppliers. |
| 14 | `GET /suppliers/active` | ❌ | all roles | No scope. Full supplier list. |
| 15 | `GET /monthly-costs` | ⚠️ | all roles | REGION/AREA_MGR scoped via Worklog.area_id; WORK_MGR/COORDINATOR/ACCOUNTANT/FIELD_WORKER fall through to global. |
| 16 | `GET /region-areas` | ⚠️ | REGION_MGR | Uses `current_user.region_id` directly; no role gate. ADMIN with no region_id gets `[]`. Other roles can call and see. |
| 17 | `GET /work-manager-summary` | ⚠️ | WORK_MANAGER | Filters by `current_user.id` only. No role gate. ADMIN gets their own personal summary instead of system view. |
| 18 | `GET /work-manager-overview` | ⚠️ | WORK_MANAGER | Alias for #17. Same. |
| 19 | `GET /region-overview` | ⚠️ | REGION_MGR | Uses `current_user.region_id`; no role gate. ADMIN gets junk data, AREA_MGR gets their region's data (probably OK). |
| 20 | `GET /area-overview` | ⚠️ | AREA_MGR | Uses `current_user.area_id`; no role gate. ADMIN gets junk. |
| 21 | `GET /coordinator-queue` | ⚠️ | ORDER_COORDINATOR | COORDINATOR scoped by `region_id`; other roles fall through to global queue. No role gate. |
| 22 | `GET /accountant-overview` | ❌ | ACCOUNTANT | All queries global; no scope, no role gate. **Anyone with `dashboard.view` sees system-wide financials.** |
| 23 | `GET /worklog-detail/{worklog_id}` | ❌ | ACCOUNTANT | **No scope, no role gate**. Returns hourly rate, cost_with_vat, cost_before_vat, full audit trail for ANY worklog by ID. |

**Tally**: 4 ✅ / 12 ⚠️ / 7 ❌.

---

## 2. Real leaks ranked by severity

### 2.1 HIGH — financial info disclosure

#### Leak D1 — `GET /worklog-detail/{worklog_id}`
- **What**: WORK_MGR / FIELD_WORKER / any non-supplier with
  `dashboard.view` can fetch ANY worklog's financials by guessing
  the ID. Exposes `hourly_rate_snapshot`, `cost_before_vat`,
  `cost_with_vat`, `overnight_total`, supplier name, audit trail.
- **Same shape as**: Worklog PDF leak closed in Wave 3.1.6.a.
  We already have `WorklogScopeStrategy` — wire it here.
- **Defense-in-depth check**: ACCOUNTANT (intended caller) is in
  `WorklogScopeStrategy.GLOBAL_ROLES`, so adding `authorize()` is
  no-op for the legitimate use case.

#### Leak D2 — `GET /accountant-overview`
- **What**: System-wide financial KPIs (`pending_amount`,
  `monthly_approved`, draft invoice amounts), worklogs list with
  costs and rates, project + supplier filter options.
- **Risk**: AREA_MGR / WORK_MGR / COORDINATOR / FIELD_WORKER can
  enumerate financial flow they don't otherwise see in their UI.
- **Fix**: Role gate (`require_role("ACCOUNTANT", "ADMIN")`)
  AND scope filter on the worklogs list (already have
  WorklogScopeStrategy).

### 2.2 MEDIUM — operational info disclosure

#### Leak D3 — `GET /live-counts`
- **What**: 17+ counts (`users_active`, `equipment_total`,
  `suppliers_active`, `wo_pending`, `tickets_open`, `invoices_*`,
  etc.). All global.
- **Risk**: Low per-row, but a consistent reconnaissance surface.
  AREA_MGR sees "system has 315 users, 45 suppliers" — info they
  shouldn't need.
- **Fix**: Per-count scope filter where applicable; some counts
  (e.g. `users_total`) admin-only.

#### Leak D4 — `GET /equipment/active`, `GET /suppliers/active`
- **What**: Full equipment + supplier lists, no scope.
- **Risk**: Operational reconnaissance. Especially supplier list —
  competitors-style leakage if multiple suppliers' users somehow
  get `dashboard.view`.
- **Fix**: Scope by user's region/area/assigned-projects;
  ACCOUNTANT/ADMIN can see all.

### 2.3 LOW — KPI inconsistency, no real data leakage

- **D5 (`/summary`, `/stats`)**: entity counts global. AREA_MGR sees
  "system has 315 users". Consistent with HOW the dashboards
  display today, not a security concern, but cleanup-worthy.
- **D6 (`/region-overview`, `/area-overview`, `/work-manager-*`,
  `/coordinator-queue`)**: no role gate. A non-target role can
  call and see partial / odd data. UI-level guard exists per role's
  Dashboard.tsx, so end-user impact is zero. Backend defense-in-
  depth missing.

### 2.4 BUG — `GET /alerts`

```python
overbudget_query = db.query(Budget).filter(...)
if current_user.role.code == "REGION_MANAGER":
    overbudget_query = overbudget_query.filter(Project.region_id == ...)
```

Filtering on `Project.region_id` without joining `Project` to a
`Budget` query — depending on SQLAlchemy version this either
throws or silently produces a Cartesian product. Either way, the
intended scope filter doesn't actually narrow.

**Severity**: Low — `Budget.region_id` exists as a denormalized
column already, so the fix is `Budget.region_id == user.region_id`
(matches what `/financial-summary` does correctly).

---

## 3. Duplicate logic / patterns observed

| Pattern | Where | Recommendation |
|---|---|---|
| `if role == REGION_MANAGER: filter by region_id; elif AREA_MANAGER: filter by area_id` | Repeated in /summary, /map, /projects, /alerts, /statistics, /financial-summary, /monthly-costs | Extract a `_scope_project_ids(user)` helper, OR adopt `AuthorizationService.filter_query` |
| Role-based query scoping with `if user.role.code == "X"` | 23 endpoints, 50+ branches | Same |
| Raw SQL `WHERE project_id IN (id_list)` building strings via str-join (region_overview, area_overview) | `f"... project_id IN ({id_list})..."` — not parametrized | Use bind params; tracked as small SQL hygiene debt |
| Manual day-by-day loop building 14-day chart | /admin-overview, /region-overview, /area-overview | Could DRY into helper. Low priority. |
| `db.execute(text("..."))` raw SQL across many endpoints | All overviews | Existing pattern; acceptable for read-heavy aggregation. |

---

## 4. Recommended fix policy

A pragmatic 4-level policy, applied per endpoint:

| Level | Rule | When to apply |
|---|---|---|
| L1 | **Role gate** (`require_role("ADMIN")` or similar) | Endpoint is intended for one specific role, e.g. /accountant-overview, /work-manager-summary. Today some have it, some don't. |
| L2 | **Resource-level scope** via `AuthorizationService.authorize(...)` | Single-row endpoints — e.g. /worklog-detail/{id}. Use the existing strategy. |
| L3 | **List-level scope** via `AuthorizationService.filter_query(...)` | Worklog/WorkOrder lists. Same approach as Wave 3.1.6.a's post-hoc filter, but better is service-level pushdown. |
| L4 | **Per-query field scope** | Counts and aggregations — narrow each scalar query independently to the caller's region/area scope. |

Priority order for fixes: D1 → D2 → D3/D4 → D5/D6.

---

## 5. Proposed sub-waves

To keep PRs small and reviewable:

### Wave 2.2.a — close D1 (worklog-detail leak)
- **1 endpoint**: `/worklog-detail/{worklog_id}`
- Wire `AuthorizationService.authorize(... resource_type="Worklog")`
  on the row. Strategy already shipped in Wave 3.1.6.a.
- Tests: regression for the leak (WORK_MGR fetching another user's
  detail → 403), admin/accountant pass.
- **Effort**: ~1 hour. ~6 tests.

### Wave 2.2.b — close D2 (accountant-overview leak)
- **1 endpoint**: `/accountant-overview`
- Add role gate (ACCOUNTANT/ADMIN).
- Apply WorklogScopeStrategy filter to the worklogs list.
- Project/supplier filter options stay global (intended UX for
  accountant).
- Tests: non-accountant non-admin → 403; accountant sees worklogs
  list.
- **Effort**: ~half day. ~8 tests.

### Wave 2.2.c — fix the SQL bug (D in /alerts)
- **1 endpoint**: `/alerts`
- Replace `Project.region_id` filter on Budget query with
  `Budget.region_id`. Same for area.
- Tests: REGION_MGR with overruns in their region sees them;
  cross-region overruns excluded.
- **Effort**: ~1 hour. ~3 tests.

### Wave 2.2.d — close D4 (equipment/suppliers active)
- **2 endpoints**: `/equipment/active`, `/suppliers/active`
- Scope: ACCOUNTANT/ADMIN see all; REGION/AREA narrowed to
  region/area's projects; WORK_MGR narrowed to assigned projects;
  others get an empty list with a clear log line.
- **Effort**: ~half day. ~10 tests.

### Wave 2.2.e — role gates for role-specific dashboards
- **5 endpoints**: `/work-manager-summary`, `/work-manager-overview`,
  `/region-overview`, `/area-overview`, `/coordinator-queue`,
  `/region-areas`
- Add explicit role allowlist + 403 for others. Today the UI
  already routes correctly per role, so end-user impact is zero;
  backend defense-in-depth.
- **Effort**: ~half day. ~10 tests.

### Wave 2.2.f — D3 (live-counts cleanup)
- **1 endpoint**: `/live-counts`
- Per-count narrowing: keep system-wide for ADMIN/COORDINATOR/
  ACCOUNTANT; narrow region/area-relevant counts (`projects_active`,
  `wo_pending`, etc.) for region/area managers.
- **Effort**: ~half day. ~10 tests.

### Defer
- D5 (`/summary` + `/stats` entity counts) — UI already correct
  per role via Dashboard.tsx routing; backend cleanup nice-to-have
  but not urgent.
- Pattern extraction into `_scope_project_ids(user)` helper —
  refactor wave once D1-D4 close.

---

## 6. Open product questions

| # | Question | Default if no answer |
|---|---|---|
| Q1 | Should ACCOUNTANT see worklogs cross-region/area, or scoped to a region/area? | Today: cross-region (no scope on /accountant-overview). Default: keep cross-region for ACCOUNTANT (financial role); scope only when product asks. |
| Q2 | Should `/work-manager-summary` 403 for ADMIN, or return ADMIN's own personal data (current behavior)? | Default: keep current — ADMIN sees their personal version. Add explicit role gate that includes ADMIN for "view-as" capability. |
| Q3 | `/region-areas` — should AREA_MANAGER see other areas in their region? | Today: yes (no role gate, scope = user.region_id). Default: keep — useful for cross-area context. |
| Q4 | `/equipment/active` — should AREA_MGR see all equipment in their area, or only equipment on assigned WOs? | Default: by area (matches /map and /projects). |

---

## 7. Risks of each fix

| # | Risk | Mitigation |
|---|---|---|
| R1 | Frontend UI assumed global counts in `/live-counts` and breaks when narrowed | Run TypeScript build, scan for usages; keep field shape, just narrow values. |
| R2 | `/accountant-overview` role gate breaks ADMIN's "view as" UX | Include ADMIN in the role allowlist. |
| R3 | `/worklog-detail/{id}` 403 vs the FE 404-style usage | Frontend handles 403 in axios interceptor; should be fine. Check live behavior on staging. |
| R4 | Pattern: `Project.region_id` filter on `Budget` query (D bug) — current production behavior may have been silently returning ZERO overrun alerts to region/area managers | Document the change in the commit; add staging-time check that an alert appears for known overruns. |

---

## 8. Strategies in scope to reuse

| Strategy | Used by |
|---|---|
| `WorklogScopeStrategy` | D1 fix (/worklog-detail), D2 fix (/accountant-overview list) |
| `WorkOrderScopeStrategy` | D3 partial (wo_pending counts), D5 (/summary) |
| `BudgetScopeStrategy` | D5 (/summary), D bug in /alerts |
| `ProjectScopeStrategy` | D5 (/summary projects), D4 (/equipment/active scope) |

All four are already registered in `STRATEGIES`. No new strategy
needed for Wave 2.2.

---

## 9. Performance considerations

- `/region-overview` and `/area-overview` issue **N+1** queries:
  one per area + one per day for the 14-day chart, all serial.
  At scale (100+ areas) this is slow. **Not worse after the fix**;
  flag for PD-3 if it ever becomes a real complaint.
- The raw-SQL `WHERE project_id IN ({id_list})` string concat is
  not a SQL injection risk because `id_list` is built from
  `Project.id` integers, but it's a code-review smell. Migrate to
  bind params during the same PRs as the scope fixes.

---

## 10. Summary

- **23 endpoints**: 4 ✅, 12 ⚠️, 7 ❌.
- **2 high-severity leaks**: D1 (worklog-detail), D2 (accountant-overview).
- **1 SQL bug**: `/alerts` Project-on-Budget filter without join.
- **6 sub-waves proposed**, totaling ~3 days, ~50 new tests, 0 DB changes, 0 frontend changes.
- **No new strategies needed** — Wave 3.1.6 left us with the right toolkit.

Awaiting approval to start with **Wave 2.2.a** (D1 — worklog-detail
leak) as the highest-value fix.
