"""repair missing id sequences

Revision ID: 53f4417291ec
Revises: 79c994c316ed
Create Date: 2026-02-21 23:20:37.093701

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "53f4417291ec"
down_revision: Union[str, None] = "79c994c316ed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Repair tables that use integer PK(id) but lost sequence/default.
    op.execute(
        """
        DO $$
        DECLARE
            r RECORD;
            seq_name text;
        BEGIN
            FOR r IN
                SELECT c.table_name
                FROM information_schema.columns c
                JOIN information_schema.tables t
                  ON t.table_schema = c.table_schema
                 AND t.table_name = c.table_name
                JOIN information_schema.table_constraints tc
                  ON tc.table_schema = c.table_schema
                 AND tc.table_name = c.table_name
                 AND tc.constraint_type = 'PRIMARY KEY'
                JOIN information_schema.key_column_usage kcu
                  ON kcu.constraint_schema = tc.constraint_schema
                 AND kcu.constraint_name = tc.constraint_name
                 AND kcu.table_schema = tc.table_schema
                 AND kcu.table_name = tc.table_name
                JOIN pg_catalog.pg_tables pgt
                  ON pgt.schemaname = c.table_schema
                 AND pgt.tablename = c.table_name
                WHERE c.table_schema = 'public'
                  AND t.table_type = 'BASE TABLE'
                  AND c.column_name = 'id'
                  AND c.data_type = 'integer'
                  AND c.column_default IS NULL
                  AND COALESCE(c.is_identity, 'NO') = 'NO'
                  AND kcu.column_name = 'id'
                  AND pgt.tableowner = current_user
                GROUP BY c.table_name
            LOOP
                seq_name := r.table_name || '_id_seq';

                EXECUTE format(
                    'CREATE SEQUENCE IF NOT EXISTS public.%I',
                    seq_name
                );
                EXECUTE format(
                    'ALTER SEQUENCE public.%I OWNED BY public.%I.id',
                    seq_name,
                    r.table_name
                );
                EXECUTE format(
                    'ALTER TABLE public.%I ALTER COLUMN id SET DEFAULT nextval(%L)',
                    r.table_name,
                    'public.' || seq_name
                );
                EXECUTE format(
                    'SELECT setval(%L, COALESCE((SELECT MAX(id) FROM public.%I), 0) + 1, false)',
                    'public.' || seq_name,
                    r.table_name
                );
            END LOOP;
        END
        $$;
        """
    )


def downgrade() -> None:
    # Intentionally no-op: this migration repairs drift and is safe to keep.
    return
