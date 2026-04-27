# Forewise — UI Redesign / UX Proposal

**Date**: 2026-04-27
**Status**: Proposal only. No code changes yet.
**Audience**: product owner + frontend lead.
**Goal**: identify the UX rough edges in the current 10-dashboard, RTL,
Hebrew system, and propose a focused improvement path that respects
the recent backend lockdown work (Phase 3).

---

## 1. Current state — what's actually shipped

### 1.1 Inventory

- **10 role-specific dashboard components** in `pages/Dashboard/`:
  Admin, Region/Area/WorkManager, Coordinator, Accountant,
  FieldWorker, SupplierManager, Viewer, Default.
- **Dynamic side menu** (`menuConfig.ts`, 513 lines, ~30 menu items
  filtered per-role).
- **Common components**: `UnifiedLoader`, `Toast`, `Card`, modals,
  table widgets, brand splash.
- **Hebrew + RTL** baked in (`dir="rtl"` everywhere I checked,
  text-right alignment, lucide-react icons mirrored implicitly via
  flex direction).
- **Mobile awareness**: `useIsMobile` hook drives a drawer-style
  navigation + responsive grid breakpoints (sm: lg:).
- **Visual brand**: dark green gradient header on every dashboard,
  white KPI cards with colour-tinted icons, gray-50 page background.

### 1.2 Style snapshot (what every dashboard does today)

```
┌─────────────────────────────────────────────────────┐
│  GREEN GRADIENT HEADER                              │
│  greeting + role-name + 1-line summary + [רענן]    │
└─────────────────────────────────────────────────────┘

┌──── KPI ────┐ ┌──── KPI ────┐ ┌──── KPI ────┐ ┌── KPI ──┐
│ icon + 2xl  │ │             │ │             │ │         │
│ number +    │ │             │ │             │ │         │
│ tiny label  │ │             │ │             │ │         │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────┘

[ alert strip if any — colored row ]

┌── primary content (table / activity feed / queue) ──┐ ┌─ side ─┐
│                                                      │ │ quick  │
│                                                      │ │ actions│
│                                                      │ │        │
└──────────────────────────────────────────────────────┘ └────────┘
```

### 1.3 File-size signal (proxy for screen complexity)

| Dashboard | Lines | Complexity |
|---|---|---|
| AccountantDashboard | **541** | very dense — modal, filters, audit trail, invoice selection |
| DefaultDashboard | 554 | high — fallback shows lots |
| OrderCoordinatorDashboard | 334 | medium-high |
| AreaManagerDashboard | 254 | medium |
| AdminDashboard | 217 | medium |
| RegionManagerDashboard | 214 | medium |
| WorkManagerDashboard | 179 | medium |
| Dashboard.tsx (router) | 79 | small (just role-routing) |
| FieldWorkerDashboard | 10 | placeholder |
| SupplierManagerDashboard | 18 | placeholder |
| ViewerDashboard | 18 | placeholder |

**Three placeholders ship in production** — FieldWorker, SupplierManager,
Viewer fall back to empty-ish screens.

---

## 2. UX issues observed

### 2.1 HIGH-impact (frequent, irritating, role-blocking)

| # | Issue | Where | Impact |
|---|---|---|---|
| **U-1** | Accountant dashboard is **541 lines in one screen** — KPIs + filter bar + table + per-row actions + modal with audit trail + invoice selection bar. It works but it's overwhelming. | `AccountantDashboard.tsx` | the most-used screen by the most-loaded role; primary daily-driver. |
| **U-2** | Top-line KPIs are **just numbers**, no trend, no sparkline, no period context. "26 unread notifications" — better than yesterday or worse? Don't know. | every dashboard | hard to spot-trend operational health. |
| **U-3** | The same green-gradient header pattern repeats verbatim across 10 dashboards — **no role-specific visual identity**. ADMIN and FIELD_WORKER look 95% identical. | every dashboard | reduces "I'm in the right place" feedback for the user. |
| **U-4** | **3 placeholder dashboards** ship: FieldWorker (10 lines), SupplierManager (18), Viewer (18). Users with these roles land on a near-empty page after login. | Dashboard router | broken first impression. |
| **U-5** | Side menu has **30+ items** filtered per role (`menuConfig.ts:513 lines`), but **no grouping** — items are listed flat. Region manager gets a long unstructured scroll. | `menuConfig.ts` | menu "wall of text"; navigation slow; no visual hierarchy beyond `dividerAfter`. |
| **U-6** | Quick Actions block is **identical for every role** in the layout (vertical stack of buttons, right column on desktop) but content differs. Could become a flexible pattern. | most dashboards | not a problem now, but each new role copies the same 4-button block. |
| **U-7** | Tables are **plain rows** with mixed-density cells. Long projects/work-orders don't paginate visibly; the user has to scroll inside a fixed-height div. No sticky header. | accountant + coordinator queues | tedious for daily use. |

