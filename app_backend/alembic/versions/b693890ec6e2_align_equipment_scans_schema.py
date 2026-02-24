"""align equipment_scans schema

Revision ID: b693890ec6e2
Revises: c387b2bc8d06
Create Date: 2026-02-21 23:24:51.624137

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b693890ec6e2"
down_revision: Union[str, None] = "c387b2bc8d06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "equipment_scans" not in inspector.get_table_names():
        return

    def has_col(name: str) -> bool:
        cols = inspector.get_columns("equipment_scans")
        return any(c["name"] == name for c in cols)

    if has_col("scanned_by_id") and not has_col("scanned_by"):
        op.alter_column(
            "equipment_scans",
            "scanned_by_id",
            new_column_name="scanned_by",
            existing_type=sa.Integer(),
            existing_nullable=False,
        )
        inspector = sa.inspect(bind)

    if has_col("location_lat") and not has_col("latitude"):
        op.alter_column(
            "equipment_scans",
            "location_lat",
            new_column_name="latitude",
            existing_type=sa.Float(),
            existing_nullable=True,
        )
        inspector = sa.inspect(bind)

    if has_col("location_lng") and not has_col("longitude"):
        op.alter_column(
            "equipment_scans",
            "location_lng",
            new_column_name="longitude",
            existing_type=sa.Float(),
            existing_nullable=True,
        )
        inspector = sa.inspect(bind)

    if has_col("scan_date") and not has_col("scan_timestamp"):
        op.add_column(
            "equipment_scans",
            sa.Column("scan_timestamp", sa.DateTime(), nullable=True),
        )
        op.execute(
            "UPDATE equipment_scans "
            "SET scan_timestamp = (scan_date::timestamp) "
            "WHERE scan_timestamp IS NULL AND scan_date IS NOT NULL"
        )
        op.alter_column(
            "equipment_scans",
            "scan_timestamp",
            nullable=False,
            existing_type=sa.DateTime(),
        )
        inspector = sa.inspect(bind)

    if not has_col("scan_value"):
        op.add_column(
            "equipment_scans",
            sa.Column("scan_value", sa.String(length=100), nullable=True),
        )
        op.execute(
            "UPDATE equipment_scans "
            "SET scan_value = COALESCE(scan_value, 'SCAN-' || id::text)"
        )
        op.alter_column(
            "equipment_scans",
            "scan_value",
            nullable=False,
            existing_type=sa.String(length=100),
        )
        inspector = sa.inspect(bind)

    if not has_col("device_info"):
        op.add_column(
            "equipment_scans",
            sa.Column("device_info", sa.Text(), nullable=True),
        )

    if not has_col("purpose"):
        op.add_column(
            "equipment_scans",
            sa.Column("purpose", sa.String(length=50), nullable=True),
        )

    if not has_col("status"):
        op.add_column(
            "equipment_scans",
            sa.Column(
                "status", sa.String(length=20), nullable=True, server_default="COMPLETED"
            ),
        )
        op.execute(
            "UPDATE equipment_scans SET status = 'COMPLETED' WHERE status IS NULL"
        )
        op.alter_column(
            "equipment_scans",
            "status",
            nullable=False,
            existing_type=sa.String(length=20),
            server_default=None,
        )

    # Ensure trigger exists for updated_at maintenance on updates.
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_trigger t
                JOIN pg_class c ON c.oid = t.tgrelid
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public'
                  AND c.relname = 'equipment_scans'
                  AND t.tgname = 'trg_equipment_scans_set_updated_at'
            ) THEN
                CREATE TRIGGER trg_equipment_scans_set_updated_at
                BEFORE UPDATE ON public.equipment_scans
                FOR EACH ROW
                EXECUTE FUNCTION public.set_updated_at_timestamp();
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "equipment_scans" not in inspector.get_table_names():
        return

    def has_col(name: str) -> bool:
        cols = inspector.get_columns("equipment_scans")
        return any(c["name"] == name for c in cols)

    if has_col("scanned_by") and not has_col("scanned_by_id"):
        op.alter_column(
            "equipment_scans",
            "scanned_by",
            new_column_name="scanned_by_id",
            existing_type=sa.Integer(),
            existing_nullable=False,
        )
