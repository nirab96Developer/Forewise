"""merge legacy heads with new strings/case-insensitive migrations

Revision ID: b243458ed40d
Revises: add_deleted_at_budget_transfers, add_user_lifecycle_columns, create_all_missing_tables, e3a4b5c6d7e8
Create Date: 2026-04-20 22:53:37.908527

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b243458ed40d"
down_revision: Union[str, None] = (
    "add_deleted_at_budget_transfers",
    "add_user_lifecycle_columns",
    "create_all_missing_tables",
    "e3a4b5c6d7e8",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