### 2.2 MEDIUM-impact

| # | Issue |
|---|---|
| U-8 | Loading states use a single `UnifiedLoader` overlay. Skeleton-style placeholders would feel faster on slow networks. |
| U-9 | Empty states are mostly plain text ("אין פעולות אחרונות"). No illustration, no "what does this mean / what to do next" guidance. |
| U-10 | Error states for failed API calls fall back to "שגיאת שרת" toast — no actionable next step (retry, contact admin, reload). |
| U-11 | Refresh is manual everywhere (a `[רענן]` button in the header). No auto-refresh, no "X seconds ago" freshness indicator. |
| U-12 | The filter bars in Accountant + Coordinator screens use small `<select>` + `<input>` elements — workable on desktop, cramped on mobile. |
| U-13 | Status pills (`SUBMITTED`, `IN_PROGRESS`, `APPROVED_AND_SENT`) are **English in some places, Hebrew in others** depending on whether the screen routes through `getWorklogStatusLabel` / `getWorkOrderStatusLabel`. Inconsistent. |
| U-14 | Date formatting is inconsistent: ISO in some places (`2026-04-27`), `dd/mm/yyyy` in others, "לפני 3 שע׳" relative time in audit trails. Mix is OK if intentional but it's not. |
| U-15 | Notifications list (bell icon dropdown vs `/notifications` page) has two separate UX paths and they don't mirror each other's actions exactly. |

### 2.3 LOW-impact / cosmetic

| # | Issue |
|---|---|
| U-16 | Green-gradient header is taller on mobile than it needs (`p-5 sm:p-6`). Eats first-paint screen real-estate. |
| U-17 | KPI numbers use the system font's regular weight — `font-bold` would help readability at the typical 2xl size. (Some dashboards already do this; not all.) |
| U-18 | The bug-icon debug button in dev mode (`Ctrl+Shift+D`) is wired but the panel itself isn't rendered — dead UI for now. |
| U-19 | Version footer (Wave 2.6) is at `bottom-1 left-2` with text-`[10px]` — visible but very low-contrast (`text-gray-400`). On a white background it's almost invisible. |
| U-20 | Some role dashboards lack a "back to top" or "scroll-to-top" affordance once the table is long. |

---

## 3. Proposed redesign — per role

The proposal is **incremental**, not a re-skin. Each role keeps its
URL, its component file, and its API contract. Visual changes go
inside the existing component shells.

### 3.1 ADMIN
**Today**: 4 KPI cards (users / suppliers / projects / alerts) + activity feed + 4-button quick actions.

**Proposal**:
- Replace single-number KPIs with **mini sparkline** showing last-14-day trend (admin-overview already returns `wo_chart` + `wl_chart`).
- Activity feed is good but limit to 10 items + "טעינת עוד" → don't render 400px scroll div.
- Quick actions: **2 columns of 2** instead of 4-stacked; faster scan.
- Add **system-health pill** at the top of the header: "כל המערכות פועלות" / "DB error" — pulled from `/health/deep`.

**Wireframe (verbal)**:
```
[gradient header]
  Right side: greeting + "ניהול מערכת" + alerts summary
  Left side: [system health pill: green dot "הכל תקין"] + [רענן]

[KPI row × 4]
  Each card: icon + number + 14-day mini-sparkline (svg)

[alerts strip if any]

[2/3]: activity feed (10 items, "טעינת עוד" footer)
[1/3]: quick actions (2×2 grid)
```

### 3.2 REGION_MANAGER
**Today**: 6 KPIs (budget total/spent/committed/util%/open WOs/overrun areas) + areas table + 14-day WO trend.

**Proposal**:
- KPIs grouped: **financial column** (total / spent / util%) and **operational column** (open WOs / stuck / overrun).
- Areas table → **map view by default** (the `/dashboard/map` data we already serve), **table view as toggle**. Region managers think geographically.
- WO trend chart: keep, but as a small embedded card not full-width.
- Add **"my areas at-a-glance" sparkline grid**: each area gets its own tiny card with name + util% + open-WO count.

### 3.3 AREA_MANAGER
**Today**: 5 KPIs (open WOs / stuck / pending approval / draft invoices / total projects) + budget block + WO list (10 rows) + pending approvals list (10 rows).

