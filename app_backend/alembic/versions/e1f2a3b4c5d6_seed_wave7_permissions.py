"""Wave 7.A — seed missing permissions for upcoming Wave 7 enforcement.

Revision ID: e1f2a3b4c5d6
Revises: c0d1e2f3a4b5
Create Date: 2026-04-24

Adds 9 permission codes that the Wave 7 audit identified as missing
from the `permissions` table, then assigns each to the appropriate
roles per the agreed matrix:

  supplier_rotations.read    -> ADMIN, ORDER_COORDINATOR, AREA_MANAGER, REGION_MANAGER
  supplier_rotations.list    -> ADMIN, ORDER_COORDINATOR, AREA_MANAGER, REGION_MANAGER
  supplier_rotations.create  -> ADMIN, ORDER_COORDINATOR
  supplier_rotations.update  -> ADMIN, ORDER_COORDINATOR
  supplier_rotations.delete  -> ADMIN
  activity_types.create      -> ADMIN
  activity_types.update      -> ADMIN
  activity_types.delete      -> ADMIN
  notifications.manage       -> ADMIN

Data-only. No schema changes. No code changes elsewhere in this commit.
The actual `require_permission` calls on the routes that need these
perms come in Waves 7.B / 7.C / 7.D.

ADMIN bypass in dependencies.require_permission means admin always
passes regardless of role_permission rows, so the ADMIN assignments
here are belt-and-suspenders. Other roles MUST have the perm or 403.

Idempotent — both INSERTs use ON CONFLICT DO NOTHING against the
existing UNIQUE constraints (`permissions.code` and
`role_permissions(role_id, permission_id)`).
"""
from alembic import op


revision = "e1f2a3b4c5d6"
down_revision = "c0d1e2f3a4b5"
branch_labels = None
depends_on = None


PERMS = [
    # (code, name, category, description)
    ("supplier_rotations.read",   "צפייה ברוטציית ספקים",  "supplier_rotations", "Read a single rotation row"),
    ("supplier_rotations.list",   "רשימת רוטציית ספקים",   "supplier_rotations", "List rotation rows"),
    ("supplier_rotations.create", "יצירת רוטציית ספקים",   "supplier_rotations", "Create rotation entries"),
    ("supplier_rotations.update", "עדכון רוטציית ספקים",   "supplier_rotations", "Update rotation entries"),
    ("supplier_rotations.delete", "מחיקת רוטציית ספקים",   "supplier_rotations", "Delete rotation entries"),
    ("activity_types.create",     "יצירת סוג פעולה",       "activity_types",     "Create activity types"),
    ("activity_types.update",     "עדכון סוג פעולה",       "activity_types",     "Update activity types"),
    ("activity_types.delete",     "מחיקת סוג פעולה",       "activity_types",     "Delete activity types"),
    ("notifications.manage",      "ניהול התראות",          "notifications",      "Bulk / cleanup notification ops"),
]

ASSIGNMENTS = [
    # (perm_code, role_codes)
    ("supplier_rotations.read",   ["ADMIN", "ORDER_COORDINATOR", "AREA_MANAGER", "REGION_MANAGER"]),
    ("supplier_rotations.list",   ["ADMIN", "ORDER_COORDINATOR", "AREA_MANAGER", "REGION_MANAGER"]),
    ("supplier_rotations.create", ["ADMIN", "ORDER_COORDINATOR"]),
    ("supplier_rotations.update", ["ADMIN", "ORDER_COORDINATOR"]),
    ("supplier_rotations.delete", ["ADMIN"]),
    ("activity_types.create",     ["ADMIN"]),
    ("activity_types.update",     ["ADMIN"]),
    ("activity_types.delete",     ["ADMIN"]),
    ("notifications.manage",      ["ADMIN"]),
]


def upgrade():
    bind = op.get_bind()

    # 1. Insert the 9 permission rows (idempotent via UNIQUE on code).
    for code, name, category, desc in PERMS:
        bind.exec_driver_sql(
            """
            INSERT INTO permissions (code, name, category, description, is_active)
            VALUES (%(code)s, %(name)s, %(category)s, %(desc)s, TRUE)
            ON CONFLICT (code) DO NOTHING
            """,
            {"code": code, "name": name, "category": category, "desc": desc},
        )

    # 2. Wire each permission to the agreed roles (idempotent via UNIQUE
    #    on (role_id, permission_id)).
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

    # Drop role_permissions rows first, then the permissions.
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
