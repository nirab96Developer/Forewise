#!/usr/bin/env python3
"""
Cross-reference backend FastAPI routes vs frontend axios calls.
Resolves `${this.baseUrl}` substitutions per service file.
"""
import re
import os

BACKEND_FILE = "/tmp/backend_routes.txt"
FRONTEND_DIR = "/root/forewise/app_frontend/src"
PREFIX = "/api/v1"


def normalize(path: str) -> str:
    p = path.strip()
    p = p.split("?")[0]
    if p.startswith(PREFIX):
        p = p[len(PREFIX):]
    elif p.startswith("/api/v1"):
        p = p[len("/api/v1"):]
    if len(p) > 1 and p.endswith("/"):
        p = p[:-1]
    p = re.sub(r"\$\{[^}]+\}", "{}", p)
    p = re.sub(r":([a-zA-Z_][a-zA-Z0-9_]*)", "{}", p)
    p = re.sub(r"\{[^}]+\}", "{}", p)
    if not p.startswith("/"):
        p = "/" + p
    return p


def load_backend():
    routes = set()
    skip_paths = {"/", "/health", "/info", "/openapi.json", "/redoc", "/test", "/docs",
                  "/admin/health"}
    with open(BACKEND_FILE) as f:
        for line in f:
            m = re.match(r"^(GET|POST|PUT|PATCH|DELETE)\s+(\S+)\s*$", line.rstrip())
            if not m:
                continue
            method, path = m.groups()
            if path in skip_paths:
                continue
            routes.add((method, normalize(path), path))
    return routes


def extract_baseurl(text: str) -> str | None:
    """Find class-level `baseUrl = '/...'` or `BASE_URL = '...'`"""
    m = re.search(
        r"\b(?:private|public|readonly|const|let)?\s*(?:baseUrl|BASE_URL|baseURL)\s*=\s*['\"`]([^'\"`]+)['\"`]",
        text,
    )
    return m.group(1) if m else None


def load_frontend():
    calls = set()
    pat_call = re.compile(
        r"\b(?:api|axios|client|http|this\.api|this\.client)\s*\.\s*(get|post|put|patch|delete)\s*\(\s*[`'\"]([^`'\"]+)[`'\"]",
        re.IGNORECASE,
    )
    pat_call2 = re.compile(
        r"\b(?:api|axios|client|http)\s*\.\s*(get|post|put|patch|delete)\s*\(\s*\$?\{?\s*this\.baseUrl\s*\}?\s*[,)]",
        re.IGNORECASE,
    )
    for root, _, files in os.walk(FRONTEND_DIR):
        for fname in files:
            if not fname.endswith((".ts", ".tsx", ".js", ".jsx")):
                continue
            full = os.path.join(root, fname)
            try:
                with open(full, errors="ignore") as f:
                    text = f.read()
            except OSError:
                continue
            base = extract_baseurl(text) or ""
            relfile = os.path.relpath(full, FRONTEND_DIR)
            for m in pat_call.finditer(text):
                method = m.group(1).upper()
                path = m.group(2)
                if path.startswith(("http", "blob:", "data:", "/auth/login")):
                    pass  # keep auth-related but skip absolute URLs
                if path.startswith(("http", "blob:", "data:")):
                    continue
                # Substitute baseUrl
                resolved = path.replace("${this.baseUrl}", base)
                if not resolved.startswith("/"):
                    resolved = base + ("/" if not resolved.startswith("?") else "") + resolved
                if not resolved.startswith("/"):
                    resolved = "/" + resolved
                calls.add((method, normalize(resolved), path, relfile))
            # Calls that are JUST `api.post(this.baseUrl, ...)` with no extra path
            for m in pat_call2.finditer(text):
                method = m.group(1).upper()
                if base:
                    calls.add((method, normalize(base), "this.baseUrl", relfile))
    return calls


def main():
    backend = load_backend()
    frontend = load_frontend()

    backend_keys = {(m, p) for m, p, _ in backend}
    frontend_keys = {(m, p) for m, p, _, _ in frontend}

    orphan_fe = sorted(
        (m, p, src, file_)
        for m, p, src, file_ in frontend
        if (m, p) not in backend_keys
    )
    orphan_be = sorted(
        (m, p, src)
        for m, p, src in backend
        if (m, p) not in frontend_keys
    )
    matched = backend_keys & frontend_keys

    with open("/tmp/diff_orphan_frontend.txt", "w") as f:
        f.write(f"# Frontend calls with no matching backend route ({len(orphan_fe)})\n")
        f.write("# Format: METHOD  resolved_path  source_in_code  file\n\n")
        for m, p, src, file_ in orphan_fe:
            f.write(f"{m:6s}  {p:55s}  {src:50s}  {file_}\n")

    with open("/tmp/diff_orphan_backend.txt", "w") as f:
        f.write(f"# Backend routes never called from frontend ({len(orphan_be)})\n")
        f.write("# Format: METHOD  normalized_path  raw_path\n\n")
        for m, p, src in orphan_be:
            f.write(f"{m:6s}  {p:55s}  {src}\n")

    # Also write the matched set so the matrix builder can mark
    # ui_exposed=yes per (method, normalized_path).
    with open("/tmp/diff_matched.txt", "w") as f:
        f.write(f"# Matched (method, normalized_path) pairs ({len(matched)})\n\n")
        for m, p in sorted(matched):
            f.write(f"{m:6s}  {p}\n")

    print(f"Backend routes:  {len(backend)}")
    print(f"Frontend calls:  {len(frontend)}")
    print(f"Matched:         {len(matched)}")
    print(f"Orphan frontend: {len(orphan_fe)}")
    print(f"Orphan backend:  {len(orphan_be)}")


if __name__ == "__main__":
    main()