**Proposal**:
- **Two-column main layout**: left "WOs requiring attention" (stuck + pending), right "Worklogs awaiting my action".
- **Inline approve/reject buttons** on the worklog list — currently you must click into the worklog detail page. Save 2 clicks.
- Budget block: graphical bar (spent/committed/remaining as stacked horizontal bar), not 4 numbers.
- "אזור: גליל עליון ורמת הגולן" badge in the header — area managers need constant orientation.

### 3.4 WORK_MANAGER
**Today**: 4 KPIs (hours-this-week / open WOs / equipment-in-use / pending worklogs) + 2 quick action buttons + my-projects card list.

**Proposal**:
- **Today-focused layout**: top of screen = "what do I need to do today".
  - Pending scans card with big tap target
  - Pending worklogs card with deep link to /work-logs/new/{wo_id}
- KPIs move to a thin secondary row, not the visual focus.
- "My projects" → **status-coloured tiles** (green/yellow/red dot) instead of plain card list — work managers want to scan health quickly.
- Add **"area manager contact" pill** in the header (we already fetch this in `work-manager-summary`) — one tap to call.

### 3.5 ORDER_COORDINATOR
**Today**: huge work-orders queue (50 rows) with filter bar + KPI strip + alert badges.

**Proposal**:
- Queue view = **kanban columns by status** (PENDING → DISTRIBUTING → SUPPLIER_ACCEPTED → APPROVED_AND_SENT → EXPIRED), each card draggable to next stage. Coordinators dispatch all day; columns map to their mental model.
- Filter bar collapses into a single **"חיפוש מתקדם"** drawer.
- Each WO card has: order number, supplier name, time-since-sent (with a colour ramp green→yellow→red as it approaches the 3h portal expiry), 1-tap "שלח לספק הבא".
- Forced-selection (`is_forced`) cards get a special border + tooltip with the constraint reason.

### 3.6 ACCOUNTANT (largest UX win opportunity)
**Today**: 6 KPIs + filter bar + worklogs table + per-row preview button + modal with full detail + audit trail + invoice selection.

**Proposal**:
- **Split into two views** with a tab switcher:
  - **"דיווחים לאישור"** (default) — cleaner table, sticky header, per-row "אשר/דחה" buttons inline, no modal opens for routine actions.
  - **"חשבוניות"** — separate view; takes the invoice-selection logic that's currently bolted onto the worklogs page.
- Modal redesign: when the user does need to drill in, the modal is **3 tabs**: Details / Audit Trail / Linked Invoice — easier than 1 long scrolling sheet.
- KPIs: keep the 6 but use **traffic-light backgrounds** (red if anomalies > 0, amber if pending > 5, etc.).
- **Bulk actions toolbar** appears only when ≥1 row is selected (currently always-on at the bottom).

### 3.7 FIELD_WORKER (currently 10 lines!)
**Today**: empty placeholder.

**Proposal**:
- Big "סרוק כלי" card with camera icon — primary action.
- "הדיווחים שלי" list — 5 most recent.
- "עזרה" button → opens the support chat widget.
- That's it. Field workers don't need 14 KPIs.

### 3.8 SUPPLIER_MANAGER, VIEWER, DEFAULT
Either:
- Build them out properly (each ~150 lines, like WorkManager).
- Or **delete the routes** and route those role codes to a clear "אין דשבורד מותאם — צור קשר עם מנהל מערכת" page.

Recommendation: delete + redirect. Don't ship empty placeholders.

---

## 4. Quick wins (low effort, high visibility)

| # | Item | Effort | Impact |
|---|---|---|---|
| Q-1 | **Standardize status pills via central dictionary** — make sure every status reference goes through `getWorkOrderStatusLabel` / `getWorklogStatusLabel`. Eliminates U-13. | ~4h | every screen consistent. |
| Q-2 | **Bump version footer contrast**: change `text-gray-400` → `text-gray-600` and `[10px]` → `text-xs`. Still small, but readable. | 5 min | U-19 closes. |
| Q-3 | **Add "X seconds ago" freshness indicator** below the [רענן] button on each dashboard, so users know how stale the data is. | ~2h | U-11 partial. |
| Q-4 | **Skeleton loaders** for the 3 most common screens (accountant table, coordinator queue, region overview). | ~1d | U-8 partial; perceived perf jump. |
| Q-5 | **Empty-state component**: 1 reusable `<EmptyState icon title hint actionLabel onAction>`. Replace ~15 inline empty divs across the codebase. | ~half day | U-9 closes. |
| Q-6 | **Delete the 3 placeholder dashboards** and redirect to a meaningful page. | 1h | U-4 closes. |
| Q-7 | **Sticky table headers** on accountant + coordinator queues. | ~1h | U-7 partial. |
| Q-8 | **Date formatting helper**: every date renders through `formatDate(d, mode)` with modes `short` / `long` / `relative`. | ~2h | U-14 closes. |

