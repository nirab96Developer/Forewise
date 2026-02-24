"""ensure updated_at triggers

Revision ID: 118e55ea8d03
Revises: 425da8d79433
Create Date: 2026-02-21 23:16:43.919290

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "118e55ea8d03"
down_revision: Union[str, None] = "425da8d79433"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Single shared trigger function for updated_at maintenance.
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

    # Attach trigger to every base table in public that has an updated_at column.
    op.execute(
        """
        DO $$
        DECLARE
            r RECORD;
            trigger_name text;
        BEGIN
            FOR r IN
                SELECT c.table_name
                FROM information_schema.columns c
                JOIN information_schema.tables t
                  ON t.table_schema = c.table_schema
                 AND t.table_name = c.table_name
                JOIN pg_catalog.pg_tables pgt
                  ON pgt.schemaname = c.table_schema
                 AND pgt.tablename = c.table_name
                WHERE c.table_schema = 'public'
                  AND c.column_name = 'updated_at'
                  AND t.table_type = 'BASE TABLE'
                  AND pgt.tableowner = current_user
            LOOP
                EXECUTE format(
                    'UPDATE public.%I SET updated_at = now() WHERE updated_at IS NULL',
                    r.table_name
                );
                EXECUTE format(
                    'ALTER TABLE public.%I ALTER COLUMN updated_at SET DEFAULT now()',
                    r.table_name
                );

                trigger_name := 'trg_' || r.table_name || '_set_updated_at';
                IF length(trigger_name) > 63 THEN
                    trigger_name := 'trg_' || substr(md5(r.table_name), 1, 20) || '_upd';
                END IF;

                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_trigger t
                    JOIN pg_class c ON c.oid = t.tgrelid
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE n.nspname = 'public'
                      AND c.relname = r.table_name
                      AND t.tgname = trigger_name
                ) THEN
                    EXECUTE format(
                        'CREATE TRIGGER %I BEFORE UPDATE ON public.%I ' ||
                        'FOR EACH ROW EXECUTE FUNCTION public.set_updated_at_timestamp()',
                        trigger_name,
                        r.table_name
                    );
                END IF;
            END LOOP;
        END
        $$;
        """
    )


def downgrade() -> None:
    # Drop all public triggers using this helper function, then drop function.
    op.execute(
        """
        DO $$
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN
                SELECT n.nspname AS schema_name,
                       c.relname AS table_name,
                       t.tgname AS trigger_name
                FROM pg_trigger t
                JOIN pg_class c ON c.oid = t.tgrelid
                JOIN pg_namespace n ON n.oid = c.relnamespace
                JOIN pg_proc p ON p.oid = t.tgfoid
                WHERE n.nspname = 'public'
                  AND NOT t.tgisinternal
                  AND p.proname = 'set_updated_at_timestamp'
            LOOP
                EXECUTE format(
                    'DROP TRIGGER IF EXISTS %I ON %I.%I',
                    r.trigger_name,
                    r.schema_name,
                    r.table_name
                );
            END LOOP;
        END
        $$;
        """
    )
    op.execute("DROP FUNCTION IF EXISTS public.set_updated_at_timestamp()")
