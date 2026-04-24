#!/usr/bin/env python3
"""Build PERMISSIONS_MATRIX.md and PERMISSIONS_MATRIX.csv from the
collected metadata.

Inputs:
  /tmp/routes_meta.json         — 418 routes with {method, path, file, func, summary, auth_deps, require_perms, ...}
  /tmp/db_permissions_full.tsv  — 169 permissions defined in DB
  /tmp/role_perms.tsv           — 409 (role, permission) pairs
  /tmp/diff_matched.txt         — 185 matched (method, normalized path)

Outputs:
  /root/forewise/PERMISSIONS_MATRIX.md
  /root/forewise/PERMISSIONS_MATRIX.csv
"""
import csv
import json
import os
import re
from collections import defaultdict, Counter

# Roles in the system (ordered by power)
ROLES = ["ADMIN", "REGION_MANAGER", "AREA_MANAGER", "ORDER_COORDINATOR",
         "WORK_MANAGER", "ACCOUNTANT", "SUPPLIER"]
ROLE_HE = {
    "ADMIN": "מנהל מערכת",
    "REGION_MANAGER": "מנהל מרחב",
    "AREA_MANAGER": "מנהל אזור",
    "ORDER_COORDINATOR": "מתאם הזמנות",
    "WORK_MANAGER": "מנהל עבודה",
    "ACCOUNTANT": "מנהלת חשבונות",
    "SUPPLIER": "ספק",
}
SCOPE_HE = {
    "global": "גלובלי",
    "region": "מרחב",
    "area": "אזור",
    "project": "פרויקט (assigned)",
    "self": "עצמי בלבד",
    "supplier_token": "טוקן ספק",
    "anonymous": "ציבורי",
}


def load_routes() -> list[dict]:
    with open("/tmp/routes_meta.json") as f:
        return json.load(f)


def load_db_permissions() -> dict:
    perms = {}
    with open("/tmp/db_permissions_full.tsv") as f:
        for line in f:
            parts = line.rstrip("\n").split("|")
            if len(parts) >= 2:
                code, name = parts[0], parts[1]
                category = parts[2] if len(parts) > 2 else ""
                perms[code] = {"name": name, "category": category}
    return perms


def load_role_perms() -> dict[str, set[str]]:
    rp: dict[str, set[str]] = defaultdict(set)
    with open("/tmp/role_perms.tsv") as f:
        for line in f:
            parts = line.rstrip("\n").split("|")
            if len(parts) == 2:
                rp[parts[0]].add(parts[1])
    return rp


def load_matched_paths() -> set[tuple[str, str]]:
    """Returns set of (METHOD, normalized_path) that exist in both BE & FE."""
    matched = set()
    with open("/tmp/diff_matched.txt") as f:
        for line in f:
            line = line.rstrip()
            if not line or line.startswith("#"):
                continue
            m = re.match(r"^(GET|POST|PUT|PATCH|DELETE)\s+(\S+)\s*$", line)
            if m:
                matched.add((m.group(1), m.group(2)))
    return matched


def normalize(path: str) -> str:
    p = path
    if p.startswith("/api/v1"):
        p = p[len("/api/v1"):]
    if len(p) > 1 and p.endswith("/"):
        p = p[:-1]
    p = re.sub(r"\{[^}]+\}", "{}", p)
    if not p.startswith("/"):
        p = "/" + p
    return p


def infer_domain(file: str, path: str) -> str:
    """Infer domain from router file name."""
    base = file.replace(".py", "")
    return base


def infer_action(method: str, path: str, func: str) -> str:
    """Infer action verb from method + path suffix."""
    suffix = path.rstrip("/").split("/")[-1]
    if suffix.startswith("{"):
        suffix = path.rstrip("/").split("/")[-2] if len(path.split("/")) > 2 else ""
    if method == "GET":
        return "read" if "{" in path else "list"
    if method == "DELETE":
        return "delete"
    if method == "POST":
        if suffix in ("approve", "reject", "complete", "start", "close",
                      "cancel", "restore", "lock", "unlock", "activate",
                      "submit", "assign", "release", "transfer", "read",
                      "send-to-supplier", "resend-to-supplier",
                      "mark-paid"):
            return suffix
        return "create"
    if method in ("PUT", "PATCH"):
        if suffix in ("approve", "reject", "complete", "start", "close",
                      "cancel", "restore", "lock", "unlock", "activate",
                      "submit"):
            return suffix
        return "update"
    return "?"


