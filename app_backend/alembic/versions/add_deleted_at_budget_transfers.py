"""add deleted_at to budget_transfers

Revision ID: add_deleted_at_budget_transfers
Revises: 
Create Date: 2026-03-08

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_deleted_at_budget_transfers'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE budget_transfers
        ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE
    """)


def downgrade():
    op.drop_column('budget_transfers', 'deleted_at')
