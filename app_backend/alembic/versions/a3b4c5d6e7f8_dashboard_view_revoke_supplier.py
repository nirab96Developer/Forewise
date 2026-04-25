"""Wave Dashboard — revoke DASHBOARD.VIEW from SUPPLIER role.

Revision ID: a3b4c5d6e7f8
Revises: f2a3b4c5d6e7
Create Date: 2026-04-25

DASHBOARD.VIEW already exists in the permissions table. The next step
in the FE↔BE alignment plan adds `require_permission("dashboard.view")`
to every /api/v1/dashboard/* endpoint. Currently DASHBOARD.VIEW is
assigned to ALL 7 roles, including SUPPLIER. The product decision is
that suppliers must NOT see the internal manager dashboard — they
have their own portal flow via supplier_portal tokens.

This migration removes the SUPPLIER → DASHBOARD.VIEW assignment so
that when the router enforcement lands in the next commit, suppliers
get a clean 403 instead of a "scoped" empty dashboard.

Idempotent — DELETE is no-op if the row was already removed.
"""
from alembic import op


revision = "a3b4c5d6e7f8"
down_revision = "f2a3b4c5d6e7"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    bind.exec_driver_sql(
        """
        DELETE FROM role_permissions
        WHERE role_id = (SELECT id FROM roles WHERE code = 'SUPPLIER')
          AND permission_id = (SELECT id FROM permissions WHERE code = 'DASHBOARD.VIEW')
        """
    )


def downgrade():
    """Restore SUPPLIER → DASHBOARD.VIEW."""
    bind = op.get_bind()
    bind.exec_driver_sql(
        """
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.code = 'SUPPLIER' AND p.code = 'DASHBOARD.VIEW'
        ON CONFLICT (role_id, permission_id) DO NOTHING
        """
    )
