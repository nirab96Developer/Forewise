"""align lookup tables and supplier rejection reasons

Revision ID: e1f3b4c5d6e7
Revises: c6b8f8f4a1d2
Create Date: 2026-02-23 23:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e1f3b4c5d6e7"
down_revision: Union[str, None] = "c6b8f8f4a1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _add_col_if_missing(table_name: str, column: sa.Column) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if table_name not in tables:
        return
    cols = {c["name"] for c in inspector.get_columns(table_name)}
    if column.name not in cols:
        op.add_column(table_name, column)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    # role_permissions model expects created_at
    _add_col_if_missing(
        "role_permissions",
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
    )

    # status models expect created_at / updated_at
    _add_col_if_missing(
        "work_order_statuses",
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
    )
    _add_col_if_missing(
        "work_order_statuses",
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
    )
    _add_col_if_missing(
        "worklog_statuses",
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
    )
    _add_col_if_missing(
        "worklog_statuses",
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
    )

    # Create table if missing (required by current models/tests)
    if "supplier_rejection_reasons" not in tables:
        op.create_table(
            "supplier_rejection_reasons",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column("code", sa.String(length=50), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("description", sa.String(length=500), nullable=True),
            sa.Column("category", sa.String(length=50), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.text("true")),
            sa.Column(
                "requires_additional_text",
                sa.Boolean(),
                nullable=True,
                server_default=sa.text("false"),
            ),
            sa.Column(
                "requires_approval", sa.Boolean(), nullable=True, server_default=sa.text("false")
            ),
            sa.Column("display_order", sa.Integer(), nullable=True, server_default=sa.text("0")),
            sa.Column("usage_count", sa.Integer(), nullable=True, server_default=sa.text("0")),
            sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
        )
        op.create_index(
            "ix_supplier_rejection_reasons_code",
            "supplier_rejection_reasons",
            ["code"],
            unique=True,
        )

        op.execute(
            """
            INSERT INTO supplier_rejection_reasons (code, name, description, is_active, display_order)
            VALUES
              ('NOT_AVAILABLE', 'ספק לא זמין', 'ספק לא זמין לביצוע העבודה', true, 1),
              ('PRICE_MISMATCH', 'אי התאמת מחיר', 'מחיר לא תואם ציפיות', true, 2),
              ('TECHNICAL_LIMIT', 'מגבלה טכנית', 'מגבלה טכנית אצל הספק', true, 3)
            """
        )


def downgrade() -> None:
    # Keep downgrade conservative; we do not drop alignment columns automatically.
    # Drop only the table we create in this migration.
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "supplier_rejection_reasons" in set(inspector.get_table_names()):
        op.drop_index(
            "ix_supplier_rejection_reasons_code",
            table_name="supplier_rejection_reasons",
        )
        op.drop_table("supplier_rejection_reasons")
