# Forewise — Handoff Document

**תאריך עדכון אחרון**: 2026-04-23
**Repo**: `nirab96Developer/Forewise`, branch `main`
**Production**: `https://forewise.co` (server: 167.99.228.10)

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

## מצב נוכחי (אחרי סבב סגירה מלא)

- **Commit לפני הסבב הראשון**: `706132f` (mobile UX hardening)
- **Commit אחרון**: `c0d1e2f3a4b5` (data hygiene + wo_coord_logs)
- **Diff מצטבר**: 13 commits (11 פאזות + HANDOFF + סגירה), 7 migrations, ~40 קבצים.
- **CI status**: ✅ ירוק
- **alembic head**: `c0d1e2f3a4b5` (זהה בDB ובריפו)
- **alembic check**: רץ עד הסוף בלי קריסה (יש drift בין models ל-DB ב-13 טבלאות + הרבה עמודות; הכל **קיים מלפני הסבב**, לא נוצר על ידינו, לא משפיע על runtime).
- **pytest CI subset**: 174/174 passing
- **pytest כל הקבצים שנותרו**: 395 collected, 0 collection errors

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
| 12 | `76f9350` | docs | HANDOFF.md ראשון |
| 13 | TBD | sealing | סגירת חורים: __init__ imports, dead code, wo_coord_logs table, data hygiene |

---

## Migrations שהוחלו (head = `c0d1e2f3a4b5`)

| Phase | Revision | תוכן |
|---|---|---|
| 0 | `c4d5e6f7a8b9` | normalize budgets.status → UPPERCASE |
| 1.1 | `d5e6f7a8b9c0` | create `budget_commitments` + reconcile legacy `committed_amount` |
| 1.2 | `e6f7a8b9c0d1` | create `invoice_work_orders` + backfill מ-`invoice_items` |
| 1.3 | `f7a8b9c0d1e2` | drop `supplier_rotations.equipment_category_id`; add `equipment_models.equipment_type_id` עם backfill |
| 2.1 | `a8b9c0d1e2f3` | CHECK constraints על work_orders/worklogs/invoices/budgets/budget_commitments status |
| 3 | `b9c0d1e2f3a4` | typo fix T2 + backfill `equipment.category_id` 752 שורות |
| sealing | `c0d1e2f3a4b5` | create `work_order_coordination_logs` + backfill 5 equipment_models + deactivate 21 supplier_rotations + cleanup 3 NULL committed + soft-delete 8 orphan budgets |

---

## באגים אמיתיים שתוקנו (סבב ראשון — Phase 0–3)

1. **🔥 PROD 500 על `send-to-supplier`** — FK violation; תוקן ב-Phase 0, גוצב ב-Phase 1.3.
2. **🔥 `mark-paid` לא שחרר frozen budget** — תקציבים committed לנצח. תוקן ב-Phase 0 + שיפור ב-Phase 1.2.
3. **🔥 שחרור freeze ביצירת invoice עם actual=0** — שיחרר בלי לרשום spend. הוסר ב-Phase 0.
4. **🔴 `/suppliers/equipment-models/active` → 404** — 10 hits/יומיים. נוסף `/equipment-models/active`.
5. **🔴 `/api/v1/reports/export/excel` בלי הרשאות** — נוספו `require_permission` per-type ב-Phase 0.
6. **🟡 `PATCH /supplier-constraint-reasons/{id}` → 405**. תוקן ב-Phase 0.
7. **🟡 `budgets.status` mixed case**. תוקן.
8. **🧹 7 שיטות זומבי ב-supplierService.ts** שפנו ל-endpoints שלא קיימים. נמחקו.
9. **🧹 `requirements.txt` חסר בריפו** — נוצר.

---

## באגים אמיתיים שתוקנו בסבב הסגירה (commit #13)

10. **🔥 `POST /api/v1/work-order-coordination-logs` היה גורם 500** — Phase 2.3 הוסיף router + frontend אבל לא יצר את הטבלה. נוצרה במיגרציה `c0d1e2f3a4b5` עם CHECK על action_type.
11. **🔴 `alembic check` קרס עם `NoReferencedTableError: equipment_categories`** — `app/models/__init__.py` חסר 18 imports. כל המודלים נטענו lazily דרך `from app.models.X import Y` בתוך פונקציות. ניתקנו את כל ה-18.
12. **🟡 `equipment_models` 5 שורות פעילות בלי `equipment_type_id`** — Phase 1.3 backfill לא כיסה אותן. תוקן: 4 משאיות מים → `equipment_type_id=172`, 1 LEGACY_UNKNOWN → `is_active=false`.
13. **🟡 `supplier_rotations` 21 שורות פעילות בלי `equipment_type_id`** — seed data ישנה לפני Phase 1.3. הופנתה ל-`is_active=false, is_available=false` (לא יכולה להשתתף בסבב הוגן ממילא).
14. **🟡 `budgets.committed_amount IS NULL`** ב-3 שורות — נמחקה ל-0 (תואם default + Phase 1.1 invariant).
15. **🟡 8 budgets שהצביעו ל-projects מחוקים** (כל הסכומים = 0, כבר inactive) — soft-deleted.
16. **🧹 `routers/invoice_items.py`** — קוד מת: ה-router לא נרשם ב-`ROUTER_MODULES`, השירות `InvoiceItemService` לא קיים. נמחק.
17. **🧹 3 קבצי טסט שבורים** (`test_activity_types_crud`, `test_invoice_items_crud`, `test_integration_invoice_full_flow`) שנכשלו בקולקציה — מתייחסים לשירותים שלא קיימים. נמחקו.
18. **🧹 `pricing_override` model + import** — הטבלה לא קיימת ב-DB, אף אחד לא משתמש בקלאס. נמחק לחלוטין (model + import + reference ב-docstring של `pricing.py`).
19. **🧹 `app/schemas/invoice_item.py`** — schemas יתום אחרי מחיקת ה-router. נמחק.

