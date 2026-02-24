"""fix budget_transfers id sequence

Revision ID: 425da8d79433
Revises: b0dccf6f50d9
Create Date: 2026-02-21 23:13:32.193867

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "425da8d79433"
down_revision: Union[str, None] = "b0dccf6f50d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Handle both cases:
    # A) table exists but sequence/default is missing
    # B) table is missing entirely
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS public.budget_transfers (
            id integer NOT NULL,
            from_budget_id integer NOT NULL,
            to_budget_id integer NOT NULL,
            requested_by integer NOT NULL,
            approved_by integer NULL,
            amount numeric(15, 2) NOT NULL,
            transfer_type varchar(50) NOT NULL,
            reason varchar(500) NOT NULL,
            status varchar(50) NULL DEFAULT 'PENDING',
            is_active boolean NULL DEFAULT true,
            requested_at timestamp without time zone NULL,
            approved_at timestamp without time zone NULL,
            executed_at timestamp without time zone NULL,
            notes text NULL,
            created_at timestamp without time zone NULL DEFAULT now(),
            updated_at timestamp without time zone NULL DEFAULT now(),
            CONSTRAINT pk_budget_transfers PRIMARY KEY (id),
            CONSTRAINT fk_budget_transfers_from_budget
                FOREIGN KEY (from_budget_id) REFERENCES public.budgets(id),
            CONSTRAINT fk_budget_transfers_to_budget
                FOREIGN KEY (to_budget_id) REFERENCES public.budgets(id),
            CONSTRAINT fk_budget_transfers_requested_by
                FOREIGN KEY (requested_by) REFERENCES public.users(id),
            CONSTRAINT fk_budget_transfers_approved_by
                FOREIGN KEY (approved_by) REFERENCES public.users(id)
        );
        """
    )

    op.execute("CREATE SEQUENCE IF NOT EXISTS public.budget_transfers_id_seq")
    op.execute(
        "ALTER SEQUENCE public.budget_transfers_id_seq "
        "OWNED BY public.budget_transfers.id"
    )
    op.execute(
        "ALTER TABLE public.budget_transfers "
        "ALTER COLUMN id SET DEFAULT nextval('public.budget_transfers_id_seq')"
    )
    op.execute(
        """
        SELECT setval(
            'public.budget_transfers_id_seq',
            COALESCE((SELECT MAX(id) FROM public.budget_transfers), 0) + 1,
            false
        );
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE public.budget_transfers ALTER COLUMN id DROP DEFAULT")
    op.execute("DROP SEQUENCE IF EXISTS public.budget_transfers_id_seq")
