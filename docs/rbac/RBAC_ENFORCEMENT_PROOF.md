# RBAC Enforcement Proof

## Enforcement Components

- Authentication and permission loader:
  - `app_backend/app/core/dependencies.py`
- Permission checks in routers:
  - `require_permission(current_user, "<permission.code>")`

## Critical Endpoint Examples

1. Work Orders
- File: `app_backend/app/routers/work_orders.py`
- Examples:
  - `require_permission(current_user, "work_orders.read")`
  - `require_permission(current_user, "work_orders.approve")`

2. Worklogs
- File: `app_backend/app/routers/worklogs.py`
- Examples:
  - `require_permission(current_user, "worklogs.read")`
  - `require_permission(current_user, "worklogs.approve")`

## Scope Enforcement Policy (Area Rule)

Policy baseline for area-scoped roles:

- List queries must include area scope:
  - `WHERE project.area_id = user.area_id`
- GET by id must re-check scope after fetch.
- Violations return `403` (or `404` by concealment policy).

Reference implementation helper:
- `check_project_access` in `app_backend/app/core/dependencies.py`

