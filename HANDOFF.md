# Forewise — Handoff Document

**תאריך**: 2026-04-22
**Repo**: `nirab96Developer/Forewise`, branch `main`
**Production**: `https://forewise.co` (server: 167.99.228.10)

---

## תשתית בפועל

- **Backend**: Gunicorn + 16 uvicorn workers דרך systemd (`forewise.service`), port 8000. *לא Docker.*
- **Frontend**: build סטטי ב-`/root/forewise/app_frontend/dist`, מוגש ע"י nginx.
- **DB**: PostgreSQL host-installed, `localhost:5432`, DB `forewise_prod`, user `forewise_app`.
- **CI/CD**: `.github/workflows/deploy.yml` ב-push ל-main → SSH לשרת:
  `git pull → pip install → pytest → DB backup → alembic upgrade → npm build → restart → health 90s → nginx reload`.
- **Docker files** קיימים אבל לא בשימוש בפרודקשן.
- **משתמשים**: 6 פעילים, סיסמה אחידה `Forewise2026!`, OTP ל-`avitbulnir+ROLE.x@gmail.com`:
  `admin`, `nira` (AREA), `yaira` (REGION), `adira` (WORK), `yehudita` (ACCOUNT), `leea` (COORDINATOR).

---

## מצב התחלה → סוף

- **Commit לפני הסבב**: `706132f` (mobile UX hardening)
- **Commit אחרון**: `01b3425` (Phase 3)
- **Diff**: 11 commits, 6 migrations חדשות, 34 קבצים, +2151/-275 שורות
- **CI status**: 2 הruns האחרונים ✅ success
- **alembic head**: `b9c0d1e2f3a4` (זהה בDB ובריפו)
- **pytest**: 174/174 passing

---

## Commits לפי סדר

| # | SHA | Phase | תוכן |
|---|---|---|---|
| 1 | `a6bd7ba` | 0 | 10 תיקוני ייצוב — PROD 500, /equipment-models/active, mark-paid, excel perms, otp cleanup, budgets case |
| 2 | `64e274b` | 1.1 | `budget_commitments` ledger — מחליף את המוטציה הסמויה של `committed_amount` |
| 3 | `81ba0a8` | 1.2 | `invoice_work_orders` — N:N link, מחליף 3-hop derivation דרך worklogs |
| 4 | `8b7e2a6` | 1.3 | rotation single-key — drop `equipment_category_id`, add `equipment_models.equipment_type_id` |
| 5 | `1ac7663` | CI | step של `pip install -r requirements.txt` |
| 6 | `ef36e1f` | 2.1 | CHECK constraints על 5 status columns |
| 7 | `1f8e159` | 2.2 | `authService.refreshCurrentUser()` אחרי login (DB = source of truth) |
| 8 | `323a366` | 2.3 | dashboard read-only + URL `?focus=` ל-`/order-coordination` |
| 9 | `f2beb2e` | CI fix | יצירת `requirements.txt` שלא היה בריפו (136 packages, exact versions) |
| 10 | `09073d2` | test fix | התאמת mock אחרי Phase 1.1 split |
| 11 | `01b3425` | 3 | equipment hierarchy — typo fix + backfill `equipment.category_id` (272→1024) |

---

## Migrations שהוחלו (head = `b9c0d1e2f3a4`)

| Phase | Revision | תוכן |
|---|---|---|
| 0 | `c4d5e6f7a8b9` | normalize budgets.status → UPPERCASE |
| 1.1 | `d5e6f7a8b9c0` | create `budget_commitments` + reconcile legacy `committed_amount` |
| 1.2 | `e6f7a8b9c0d1` | create `invoice_work_orders` + backfill מ-`invoice_items` |
| 1.3 | `f7a8b9c0d1e2` | drop `supplier_rotations.equipment_category_id`; add `equipment_models.equipment_type_id` עם backfill |
| 2.1 | `a8b9c0d1e2f3` | CHECK constraints על work_orders/worklogs/invoices/budgets/budget_commitments status |
| 3 | `b9c0d1e2f3a4` | typo fix T2 + backfill `equipment.category_id` 752 שורות |