**Total estimate**: ~3–4 days of focused frontend work, no backend.

---

## 5. Bigger changes (medium-large effort)

| # | Item | Effort | Notes |
|---|---|---|---|
| B-1 | **Split AccountantDashboard** into 2 views (worklogs / invoices). | 3–5 days | biggest single UX win. |
| B-2 | **Coordinator queue → kanban with drag-and-drop**. | 5–7 days | user love-it/hate-it; pilot with 1 coordinator first. |
| B-3 | **Region manager map-first view**. | 4–6 days | needs Google Maps tile integration we already have. |
| B-4 | **Sparkline KPI cards** on Admin + Region. | 2–3 days | requires the backend to expose 14-day series (most already do). |
| B-5 | **Side menu grouping + sub-headers** (e.g. "ניהול תפעולי" / "פיננסי" / "מערכת"). | 1–2 days | `menuConfig.ts` refactor. |
| B-6 | **FieldWorker dashboard** built out properly. | 2 days | huge for that role's daily flow. |

---

## 6. Frontend-only items (no backend touch)

All of these can ship without a backend release:

- All Quick Wins (Q-1 through Q-8)
- B-5 (menu grouping)
- AccountantDashboard split (B-1) — same backend endpoints
- Status pill consistency (Q-1)
- Empty/loading/error state components
- Mobile drawer polish
- Color/spacing tokens consolidation

---

## 7. Items that need backend support

- **B-4 (sparklines)**: most are present (`wo_chart`, `wl_chart` in `/admin-overview`); **`/region-overview` and `/area-overview` would benefit from a 14-day series for THEIR scope**. Currently they only have a single-day count.
- **B-2 (kanban)**: would need a `PATCH /work-orders/{id}/move-to-stage` endpoint or reuse existing approve/reject — preferable.
- **B-3 (map-first)**: `/dashboard/map` already exists; for Region we'd need it to return scope-filtered points (currently global for non-region/area).
- **Q-3 (freshness)**: zero backend change — just `Date.now() - lastFetchedAt`.
- **B-1 (accountant split)**: zero backend change — same data sources.

So roughly **3 endpoints need light additions** to support the bigger frontend changes; everything else is frontend-only.

---

## 8. Recommended path forward

A 3-track plan:

### Track A — Quick Wins sprint (1 week, frontend only)
Q-1, Q-2, Q-5, Q-6, Q-7, Q-8 + Q-3 + Q-4. ~10 small PRs. Closes 6 of the 15 issues; immediate UX uplift. **No risk.**

### Track B — Accountant + FieldWorker rebuild (2 weeks)
B-1 + B-6. Largest UX wins; both are frontend-only. **Pilot with 1 user from each role before merging.**

### Track C — Strategic redesign (4–6 weeks)
B-2 (kanban), B-3 (map-first), B-4 (sparklines), B-5 (menu groups). Heavier, requires design review + 3 backend tweaks. Schedule **after** F-1 from the live verification report is closed.

---

## 9. What we are NOT proposing

- ❌ Full design-system rewrite (Storybook, design tokens, theme switcher) — way out of scope; would cost months and the current visual is fine.
- ❌ Switching to a UI kit (Mantine, Chakra, MUI). The bespoke Tailwind approach works.
- ❌ Mobile-first reflow. Mobile already works ok via `useIsMobile`; polish via Q-4/Q-5 is enough for now.
- ❌ Renaming the routes / changing the menu structure for users. Continuity matters more than purity.
- ❌ Light-mode variants, dark-mode, accessibility audit. These are real but separate efforts.

---

## 10. Decision points (for product/design)

1. **Approve Track A (Quick Wins) immediately?** Default: yes. Pure frontend, ~1 week.
2. **B-1 (accountant split) — pilot or ship-direct?** Default: pilot with `yehudita` for 3 days, then ship.
3. **B-2 (kanban) — feasibility test?** Default: prototype on a feature branch, get coordinator feedback, decide.
4. **B-6 (FieldWorker buildout) — when?** Default: after F-1 closes (live-verification dependency).
5. **3 placeholder dashboards — delete or build?** Default: delete + redirect to a "no dashboard" page; build only when the role becomes actually used.

---

## Appendix — the central rule for every change

> **Don't break what works.** All ~73 backend probes pass live; the
> backend is in a good state. Frontend changes must keep the same API
> contracts and the same role gates. UX improvements, not API redesigns.

If a UX change reveals a backend gap, document it and route it back
through the recon → wave loop we've used in Phase 3.