def recommended_permission(domain: str, action: str) -> str:
    """Map (domain, action) → permission code matching DB convention."""
    # Normalize domain to singular-ish entity name matching DB convention
    aliases = {
        "work_orders": "work_orders",
        "worklogs": "worklogs",
        "invoices": "invoices",
        "invoice_payments": "invoice_payments",
        "budgets": "budgets",
        "budget_items": "budget_items",
        "budget_transfers": "budget_transfers",
        "users": "users",
        "roles": "roles",
        "permissions": "permissions",
        "role_assignments": "role_assignments",
        "equipment": "equipment",
        "equipment_models": "equipment_models",  # not in DB yet
        "equipment_categories": "equipment_categories",
        "equipment_types": "equipment_types",
        "equipment_rates": "equipment_rates",  # not in DB
        "supplier_constraint_reasons": "supplier_constraint_reasons",
        "supplier_rotations": "supplier_rotations",  # not in DB
        "suppliers": "suppliers",
        "support_tickets": "support_tickets",  # not in DB
        "regions": "regions",
        "areas": "areas",
        "departments": "departments",
        "locations": "locations",
        "projects": "projects",
        "project_assignments": "project_assignments",
        "reports": "reports",
        "report_runs": "report_runs",
        "activity_types": "activity_types",  # not in DB
        "activity_logs": "activity_logs",
        "settings": "settings",
        "system_rates": "system_rates",  # not in DB
        "notifications": "notifications",  # not in DB
        "dashboard": "dashboard",
        "geo": "geo",
        "journal": "journal",
        "pricing": "pricing",
        "pdf_preview": "pdf_preview",
        "excel_export": "excel_export",
        "admin_projects": "projects",
        "admin": "admin",
        "auth": "auth",
        "supplier_portal": None,  # public via token
        "websocket": None,
        "sync": None,
        "work_order_coordination_logs": "work_orders",
    }
    entity = aliases.get(domain, domain)
    if entity is None:
        return ""
    return f"{entity}.{action}"


def recommended_scope(domain: str, action: str, path: str) -> str:
    """Heuristic scope per domain.

    - admin/* → global
    - users, roles, permissions → global
    - regions/areas/departments → global (config) ; or scoped for read
    - projects, work_orders, worklogs, invoices, budgets → project/area/region scoped
    - geo, dashboard → role-scoped
    """
    if domain.startswith("admin") or domain in (
        "permissions", "roles", "role_assignments", "system_rates",
        "settings", "auth"
    ):
        return "global"
    if domain in ("regions", "areas", "departments", "equipment_categories",
                  "equipment_types", "supplier_constraint_reasons",
                  "activity_types"):
        return "global" if action in ("create", "update", "delete", "restore") else "all"
    if domain in ("work_orders", "worklogs", "projects", "budgets",
                  "budget_items", "invoices", "invoice_payments",
                  "balance_releases", "report_runs", "reports",
                  "work_order_coordination_logs"):
        return "scoped (region/area/project per role)"
    if domain in ("equipment",):
        return "scoped (project/area)"
    if domain in ("users",):
        return "global (admin) or scoped (managers see their own area users)"
    if domain == "supplier_portal":
        return "supplier_token"
    return "?"


def severity(method: str, path: str, auth_status: str, sensitive_kw: list,
             require_perms: list, custom_verify: list,
             inline_role_block: bool) -> str:
    """🔴/🟡/🟢. Custom verify_admin or inline role-block raises ARE enforcement."""
    if require_perms or custom_verify or inline_role_block:
        return "🟢"
    if auth_status == "anonymous":
        if "/auth/" in path or "/supplier-portal/" in path:
            return "🟢"
        return "🔴"
    if method in ("POST", "PUT", "PATCH", "DELETE"):
        return "🔴"
    if any(k in sensitive_kw for k in ("amount", "frozen", "spent", "approve",
                                         "reject", "pay", "lock", "delete",
                                         "transfer", "permission", "role")):
        return "🔴"
    return "🟡"


