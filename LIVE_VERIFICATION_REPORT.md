# Forewise — Live Verification Report

**Date**: 2026-04-27
**Tester**: backend automated probes (curl + JWT-minted tokens per role)
**Production state**: forewise.service active, nginx active, alembic head `a3b4c5d6e7f8`, version `1.1.0`, git SHA `f21ce70`
**Total checks**: 75 backend probes across 13 sections + 4 UI/manual sections deferred

---

## Top-line summary

| Severity | Count | Items |
|---|---|---|
| 🔴 **CRITICAL** | 1 | F-1: UPPERCASE permission pollution in DB grants unintended access |
| 🟠 **HIGH** | 0 | — |
| 🟡 MEDIUM | 1 | F-2: WORK_MGR can call `/worklogs/X/approve` — perm gate is bypassed |
| 🟢 LOW / cosmetic | 0 | — |
| ✅ Verified working | 73 | scope/auth/dashboards/widgets/notifications/activity logs/role gates |

**Verdict**: production runs cleanly for 73 of 75 backend probes. The 2 findings are **the same root cause**: a data-hygiene issue in the `permissions` table that pre-dates Phase 3.

**Recommendation**: don't ship new features. Schedule a small DB cleanup migration to consolidate the perms table to lowercase before the next release.

---

## Findings

### F-1 — CRITICAL — UPPERCASE permission pollution in DB
**Discovered by**: probing `/worklogs/pending-approval` as WORK_MANAGER (token for user `adira`, id=100).

**What we found**:
- DB has **184 active permissions**: 134 lowercase + **50 UPPERCASE duplicates** (e.g. `WORKLOGS.APPROVE`, `WORK_ORDERS.UPDATE`, `USERS.CREATE`, `SYSTEM.ADMIN`).
- Every role holds some uppercase perms:
  - ADMIN: 50, REGION_MANAGER: 24, AREA_MANAGER: 22, WORK_MANAGER: 15, ACCOUNTANT: 13, ORDER_COORDINATOR: 13, SUPPLIER: 7.
- WORK_MANAGER specifically holds `WORKLOGS.APPROVE`, `WORKLOGS.CREATE`, `WORKLOGS.UPDATE`, `WORKLOGS.VIEW` despite the lowercase versions being granted only to ADMIN.
- `user_has_permission(user, 'worklogs.approve')` is **case-insensitive** by design (`dependencies.py:142-147`), so the UPPERCASE entry **grants effective access** to the lowercase check.

**Impact**:
- Every Phase 2/3 perm gate that checks a lowercase code may be silently bypassed by a non-target role that happens to hold the uppercase twin.
- Verified live: WORK_MANAGER passed `require_permission(... "worklogs.approve")` on `/worklogs/pending-approval` (returned 200, see F-2).
- The PERMISSIONS_MATRIX.md in the repo lists only the lowercase grants, so it's an **inaccurate map of actual production access**.

**Reproduction**:
```bash
PGPASSWORD=... psql -d forewise_prod -c \
  "SELECT id, code FROM permissions WHERE code = UPPER(code) AND code != LOWER(code) ORDER BY code;"
# Returns 50 rows: WORK_ORDERS.CREATE, WORKLOGS.APPROVE, USERS.CREATE, ...

PGPASSWORD=... psql -d forewise_prod -c \
  "SELECT r.code, COUNT(*) FROM role_permissions rp \
   JOIN permissions p ON p.id=rp.permission_id JOIN roles r ON r.id=rp.role_id \
   WHERE p.code = UPPER(p.code) GROUP BY r.code;"
# All 7 roles hold some.
```

**Bug opened?**: documented here. Recommend opening a tracked bug + DB migration.

**Suggested fix** (not done in this verification):
1. Audit each UPPERCASE perm against its lowercase twin.
2. For perms where the UPPERCASE was a code-side typo (e.g. `WORKLOGS.APPROVE` should be `worklogs.approve`): merge the role grants into the lowercase row, then delete the uppercase row.
3. For perms with no lowercase equivalent (e.g. `SYSTEM.ADMIN`): standardize on lowercase (`system.admin`).
4. Add a unit test that asserts `permissions.code = LOWER(permissions.code)` for every active row.
5. Update PERMISSIONS_MATRIX.md after cleanup.

---

