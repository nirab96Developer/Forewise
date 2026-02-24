# Role Permission Matrix

## Purpose
This document provides a handoff-ready RBAC matrix.  
The runtime source of truth is the database tables `roles`, `permissions`, and `role_permissions`.

## Role Baseline

Primary backend role codes (`app_backend/app/models/role.py`):
- `ADMIN`
- `REGION_MANAGER`
- `AREA_MANAGER`
- `WORK_MANAGER`
- `ACCOUNTANT`
- `SUPPLIER`
- `VIEWER`

Frontend also references additional operational roles (`app_frontend/src/utils/permissions.ts`):
- `ORDER_COORDINATOR`
- `FIELD_WORKER`
- `SUPPLIER_MANAGER`

## Permission Domains (Representative)

From frontend/backend contract conventions (example codes):
- `DASHBOARD.*`
- `PROJECTS.*`
- `WORK_ORDERS.*`
- `WORKLOGS.*`
- `EQUIPMENT.*`
- `SUPPLIERS.*`
- `INVOICES.*`
- `BUDGETS.*`
- `REPORTS.*`
- `USERS.*`
- `ROLES.*`
- `REGIONS.*`
- `AREAS.*`
- `ACTIVITY_LOG.*`
- `SYSTEM.*`

## Matrix (Baseline for Handoff)

Legend:
- `A` = full domain admin/manage
- `R` = read/view only
- `O` = operational write subset
- `-` = no default access

| Role | Dashboard | Projects | Work Orders | Worklogs | Equipment | Suppliers | Finance (Budgets/Invoices) | Reports | Users/Roles | Geography | System |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ADMIN | A | A | A | A | A | A | A | A | A | A | A |
| REGION_MANAGER | R | A | A | O | O | O | R | R | - | A | - |
| AREA_MANAGER | R | O | A | O | O | O | R | R | - | O | - |
| WORK_MANAGER | R | O | A | A | O | O | - | R | - | - | - |
| ORDER_COORDINATOR | R | O | A | O | O | O | - | R | - | - | - |
| ACCOUNTANT | R | R | R | R | - | - | A | A | - | - | - |
| SUPPLIER_MANAGER | R | R | O | O | O | A | - | R | - | - | - |
| FIELD_WORKER | R | R | O | A | O | - | - | - | - | - | - |
| SUPPLIER | R | - | O (assigned scope) | O (assigned scope) | - | O (portal scope) | - | - | - | - | - |
| VIEWER | R | R | R | R | R | R | R | R | - | R | - |

## Extraction Query (Authoritative Mapping)

Use this query to export the exact active mapping from production/staging DB:

```sql
SELECT
  r.code AS role_code,
  p.code AS permission_code
FROM role_permissions rp
JOIN roles r ON r.id = rp.role_id
JOIN permissions p ON p.id = rp.permission_id
WHERE rp.deleted_at IS NULL
  AND r.deleted_at IS NULL
  AND p.deleted_at IS NULL
ORDER BY r.code, p.code;
```

## Notes
- This matrix is a governance baseline for handoff and review.
- Final enforcement is always backend-side via permission checks.
- Any mismatch found in UI menus should be resolved by aligning menu guards to backend permission codes.

