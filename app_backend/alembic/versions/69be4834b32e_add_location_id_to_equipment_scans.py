"""add location_id to equipment_scans

Revision ID: 69be4834b32e
Revises: b693890ec6e2
Create Date: 2026-02-21 23:26:22.608141

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "69be4834b32e"
down_revision: Union[str, None] = "b693890ec6e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "equipment_scans" not in inspector.get_table_names():
        return

    cols = {c["name"] for c in inspector.get_columns("equipment_scans")}
    if "location_id" not in cols:
        op.add_column(
            "equipment_scans",
            sa.Column("location_id", sa.Integer(), nullable=True),
        )
        # Add FK only if locations table exists and FK not already present.
        if "locations" in inspector.get_table_names():
            op.create_foreign_key(
                "fk_equipment_scans_location_id",
                "equipment_scans",
                "locations",
                ["location_id"],
                ["id"],
            )
        op.create_index(
            "ix_equipment_scans_location_id", "equipment_scans", ["location_id"]
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "equipment_scans" not in inspector.get_table_names():
        return

    cols = {c["name"] for c in inspector.get_columns("equipment_scans")}
    if "location_id" in cols:
        try:
            op.drop_constraint(
                "fk_equipment_scans_location_id",
                "equipment_scans",
                type_="foreignkey",
            )
        except Exception:
            pass
        try:
            op.drop_index("ix_equipment_scans_location_id", table_name="equipment_scans")
        except Exception:
            pass
        op.drop_column("equipment_scans", "location_id")
