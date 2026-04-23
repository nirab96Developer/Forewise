"""data hygiene + create work_order_coordination_logs

Revision ID: c0d1e2f3a4b5
Revises: b9c0d1e2f3a4
Create Date: 2026-04-23

This migration closes the remaining gaps from the Phase 0–3 audit:

1. Creates `work_order_coordination_logs` — model + frontend + router all
   already exist (Phase 2.3) but the table was never created. Any POST to
   `/work-order-coordination-logs` would 500. Idempotent.

2. Backfills `equipment_models.equipment_type_id` for the 5 rows that the
   Phase 1.3 backfill missed:
     - id 11  (LEGACY_UNKNOWN_DO_NOT_ROTATE) → is_active=false
     - ids 12,13,16,17 (water-truck variants) → equipment_type_id=172
       (id 172 is the WATER_TRUCK equipment_type)

3. Deactivates 21 `supplier_rotations` rows where equipment_type_id is NULL.
   They were seed data created before Phase 1.3; they cannot participate in
   fair rotation (the rotation key is equipment_type_id) so they are dead
   weight that confuses queries.

4. Resets `budgets.committed_amount` from NULL → 0 for 3 rows. The DB
   default is 0 but these rows pre-date the constraint.

5. Soft-deletes 8 budgets (ids 593..600) that point to projects which
   no longer exist. All have total=0, committed=0, spent=0, is_active=false
   — pure stale data, safe to remove from default queries.

Idempotent. All updates use `WHERE` predicates so re-running is a no-op.
"""

from alembic import op
import sqlalchemy as sa


revision = "c0d1e2f3a4b5"
down_revision = "b9c0d1e2f3a4"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # 1. Create work_order_coordination_logs (idempotent)
    if "work_order_coordination_logs" not in inspector.get_table_names():
        op.create_table(
            "work_order_coordination_logs",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("work_order_id", sa.Integer,
                      sa.ForeignKey("work_orders.id", ondelete="CASCADE"),
                      nullable=False, index=True),
            sa.Column("created_by_user_id", sa.Integer,
                      sa.ForeignKey("users.id", ondelete="RESTRICT"),
                      nullable=False, index=True),
            sa.Column("old_supplier_id", sa.Integer,
                      sa.ForeignKey("suppliers.id", ondelete="SET NULL"),
                      nullable=True),
            sa.Column("new_supplier_id", sa.Integer,
                      sa.ForeignKey("suppliers.id", ondelete="SET NULL"),
                      nullable=True),
            sa.Column("action_type", sa.String(50), nullable=False),
            sa.Column("note", sa.Text, nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=False,
                      server_default=sa.text("NOW()")),
            sa.Column("updated_at", sa.DateTime, nullable=False,
                      server_default=sa.text("NOW()")),
            sa.Column("deleted_at", sa.DateTime, nullable=True),
            sa.Column("is_active", sa.Boolean, nullable=False,
                      server_default=sa.text("TRUE")),
            sa.Column("version", sa.Integer, nullable=False,
                      server_default=sa.text("1")),
            sa.CheckConstraint(
                "action_type IN ('CALL','RESEND','ESCALATE','NOTE',"
                "'MOVE_NEXT','STATUS_UPDATE')",
                name="ck_wo_coord_logs_action_type",
            ),
        )
        op.create_index(
            "ix_wo_coord_logs_wo_created",
            "work_order_coordination_logs",
            ["work_order_id", "created_at"],
        )

    # 2. Backfill equipment_models
    # Look up the WATER_TRUCK equipment_type_id by code so we don't hardcode
    # a numeric id that might differ across environments.
    water_truck_type_id = bind.execute(sa.text(
        "SELECT id FROM equipment_types WHERE code = 'WATER_TRUCK' LIMIT 1"
    )).scalar()

    if water_truck_type_id:
        op.execute(sa.text("""
            UPDATE equipment_models
            SET equipment_type_id = :type_id,
                updated_at = NOW()
            WHERE name LIKE 'משאית מים%'
              AND equipment_type_id IS NULL
              AND is_active = TRUE
        """).bindparams(type_id=water_truck_type_id))

    # The LEGACY_UNKNOWN sentinel is not a real model — keep it in the table
    # for FK history but mark it inactive so it never appears in dropdowns
    # or fair-rotation candidates.
    op.execute("""
        UPDATE equipment_models
        SET is_active = FALSE,
            updated_at = NOW()
        WHERE name = 'LEGACY_UNKNOWN_DO_NOT_ROTATE'
          AND is_active = TRUE
    """)

    # 3. Deactivate orphan supplier_rotations
    op.execute("""
        UPDATE supplier_rotations
        SET is_active = FALSE,
            is_available = FALSE,
            updated_at = NOW()
        WHERE equipment_type_id IS NULL
          AND is_active = TRUE
    """)

    # 4. Reset NULL committed_amount to 0 (matches DB default and the
    #    Phase 1.1 reconciliation invariant SUM(commitments) = committed_amount)
    op.execute("""
        UPDATE budgets
        SET committed_amount = 0,
            spent_amount = COALESCE(spent_amount, 0),
            updated_at = NOW()
        WHERE committed_amount IS NULL
          AND deleted_at IS NULL
    """)

    # 5. Soft-delete budgets that point to non-existent projects.
    #    Defensive: also require zero money to avoid silently hiding
    #    real budgets if the FK ever gets accidentally broken.
    op.execute("""
        UPDATE budgets b
        SET deleted_at = NOW(),
            is_active = FALSE,
            updated_at = NOW()
        WHERE b.deleted_at IS NULL
          AND b.project_id IS NOT NULL
          AND COALESCE(b.total_amount, 0) = 0
          AND COALESCE(b.committed_amount, 0) = 0
          AND COALESCE(b.spent_amount, 0) = 0
          AND NOT EXISTS (
            SELECT 1 FROM projects p
            WHERE p.id = b.project_id AND p.deleted_at IS NULL
          )
    """)


def downgrade():
    # Restoring soft-deleted budgets / NULL committed_amount / dropped
    # rotations is risky and bypasses the data-quality intent. Only undo
    # the schema change.
    op.drop_index(
        "ix_wo_coord_logs_wo_created",
        table_name="work_order_coordination_logs",
    )
    op.drop_table("work_order_coordination_logs")