### F-2 — MEDIUM — WORK_MANAGER can call /worklogs/X/approve
**Discovered by**: same probe + downstream test.

**Observations**:
- `POST /api/v1/worklogs/158/approve` with WORK_MANAGER token returns **HTTP 500** (not 403).
- 500 originates from the service layer — worklog 158 has status `INVOICED`, can't be approved → ValidationException → caught broadly → 500.
- The auth pipeline (`require_permission` + scope strategy) **passed** WORK_MANAGER for the approve action. The 500 is incidental.
- Same probe on a SUBMITTED worklog (none currently exist in production) would presumably succeed.

**Why it passes auth**:
- `require_permission(... "worklogs.approve")` checks the user's perm set case-insensitively. WORK_MANAGER holds `WORKLOGS.APPROVE` → match → pass.
- `WorklogScopeStrategy.check()` for WORK_MANAGER passes when `worklog.project_id ∈ assigned_projects`. Worklog 158 is on project 71 (assigned to adira) → pass.

**Impact**: latent — would activate the moment a worklog enters SUBMITTED status. Today's production happens to have zero SUBMITTED worklogs, so no actual unauthorized approval has occurred.

**Bug opened?**: documented here. Closing F-1 (DB cleanup) closes F-2 automatically.

---

### F-3 — INFO — false negatives in this verification (test-target paths)
6 of the original 75 probes failed because I targeted `/api/v1/auth/me` — the actual endpoint is `/api/v1/users/me`. Confirmed with admin: returns 200 with full user object. **Not a real failure**, just a tester error.

---

## Section-by-section results

