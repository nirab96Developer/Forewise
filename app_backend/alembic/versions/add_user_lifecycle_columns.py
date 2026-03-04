"""add user lifecycle columns: suspended_at, suspension_reason, scheduled_deletion_at, previous_role_id

Revision ID: add_user_lifecycle_columns
Revises: c6b8f8f4a1d2
Create Date: 2026-03-03

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_user_lifecycle_columns'
down_revision = 'c6b8f8f4a1d2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('suspended_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('suspension_reason', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('scheduled_deletion_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('previous_role_id', sa.Integer(),
                                     sa.ForeignKey('roles.id', ondelete='SET NULL'),
                                     nullable=True))


def downgrade():
    op.drop_column('users', 'previous_role_id')
    op.drop_column('users', 'scheduled_deletion_at')
    op.drop_column('users', 'suspension_reason')
    op.drop_column('users', 'suspended_at')
