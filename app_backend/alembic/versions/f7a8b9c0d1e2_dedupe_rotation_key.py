"""dedupe rotation key + add equipment_type_id to equipment_models

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-04-22

Phase 1.3 of the model-restructure roadmap.

Problem
-------
`supplier_rotations` had two competing keys: `equipment_type_id` (FK to
equipment_types) and `equipment_category_id` (FK to equipment_categories).
The audit found:
  * 174 rows used equipment_type_id
  * 0 rows used equipment_category_id
  * The fair-rotation queue (`get_rotation_queue`) only filters by
    equipment_type_id

The dual key existed because `equipment_models.category_id` points at
equipment_categories, but the rotation logic keys off equipment_types,
forcing every dispatch to fudge the conversion. The Phase-0 hotfix dodged
the mismatch by writing to `equipment_category_id` — correct from FK
perspective, wrong for business semantics (the rotation queue then
couldn't find those rows).

Fix
---
1. Add `equipment_type_id` directly on `equipment_models` with a name-based
   backfill from the existing `category_id` chain. (equipment_types and
   equipment_categories have an overlapping but not identical name list.)
2. Drop `equipment_category_id` from `supplier_rotations`. Single key now.

Phase 3 will collapse the duplicate equipment_types/equipment_categories
tables entirely.
"""

from alembic import op
import sqlalchemy as sa


revision = "f7a8b9c0d1e2"
down_revision = "e6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # 1. Add equipment_type_id to equipment_models (nullable, FK to equipment_types).
    em_cols = {c["name"] for c in inspector.get_columns("equipment_models")}
    if "equipment_type_id" not in em_cols:
        op.add_column(
            "equipment_models",
            sa.Column("equipment_type_id", sa.Integer, nullable=True),
        )
        op.create_foreign_key(
            "fk_equipment_models_equipment_type_id",
            "equipment_models", "equipment_types",
            ["equipment_type_id"], ["id"],
            ondelete="SET NULL",
        )
        op.create_index(
            "ix_equipment_models_equipment_type_id",
            "equipment_models", ["equipment_type_id"],
        )

    # Backfill: match by name through the category. We ignore models with
    # no category, no matching category name in equipment_types, or that
    # already have equipment_type_id set.
    op.execute("""
        UPDATE equipment_models m
        SET equipment_type_id = et.id
        FROM equipment_categories ec
        JOIN equipment_types et ON et.name = ec.name
        WHERE m.category_id = ec.id
          AND m.equipment_type_id IS NULL
    """)

    # 2. Drop equipment_category_id from supplier_rotations.
    sr_cols = {c["name"] for c in inspector.get_columns("supplier_rotations")}
    if "equipment_category_id" in sr_cols:
        # Drop FK + index first, then column.
        # (The constraint name follows the default Postgres pattern.)
        for fk in inspector.get_foreign_keys("supplier_rotations"):
            if fk.get("constrained_columns") == ["equipment_category_id"]:
                op.drop_constraint(fk["name"], "supplier_rotations", type_="foreignkey")
        for idx in inspector.get_indexes("supplier_rotations"):
            if idx.get("column_names") == ["equipment_category_id"]:
                op.drop_index(idx["name"], table_name="supplier_rotations")
        op.drop_column("supplier_rotations", "equipment_category_id")


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    sr_cols = {c["name"] for c in inspector.get_columns("supplier_rotations")}
    if "equipment_category_id" not in sr_cols:
        op.add_column(
            "supplier_rotations",
            sa.Column("equipment_category_id", sa.Integer, nullable=True),
        )
        op.create_foreign_key(
            "supplier_rotations_equipment_category_id_fkey",
            "supplier_rotations", "equipment_categories",
            ["equipment_category_id"], ["id"],
        )
        op.create_index(
            "ix_supplier_rotations_equipment_category_id",
            "supplier_rotations", ["equipment_category_id"],
        )

    em_cols = {c["name"] for c in inspector.get_columns("equipment_models")}
    if "equipment_type_id" in em_cols:
        op.drop_index("ix_equipment_models_equipment_type_id",
                      table_name="equipment_models")
        op.drop_constraint("fk_equipment_models_equipment_type_id",
                           "equipment_models", type_="foreignkey")
        op.drop_column("equipment_models", "equipment_type_id")
