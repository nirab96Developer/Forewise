# Forewise — Handoff Document

**תאריך עדכון אחרון**: 2026-04-25
**Repo**: `nirab96Developer/Forewise`, branch `main`
**Production**: `https://forewise.co` (server: 167.99.228.10)
**מצב**: ✅ Phase 2 (Permission Enforcement) **נסגר**. ממתין לבדיקה ידנית בלייב לפני המשך.

---

## תשתית בפועל

- **Backend**: Gunicorn + 16 uvicorn workers דרך systemd (`forewise.service`), port 8000. *לא Docker.*
- **Frontend**: build סטטי ב-`/root/forewise/app_frontend/dist`, מוגש ע"י nginx.
- **DB**: PostgreSQL host-installed, `localhost:5432`, DB `forewise_prod`, user `forewise_app`.
- **CI/CD**: `.github/workflows/deploy.yml` ב-push ל-main → SSH לשרת:
  `git pull → pip install → pytest (CI subset) → DB backup → alembic upgrade → npm build → restart → health 90s → nginx reload`.
- **Docker files** קיימים אבל לא בשימוש בפרודקשן.
- **משתמשים**: 6 פעילים, סיסמה אחידה `Forewise2026!`, OTP ל-`avitbulnir+ROLE.x@gmail.com`:
  `admin`, `nira` (AREA), `yaira` (REGION), `adira` (WORK), `yehudita` (ACCOUNT), `leea` (COORDINATOR).

---

## מצב נוכחי (אחרי Phase 2)

| מטריקה | ערך |
|---|---|
| Commit אחרון | `71be490` (audit tooling extractor fix) |
| **alembic head** | `a3b4c5d6e7f8` (DB == repo) |
| **CI subset tests** | **370/370** passing |
| **🔴 critical (real)** | **0** — כל ה-35 שנותרו ב-matrix הם false positives מתועדים |
| **🟢 enforced** | 350/418 endpoints |
| **DB perms** | 184 (התחלנו עם 169) |
| Service | `active`, `/health` 200 |

---

## Phases שהושלמו

### סבב ראשון — Phase 0–3 (commits `a6bd7ba` … `01b3425`)
- Phase 0: 10 תיקוני ייצוב (PROD 500, mark-paid, excel perms, OTP cleanup)
- Phase 1.1: `budget_commitments` ledger
- Phase 1.2: `invoice_work_orders` (N:N)
- Phase 1.3: rotation single-key (`equipment_type_id`)
- Phase 2.1: CHECK constraints על 5 status columns
- Phase 2.2: `authService.refreshCurrentUser()` post-login
- Phase 2.3: dashboard read-only + URL `?focus=`
- Phase 3: equipment hierarchy backfill (272→1024)

### סבב סגירה (commit `487a277`)
- 18 missing imports ב-`__init__.py` → `alembic check` עובד
- מחיקת `pricing_override`, `routers/invoice_items.py`, 3 קבצי טסט שבורים
- מיגרציה `c0d1e2f3a4b5`: `work_order_coordination_logs` + data hygiene

### Phase 2 — Permission Enforcement (16 commits, `2a790d5` … `71be490`)

| Wave | תוכן | Commit |
|---|---|---|
| 1.A | auth admin endpoints (lock/unlock/audit/login-attempts) | `2a790d5` |
| 1.B+1.C | sessions ownership + 2FA verify-setup vulnerability fix | `f1055c5` |
| 5 | budgets scope helper (3 financial leaks סגרו) | `57c7705` |
| 6 | equipment scan + release | `9a20c2b` |
| 7.A | seed migration: 9 perms | `11720f4` |
| 7.B | system_rates → `system.settings` | `61ae94a` |
| 7.C | activity_types (היו anonymous!) | `9e45e08` |
| 7.D | supplier_rotations + scope helper | `ed4227f` |
| 7.E.1 | seed migration: 6 project_assignments perms | `14ee782` |
| 7.F | extractor + recon | `c0be1bc` |
| 7.G | notifications: 5 admin + 4 ownership | `b887574` |
| 7.H | pricing reports → `budgets.read` | `f1fa05d` |
| 7.I | support_tickets ownership lock-in | `210be5b` |
| 7.J | edge cases: otp/cleanup, wo-coord-logs, sync | `b535b88` |
| Cleanup | 2 handler bugs (SystemRate, supplier_rotations) | `3925d77` |
| Dashboard | 23 endpoints + revoke SUPPLIER | `53f0e7c` |
| Audit fix | extractor recognizes Depends wrappers | `71be490` |

