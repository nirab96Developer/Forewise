"""align invoice_payments schema

Revision ID: efe13a731bc9
Revises: 48a71c5f4f42
Create Date: 2026-02-21 23:43:44.851707

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "efe13a731bc9"
down_revision: Union[str, None] = "48a71c5f4f42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "invoice_payments" not in inspector.get_table_names():
        return

    def has_col(name: str) -> bool:
        cols = inspector.get_columns("invoice_payments")
        return any(c["name"] == name for c in cols)

    # Rename legacy creator column to runtime field name.
    if has_col("created_by") and not has_col("processed_by"):
        op.alter_column(
            "invoice_payments",
            "created_by",
            new_column_name="processed_by",
            existing_type=sa.Integer(),
            existing_nullable=True,
        )
        inspector = sa.inspect(bind)

    if not has_col("processed_by"):
        op.add_column(
            "invoice_payments",
            sa.Column("processed_by", sa.Integer(), nullable=True),
        )
        inspector = sa.inspect(bind)

    if not has_col("transaction_id"):
        op.add_column(
            "invoice_payments",
            sa.Column("transaction_id", sa.String(length=100), nullable=True),
        )

    if not has_col("bank_name"):
        op.add_column(
            "invoice_payments",
            sa.Column("bank_name", sa.String(length=100), nullable=True),
        )

    if not has_col("account_number"):
        op.add_column(
            "invoice_payments",
            sa.Column("account_number", sa.String(length=50), nullable=True),
        )

    if not has_col("metadata_json"):
        op.add_column(
            "invoice_payments",
            sa.Column("metadata_json", sa.Text(), nullable=True),
        )

    if not has_col("version"):
        op.add_column(
            "invoice_payments",
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        )
        op.execute("UPDATE invoice_payments SET version = 1 WHERE version IS NULL")
        op.alter_column(
            "invoice_payments",
            "version",
            server_default=None,
            existing_type=sa.Integer(),
        )

    # Add FK/index for processed_by if users table exists.
    if "users" in inspector.get_table_names():
        fk_names = {fk["name"] for fk in inspector.get_foreign_keys("invoice_payments")}
        if "fk_invoice_payments_processed_by_users" not in fk_names:
            op.create_foreign_key(
                "fk_invoice_payments_processed_by_users",
                "invoice_payments",
                "users",
                ["processed_by"],
                ["id"],
            )

    index_names = {idx["name"] for idx in inspector.get_indexes("invoice_payments")}
    if "ix_invoice_payments_processed_by" not in index_names:
        op.create_index(
            "ix_invoice_payments_processed_by", "invoice_payments", ["processed_by"]
        )

    op.execute(
        "UPDATE invoice_payments SET updated_at = now() WHERE updated_at IS NULL"
    )
    op.execute("ALTER TABLE invoice_payments ALTER COLUMN updated_at SET DEFAULT now()")
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
                  AND c.relname = 'invoice_payments'
                  AND t.tgname = 'trg_invoice_payments_set_updated_at'
            ) THEN
                CREATE TRIGGER trg_invoice_payments_set_updated_at
                BEFORE UPDATE ON public.invoice_payments
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
    if "invoice_payments" not in inspector.get_table_names():
        return

    if any(
        c["name"] == "processed_by" for c in inspector.get_columns("invoice_payments")
    ):
        try:
            op.drop_constraint(
                "fk_invoice_payments_processed_by_users",
                "invoice_payments",
                type_="foreignkey",
            )
        except Exception:
            pass
        try:
            op.drop_index(
                "ix_invoice_payments_processed_by", table_name="invoice_payments"
            )
        except Exception:
            pass