---

## באגים אמיתיים שתוקנו

1. **🔥 PROD 500 על `send-to-supplier`** — FK violation; תוקן ב-Phase 0, גוצב ב-Phase 1.3.
2. **🔥 `mark-paid` לא שחרר frozen budget** — תקציבים committed לנצח. תוקן ב-Phase 0 + שיפור ב-Phase 1.2.
3. **🔥 שחרור freeze ביצירת invoice עם actual=0** — שיחרר בלי לרשום spend. הוסר ב-Phase 0.
4. **🔴 `/suppliers/equipment-models/active` → 404** — 10 hits/יומיים. נוסף `/equipment-models/active`.
5. **🔴 `/excel-export/excel` בלי הרשאות** — תוקן ב-Phase 0.
6. **🟡 `PATCH /supplier-constraint-reasons/{id}` → 405**. תוקן ב-Phase 0.
7. **🟡 `budgets.status` mixed case**. תוקן.
8. **🧹 7 שיטות זומבי ב-supplierService.ts** שפנו ל-endpoints שלא קיימים. נמחקו.
9. **🧹 `requirements.txt` חסר בריפו** — נוצר.

---

## חוב טכני שנדחה במכוון

1. **Phase 2.1b**: לנעול `users.status`, `projects.status`, `equipment.status` ב-CHECK. צריך normalize ידני קודם.
2. **Phase 3 cutover**: `budgets.committed_amount`, `budgets.spent_amount`, `work_orders.frozen_amount`, `work_orders.remaining_frozen` — עדיין dual-write. להחליף ב-computed views ולהפיל בעוד ~3 שבועות של ייצוב.
3. **8 budgets שמצביעים ל-projects מחוקים** — data integrity מינורי.
4. **`pricing_overrides` table לא קיים ב-DB** למרות שיש מודל.
5. **Dockerfile + docker-compose.yml** — לא בשימוש. למחוק או לסמן ב-README.

---

## Live Tests שצריך לרוץ עליהם בצ'אט הבא

| Phase | מסך | מה לבדוק |
|---|---|---|
| 0 | `/order-coordination` | "סוג ציוד" מציג שם אמיתי, לא "לא צוין" |
| 0 | send-to-supplier | אין 500, סטטוס משתנה ל-DISTRIBUTING |
| 0 | `/settings/constraint-reasons` | toggle is_active עובד |
| 1.1 | יצירת WO + DB | `SELECT * FROM budget_commitments WHERE work_order_id=<חדש>` → שורת FROZEN |
| 1.1 | mark-paid | commitment עובר ל-SPENT, `spent_amount` מתעדכן |
| 1.2 | יצירת invoice חודשית | `SELECT * FROM invoice_work_orders WHERE invoice_id=<חדש>` |
| 1.3 | DB | `SELECT equipment_type_id FROM supplier_rotations` — לא NULL בWOs חדשים |
| 2.2 | login + DevTools Network | רואים `GET /api/v1/users/me` רץ אחרי `/auth/verify-otp` |
| 2.3 | dashboard coordinator | אין כפתורי action, רק "טפל" שמוביל ל-`/order-coordination?focus=<id>` |
| 3 | DB | `SELECT COUNT(*), COUNT(category_id) FROM equipment` → 1026/1024 |

---

## הוראה לצ'אט הבא

> ממשיך מסבב Phase 0–3 שהושלם ב-`main`. כל ה-CI ירוק, alembic head `b9c0d1e2f3a4`.
> השלב הבא: לבדוק flows עסקיים בלייב על `https://forewise.co` לפי הטבלה ב-HANDOFF.md.
> אחרי שכל ה-flows עובדים, להחליט על Phase הבא (אופציות: 2.1b, Phase 3 cutover מלא, או משהו חדש).
> לקרוא את `/root/forewise/HANDOFF.md` לכל ההקשר.
