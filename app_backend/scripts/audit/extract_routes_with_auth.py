#!/usr/bin/env python3
"""Extract every FastAPI route with its auth metadata.

For each (method, path) we record:
  - file        (router source)
  - func        (handler name)
  - summary     (first line of docstring or func name)
  - auth_dep    (none / get_current_user / get_current_active_user / both)
  - require_perm (list of permission codes used in the handler body)
  - require_role (list of role codes if any)
"""
import os
import sys
import re
import ast
import json

ROUTERS_DIR = "/root/forewise/app_backend/app/routers"

def parse_router_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()

    # Try AST parse first
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []

    # Find router prefix
    router_prefix = ""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "router" for t in node.targets
        ):
            if isinstance(node.value, ast.Call):
                for kw in node.value.keywords:
                    if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                        router_prefix = kw.value.value
                        break

    # Pass 1: collect every function in the file and its directly-detected
    # enforcement. Pass 2 (below) walks call edges so wrappers like
    # `patch_approve(...) -> approve(...)` inherit enforcement from the
    # function they delegate to. Without this, every PATCH/POST alias gets
    # falsely flagged as 🔴.
    func_enforcement: dict[str, dict] = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body_src = ast.unparse(node) if hasattr(ast, "unparse") else ""
        sig_src = ast.unparse(node.args) if hasattr(ast, "unparse") else ""
        # Two enforcement patterns:
        #   1. Inline:   require_permission(current_user, "perm.code")
        #   2. Factory:  Depends(require_permission("perm.code"))
        # Both count as enforcement; the matrix doesn't distinguish.
        rp = sorted(set(
            re.findall(
                r"require_permission\([^,]*,\s*['\"]([^'\"]+)['\"]", body_src
            )
            + re.findall(
                r"Depends\(\s*require_permission\(\s*['\"]([^'\"]+)['\"]", body_src
            )
        ))
        cv = sorted(set(re.findall(
            r"verify_(admin|owner|manager|coordinator)\(\s*current_user",
            body_src,
        )))
        # Direct inline raise on role-code mismatch
        irb_direct = bool(re.search(
            r"current_user\.role\.code\s*(?:!=|not\s+in)\s*\(?['\"]?\w+",
            body_src,
        )) and "raise" in body_src and ("403" in body_src or "FORBIDDEN" in body_src)
        # Indirect admin check via boolean variable:
        #   is_admin = ... current_user.role.code in (...); if not is_admin: raise 403
        irb_indirect = bool(re.search(
            r"\bis_admin\b\s*=.*current_user\.role\.code\s+in\s*\(",
            body_src,
        )) and bool(re.search(r"if\s+not\s+is_admin\s*:\s*\n[^\n]*raise", body_src))
        # Helper-function inline check: _require_X(current_user) calls
        helper_check = bool(re.findall(
            r"_require_[a-z_]+\(\s*current_user", body_src
        ))
        # Self-service scope filter — handler forces queries to current_user.id
        # before any DB read. Examples:
        #   search.user_id = current_user.id           ← attribute assignment
        #   filters["user_id"] = current_user.id       ← dict-key assignment
        # We do NOT match `kwarg=current_user.id` (logging helpers,
        # service calls etc.) because those are not query filters and
        # were producing false 🟢 on /equipment/{id}/scan and /release.
        scope_self_filter = bool(re.search(
            r"(\.user_id\s*=\s*current_user\.id"
            r"|\[\s*['\"]user_id['\"]\s*\]\s*=\s*current_user\.id)",
            body_src,
        ))
        func_enforcement[node.name] = {
            "require_perms": rp,
            "custom_verify": cv,
            "inline_role_block": irb_direct or irb_indirect,
            "helper_check": helper_check,
            "scope_self_filter": scope_self_filter,
            "body_src": body_src,
            "sig_src": sig_src,
        }

    # Pass 2: resolve wrapper enforcement.
    # A "wrapper" is a function whose body is essentially a single call to
    # another function in the same file. We propagate that target's
    # enforcement back. We allow up to 3 hops to handle deeper aliases.
    def _resolve_wrapper(name: str, depth: int = 0) -> dict:
        info = func_enforcement.get(name, {})
        if depth > 3 or info.get("require_perms") or info.get("custom_verify") \
                or info.get("inline_role_block") or info.get("helper_check") \
                or info.get("scope_self_filter"):
            return info
        body = info.get("body_src", "")
        # Detect direct delegation: `return X(...)` where X is in this file
        m = re.search(r"return\s+(\w+)\s*\(", body)
        if m and m.group(1) in func_enforcement and m.group(1) != name:
            target = _resolve_wrapper(m.group(1), depth + 1)
            return {
                **info,
                "require_perms": list(target.get("require_perms", [])),
                "custom_verify": list(target.get("custom_verify", [])),
                "inline_role_block": target.get("inline_role_block", False),
                "helper_check": target.get("helper_check", False),
                "scope_self_filter": target.get("scope_self_filter", False),
                "wrapper_of": m.group(1),
            }
        return info

    routes = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        # Find route decorator
        method = None
        path = None
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            if isinstance(dec.func, ast.Attribute) and isinstance(dec.func.value, ast.Name):
                if dec.func.value.id == "router":
                    m = dec.func.attr
                    if m in ("get", "post", "put", "patch", "delete"):
                        method = m.upper()
                        if dec.args and isinstance(dec.args[0], ast.Constant):
                            path = dec.args[0].value

        if method is None:
            continue

        full_path = f"/api/v1{router_prefix}{path or ''}"
        full_path = re.sub(r"//+", "/", full_path)
        if full_path.endswith("/") and full_path != "/":
            full_path_stripped = full_path[:-1]
        else:
            full_path_stripped = full_path

        # Auth deps from function args
        auth_deps = set()
        sig = ast.unparse(node.args) if hasattr(ast, "unparse") else ""
        for dep in ("get_current_user", "get_current_active_user"):
            if dep in sig:
                auth_deps.add(dep)

        # Resolve enforcement (pass 2 above propagated wrapper -> target).
        resolved = _resolve_wrapper(node.name)
        body_src = resolved.get("body_src", ast.unparse(node) if hasattr(ast, "unparse") else "")
        require_perms = list(resolved.get("require_perms", []))
        custom_verify = list(resolved.get("custom_verify", []))
        # `inline_role_block` collapses ALL non-permission-based enforcement
        # patterns: direct role check, indirect (`is_admin` variable),
        # helper-call check, AND self-service scope filter on user_id.
        # The matrix renders all of these as 🟢; the CSV's `enforcement`
        # column carries the specific pattern so a human can audit.
        inline_role_block = (
            bool(resolved.get("inline_role_block", False))
            or bool(resolved.get("helper_check", False))
            or bool(resolved.get("scope_self_filter", False))
        )
        # Roles still useful for diagnostics
        role_checks = sorted(set(re.findall(
            r"\.role\.code\s*==\s*['\"]([^'\"]+)['\"]|in_role\(['\"]([^'\"]+)['\"]",
            body_src,
        )))
        roles = sorted(set(filter(None, [a or b for a, b in role_checks])))

        # Docstring
        summary = ""
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            doc = node.body[0].value.value.strip().splitlines()[0].strip()
            summary = doc[:120]
        if not summary:
            summary = node.name

        # Detect mutation vs read
        is_mutation = method in ("POST", "PUT", "PATCH", "DELETE")

        # Detect financial / sensitive keywords
        body_lower = body_src.lower()
        sensitive_kw = []
        for kw in (
            "amount", "frozen", "spent", "approve", "reject", "pay",
            "lock", "unlock", "delete", "transfer", "permission", "role",
        ):
            if kw in body_lower:
                sensitive_kw.append(kw)

        routes.append({
            "method": method,
            "path": full_path_stripped,
            "file": os.path.basename(path),
            "func": node.name,
            "summary": summary,
            "auth_deps": sorted(auth_deps),
            "require_perms": require_perms,
            "roles_checked": roles,
            "custom_verify": custom_verify,
            "inline_role_block": inline_role_block,
            "is_mutation": is_mutation,
            "sensitive_kw": sensitive_kw,
        })

    # path is shadowed above; restore
    return routes


def main():
    all_routes = []
    for fname in sorted(os.listdir(ROUTERS_DIR)):
        if not fname.endswith(".py") or fname.startswith("__"):
            continue
        full = os.path.join(ROUTERS_DIR, fname)
        try:
            routes = parse_router_file(full)
            for r in routes:
                r["file"] = fname
            all_routes.extend(routes)
        except Exception as e:
            print(f"ERROR {fname}: {e}", file=sys.stderr)

    print(json.dumps(all_routes, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
