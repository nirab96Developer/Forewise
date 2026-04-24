# Permissions Audit Tooling

Three small scripts that produce `PERMISSIONS_MATRIX.{md,csv}` at the repo root.

## Run

```bash
cd /root/forewise/app_backend && source .venv/bin/activate
python3 scripts/audit/extract_routes_with_auth.py > /tmp/routes_meta.json
python3 scripts/audit/build_permissions_matrix.py
# Optionally regenerate the FE↔BE diff
python3 scripts/audit/api_diff.py
```

## What each script does

### `extract_routes_with_auth.py`

AST-walks every `app/routers/*.py` file. For each route handler records:

- `method`, `path`, `func`, `summary`, `file`
- Auth dependency (`get_current_user` / `get_current_active_user`)
- Detected enforcement patterns:
  - `require_permission(current_user, "...")` calls
  - `verify_admin(current_user)` style helpers
  - Inline role-code raises (`if current_user.role.code != "ADMIN": raise 403`)
  - Indirect admin checks via boolean (`is_admin = ... in (...); if not is_admin: raise`)
  - Helper-function calls (`_require_order_coordinator_or_admin(current_user)`)
  - **Self-service scope filters** — handlers that force `search.user_id = current_user.id`
    before reading. These are valid enforcement (the user can never
    see another user's data) and counting them lets us avoid flagging
    `/my-worklogs`, `/my-orders` etc. as critical.
  - **Wrappers** — when a handler is just `return other_func(...)`, the
    enforcement of the target propagates back. This avoids false 🔴
    on PATCH-aliases-of-POST and similar back-compat shims.

Up to 3 hops of wrapper resolution.

### `build_permissions_matrix.py`

Cross-joins `routes_meta.json` with the live DB:

- `permissions` table (169 rows in prod)
- `role_permissions` table (409 rows across 7 roles)

And the FE↔BE call diff (`/tmp/diff_matched.txt` produced by `api_diff.py`).

Outputs `/root/forewise/PERMISSIONS_MATRIX.md` (human report) and
`PERMISSIONS_MATRIX.csv` (one row per endpoint, 16 columns, fits in Excel).

### `api_diff.py`

Walks `app_frontend/src/**/*.{ts,tsx}` and extracts every axios call,
resolving `${this.baseUrl}` per service. Cross-joins against the parsed
backend routes to produce `/tmp/diff_matched.txt`,
`/tmp/diff_orphan_backend.txt`, `/tmp/diff_orphan_frontend.txt`.

## When to re-run

Whenever you add `require_permission(...)` to a handler or restructure a
router. The matrix shifts as enforcement is added; CI doesn't run these
scripts (they're audit tools, not tests).

## Auditing false positives

The extractor is intentionally generous about "what counts as enforcement"
because the codebase has at least 6 different enforcement patterns. If a
handler is flagged as `🔴 NONE` but you know it's protected, check for
patterns the extractor doesn't yet handle and either:

1. Add a regex for the new pattern in `extract_routes_with_auth.py`, OR
2. Document the false positive in `PERMISSIONS_MATRIX.md` § "Audited
   false positives" so future readers don't waste time on it.
