"""Wave 7.E.1 — seed 6 missing project_assignments permissions.

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-04-25

Adds the six permission codes that `app/routers/project_assignments.py`
already calls via `Depends(require_permission(...))` but that the
permissions table never carried. ADMIN bypasses require_permission so
admin flows worked, but every non-admin manager (REGION_MANAGER,
AREA_MANAGER, WORK_MANAGER) hit 403 the moment they tried to update,
complete, transfer, bulk-assign, or run availability/conflicts checks.

Permissions added
-----------------
  project_assignments.update             -> ADMIN, REGION_MANAGER
  project_assignments.complete           -> ADMIN, REGION_MANAGER, AREA_MANAGER, WORK_MANAGER
  project_assignments.transfer           -> ADMIN, REGION_MANAGER
  project_assignments.bulk_assign        -> ADMIN, REGION_MANAGER
  project_assignments.check_availability -> ADMIN, REGION_MANAGER, AREA_MANAGER
  project_assignments.check_conflicts    -> ADMIN, REGION_MANAGER, AREA_MANAGER

ADMIN appears in every row as belt-and-suspenders. The runtime ADMIN
bypass in dependencies.require_permission already short-circuits all
permission checks for that role, but the explicit assignment keeps the
audit trail consistent with the other 8 project_assignments perms.

Data-only. No schema changes. No router code touched in this commit.
After this migration:
  - WORK_MANAGER can mark their own project assignment complete.
  - AREA_MANAGER can run availability and conflicts checks.
  - REGION_MANAGER can update / transfer / bulk-assign.
  - SUPPLIER and ACCOUNTANT continue to get 403.

Idempotent — both INSERTs use ON CONFLICT DO NOTHING against the
existing UNIQUE constraints (`permissions.code` and
`role_permissions(role_id, permission_id)`).
"""
from alembic import op


revision = "f2a3b4c5d6e7"
down_revision = "e1f2a3b4c5d6"
branch_labels = None
depends_on = None


PERMS = [
    # (code, name, category, description)
    ("project_assignments.update",
     "עדכון הקצאת פרויקט",
     "project_assignments",
     "Update an existing project_assignment row."),
    ("project_assignments.complete",
     "סימון הקצאת פרויקט כהושלמה",
     "project_assignments",
     "Mark a project_assignment as completed."),
    ("project_assignments.transfer",
     "העברת הקצאות פרויקט",
     "project_assignments",
     "Transfer assignments between users."),
    ("project_assignments.bulk_assign",
     "הקצאת רבים בפרויקט",
     "project_assignments",
     "Bulk-assign multiple users to a project."),
    ("project_assignments.check_availability",
     "בדיקת זמינות משתמש",
     "project_assignments",
     "Query whether a user is available for assignment."),
    ("project_assignments.check_conflicts",
     "בדיקת קונפליקטים בהקצאות",
     "project_assignments",
     "Query whether a proposed assignment conflicts with existing ones."),
]

ASSIGNMENTS = [
    # (perm_code, role_codes)
    ("project_assignments.update",             ["ADMIN", "REGION_MANAGER"]),
    ("project_assignments.complete",           ["ADMIN", "REGION_MANAGER", "AREA_MANAGER", "WORK_MANAGER"]),
    ("project_assignments.transfer",           ["ADMIN", "REGION_MANAGER"]),
    ("project_assignments.bulk_assign",        ["ADMIN", "REGION_MANAGER"]),
    ("project_assignments.check_availability", ["ADMIN", "REGION_MANAGER", "AREA_MANAGER"]),
    ("project_assignments.check_conflicts",    ["ADMIN", "REGION_MANAGER", "AREA_MANAGER"]),
]


def upgrade():
    bind = op.get_bind()

    for code, name, category, desc in PERMS:
        bind.exec_driver_sql(
            """
            INSERT INTO permissions (code, name, category, description, is_active)
            VALUES (%(code)s, %(name)s, %(category)s, %(desc)s, TRUE)
            ON CONFLICT (code) DO NOTHING
            """,
            {"code": code, "name": name, "category": category, "desc": desc},
        )

    for perm_code, role_codes in ASSIGNMENTS:
        for role_code in role_codes:
            bind.exec_driver_sql(
                """
                INSERT INTO role_permissions (role_id, permission_id)
                SELECT r.id, p.id
                FROM roles r, permissions p
                WHERE r.code = %(role_code)s AND p.code = %(perm_code)s
                ON CONFLICT (role_id, permission_id) DO NOTHING
                """,
                {"role_code": role_code, "perm_code": perm_code},
            )


def downgrade():
    bind = op.get_bind()
    perm_codes = [code for code, *_ in PERMS]
    placeholders = ", ".join(["%s"] * len(perm_codes))

    bind.exec_driver_sql(
        f"""
        DELETE FROM role_permissions
        WHERE permission_id IN (
            SELECT id FROM permissions WHERE code IN ({placeholders})
        )
        """,
        tuple(perm_codes),
    )
    bind.exec_driver_sql(
        f"DELETE FROM permissions WHERE code IN ({placeholders})",
        tuple(perm_codes),
    )
