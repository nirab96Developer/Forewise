# API Contract Export Guide

## Purpose
Provide a repeatable way to export and hand over the API contract.

## Output Artifacts
- `docs/api/openapi.json`
- `docs/api/openapi.yaml` (optional conversion)
- `docs/api/postman-collection.json` (optional)

## Prerequisites
- Backend is running locally or on target env.
- OpenAPI endpoint is reachable (default: `/openapi.json`).

## 1) Export OpenAPI JSON

```bash
curl -sS "http://localhost:8000/openapi.json" -o "docs/api/openapi.json"
```

If backend runs on another host/port, replace URL accordingly.

## 2) Validate JSON (optional)

```bash
python -m json.tool "docs/api/openapi.json" > /dev/null
```

## 3) Convert to YAML (optional)

If `yq` is available:

```bash
yq -P "." "docs/api/openapi.json" > "docs/api/openapi.yaml"
```

Alternative with Node package:

```bash
npx --yes @redocly/cli@latest bundle "docs/api/openapi.json" -o "docs/api/openapi.yaml"
```

## 4) Generate Postman Collection (optional)

```bash
npx --yes openapi-to-postmanv2@latest \
  -s "docs/api/openapi.json" \
  -o "docs/api/postman-collection.json" \
  -p
```

## 5) Handoff Checklist for API Contract

- [ ] `openapi.json` exported from current deployed version
- [ ] optional `openapi.yaml` generated
- [ ] optional Postman collection generated
- [ ] auth flows (`/auth/login`, `/auth/refresh`, reset flows) visible in spec
- [ ] role/permission-protected endpoints documented
- [ ] artifact date/version added to release notes

## Version Tag Recommendation

Add this header block to each exported file package:

- export datetime
- app version / git commit
- environment (staging/production)

