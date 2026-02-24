"""align budget_items schema

Revision ID: b0dccf6f50d9
Revises: create_all_missing_tables
Create Date: 2026-02-21 22:47:18.924107

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b0dccf6f50d9"
down_revision: Union[str, None] = "create_all_missing_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "budget_items" not in inspector.get_table_names():
        return

    def has_col(column_name: str) -> bool:
        cols = inspector.get_columns("budget_items")
        return any(col["name"] == column_name for col in cols)

    # Keep existing data by renaming legacy "name" to the model field.
    if has_col("name") and not has_col("item_name"):
        op.alter_column(
            "budget_items",
            "name",
            new_column_name="item_name",
            existing_type=sa.String(length=100),
            existing_nullable=False,
        )
        inspector = sa.inspect(bind)

    # If table came from another branch and still lacks item_name, add it safely.
    if not has_col("item_name"):
        op.add_column(
            "budget_items",
            sa.Column("item_name", sa.Unicode(length=200), nullable=True),
        )
        op.execute(
            "UPDATE budget_items SET item_name = 'Unnamed item' WHERE item_name IS NULL"
        )
        op.alter_column("budget_items", "item_name", nullable=False)
        inspector = sa.inspect(bind)

    if not has_col("item_code"):
        op.add_column(
            "budget_items",
            sa.Column("item_code", sa.Unicode(length=50), nullable=True),
        )

    if not has_col("description"):
        op.add_column(
            "budget_items",
            sa.Column("description", sa.Unicode(), nullable=True),
        )

    if not has_col("item_type"):
        op.add_column(
            "budget_items",
            sa.Column("item_type", sa.Unicode(length=50), nullable=True),
        )
        op.execute(
            "UPDATE budget_items SET item_type = COALESCE(category, 'EXPENSE') "
            "WHERE item_type IS NULL"
        )
        op.alter_column("budget_items", "item_type", nullable=False)
        inspector = sa.inspect(bind)

    if not has_col("priority"):
        op.add_column(
            "budget_items", sa.Column("priority", sa.Integer(), nullable=True)
        )

    if not has_col("planned_amount"):
        op.add_column(
            "budget_items",
            sa.Column(
                "planned_amount", sa.Numeric(18, 2), nullable=True, server_default="0"
            ),
        )
        if has_col("allocated_amount"):
            op.execute(
                "UPDATE budget_items "
                "SET planned_amount = COALESCE(allocated_amount, planned_amount, 0)"
            )
        op.alter_column(
            "budget_items",
            "planned_amount",
            nullable=False,
            server_default=None,
            existing_type=sa.Numeric(18, 2),
        )
        inspector = sa.inspect(bind)

    if not has_col("approved_amount"):
        op.add_column(
            "budget_items",
            sa.Column("approved_amount", sa.Numeric(18, 2), nullable=True),
        )
        if has_col("allocated_amount"):
            op.execute(
                "UPDATE budget_items "
                "SET approved_amount = COALESCE(approved_amount, allocated_amount)"
            )

    if not has_col("committed_amount"):
        op.add_column(
            "budget_items",
            sa.Column("committed_amount", sa.Numeric(18, 2), nullable=True),
        )
        if has_col("locked_amount"):
            op.execute(
                "UPDATE budget_items "
                "SET committed_amount = COALESCE(committed_amount, locked_amount)"
            )

    if not has_col("actual_amount"):
        op.add_column(
            "budget_items",
            sa.Column("actual_amount", sa.Numeric(18, 2), nullable=True),
        )
        if has_col("used_amount"):
            op.execute(
                "UPDATE budget_items "
                "SET actual_amount = COALESCE(actual_amount, used_amount)"
            )

    if not has_col("notes"):
        op.add_column(
            "budget_items",
            sa.Column("notes", sa.Unicode(), nullable=True),
        )

    if not has_col("metadata_json"):
        op.add_column(
            "budget_items",
            sa.Column("metadata_json", sa.Unicode(), nullable=True),
        )

    # BaseModel optional columns expected by services.
    if not has_col("deleted_at"):
        op.add_column(
            "budget_items",
            sa.Column("deleted_at", sa.DateTime(), nullable=True),
        )

    if not has_col("version"):
        op.add_column(
            "budget_items",
            sa.Column("version", sa.Integer(), nullable=True, server_default="1"),
        )
        op.execute("UPDATE budget_items SET version = 1 WHERE version IS NULL")
        op.alter_column(
            "budget_items",
            "version",
            server_default=None,
            existing_type=sa.Integer(),
        )

    if has_col("category"):
        op.alter_column(
            "budget_items",
            "category",
            existing_type=sa.String(length=50),
            nullable=True,
        )

    if has_col("updated_at"):
        op.execute(
            "UPDATE budget_items SET updated_at = now() WHERE updated_at IS NULL"
        )
        op.execute("ALTER TABLE budget_items ALTER COLUMN updated_at SET DEFAULT now()")

    # Keep test/runtime behavior consistent: update updated_at on every row update.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION public.set_updated_at_timestamp()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_trigger t
                JOIN pg_class c ON c.oid = t.tgrelid
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE t.tgname = 'trg_budget_items_set_updated_at'
                  AND n.nspname = 'public'
                  AND c.relname = 'budget_items'
            ) THEN
                CREATE TRIGGER trg_budget_items_set_updated_at
                BEFORE UPDATE ON public.budget_items
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
    if "budget_items" not in inspector.get_table_names():
        return

    def has_col(column_name: str) -> bool:
        cols = inspector.get_columns("budget_items")
        return any(col["name"] == column_name for col in cols)

    if has_col("item_name") and not has_col("name"):
        op.alter_column(
            "budget_items",
            "item_name",
            new_column_name="name",
            existing_type=sa.Unicode(length=200),
            existing_nullable=False,
        )

    op.execute(
        "DROP TRIGGER IF EXISTS trg_budget_items_set_updated_at ON public.budget_items"
    )