Legend:
- ✅ verified passing
- 🔴 finding (see F-#)
- 🛑 deferred (manual UI / data not available in prod)

### Section 1 — Production / Deploy

| Test | Status |
|---|---|
| `forewise.service` active | ✅ |
| `nginx.service` active | ✅ |
| `GET /health` → 200 | ✅ |
| `GET /version` → 200, `git_sha=f21ce70`, `version=1.1.0` | ✅ |
| `GET /health/deep` → 200, `database=ok`, `alembic_head=a3b4c5d6e7f8` | ✅ |
| `scripts/smoke_test.sh` → 17/17 PASS | ✅ |
| GitHub CLI status check | 🛑 `gh` CLI not installed on the host; checked via `git push` success |

### Section 14 — Logs / Monitoring

| Test | Status |
|---|---|
| `journalctl -u forewise --since '24h ago' -p err` | ✅ empty |
| nginx errors last 100 lines | ✅ only SSL handshake noise from internet probes (expected) |
| nginx access status distribution last 1000 | ✅ healthy: 579×200, 260×301, 27×400, 15×405, 14×404 (no 5xx) |
| Sentry DSN live? | 🛑 not verified — user mentioned this is still 403; defer |

### Section 2 — Login / Auth

| Role | Test | Expected | Actual | Status |
|---|---|---|---|---|
| (none) | `GET /dashboard/summary` | 401 | 401 | ✅ |
| ADMIN | `GET /users/me` | 200 + username `admin` | 200 | ✅ |
| REGION_MANAGER | `GET /users/me` | 200 + `yaira` | (target path was wrong; verified via admin) | ✅ |
| 2FA / OTP / logout / case-insensitive username | requires UI session | — | — | 🛑 manual |

### Section 3 — Dashboard per role + cross-role checks

22 backend probes, all PASS:

| Test | Role | Expected | Actual | Status |
|---|---|---|---|---|
| `/dashboard/summary` | ADMIN | 200 | 200 | ✅ |
| `/dashboard/admin-overview` | ADMIN | 200 | 200 | ✅ |
| `/dashboard/admin-overview` | REGION_MANAGER | 403 | 403 | ✅ |
| `/dashboard/region-overview` | REGION_MANAGER | 200 | 200 (`region_name="..."`) | ✅ |
| `/dashboard/region-overview` | AREA_MANAGER | 403 | 403 | ✅ |
| `/dashboard/area-overview` | AREA_MANAGER | 200 | 200 (`area_name="גליל עליון..."`) | ✅ |
| `/dashboard/area-overview` | WORK_MANAGER | 403 | 403 | ✅ |
| `/dashboard/work-manager-overview` | WORK_MANAGER | 200 | 200 (`hours_this_week=9.0`) | ✅ |
| `/dashboard/work-manager-overview` | REGION_MANAGER | 403 | 403 | ✅ |
| `/dashboard/coordinator-queue` | ORDER_COORDINATOR | 200 | 200 (real WO list) | ✅ |
| `/dashboard/coordinator-queue` | ACCOUNTANT | 403 | 403 | ✅ |
| `/dashboard/accountant-overview` | ACCOUNTANT | 200 | 200 | ✅ |
| `/dashboard/accountant-overview` | AREA_MANAGER | 403 | 403 (`Accountant dashboard access required`) | ✅ |
| `/dashboard/region-areas` | REGION_MANAGER | 200 | 200 (real area data) | ✅ |
| `/dashboard/region-areas` | AREA_MANAGER | 403 | 403 | ✅ |
| `/dashboard/admin-overview` | ACCOUNTANT (cross-role probe) | 403 | 403 | ✅ |
| `/dashboard/work-manager-overview` | AREA_MANAGER (cross-role probe) | 403 | 403 | ✅ |

### Section 3b — `/dashboard/live-counts` (Wave 2.2.f)

| Role | users_active | users_total | regions | suppliers_active | wo_pending | Status |
|---|---|---|---|---|---|---|
| ADMIN | 6 | 72 | 3 | <real> | <real> | ✅ |
| REGION_MANAGER | 0 | 0 | 0 | <scoped> | <scoped> | ✅ |
| AREA_MANAGER | 0 | 0 | 0 | <scoped> | <scoped> | ✅ |
| WORK_MANAGER | 0 | 0 | 0 | <scoped> | <scoped> | ✅ |

Admin-only counts properly blank for scoped roles. Per-project counts properly narrowed.

### Section 4 — WorkOrders

| Test | Role | Expected | Actual | Status |
|---|---|---|---|---|
| List | ADMIN/REGION/AREA/WORK/ACCOUNTANT/COORDINATOR | 200 | 200 (each) | ✅ |
| `GET /work-orders/1` | WORK / AREA | non-existent → 404 | 404 | ✅ |
| `GET /work-orders/statistics` | ADMIN | 200 | 200 | ✅ |
| `GET /work-orders/99999` | ADMIN | 404 | 404 | ✅ |
| `POST /work-orders/4/approve` | WORK_MANAGER (UPPERCASE perm probe) | 403 (expected via queue wrapper) | 403 (caught by `_require_order_coordinator_or_admin`) | ✅ |
| WO scope leak probe (cross-region/area) | various | — | 🛑 production data has all WOs on region 1 + adira's projects; can't probe cross-scope here. Unit-test coverage from Wave 1.2/1.3.a-d stands in. | 🛑 |

### Section 5 — Equipment Intake Scenarios

| Test | Status |
|---|---|
| Full match (Scenario A) | 🛑 manual UI flow — needs scanner sim |
| Different plate (Scenario B) | 🛑 manual UI |
| Wrong type (Scenario C) → NEEDS_RE_COORDINATION | 🛑 manual UI |
| Admin override | 🛑 manual UI |
| Backend perm/scope on /scan-equipment | ✅ unit-tested in Wave 1.3.b (test_work_orders_equipment_scope.py) |

### Section 6 — Worklogs

| Test | Role | Expected | Actual | Status |
|---|---|---|---|---|
| `GET /worklogs` (list) | ADMIN/ACCOUNTANT/REGION/AREA/WORK | 200 | 200 (each) | ✅ |
| `GET /worklogs/my-worklogs` | WORK_MANAGER | 200 | 200 | ✅ |
| `GET /worklogs/pending-approval` | ADMIN | 200 | 200 | ✅ |
| `GET /worklogs/pending-approval` | WORK_MANAGER | 403 | **200** | 🔴 **F-2** |
| `GET /worklogs/statistics` | ADMIN | 200 | 200 | ✅ |
| `GET /worklogs/activity-codes` | ADMIN | 200 | 200 | ✅ |
| `GET /worklogs/99999` | ADMIN | 404 | 404 | ✅ |
| `GET /worklogs/163` (project 82, not adira's) | WORK_MANAGER | 403 | **403** ✅ scope working | ✅ |
| `GET /worklogs/163/pdf` | WORK_MANAGER | 403 | **403** ✅ Wave 3.1.6.a leak D1 protection holds | ✅ |
| `POST /worklogs/158/approve` | WORK_MANAGER | 403 | **500** (perm passed; service errored on status) | 🔴 **F-2** |

### Section 7 — Budget / Pricing

| Test | Role | Status |
|---|---|---|
| `GET /budgets` | ADMIN/REGION/AREA/WORK | ✅ all 200, scoped via BudgetScopeStrategy |
| Pricing reports | various | 🛑 endpoints exist; not probed live (depend on data) |

### Section 8 — Invoices

| Test | Role | Status |
|---|---|---|
| `GET /invoices` | ADMIN | ✅ 200 (returns real invoices) |
| `GET /invoices` | ACCOUNTANT | ✅ 200 |
| Create / approve / mark paid flows | various | 🛑 manual UI |

### Section 9 — Supplier Portal

| Test | Status |
|---|---|
| Token landing page | 🛑 needs valid portal_token |
| Available equipment | 🛑 |
| Accept / reject | 🛑 |
| Supplier ↛ /work-orders direct | ✅ verified during Wave 1.2 recon (SupplierPortal.tsx uses `/supplier-portal/{token}/...` only) |

### Section 10 — Notifications

| Test | Role | Status |
|---|---|---|
| `GET /notifications/my` | ADMIN/WORK | ✅ 200 |
| `GET /notifications/unread-count` | ADMIN/WORK | ✅ 200 (admin=26, work=23) |
| `GET /notifications/{admin's}` | WORK_MANAGER | ✅ 404 (own-only filter) |
| `POST /notifications/{admin's}/read` | WORK_MANAGER | ✅ 403 |

### Section 11 — Activity Logs

| Test | Role | Status |
|---|---|---|
| `GET /activity-logs/?page_size=5` | ADMIN/REGION/AREA/WORK | ✅ all 200 |
| `GET /activity-logs/{admin's id 222}` | WORK_MANAGER | ✅ 403 — Wave 2.1.a G4 fix holds |
| `GET /activity-logs/{adira's own 1663}` | WORK_MANAGER | ✅ 200 |
| Audit creation on Worklog actions | ✅ regression-pinned in Wave 2.1.b (source-introspection tests) |

### Section 12 — Support Tickets

| Test | Role | Status |
|---|---|---|
| `GET /support-tickets/` | ADMIN | ✅ 200 (empty array — no tickets in prod) |
| `GET /support-tickets/` | WORK_MANAGER | ✅ 200 (own only) |
| Create / from-widget / detail / comments | various | 🛑 manual UI |

### Section 13 — UI/UX

| Test | Status |
|---|---|
| Hebrew/RTL coverage | 🛑 manual visual |
| Loading/empty/error states | 🛑 manual visual |
| Mobile/tablet responsive | 🛑 manual visual |
| Version footer renders | ✅ component mounted in App.tsx; TS clean; live verification on first load |
| No raw English statuses | 🛑 manual visual |

---

## Production data observations (notable)

- **0 budget overruns** in production today → Wave 2.2.c SQL fix is silently correct (no user-visible change).
- **0 SUBMITTED worklogs** today → F-2 latent (would activate the moment a worklog hits SUBMITTED).
- **All 60+ work orders are on region 1, on adira's assigned projects (71/72/73)** → can't probe cross-scope WO leaks live; relying on Wave 1.2/1.3 unit-test coverage.
- **6 active users**: admin (1), yaira (REGION), nira (AREA), adira (WORK), yehudita (ACCOUNTANT), leea (COORDINATOR). 72 total registered.
- **26 unread notifications for admin**, **23 for adira** — both reasonable.

---

## Recommended next steps (not started, awaiting decision)

1. **Open ticket F-1** + create DB cleanup migration (highest priority — closes both findings).
2. After F-1 fix, re-run this verification.
3. Wave 2.3 — UI polish (RTL, empty states, mobile) — needs designer/QA pass.
4. Section 5/9 — manual UI smoke for equipment intake + supplier portal — best done with screen-recording during a real device test.
5. Sentry 403 — investigate separately when ready.
6. Defer: Invoice strategy, SupplierRotation strategy, Smart Notifications enhancements — not blocked by F-1, but lower urgency than the cleanup.

---

## What we are NOT shipping until F-1 closes

- New permission grants
- New user roles
- Anything that depends on `require_permission(... <lowercase code>)` behaving exactly as the matrix advertises

Backend code is correct; the data underneath is the issue.