---

## Migrations שהוחלו (head = `a3b4c5d6e7f8`)

| Phase | Revision | תוכן |
|---|---|---|
| 0 | `c4d5e6f7a8b9` | normalize budgets.status |
| 1.1 | `d5e6f7a8b9c0` | create `budget_commitments` |
| 1.2 | `e6f7a8b9c0d1` | create `invoice_work_orders` |
| 1.3 | `f7a8b9c0d1e2` | drop `equipment_category_id`; add `equipment_type_id` |
| 2.1 | `a8b9c0d1e2f3` | CHECK constraints על 5 status columns |
| 3 | `b9c0d1e2f3a4` | equipment.category_id backfill |
| sealing | `c0d1e2f3a4b5` | wo_coord_logs + data hygiene |
| 7.A | `e1f2a3b4c5d6` | seed 9 perms (supplier_rotations + activity_types + notifications) |
| 7.E.1 | `f2a3b4c5d6e7` | seed 6 project_assignments perms |
| Dashboard | `a3b4c5d6e7f8` | revoke DASHBOARD.VIEW מ-SUPPLIER |

---

## ה-35 false positives ב-matrix (לא לטפל)

| Domain | כמות | הסבר |
|---|---|---|
| auth | 15 | self-service via `current_user.id` (Wave 1.B/1.C audited) |
| notifications | 4 | mark-as-read self-service (Wave 7.G ownership נוסף) |
| support_tickets | 3 | self-service POSTs (Wave 7.I lock-in) |
| journal | 3 | `/users/me/*` path constraint |
| otp | 2 | login flow (חייב anonymous) |
| activity_types | 2 | public lookup reads |
| 6 שונות | 6 | wrappers, public widgets, batch sync |

ראה `WAVE7F_RECON.md` לdrill-down.

---

## חוב טכני שעדיין פתוח (לא במסגרת Phase 2)

1. **Phase 2.1b**: לנעול `users.status`, `projects.status`, `equipment.status` ב-CHECK. דורש normalize ידני קודם.
2. **Phase 3 cutover**: dual-write columns על budgets/work_orders. להחליף ב-computed views אחרי ~3 שבועות ייצוב.
3. **Dockerfile + docker-compose.yml** — לא בשימוש. למחוק או לסמן.
4. **alembic drift קיים-מלפני** (4 מודלים בלי טבלה, 9 טבלאות בלי מודל). לא משפיע runtime, דורש החלטה אסטרטגית.
5. **5 שירותים בלי route** — מיובאים ב-`services/__init__.py` אבל לא נקראים. למחוק או לחבר.

---

## ✅ Smoke Tests עסקיים — לבצע בלייב לפני Phase הבא

### לכל role: כניסה דרך OTP
| Role | User | OTP destination |
|---|---|---|
| ADMIN | `admin` | `avitbulnir+ADMIN.x@gmail.com` |
| REGION | `yaira` | `avitbulnir+REGION.x@gmail.com` |
| AREA | `nira` | `avitbulnir+AREA.x@gmail.com` |
| WORK | `adira` | `avitbulnir+WORK.x@gmail.com` |
| ACCOUNTANT | `yehudita` | `avitbulnir+ACCOUNT.x@gmail.com` |
| COORDINATOR | `leea` | `avitbulnir+COORDINATOR.x@gmail.com` |