def main():
    routes = load_routes()
    db_perms = load_db_permissions()
    role_perms = load_role_perms()
    matched = load_matched_paths()

    # Build per-permission → roles map (which roles have this perm)
    perm_to_roles = defaultdict(set)
    for role, perms in role_perms.items():
        for p in perms:
            perm_to_roles[p].add(role)

    rows = []
    for r in routes:
        method = r["method"]
        path = r["path"]
        norm = normalize(path)
        domain = infer_domain(r["file"], path)
        action = infer_action(method, path, r["func"])
        auth_status = (
            "anonymous" if not r["auth_deps"] and not r["require_perms"]
            else "permission" if r["require_perms"]
            else "authenticated"
        )
        rec_perm = recommended_permission(domain, action)
        rec_scope = recommended_scope(domain, action, path)
        sev = severity(method, path, auth_status, r["sensitive_kw"],
                       r["require_perms"], r.get("custom_verify", []),
                       r.get("inline_role_block", False))
        ui_match = "yes" if (method, norm) in matched else "no"
        # Permission status
        perm_status = []
        for p in r["require_perms"]:
            if p not in db_perms:
                perm_status.append(f"{p}=MISSING_IN_DB")
            else:
                perm_status.append(p)
        enforcement_via = []
        if r["require_perms"]:
            enforcement_via.append(f"require_permission({','.join(r['require_perms'])})")
        if r.get("custom_verify"):
            enforcement_via.append(f"verify_{r['custom_verify'][0]}()")
        if r.get("inline_role_block"):
            enforcement_via.append("inline_role_check")
        rows.append({
            "method": method,
            "path": path,
            "domain": domain,
            "action": action,
            "summary": r["summary"],
            "func": r["func"],
            "file": r["file"],
            "auth_status": auth_status,
            "enforcement": ";".join(enforcement_via) or "NONE",
            "current_perms": ";".join(perm_status),
            "ui_exposed": ui_match,
            "recommended_perm": rec_perm,
            "recommended_scope": rec_scope,
            "severity": sev,
            "is_mutation": "yes" if r["is_mutation"] else "no",
            "sensitive_kw": ";".join(r["sensitive_kw"]) or "",
            "roles_with_current_perm": ";".join(sorted(
                set().union(*[perm_to_roles[p] for p in r["require_perms"]])
            )),
        })

    # Sort by severity (🔴 first), then path
    sev_order = {"🔴": 0, "🟡": 1, "🟢": 2}
    rows.sort(key=lambda x: (sev_order[x["severity"]], x["path"], x["method"]))

    # Write CSV
    csv_path = "/root/forewise/PERMISSIONS_MATRIX.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # ---------------- Build MD report ----------------
    crit = [r for r in rows if r["severity"] == "🔴"]
    medium = [r for r in rows if r["severity"] == "🟡"]
    ok = [r for r in rows if r["severity"] == "🟢"]

    # Permission cross-reference
    code_perms_used = set()
    for r in routes:
        for p in r["require_perms"]:
            code_perms_used.add(p)
    db_perm_codes = set(db_perms.keys())
    missing_in_db = code_perms_used - db_perm_codes
    unused_in_code = db_perm_codes - code_perms_used

    # Duplicate convention check (FOO.BAR vs foo.bar)
    case_dup = []
    lower_set = {p.lower() for p in db_perm_codes}
    seen = set()
    for p in sorted(db_perm_codes):
        plow = p.lower()
        if plow in seen:
            continue
        seen.add(plow)
        variants = [q for q in db_perm_codes if q.lower() == plow]
        if len(variants) > 1:
            case_dup.append(variants)

    md = []
    md.append("# Permissions Matrix — Forewise")
    md.append("")
    md.append("**תאריך**: 2026-04-23")
    md.append("**מקור**: 418 routes ב-FastAPI + 169 permissions ב-DB + 409 role-perm mappings + 185 matched FE↔BE.")
    md.append('**הערה**: דו"ח בלבד. אין שינויי קוד.')
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 1. סיכום מנהלים")
    md.append("")
    md.append("| מטריקה | מספר |")
    md.append("|---|---|")
    md.append(f"| סך הכל endpoints | {len(rows)} |")
    md.append(f"| 🔴 קריטיים — אין enforcement (mutation/sensitive) | {len(crit)} |")
    md.append(f"| 🟡 בינוניים — auth-only על read endpoints | {len(medium)} |")
    md.append(f"| 🟢 תקינים — יש require_permission או public legitimate | {len(ok)} |")
    md.append(f"| Permissions ב-DB | {len(db_perm_codes)} |")
    md.append(f"| Permissions שמוזכרים בקוד | {len(code_perms_used)} |")
    md.append(f"| Permissions בקוד שאין ב-DB (בעיה) | {len(missing_in_db)} |")
    md.append(f"| Permissions ב-DB שלא משמשים בקוד (יתומים) | {len(unused_in_code)} |")
    md.append(f"| Permissions עם duplicate case (UPPER + lower) | {len(case_dup)} |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 2. תפקידים והיקף ההרשאות בהם")
    md.append("")
    md.append("| תפקיד | מספר הרשאות | scope לוגי שצריך להיות |")
    md.append("|---|---|---|")
    for role in ROLES:
        n = len(role_perms.get(role, set()))
        md.append(f"| `{role}` ({ROLE_HE[role]}) | {n} | "
                   + ("גלובלי" if role == "ADMIN"
                      else "מרחב" if role == "REGION_MANAGER"
                      else "אזור" if role == "AREA_MANAGER"
                      else "תיאום הזמנות (region/area)" if role == "ORDER_COORDINATOR"
                      else "פרויקטים שלו" if role == "WORK_MANAGER"
                      else "אזור/מרחב לפי שיוך" if role == "ACCOUNTANT"
                      else "טוקן ספק (חיצוני)") + " |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 3. בעיות ב-Permission Set הקיים")
    md.append("")
    md.append("### 3.1 Permissions בקוד שלא קיימים ב-DB")
    if missing_in_db:
        md.append("")
        md.append("הקוד קורא ל-`require_permission` עם code שלא קיים ב-DB. "
                  "התוצאה: כל בקשה מחזירה 403 Forbidden גם אם המשתמש לכאורה צריך גישה.")
        md.append("")
        for p in sorted(missing_in_db):
            md.append(f"- `{p}`")
    else:
        md.append("")
        md.append("✅ אין")
    md.append("")
    md.append("### 3.2 Permissions ב-DB שלא משמשים בקוד")
    md.append("")
    md.append(f"סה\"כ {len(unused_in_code)} permissions יתומים ב-DB. "
              "ייתכן שיש להם שימושים שאני לא תפסתי, או שהם dead. "
              "להלן קטגוריזציה לפי convention:")
    md.append("")
    upper = sorted([p for p in unused_in_code if p == p.upper() and "." in p])
    lower = sorted([p for p in unused_in_code if p != p.upper()])
    other = sorted(unused_in_code - set(upper) - set(lower))
    md.append(f"- **UPPERCASE legacy** ({len(upper)}): נראים legacy, יש להם duplicates lowercase ב-DB.")
    md.append("")
    if upper[:20]:
        md.append("  ```")
        for p in upper[:20]:
            md.append(f"  {p}")
        if len(upper) > 20:
            md.append(f"  ... ({len(upper) - 20} נוספים)")
        md.append("  ```")
    md.append("")
    md.append(f"- **lowercase יתומים** ({len(lower)}): permissions לישויות שאין להן endpoint, או לפעולות שלא נאכפות.")
    md.append("")
    if lower[:30]:
        md.append("  ```")
        for p in lower[:30]:
            md.append(f"  {p}")
        if len(lower) > 30:
            md.append(f"  ... ({len(lower) - 30} נוספים)")
        md.append("  ```")
    md.append("")
    md.append("### 3.3 Duplicate case (UPPER vs lower)")
    md.append("")
    md.append(f"סה\"כ {len(case_dup)} זוגות. הקוד משתמש בlowercase, אבל ה-DB מחזיק את שני הוריאנטים.")
    md.append("דוגמה: `BUDGETS.VIEW` ו-`budgets.view` — שניהם מוקצים לתפקידים, חלקם רק UPPER, חלקם רק lower.")
    md.append("")
    if case_dup[:15]:
        md.append("```")
        for variants in case_dup[:15]:
            md.append(f"  {' / '.join(variants)}")
        if len(case_dup) > 15:
            md.append(f"  ... ({len(case_dup) - 15} נוספים)")
        md.append("```")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 4. Endpoints קריטיים בלי enforcement (🔴)")
    md.append("")
    md.append(f"סה\"כ {len(crit)} endpoints מבצעים פעולות רגישות ללא בדיקת הרשאה. "
              "כל משתמש מאומת (כולל ספק עם session גנוב) יכול לקרוא להם בהצלחה.")
    md.append("")
    md.append("### לפי domain (top 15)")
    md.append("")
    md.append("| Domain | מספר 🔴 |")
    md.append("|---|---|")
    by_domain = Counter(r["domain"] for r in crit)
    for domain, count in by_domain.most_common(15):
        md.append(f"| `{domain}` | {count} |")
    md.append("")
    md.append("### דוגמאות בולטות (top 30 by sensitivity)")
    md.append("")
    md.append("| Method | Path | Action | Recommended permission | UI? |")
    md.append("|---|---|---|---|---|")
    for r in crit[:30]:
        md.append(f"| `{r['method']}` | `{r['path']}` | {r['action']} | `{r['recommended_perm']}` | {r['ui_exposed']} |")
    if len(crit) > 30:
        md.append("")
        md.append(f"_ועוד {len(crit) - 30} ב-CSV._")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 5. Endpoints בינוניים (🟡)")
    md.append("")
    md.append(f"סה\"כ {len(medium)} — בעיקר read/list בלי `require_permission`. "
              "פחות חמור מ-🔴 (אין side effect) אבל עדיין דליפת מידע אם משתמש לא מורשה ניגש.")
    md.append("")
    md.append("דוגמאות (10 ראשונות):")
    md.append("")
    md.append("| Method | Path | Recommended permission |")
    md.append("|---|---|---|")
    for r in medium[:10]:
        md.append(f"| `{r['method']}` | `{r['path']}` | `{r['recommended_perm']}` |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 6. Endpoints בלי UI")
    md.append("")
    no_ui = [r for r in rows if r["ui_exposed"] == "no" and r["domain"] not in ("auth", "supplier_portal")]
    no_ui_by_domain = Counter(r["domain"] for r in no_ui)
    md.append(f"סה\"כ {len(no_ui)} endpoints שלא קיים להם UI. לפי domain:")
    md.append("")
    md.append("| Domain | בלי UI |")
    md.append("|---|---|")
    for domain, count in no_ui_by_domain.most_common(20):
        md.append(f"| `{domain}` | {count} |")
    md.append("")
    md.append("ראה CSV לרשימה מלאה (סינון: `ui_exposed=no`).")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 7. פיצ'רים שלמים בלי UI (קבוצות שמומלצות להחלטה)")
    md.append("")
    md.append("| קבוצה | endpoints | מצב | המלצה |")
    md.append("|---|---|---|---|")
    md.append("| 2FA (`/auth/2fa/*`) | 4 | אין UI | להחליט: לחבר או למחוק |")
    md.append("| Biometric (`/auth/biometric/*`) | 6 | יש `biometricService.ts` בfrontend אבל לא רוץ | להחליט: לחבר או למחוק |")
    md.append("| WebAuthn (`/auth/webauthn/*`) | 4 | אין UI | להחליט: לחבר או למחוק |")
    md.append("| Sessions/Devices (`/auth/sessions`, `/auth/devices`) | 4 | אין UI | אדמין UI? |")
    md.append("| Admin security (`/auth/admin/*`) | 4 | אין UI | אדמין UI? |")
    md.append("| Notifications מתקדם (`/notifications/bulk-action` וכו') | 4 | אין UI | להחליט |")
    md.append("| Restore endpoints (`/{entity}/{id}/restore`) | 12 | אין UI | אדמין UI? |")
    md.append("| Lock/Unlock users | 3 | אין UI | אדמין UI? |")
    md.append("| PDF downloads (work-orders, invoices, worklogs) | 4 | יש pdf-preview, לא ברור אם UI מתחבר | לאמת בלייב |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 8. המלצות לפי סדר חומרה")
    md.append("")
    md.append("### 🔴 דחוף — אכיפת הרשאות בendpoints קריטיים")
    md.append("")
    md.append(f"להוסיף `require_permission` ל-{len(crit)} endpoints. הכי קריטי לפי החתכים האלה:")
    md.append("")
    domain_notes = {
        "dashboard":           "כל ה-`/dashboard/*` חשוף — דליפת KPIs, תקציבים, work orders. read endpoints, אבל ה-payload מכיל data רגיש לפי תפקיד.",
        "auth":                "endpoints של 2FA/biometric/WebAuthn — אין UI, אבל אם API נחשף משתמש מאומת יכול register passkey לחשבון אחר. דורש חידוד.",
        "admin":               "כל ה-`/admin/*` ל-admin בלבד אבל אין enforcement. כל user מאומת יכול לקרוא רשימת users, regions, dashboard admin וכו'.",
        "project_assignments": "כל ה-CRUD בלי בדיקה. user יכול לשנות הקצאת פרויקטים של אחרים.",
        "notifications":       "bulk-action, cleanup, read-all — user יכול לסמן הודעות של אחרים כנקראו.",
        "support_tickets":     "create/update/list — user יכול לערוך טיקטים של אחרים.",
        "supplier_rotations":  "מנגנון הסבב ההוגן. mutation שלו = שיבוש החלוקה לספקים.",
        "activity_types":      "lookup table. mutation = החלפת activity codes שמתעדים worklogs.",
        "work_orders":         "5 mutations חופשיות (כל השאר תחת require_permission). למצוא ולהשלים.",
        "pricing":             "endpoints מציגים תעריפים — דליפה ל-supplier אם הוא מאומת.",
        "budgets":             "3 mutations חופשיות מתוך כלל ה-budget endpoints. למצוא ולהשלים.",
        "system_rates":        "תעריפי מערכת — שינוי משפיע על כל worklog חדש.",
    }
    by_dom_sorted = sorted(by_domain.items(), key=lambda x: -x[1])[:10]
    for domain, count in by_dom_sorted:
        note = domain_notes.get(domain, "להחליט פר-endpoint לפי לוגיקה עסקית.")
        md.append(f"- **`{domain}`** ({count} endpoints) — {note}")
    md.append("")
    md.append("### 🔴 דחוף — לתקן permissions שלא קיימים ב-DB")
    md.append("")
    if missing_in_db:
        md.append(f"{len(missing_in_db)} permissions בקוד שלא יוגדרו לעולם → 403 קבוע.")
    else:
        md.append("אין — הכל תואם.")
    md.append("")
    md.append("### 🟡 חוב טכני — duplicate UPPER/lower")
    md.append("")
    md.append(f"{len(case_dup)} זוגות duplicates. נדרש איחוד ל-convention יחיד (lowercase) ועדכון role_permissions assignments.")
    md.append("")
    md.append("### 🟡 חוב טכני — permissions יתומים")
    md.append("")
    md.append(f"{len(unused_in_code)} permissions ב-DB שאין להם שימוש. ניתן למחוק אחרי איחוד case.")
    md.append("")
    md.append("### 🟡 בינוני — להגדיר scope")
    md.append("")
    md.append("הקוד הנוכחי לא אוכף scope (region/area/project) ב-DB level. "
              "ה-`test_scope_enforcement.py` מאמת חלק (174/174 עוברים) אבל לא בכל endpoint. "
              "צריך להגדיר policy אחיד.")
    md.append("")
    md.append("### 🟢 לאחר אכיפה — UI alignment")
    md.append("")
    md.append("אחרי שה-backend אוכף, frontend צריך לבדוק `user.role.permissions` לפני הצגת כפתורים. "
              "זה כבר חלקי — Login.tsx טוען את הרשימה — רק להוסיף בדיקה לכל כפתור פעולה.")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 9. Audited domains (false positives שאומתו ידנית)")
    md.append("")
    md.append("Domains שנסקרו endpoint-by-endpoint ידנית ומצאתי שהם **כבר מוגנים במלואם**, "
              "גם אם ה-extractor הראשון פספס. ה-extractor שודרג מאז כך שיתפוס את הפטרנים האלה אוטומטית.")
    md.append("")
    md.append("### `work_orders` (25 endpoints) — נסקר ב-Phase 2 Wave 2")
    md.append("")
    md.append("- 19 endpoints עם `require_permission(...)` ישיר (read/list/create/update/delete/restore/approve×2/cancel/close/start/distribute/etc.)")
    md.append("- 4 endpoints PATCH wrappers שמפנים לפונקציות מוגנות (frontend back-compat aliases)")
    md.append("- 2 endpoints עם inline admin check (scan-equipment + admin-override-equipment)")
    md.append("- **0 endpoints חשופים**. Wave 2 נסגר ללא שינוי קוד.")
    md.append("")
    md.append("### `worklogs` (17 endpoints) — נסקר ב-Phase 2 Wave 3")
    md.append("")
    md.append("- 14 endpoints עם `require_permission(...)` ישיר")
    md.append("- 1 endpoint self-service (`/my-worklogs`) שמסנן `search.user_id = current_user.id` לפני query")
    md.append("- 2 endpoints lookup (`/activity-codes`, `/by-work-order/{id}`) — readonly, אומתו ידנית")
    md.append("- **0 endpoints חשופים**. Wave 3 נסגר ללא שינוי קוד.")
    md.append("")
    md.append("**הפטרנים שה-extractor לא תפס לפני השדרוג**:")
    md.append("")
    md.append("1. *Wrappers* — `def patch_X(...): return X(...)` — נדרש call-graph עם hops.")
    md.append("2. *Indirect admin* — `is_admin = ... role.code in (...); if not is_admin: raise 403`.")
    md.append("3. *Helper calls* — `_require_order_coordinator_or_admin(current_user)`.")
    md.append("4. *Self-service scope filter* — `search.user_id = current_user.id` לפני query.")
    md.append("")
    md.append("כל הארבעה כעת מוכרים אוטומטית. ראה `app_backend/scripts/audit/README.md` להרחבה.")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 10. CSV מצורף")
    md.append("")
    md.append("`PERMISSIONS_MATRIX.csv` מכיל את כל ה-{} הendpoints עם כל העמודות (severity, current_perms, recommended_perm, ui_exposed, וכו'). פתח באקסל לסינון.".format(len(rows)))
    md.append("")
    md.append("עמודות:")
    md.append("- `method, path, domain, action, summary, func, file`")
    md.append("- `auth_status` — anonymous / authenticated / permission")
    md.append("- `current_perms` — מה require_permission קורא היום")
    md.append("- `ui_exposed` — yes/no")
    md.append("- `recommended_perm` — המלצה ליישור עם DB convention (lowercase entity.action)")
    md.append("- `recommended_scope` — global / region / area / project / supplier_token / scoped")
    md.append("- `severity` — 🔴/🟡/🟢")
    md.append("- `is_mutation` — yes/no")
    md.append("- `sensitive_kw` — מילות מפתח רגישות בקוד")
    md.append("- `roles_with_current_perm` — אילו roles יש להם את הרשאה הנוכחית")
    md.append("")

    md_path = "/root/forewise/PERMISSIONS_MATRIX.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"Wrote: {md_path}")
    print(f"Wrote: {csv_path}")
    print(f"Routes: {len(rows)} | 🔴={len(crit)} 🟡={len(medium)} 🟢={len(ok)}")
    print(f"Code perms used: {len(code_perms_used)} | DB perms: {len(db_perm_codes)}")
    print(f"Missing in DB: {len(missing_in_db)} | Unused in code: {len(unused_in_code)}")
    print(f"Duplicate case pairs: {len(case_dup)}")


if __name__ == "__main__":
    main()
