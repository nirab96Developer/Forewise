"""align invoice_items schema

Revision ID: 48a71c5f4f42
Revises: 69be4834b32e
Create Date: 2026-02-21 23:29:34.045067

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "48a71c5f4f42"
down_revision: Union[str, None] = "69be4834b32e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "invoice_items" not in inspector.get_table_names():
        return

    def has_col(name: str) -> bool:
        cols = inspector.get_columns("invoice_items")
        return any(c["name"] == name for c in cols)

    if not has_col("line_number"):
        op.add_column("invoice_items", sa.Column("line_number", sa.Integer(), nullable=True))
        op.execute(
            "UPDATE invoice_items i SET line_number = s.rn "
            "FROM (SELECT id, ROW_NUMBER() OVER (PARTITION BY invoice_id ORDER BY id) AS rn FROM invoice_items) s "
            "WHERE i.id = s.id AND i.line_number IS NULL"
        )
        op.alter_column("invoice_items", "line_number", nullable=False)
        op.create_index("ix_invoice_items_line_number", "invoice_items", ["line_number"])
        inspector = sa.inspect(bind)

    if not has_col("item_code"):
        op.add_column(
            "invoice_items", sa.Column("item_code", sa.String(length=50), nullable=True)
        )

    if not has_col("discount_percent"):
        op.add_column(
            "invoice_items",
            sa.Column(
                "discount_percent",
                sa.Numeric(5, 2),
                nullable=False,
                server_default="0",
            ),
        )
        op.alter_column(
            "invoice_items",
            "discount_percent",
            server_default=None,
            existing_type=sa.Numeric(5, 2),
        )

    if not has_col("discount_amount"):
        op.add_column(
            "invoice_items",
            sa.Column(
                "discount_amount",
                sa.Numeric(18, 2),
                nullable=False,
                server_default="0",
            ),
        )
        op.alter_column(
            "invoice_items",
            "discount_amount",
            server_default=None,
            existing_type=sa.Numeric(18, 2),
        )

    if not has_col("subtotal"):
        op.add_column(
            "invoice_items",
            sa.Column("subtotal", sa.Numeric(18, 2), nullable=True),
        )
        if has_col("total_price"):
            op.execute(
                "UPDATE invoice_items SET subtotal = COALESCE(subtotal, total_price)"
            )
        op.execute("UPDATE invoice_items SET subtotal = 0 WHERE subtotal IS NULL")
        op.alter_column(
            "invoice_items",
            "subtotal",
            nullable=False,
            existing_type=sa.Numeric(18, 2),
        )
        inspector = sa.inspect(bind)

    if not has_col("tax_rate"):
        op.add_column(
            "invoice_items",
            sa.Column(
                "tax_rate",
                sa.Numeric(5, 2),
                nullable=False,
                server_default="0.17",
            ),
        )
        op.alter_column(
            "invoice_items",
            "tax_rate",
            server_default=None,
            existing_type=sa.Numeric(5, 2),
        )

    if not has_col("tax_amount"):
        op.add_column(
            "invoice_items",
            sa.Column("tax_amount", sa.Numeric(18, 2), nullable=True),
        )
        op.execute("UPDATE invoice_items SET tax_amount = COALESCE(tax_amount, 0)")
        op.alter_column(
            "invoice_items",
            "tax_amount",
            nullable=False,
            existing_type=sa.Numeric(18, 2),
        )
        inspector = sa.inspect(bind)

    if not has_col("total"):
        op.add_column("invoice_items", sa.Column("total", sa.Numeric(18, 2), nullable=True))
        if has_col("total_price"):
            op.execute("UPDATE invoice_items SET total = COALESCE(total, total_price)")
        op.execute("UPDATE invoice_items SET total = COALESCE(total, 0)")
        op.alter_column(
            "invoice_items",
            "total",
            nullable=False,
            existing_type=sa.Numeric(18, 2),
        )
        inspector = sa.inspect(bind)

    if not has_col("notes"):
        op.add_column("invoice_items", sa.Column("notes", sa.Text(), nullable=True))

    if not has_col("metadata_json"):
        op.add_column("invoice_items", sa.Column("metadata_json", sa.Text(), nullable=True))

    op.execute("UPDATE invoice_items SET updated_at = now() WHERE updated_at IS NULL")
    op.execute("ALTER TABLE invoice_items ALTER COLUMN updated_at SET DEFAULT now()")
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
                  AND c.relname = 'invoice_items'
                  AND t.tgname = 'trg_invoice_items_set_updated_at'
            ) THEN
                CREATE TRIGGER trg_invoice_items_set_updated_at
                BEFORE UPDATE ON public.invoice_items
                FOR EACH ROW
                EXECUTE FUNCTION public.set_updated_at_timestamp();
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    return
