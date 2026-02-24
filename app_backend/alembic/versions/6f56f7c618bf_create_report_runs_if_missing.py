"""create report_runs if missing

Revision ID: 6f56f7c618bf
Revises: 21b5e91ba248
Create Date: 2026-02-21 23:51:55.310933

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6f56f7c618bf"
down_revision: Union[str, None] = "21b5e91ba248"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS public.report_runs (
            id integer NOT NULL,
            run_number integer NOT NULL,
            report_id integer NOT NULL,
            run_by integer NOT NULL,
            triggered_by_id integer NULL,
            parent_run_id integer NULL,
            status varchar(50) NOT NULL,
            started_at timestamp without time zone NULL,
            completed_at timestamp without time zone NULL,
            queued_at timestamp without time zone NULL,
            execution_time_ms integer NULL,
            duration_seconds integer NULL,
            result_count integer NULL,
            result_rows integer NULL,
            result_data text NULL,
            result_format varchar(50) NULL,
            result_path varchar(500) NULL,
            result_size_bytes bigint NULL,
            file_path varchar(500) NULL,
            error_message text NULL,
            error_details text NULL,
            retry_count integer NOT NULL DEFAULT 0,
            parameters text NULL,
            custom_metadata text NULL,
            created_at timestamp without time zone NOT NULL DEFAULT now(),
            updated_at timestamp without time zone NOT NULL DEFAULT now(),
            CONSTRAINT pk_report_runs PRIMARY KEY (id),
            CONSTRAINT fk_report_runs_report FOREIGN KEY (report_id) REFERENCES public.reports(id),
            CONSTRAINT fk_report_runs_run_by FOREIGN KEY (run_by) REFERENCES public.users(id),
            CONSTRAINT fk_report_runs_triggered_by FOREIGN KEY (triggered_by_id) REFERENCES public.users(id),
            CONSTRAINT fk_report_runs_parent FOREIGN KEY (parent_run_id) REFERENCES public.report_runs(id)
        );
        """
    )
    op.execute("CREATE SEQUENCE IF NOT EXISTS public.report_runs_id_seq")
    op.execute(
        "ALTER SEQUENCE public.report_runs_id_seq OWNED BY public.report_runs.id"
    )
    op.execute(
        "ALTER TABLE public.report_runs ALTER COLUMN id SET DEFAULT nextval('public.report_runs_id_seq')"
    )
    op.execute(
        "SELECT setval('public.report_runs_id_seq', COALESCE((SELECT MAX(id) FROM public.report_runs), 0) + 1, false)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_report_runs_run_number ON public.report_runs (run_number)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_report_runs_report_id ON public.report_runs (report_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_report_runs_run_by ON public.report_runs (run_by)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_report_runs_triggered_by_id ON public.report_runs (triggered_by_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_report_runs_parent_run_id ON public.report_runs (parent_run_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_report_runs_status ON public.report_runs (status)"
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
                WHERE n.nspname = 'public'
                  AND c.relname = 'report_runs'
                  AND t.tgname = 'trg_report_runs_set_updated_at'
            ) THEN
                CREATE TRIGGER trg_report_runs_set_updated_at
                BEFORE UPDATE ON public.report_runs
                FOR EACH ROW
                EXECUTE FUNCTION public.set_updated_at_timestamp();
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS public.report_runs")
