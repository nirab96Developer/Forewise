"""create equipment_maintenance if missing

Revision ID: c387b2bc8d06
Revises: b91864444566
Create Date: 2026-02-21 23:23:17.744984

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c387b2bc8d06"
down_revision: Union[str, None] = "b91864444566"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS public.equipment_maintenance (
            id integer NOT NULL,
            equipment_id integer NOT NULL,
            performed_by integer NULL,
            scheduled_by integer NULL,
            maintenance_type varchar(50) NOT NULL,
            scheduled_date date NOT NULL,
            performed_date date NULL,
            next_maintenance_date date NULL,
            description text NOT NULL,
            findings text NULL,
            actions_taken text NULL,
            parts_replaced text NULL,
            notes text NULL,
            hours_spent numeric(5, 2) NULL,
            labor_cost numeric(10, 2) NULL,
            parts_cost numeric(10, 2) NULL,
            total_cost numeric(10, 2) NULL,
            status varchar(20) NOT NULL,
            is_active boolean NOT NULL DEFAULT true,
            completed_at timestamp without time zone NULL,
            created_at timestamp without time zone NOT NULL DEFAULT now(),
            updated_at timestamp without time zone NOT NULL DEFAULT now(),
            deleted_at timestamp without time zone NULL,
            version integer NULL DEFAULT 1,
            CONSTRAINT pk_equipment_maintenance PRIMARY KEY (id),
            CONSTRAINT fk_equipment_maintenance_equipment
                FOREIGN KEY (equipment_id) REFERENCES public.equipment(id),
            CONSTRAINT fk_equipment_maintenance_performed_by
                FOREIGN KEY (performed_by) REFERENCES public.users(id),
            CONSTRAINT fk_equipment_maintenance_scheduled_by
                FOREIGN KEY (scheduled_by) REFERENCES public.users(id)
        );
        """
    )

    op.execute("CREATE SEQUENCE IF NOT EXISTS public.equipment_maintenance_id_seq")
    op.execute(
        "ALTER SEQUENCE public.equipment_maintenance_id_seq "
        "OWNED BY public.equipment_maintenance.id"
    )
    op.execute(
        "ALTER TABLE public.equipment_maintenance "
        "ALTER COLUMN id SET DEFAULT nextval('public.equipment_maintenance_id_seq')"
    )
    op.execute(
        """
        SELECT setval(
            'public.equipment_maintenance_id_seq',
            COALESCE((SELECT MAX(id) FROM public.equipment_maintenance), 0) + 1,
            false
        );
        """
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_equipment_maintenance_equipment_id "
        "ON public.equipment_maintenance (equipment_id)"
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
                  AND c.relname = 'equipment_maintenance'
                  AND t.tgname = 'trg_equipment_maintenance_set_updated_at'
            ) THEN
                CREATE TRIGGER trg_equipment_maintenance_set_updated_at
                BEFORE UPDATE ON public.equipment_maintenance
                FOR EACH ROW
                EXECUTE FUNCTION public.set_updated_at_timestamp();
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS trg_equipment_maintenance_set_updated_at "
        "ON public.equipment_maintenance"
    )
    op.execute("DROP TABLE IF EXISTS public.equipment_maintenance")
    op.execute("DROP SEQUENCE IF EXISTS public.equipment_maintenance_id_seq")
