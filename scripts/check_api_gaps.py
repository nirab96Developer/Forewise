#!/usr/bin/env python3
"""
check_api_gaps.py — Frontend↔Backend API Gap Detector

Scans frontend for all API calls and checks if matching
backend endpoints exist.

Usage:  python3 scripts/check_api_gaps.py
"""

import re
import os
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "app_frontend" / "src"
BACKEND = ROOT / "app_backend" / "app" / "routers"

# Colors
R = "\033[31m"
G = "\033[32m"
Y = "\033[33m"
C = "\033[36m"
B = "\033[1m"
N = "\033[0m"

# ──────────────────────────────────────────────
# STEP 1: Parse backend endpoints
# ──────────────────────────────────────────────
def parse_backend():
    """Extract all backend endpoints from router files."""
    endpoints = set()

    for py_file in sorted(BACKEND.glob("*.py")):
        if py_file.name == "__init__.py" or py_file.name == "__pycache__":
            continue

        code = py_file.read_text(errors="ignore")

        # Find prefix
        m = re.search(r'APIRouter\s*\([^)]*prefix\s*=\s*"([^"]*)"', code)
        if not m:
            continue
        prefix = m.group(1).rstrip("/")

        # Find all route decorators
        for dm in re.finditer(
            r'@router\.(get|post|put|patch|delete)\s*\(\s*"([^"]*)"',
            code
        ):
            method = dm.group(1).upper()
            path = dm.group(2)
            full = prefix + path
            # Normalize {param} → {*}
            norm = re.sub(r'\{[^}]+\}', '{*}', full)
            endpoints.add((method, norm))

    return endpoints


# ──────────────────────────────────────────────
# STEP 2: Parse frontend API calls
# ──────────────────────────────────────────────
def parse_frontend():
    """Extract all frontend api.method() calls."""
    calls = []

    # Pattern: api.get('/path') or api.get(`/path`) or api.get(`/path/${var}`)
    api_pat = re.compile(
        r"""api\.(get|post|put|patch|delete)\s*\(\s*(['"`])(.+?)\2""",
        re.DOTALL,
    )
    # Also match template literals: api.get(`...`)
    api_tpl = re.compile(
        r"""api\.(get|post|put|patch|delete)\s*\(\s*`([^`]+)`""",
    )

    for ext in ("*.ts", "*.tsx"):
        for ts_file in sorted(FRONTEND.rglob(ext)):
            if "node_modules" in str(ts_file) or ".d.ts" in ts_file.name:
                continue
            rel = ts_file.relative_to(FRONTEND)
            try:
                lines = ts_file.read_text(errors="ignore").splitlines()
            except Exception:
                continue

            for i, line in enumerate(lines, 1):
                # Skip comments
                stripped = line.strip()
                if stripped.startswith("//") or stripped.startswith("*"):
                    continue

                # Try template literal first
                for m in api_tpl.finditer(line):
                    method = m.group(1).upper()
                    raw_path = m.group(2).strip()
                    calls.append((method, raw_path, str(rel), i))

                # Then try quoted strings (avoid duplicates)
                for m in api_pat.finditer(line):
                    if m.group(2) == '`':
                        continue  # already caught by tpl
                    method = m.group(1).upper()
                    raw_path = m.group(3).strip()
                    calls.append((method, raw_path, str(rel), i))

    return calls


# ──────────────────────────────────────────────
# STEP 3: Normalize & match
# ──────────────────────────────────────────────
def normalize_frontend_path(raw):
    """Turn a frontend path into a matchable pattern."""
    # Remove query strings
    path = raw.split("?")[0]
    # Replace ${...} template vars with {*}
    path = re.sub(r'\$\{[^}]+\}', '{*}', path)
    # Replace remaining {anything} with {*}
    path = re.sub(r'\{[^}]+\}', '{*}', path)
    # Remove trailing slash
    path = path.rstrip("/")
    return path


def _path_to_regex(backend_path):
    """Convert a backend path like /worklogs/{*}/approve to a regex."""
    # Escape everything except {*}
    parts = backend_path.split("{*}")
    escaped = [re.escape(p) for p in parts]
    return "^" + "[^/]+".join(escaped) + "$"


def match_endpoint(method, norm_path, backend_eps):
    """Check if a frontend call matches any backend endpoint."""
    # Skip paths that are fully dynamic (e.g. just "{*}" or "{*}/{*}")
    if not norm_path.startswith("/"):
        return True  # Can't validate, skip

    # Exact match
    if (method, norm_path) in backend_eps:
        return True

    # With trailing slash
    if (method, norm_path + "/") in backend_eps:
        return True

    # Without trailing slash
    if norm_path.endswith("/") and (method, norm_path.rstrip("/")) in backend_eps:
        return True

    # Check if backend has this path with any method (method mismatch is different from missing)
    for bm, bp in backend_eps:
        if bp == norm_path:
            return True  # endpoint exists, method may differ — not a "missing" gap

    # Wildcard expansion: if frontend path has {*}, check if it could match
    # any backend endpoint when {*} is replaced with a concrete value.
    # e.g. /worklogs/{*}/{*} should match /worklogs/{*}/approve
    if "{*}" in norm_path:
        # Build regex from frontend path: {*} matches any non-slash segment
        fe_regex = "^" + re.escape(norm_path).replace(r"\{\*\}", "[^/]+") + "$"
        for bm, bp in backend_eps:
            if bm == method and re.match(fe_regex, bp):
                return True

    # Reverse: if backend path has {*}, check if frontend concrete path matches
    for bm, bp in backend_eps:
        if bm != method or "{*}" not in bp:
            continue
        be_regex = _path_to_regex(bp)
        if re.match(be_regex, norm_path):
            return True

    return False