---

## חוב טכני שעדיין פתוח (לטיפול עתידי)

1. **Phase 2.1b**: לנעול `users.status`, `projects.status`, `equipment.status` ב-CHECK. צריך normalize ידני קודם.
2. **Phase 3 cutover**: `budgets.committed_amount`, `budgets.spent_amount`, `work_orders.frozen_amount`, `work_orders.remaining_frozen` — עדיין dual-write. להחליף ב-computed views ולהפיל בעוד ~3 שבועות של ייצוב.
3. **Dockerfile + docker-compose.yml** — לא בשימוש. למחוק או לסמן ב-README.
4. **alembic drift קיים-מלפנינו**: 4 מודלים מתייחסים לטבלאות שאין ב-DB (`files`, `milestones`, `daily_work_reports`, `token_blacklist`) ו-9 טבלאות ב-DB אין להן מודל (`refresh_tokens`, `supplier_areas`, `supplier_regions`, `system_settings`, `equipment_rate_history`, `budget_allocations`, `forest_polygons`, `work_hour_settings`, `spatial_ref_sys` שהיא PostGIS). אף אחד מאלה **לא** משפיע על runtime — אין router פעיל שמתשאל את הטבלאות החסרות, ואין קוד שמתשאל את הטבלאות שאין להן מודל. דורש החלטה אסטרטגית: לבנות tables חסרים או למחוק models מתים.
5. **5 שירותים בלי route** (`file_service`, `milestone_service`, `calendar_service`, `daily_report_service`, `balance_release_service` עבור Milestone) — מיובאים ב-`services/__init__.py` ב-eager import אבל לא נקראים מאף router. אינם מחוברים לשום flow פעיל. למחוק יחד עם המודלים שלהם או לחבר לראוטרים אם רוצים בעתיד.

---

## Live Tests שצריך לרוץ עליהם

| Phase | מסך | מה לבדוק |
|---|---|---|
| 0 | `/order-coordination` | "סוג ציוד" מציג שם אמיתי, לא "לא צוין" |
| 0 | send-to-supplier | אין 500, סטטוס משתנה ל-DISTRIBUTING |
| 0 | `/settings/constraint-reasons` | toggle is_active עובד |
| 1.1 | יצירת WO + DB | `SELECT * FROM budget_commitments WHERE work_order_id=<חדש>` → שורת FROZEN |
| 1.1 | mark-paid | commitment עובר ל-SPENT, `spent_amount` מתעדכן |
| 1.2 | יצירת invoice חודשית | `SELECT * FROM invoice_work_orders WHERE invoice_id=<חדש>` |
| 1.3 | DB | `SELECT equipment_type_id FROM supplier_rotations WHERE is_active=true` — לא NULL בכלום |
| 2.2 | login + DevTools Network | רואים `GET /api/v1/users/me` רץ אחרי `/auth/verify-otp` |
| 2.3 | dashboard coordinator | אין כפתורי action, רק "טפל" שמוביל ל-`/order-coordination?focus=<id>` |
| 2.3 | OrderCoordination → log call | `POST /work-order-coordination-logs` מצליח (היה 500 לפני סבב הסגירה) |
| 3 | DB | `SELECT COUNT(*), COUNT(category_id) FROM equipment` → 1026/1024 |

---

## הוראה לצ'אט הבא

> ממשיך מסבב Phase 0–3 + סבב סגירה שהושלם ב-`main`.
> alembic head: `c0d1e2f3a4b5`. CI ירוק. 174/174 ב-CI subset. 0 חורים פתוחים מהפאזות.
> השלב הבא: לבדוק flows עסקיים בלייב על `https://forewise.co` לפי הטבלה למעלה.
> אחרי שכל ה-flows עובדים, להחליט:
>   - Phase 2.1b (normalize + CHECK על users/projects/equipment status)
>   - Phase 3 cutover מלא (להפיל את ה-dual-write columns)
>   - או: לסגור את חוב טכני #4–5 (drift + שירותים יתומים) — דורש החלטה אסטרטגית.
> לקרוא את `/root/forewise/HANDOFF.md` לכל ההקשר.
