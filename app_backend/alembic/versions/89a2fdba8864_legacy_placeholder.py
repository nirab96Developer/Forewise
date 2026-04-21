"""legacy placeholder — original migration file lost, schema already applied to DB

Revision ID: 89a2fdba8864
Revises: None
Create Date: 2026-04-20

Same situation as ``a1b2c3d4e5f6_legacy_placeholder.py``. The migration
``c6b8f8f4a1d2`` declares this id as its parent, but the original file is
missing from the repository. We create the revision as a no-op root so the
chain can be parsed and ``alembic current`` / ``alembic upgrade`` work again.
"""

revision = "89a2fdba8864"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
