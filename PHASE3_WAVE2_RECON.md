# Phase 3 — Wave 2 Recon: Audit + Visibility + UX

**Goal**: Map what already exists across the 6 sub-waves the user proposed,
identify real gaps, and recommend a focused execution order. The user
emphasized "לא לשבור התנהגות קיימת" — so this recon prioritizes
audit-and-fix over build-from-scratch.

**Status**: Read-only recon. No code/DB/frontend changes.

---

## Big-picture finding

**Most of Wave 2 is already substantially built**:

| Concern | What exists | Lines |
|---|---|---|
| Audit/activity logging model | `models/activity_log.py` | 73 |
| Audit/activity helper API | `services/activity_logger.py` | 895 |
| Audit query/scope service | `services/activity_log_service.py` | 580 |
| Activity log API endpoints | `routers/activity_logs.py` | 159 |
| Dashboard backend (23 endpoints) | `routers/dashboard.py` | 1650 |
| Frontend dashboards (10 role variants) | `pages/Dashboard/*.tsx` | — |
| Frontend activity logs (3 variants) | `pages/ActivityLog/*.tsx` | — |
| Tests for activity logs | `tests/test_audit_coverage.py` | exists |
| Tests for dashboard perms | `tests/test_dashboard_permissions.py` | exists |
| Notifications system | `routers/notifications.py` (Wave 3.1.4) | 360+ |

Wave 2 should NOT rewrite this. It should audit + fix gaps.

---

## Wave 2.1 — Audit Logs

### What exists

- **`activity_logs` table**: 20 columns (user_id, activity_type, action, entity_type, entity_id, description, category, ip_address, user_agent, session_id, custom_metadata, created_at, etc.).
- **`activity_logger.py`**: 50+ helper functions covering:
  - WorkOrder events (created, sent_to_coordinator, approved, rejected, started, completed, closed, cancelled, sent_to_supplier, resent, supplier_changed)
  - Supplier coordination (landing_page_sent, timer_started, timer_expired, confirmed, declined, constraint_rejected)
  - Equipment (scanned, mismatch_detected, transfer_approved, type_change_pending, type_change_approved)
  - Worklog (created, submitted, approved, rejected, assigned_to_invoice)
  - Invoice (created, approved, sent_to_supplier, paid)
  - Auth (login, logout, otp_verified)
  - Support tickets (created, replied, status_changed)
- **`activity_log_service.py`**: full query API, suspicious-activity detection, login history, summaries, cleanup.
- **`/activity-logs` endpoint** with role-based scope (`my` / `area` / `region` / `system`) and category filtering (operational/financial/management/system).
- **3 frontend pages**: ActivityLogNew, AccountantActivityLog, WorkManagerActivityLog.

### Real gaps

