"""create supplier_constraint_logs if missing

Revision ID: 21b5e91ba248
Revises: efe13a731bc9
Create Date: 2026-02-21 23:47:51.167508

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "21b5e91ba248"
down_revision: Union[str, None] = "efe13a731bc9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS public.supplier_constraint_logs (
            id integer NOT NULL,
            work_order_id integer NOT NULL,
            supplier_id integer NOT NULL,
            constraint_reason_id integer NULL,
            constraint_reason_text varchar(500) NOT NULL,
            justification text NULL,
            created_by integer NOT NULL,
            created_at timestamp without time zone NOT NULL DEFAULT now(),
            approved_by integer NULL,
            approved_at timestamp without time zone NULL,
            CONSTRAINT pk_supplier_constraint_logs PRIMARY KEY (id),
            CONSTRAINT fk_supplier_constraint_logs_work_order
                FOREIGN KEY (work_order_id) REFERENCES public.work_orders(id),
            CONSTRAINT fk_supplier_constraint_logs_supplier
                FOREIGN KEY (supplier_id) REFERENCES public.suppliers(id),
            CONSTRAINT fk_supplier_constraint_logs_reason
                FOREIGN KEY (constraint_reason_id) REFERENCES public.supplier_constraint_reasons(id),
            CONSTRAINT fk_supplier_constraint_logs_created_by
                FOREIGN KEY (created_by) REFERENCES public.users(id),
            CONSTRAINT fk_supplier_constraint_logs_approved_by
                FOREIGN KEY (approved_by) REFERENCES public.users(id)
        );
        """
    )
    op.execute("CREATE SEQUENCE IF NOT EXISTS public.supplier_constraint_logs_id_seq")
    op.execute(
        "ALTER SEQUENCE public.supplier_constraint_logs_id_seq OWNED BY public.supplier_constraint_logs.id"
    )
    op.execute(
        "ALTER TABLE public.supplier_constraint_logs ALTER COLUMN id SET DEFAULT nextval('public.supplier_constraint_logs_id_seq')"
    )
    op.execute(
        "SELECT setval('public.supplier_constraint_logs_id_seq', COALESCE((SELECT MAX(id) FROM public.supplier_constraint_logs), 0) + 1, false)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_supplier_constraint_logs_work_order_id ON public.supplier_constraint_logs (work_order_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_supplier_constraint_logs_supplier_id ON public.supplier_constraint_logs (supplier_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_supplier_constraint_logs_constraint_reason_id ON public.supplier_constraint_logs (constraint_reason_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_supplier_constraint_logs_created_by ON public.supplier_constraint_logs (created_by)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS public.supplier_constraint_logs")