# ──────────────────────────────────────────────
# STEP 4: Check usage (is it dead code?)
# ──────────────────────────────────────────────
def check_usage(file_path, lineno):
    """Determine if a service method is actually called from pages/components."""
    full_path = FRONTEND / file_path

    # If it's in a page or component, it's definitely active
    if not file_path.startswith("services/"):
        return "ACTIVE", "in page/component"

    # Find the method name that contains this line
    try:
        lines = full_path.read_text(errors="ignore").splitlines()
    except Exception:
        return "UNKNOWN", ""

    method_name = None
    for i in range(lineno - 1, max(lineno - 15, -1), -1):
        if i < 0 or i >= len(lines):
            continue
        m = re.search(r'async\s+(\w+)\s*\(', lines[i])
        if m:
            method_name = m.group(1)
            break

    if not method_name:
        return "UNKNOWN", ""

    # Search for this method name in pages and components
    callers = 0
    for subdir in ("pages", "components", "hooks", "context"):
        search_dir = FRONTEND / subdir
        if not search_dir.exists():
            continue
        for f in search_dir.rglob("*.tsx"):
            try:
                content = f.read_text(errors="ignore")
                if method_name in content:
                    callers += 1
            except Exception:
                pass
        for f in search_dir.rglob("*.ts"):
            if ".d.ts" in f.name:
                continue
            try:
                content = f.read_text(errors="ignore")
                if method_name in content:
                    callers += 1
            except Exception:
                pass

    if callers == 0:
        return "DEAD", f"method '{method_name}' — 0 callers"
    return "ACTIVE", f"method '{method_name}' — {callers} caller(s)"


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def main():
    print(f"\n{B}========================================={N}")
    print(f"{B}  Frontend <> Backend API Gap Detector{N}")
    print(f"{B}========================================={N}\n")

    # Step 1
    print(f"{C}[1/4] Scanning backend routers...{N}")
    backend_eps = parse_backend()
    print(f"   Found {G}{len(backend_eps)}{N} backend endpoints")

    # Step 2
    print(f"{C}[2/4] Scanning frontend API calls...{N}")
    frontend_calls = parse_frontend()
    # Deduplicate
    seen = set()
    unique_calls = []
    for method, raw, file, line in frontend_calls:
        norm = normalize_frontend_path(raw)
        key = (method, norm, file, line)
        if key not in seen:
            seen.add(key)
            unique_calls.append((method, raw, norm, file, line))
    print(f"   Found {G}{len(unique_calls)}{N} frontend API calls")

    # Step 3
    print(f"{C}[3/4] Cross-referencing...{N}\n")

    matched = 0
    gaps = []

    for method, raw, norm, file, line in unique_calls:
        if match_endpoint(method, norm, backend_eps):
            matched += 1
        else:
            gaps.append((method, norm, raw, file, line))

    print(f"{B}{'='*60}{N}")
    print(f"{B}  RESULTS{N}")
    print(f"{B}{'='*60}{N}\n")
    print(f"  Backend endpoints:   {B}{len(backend_eps)}{N}")
    print(f"  Frontend API calls:  {B}{len(unique_calls)}{N}")
    print(f"  Matched:             {G}{B}{matched}{N}")
    print(f"  Missing in backend:  {R}{B}{len(gaps)}{N}\n")

    if not gaps:
        print(f"  {G}All frontend API calls have matching backend endpoints!{N}\n")
        return

    # Step 4 — classify
    print(f"{C}[4/4] Classifying gaps...{N}\n")

    active_gaps = []
    dead_gaps = []

    for method, norm, raw, file, line in gaps:
        status, detail = check_usage(file, line)
        entry = (method, norm, file, line, detail)
        if status == "DEAD":
            dead_gaps.append(entry)
        else:
            active_gaps.append(entry)

    # Print ACTIVE gaps (real problems)
    if active_gaps:
        print(f"  {R}{B}ACTIVE GAPS — endpoints called from live pages:{N}")
        print(f"  {'─'*68}")
        print(f"  {B}{'METHOD':<8} {'ENDPOINT':<40} {'FILE:LINE'}{N}")
        print(f"  {'─'*68}")
        for method, norm, file, line, detail in sorted(active_gaps, key=lambda x: x[1]):
            print(f"  {R}{method:<8}{N} {norm:<40} {Y}{file}:{line}{N}")
            if detail:
                print(f"           {C}{detail}{N}")
        print()

    # Print DEAD gaps (cleanup candidates)
    if dead_gaps:
        print(f"  {Y}{B}DEAD CODE — service methods never called:{N}")
        print(f"  {'─'*68}")
        print(f"  {B}{'METHOD':<8} {'ENDPOINT':<40} {'FILE:LINE'}{N}")
        print(f"  {'─'*68}")
        for method, norm, file, line, detail in sorted(dead_gaps, key=lambda x: x[1]):
            print(f"  {Y}{method:<8}{N} {norm:<40} {file}:{line}")
            if detail:
                print(f"           {C}{detail}{N}")
        print()

    # Summary
    print(f"{B}{'='*60}{N}")
    print(f"  {R}{B}{len(active_gaps)}{N} active gaps (need backend endpoints or frontend fix)")
    print(f"  {Y}{B}{len(dead_gaps)}{N} dead code (safe to remove)")
    print(f"{B}{'='*60}{N}\n")


if __name__ == "__main__":
    main()