| # | Gap | Severity | Where |
|---|---|---|---|
| G1 | `routers/worklogs.py` does NOT call `log_worklog_*` helpers from any of its 18 endpoints (Wave 3.1.6 didn't add them either) | **High** — biggest hole, since worklogs are the most-watched events | `worklogs.py` |
| G2 | `routers/support_tickets.py` calls `log_support_ticket_*` correctly, but the auto-status-change in `add_ticket_comment` calls `log_support_ticket_status_changed` only once — works as-is. | None | n/a |
| G3 | `routers/work_orders.py` calls `log_work_order_created` only on create. `approve`, `reject`, `cancel`, `close`, `start` are NOT logged via the centralized helpers — they go through `service.approve(...)` etc. which may or may not log. | Medium | `work_orders.py` |
| G4 | Listed read endpoint `/activity-logs/{log_id}` has NO scope check — any authenticated user can read any log entry. The list endpoint scopes correctly; detail endpoint doesn't. | **Medium** | `activity_logs.py:143` |
| G5 | `_get_scope_for_role` doesn't include SUPER_ADMIN, ACCOUNTANT, ORDER_COORDINATOR, WORK_MANAGER explicitly. They fall through to "my". | Low (works correctly because falling to "my" is the safe default), but inconsistent with other strategies. | `activity_logs.py:25` |
| G6 | Activity logs aren't routed through `AuthorizationService` — they have their own role/scope logic. Aligning would centralize the model. | Low | `activity_logs.py` |
| G7 | No tests for `/activity-logs/{log_id}` or for the SUPER_ADMIN/ACCOUNTANT/COORDINATOR scope paths | Medium | tests |

### Recommended action for 2.1

**Wave 2.1.a — close G4 (detail leak)** + **G1 (worklog logging)**.
- Add scope check on `/activity-logs/{log_id}` (the entry must be visible per the list scope rules).
- Call `log_worklog_created`, `log_worklog_submitted`, `log_worklog_approved`, `log_worklog_rejected` from the migrated worklog endpoints (Wave 3.1.6.a/b/c/d).
- ~10 tests.

Defer G3 (work_orders state-change logging) and G5/G6 (alignment with AuthorizationService) to a later cleanup sub-wave.

---

## Wave 2.2 — Dashboard Backend

### What exists

23 endpoints in `routers/dashboard.py`:
```
/my-tasks           /summary             /admin-overview
/map                /projects            /alerts
/statistics         /live-counts         /financial-summary
/stats              /activity            /hours
/equipment/active   /suppliers/active    /monthly-costs
/region-areas       /work-manager-summary  /work-manager-overview
/region-overview    /area-overview       /coordinator-queue
/accountant-overview                     /worklog-detail/{worklog_id}
```

Per-role dashboards have their own endpoints (`work-manager-overview`, `region-overview`, `area-overview`, `coordinator-queue`, `accountant-overview`) — covers the user's spec for role-based dashboards.

`tests/test_dashboard_permissions.py` exists.

### Real gaps

| # | Gap | Severity |
|---|---|---|
| G8 | Need to check whether each role-specific endpoint properly applies scope filter or is open to any authenticated user. Without reading 1650 lines I can't tell from the inventory alone. | Unknown until audited |
| G9 | The user's wishlist mentions `/dashboard/work-orders`, `/dashboard/worklogs`, `/dashboard/invoices`, `/dashboard/alerts`, `/dashboard/activity` — most exist under different names (`/admin-overview`, `/accountant-overview`, etc.). Naming inconsistency could be a frontend coupling concern. | Low |
| G10 | None of the dashboard endpoints currently use `AuthorizationService.filter_query()`. They have their own ad-hoc role-based filtering. | Low (works), but adds maintenance debt. |

### Recommended action for 2.2

**Audit-first**: skim each of the 23 dashboard endpoints, classify them as
- ✅ already scoped correctly (admin-only / role-only / scope-aware)
- ⚠️ scoped but inconsistently (e.g. `current_user.area_id` shortcut bug like worklogs had)
- ❌ no scope at all

Then close the ❌ + ⚠️ gaps. Do NOT rewrite the working endpoints.

This is a 1-2 day audit, not a build wave.

---

## Wave 2.3 — Dashboard UI/UX

### What exists

10 dashboard React components, one per role:
- AdminDashboard
- RegionManagerDashboard
- AreaManagerDashboard
- WorkManagerDashboard
- OrderCoordinatorDashboard
- AccountantDashboard
- FieldWorkerDashboard
- SupplierManagerDashboard (likely the supplier portal landing)
- ViewerDashboard
- DefaultDashboard (fallback)

Plus `Dashboard.tsx` as the role-router.

### Real gaps

Need a UI audit per role. Without running the app and inspecting each
screen, I can flag known concerns:

- **Hebrew/RTL coverage**: the user explicitly required "כל מסך חייב להיות בעברית, ברור, RTL". Existing screens were built in Hebrew but have English leaks in some labels/error states. A targeted polish pass is needed.
- **Empty states / loading states / error states**: standard-feature gap.
- **Mobile/tablet responsive**: needs measurement.
- **Version footer**: Wave 2.6 spec — not in dashboards today.

### Recommended action for 2.3

This is a UI polish wave that benefits from being decoupled from
backend changes. **Suggested timing**: after 2.1.a + 2.2.audit close
the security gaps, do 2.3 as a focused frontend pass.

Effort estimate: ~3-5 days for a full role-by-role polish. Could be
split into 2 sub-waves (admin + region/area first; field/coordinator/
accountant second).

---

## Wave 2.4 — Smart Notifications

### What exists

`routers/notifications.py` (~360 lines), already migrated to
`NotificationScopeStrategy` in Wave 3.1.4. Existing helpers:
- `notify_work_order_created`, `_approved`, `_rejected`
- `notify_worklog_created`, `_approved`, `_rejected`
- `notify` (low-level)
- `notify_users_by_role` (role-based fan-out)

Plus per-event triggers fire from various endpoints.

### Real gaps

| # | Gap | Severity |
|---|---|---|
| G11 | The user spec mentions `send_to_user`, `send_to_role`, `send_by_resource` as a unified API. Today there are scattered functions; no single contract. | Medium (refactor) |
| G12 | "Budget near limit" trigger doesn't exist today. | Medium |
| G13 | "Supplier timeout" trigger exists in activity logs but doesn't push a notification to coordinator. | Low |
| G14 | "WorkOrder needs re-coordination" trigger fires (we saw it in `scan_equipment`'s scenario C) but only emails — should also notify in-app. | Low |
| G15 | UI: notification center — `routers/notifications.py` has the API; check whether the frontend has a dedicated page or just the bell icon. | Unknown |

### Recommended action for 2.4

**Defer.** Today's notification system works for the common cases.
The unified `send_to_*` API + new triggers (budget, timeout, etc.)
is enhancement, not security. Park until 2.1.a/2.2/2.3 ship.

---

## Wave 2.5 — Performance

### What exists

- PD-1 (work_orders.list post-hoc filter) — flagged in HANDOFF.md.
- PD-2 (worklogs.list post-hoc filter) — flagged in HANDOFF.md.
- No global slow-query log; no APM in production.

### Recommended action for 2.5

**Trigger-based**: leave PD-1/PD-2 alone until volumes hit the trigger
thresholds (200 WOs / 500 worklogs). Today they're fine. The work to
push filters into service layer is well-understood; we just don't need
it yet.

---

## Wave 2.6 — Production Readiness

### What exists

- `/health` endpoint — working.
- `alembic` migrations — working, head documented.
- CI subset that runs in deploy.yml.
- `HANDOFF.md` documents performance debt.

### What's missing

| # | Item | Effort |
|---|---|---|
| G16 | `/version` endpoint with git SHA + build time | Trivial |
| G17 | Version footer on every page | Small |
| G18 | Deep health checks (DB, Redis, Sentry) | Small |
| G19 | Backup-restore drill | Manual ops task |
| G20 | Deployment checklist | Doc only |
| G21 | Smoke test post-deploy | Small script |
| G22 | Sentry 403 issue — user mentioned this is still open | Need to investigate |
| G23 | Basic monitoring (uptime, error rate) | External service setup |

### Recommended action for 2.6

**Quick wins first** (G16, G17, G18, G21) — small commits, big visibility
boost. The rest are ops-level concerns better handled with explicit
operator engagement.

---

## Recommended execution order

Priority is **security gaps first**, then quick wins, then enhancements.

### Phase 3 Wave 2.1.a — Audit log security (1 PR)
Close G4 (detail leak) + add Hebrew-text scope test for SUPER_ADMIN /
ACCOUNTANT / COORDINATOR / WORK_MANAGER paths. Keep current
`_get_scope_for_role` shape; just plug the leak.
**Effort**: ~half day.

### Phase 3 Wave 2.1.b — Wire worklog activity logging (1 PR)
Add `log_worklog_*` calls into the 4 migrated worklog endpoints
(create, submit, approve, reject) — using helpers that already
exist. Tests verify each event is logged with the right entity_id.
**Effort**: ~half day.

### Phase 3 Wave 2.2.audit — Dashboard scope audit (1 PR for findings, optional follow-ups)
Read each of 23 dashboard endpoints; classify; close the high-risk
gaps. **Effort**: ~1 day for the audit; per-fix PRs as needed.

### Phase 3 Wave 2.6.qw — Production-readiness quick wins (1 PR)
G16-G18 + G21 (`/version`, version footer, deep health, smoke).
**Effort**: ~half day.

### Defer
- 2.3 UI polish (after security/audit are closed).
- 2.4 unified notification API (enhancement).
- 2.5 perf debt (trigger-based).
- 2.6 ops-level items (G19, G20, G22, G23).

---

## Risks if we accept this path

- The user's vision included "build a real dashboard" — they may want a more aggressive approach than "audit existing." If yes, we can do a UI overhaul wave after the security gaps.
- The `activity_logger.py` helpers are extensive but **may not all be wired** to actual call sites. Wave 2.1.b verifies this for worklogs; a similar audit for work_orders state changes would be a follow-up.

---

## Open product questions

| # | Question | Default |
|---|---|---|
| Q1 | Should ACCOUNTANT see all activity logs (system scope) or only financial-category? | Default: keep today's "my" scope; ACCOUNTANT has financial-category auto-filter. Promote only on explicit ask. |
| Q2 | Should `/activity-logs/{log_id}` apply same scope as list, or admin-only detail? | Default: same scope as list (matches the rest of Wave 3.1). |
| Q3 | Should we build a unified `notify(target, ...)` API in this wave? | Default: defer to 2.4. |

---

## Summary

- Wave 2 infrastructure is **mostly built**. The user's spec describes a vision; the codebase already has 80% of it.
- The actionable gaps are: **G1 (worklog logging)**, **G4 (activity-log detail leak)**, plus a dashboard scope audit.
- Recommended starting point: **Wave 2.1.a + 2.1.b in a single PR** (~1 day, ~15 tests). Closes the real security gap + plugs the visibility hole.
- 2.3 (UI polish) is the biggest scope but the lowest urgency. Best done as a separate, dedicated frontend wave after the backend audits are clean.

Awaiting approval to start with **2.1.a + 2.1.b**, or to redirect to a different sub-wave.