### בדיקות לפי תפקיד

**ADMIN** — חייב לראות הכל:
- [ ] Dashboard נטען עם כל המידע
- [ ] גישה ל-`/settings`, `/users`, `/admin`
- [ ] יכול לסגור OTPים (`POST /otp/cleanup` → 200)
- [ ] יכול ליצור system rate (`POST /system-rates` → 200)
- [ ] יכול לעדכן/מחוק activity_type
- [ ] יכול לראות כל budget detail/committed/spent

**REGION_MANAGER** — רק במרחב שלו:
- [ ] Dashboard מציג רק נתוני המרחב
- [ ] `/budgets/{id}/detail` של תקציב במרחב אחר → 403
- [ ] `/supplier-rotations` מציג רק את המרחב
- [ ] יכול ליצור/לעדכן project_assignment + complete

**AREA_MANAGER** — רק באזור שלו:
- [ ] Dashboard מציג רק נתוני האזור
- [ ] בודקת זמינות + קונפליקטים (חדש מ-Wave 7.E.1)
- [ ] לא יכולה לעדכן rotation (אין perm) → 403

**WORK_MANAGER** — רק פרויקטים שמוקצים:
- [ ] רואה רק WOs של פרויקטים שלו
- [ ] יכול לסמן project_assignment כ-completed (חדש מ-Wave 7.E.1)
- [ ] לא רואה תקציבים של פרויקטים אחרים → 403

**ACCOUNTANT** — לפי area/region:
- [ ] רואה pricing reports (חדש מ-Wave 7.H)
- [ ] רואה budget detail/committed/spent
- [ ] לא יכולה לסגור system_rates → 403
- [ ] לא יכולה לעדכן activity_types → 403

**ORDER_COORDINATOR** — global, queue:
- [ ] `/order-coordination` נטען עם תור WOs
- [ ] יכול ליצור coordination log (חדש מ-Wave 7.J) → 200
- [ ] יכול ליצור supplier rotation
- [ ] לא יכול למחוק rotation (admin only) → 403

**SUPPLIER** — חיצוני, מוגבל:
- [ ] **Dashboard → 403** (חדש מ-Dashboard wave)
- [ ] לא רואה pricing reports → 403
- [ ] לא רואה budgets → 403
- [ ] לא רואה supplier_rotations → 403
- [ ] יכול לסרוק equipment ב-WO שלו (Wave 6)
- [ ] לא יכול release equipment (admin/coordinator only) → 403

### בדיקות UX עברית
- [ ] כל הסטטוסים בעברית, אין fallback `'—'` (חוץ מ-NULL אמיתי)
- [ ] פרויקטים `inactive` מציגים "לא פעיל" (לא "—")
- [ ] תקציבים DRAFT מציגים "טיוטה"
- [ ] שגיאות 403 מציגות הודעה ברורה
- [ ] coordinator queue: שגיאות טעינה לא נעלמות בשקט (console.warn)

---

## הוראה לצ'אט הבא

> Phase 2 (Permission Enforcement) הושלם.
> 16 commits, 3 migrations חדשות, 196 tests חדשים, 0 real holes פתוחים.
> alembic head: `a3b4c5d6e7f8`. CI ירוק. Service active.
>
> **לפני שמתחילים פיתוח חדש**:
> 1. להריץ smoke tests לפי הטבלה למעלה (לכל 6 התפקידים)
> 2. לאמת בלייב שאין פעולה שנשברה
> 3. לעדכן את HANDOFF עם תוצאות
>
> רק אחרי אישור manual — להתחיל Phase 3 (אופציות):
>   - Phase 2.1b (CHECK על users/projects/equipment status)
>   - Phase 3 cutover (להפיל dual-write columns)
>   - חוב טכני #4–5 (drift + שירותים יתומים)
>
> לקרוא: `HANDOFF.md`, `PERMISSIONS_MATRIX.md`, `WAVE7F_RECON.md`.