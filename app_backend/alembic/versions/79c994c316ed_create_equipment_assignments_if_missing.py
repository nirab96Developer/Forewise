"""create equipment_assignments if missing

Revision ID: 79c994c316ed
Revises: 118e55ea8d03
Create Date: 2026-02-21 23:18:33.095302

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "79c994c316ed"
down_revision: Union[str, None] = "118e55ea8d03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS public.equipment_assignments (
            id integer NOT NULL,
            equipment_id integer NOT NULL,
            project_id integer NULL,
            assigned_by integer NULL,
            start_date timestamp without time zone NULL,
            end_date timestamp without time zone NULL,
            hourly_rate double precision NULL,
            daily_rate double precision NULL,
            planned_hours double precision NULL,
            actual_hours double precision NULL,
            status varchar(20) NULL,
            notes text NULL,
            metadata_json text NULL,
            created_at timestamp without time zone NOT NULL DEFAULT now(),
            updated_at timestamp without time zone NOT NULL DEFAULT now(),
            deleted_at timestamp without time zone NULL,
            is_active boolean NULL DEFAULT true,
            version integer NULL DEFAULT 1,
            CONSTRAINT pk_equipment_assignments PRIMARY KEY (id),
            CONSTRAINT fk_equipment_assignments_equipment
                FOREIGN KEY (equipment_id) REFERENCES public.equipment(id),
            CONSTRAINT fk_equipment_assignments_project
                FOREIGN KEY (project_id) REFERENCES public.projects(id)
        );
        """
    )

    op.execute("CREATE SEQUENCE IF NOT EXISTS public.equipment_assignments_id_seq")
    op.execute(
        "ALTER SEQUENCE public.equipment_assignments_id_seq "
        "OWNED BY public.equipment_assignments.id"
    )
    op.execute(
        "ALTER TABLE public.equipment_assignments "
        "ALTER COLUMN id SET DEFAULT nextval('public.equipment_assignments_id_seq')"
    )
    op.execute(
        """
        SELECT setval(
            'public.equipment_assignments_id_seq',
            COALESCE((SELECT MAX(id) FROM public.equipment_assignments), 0) + 1,
            false
        );
        """
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_equipment_assignments_equipment_id "
        "ON public.equipment_assignments (equipment_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_equipment_assignments_project_id "
        "ON public.equipment_assignments (project_id)"
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
                  AND c.relname = 'equipment_assignments'
                  AND t.tgname = 'trg_equipment_assignments_set_updated_at'
            ) THEN
                CREATE TRIGGER trg_equipment_assignments_set_updated_at
                BEFORE UPDATE ON public.equipment_assignments
                FOR EACH ROW
                EXECUTE FUNCTION public.set_updated_at_timestamp();
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS trg_equipment_assignments_set_updated_at "
        "ON public.equipment_assignments"
    )
    op.execute("DROP TABLE IF EXISTS public.equipment_assignments")
    op.execute("DROP SEQUENCE IF EXISTS public.equipment_assignments_id_seq")
