"""add equipment models and work order model lock

Revision ID: c6b8f8f4a1d2
Revises: 89a2fdba8864
Create Date: 2026-02-22 23:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c6b8f8f4a1d2"
down_revision: Union[str, None] = "89a2fdba8864"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "equipment_models" not in inspector.get_table_names():
        op.execute(
            """
            CREATE TABLE IF NOT EXISTS public.equipment_models (
                id integer NOT NULL,
                name varchar(200) NOT NULL,
                category_id integer NULL,
                is_active boolean NOT NULL DEFAULT true,
                created_at timestamp without time zone NOT NULL DEFAULT now(),
                updated_at timestamp without time zone NOT NULL DEFAULT now(),
                deleted_at timestamp without time zone NULL,
                version integer NOT NULL DEFAULT 1,
                CONSTRAINT pk_equipment_models PRIMARY KEY (id),
                CONSTRAINT fk_equipment_models_category FOREIGN KEY (category_id) REFERENCES public.equipment_categories(id)
            );
            """
        )
        op.execute("CREATE SEQUENCE IF NOT EXISTS public.equipment_models_id_seq")
        op.execute("ALTER SEQUENCE public.equipment_models_id_seq OWNED BY public.equipment_models.id")
        op.execute("ALTER TABLE public.equipment_models ALTER COLUMN id SET DEFAULT nextval('public.equipment_models_id_seq')")
        op.execute("SELECT setval('public.equipment_models_id_seq', COALESCE((SELECT MAX(id) FROM public.equipment_models), 0) + 1, false)")

    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_equipment_models_name ON public.equipment_models (name)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_equipment_models_category_id ON public.equipment_models (category_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_equipment_models_is_active ON public.equipment_models (is_active)")

    supplier_equipment_cols = {c["name"] for c in inspector.get_columns("supplier_equipment")}
    if "equipment_model_id" not in supplier_equipment_cols:
        op.add_column(
            "supplier_equipment",
            sa.Column("equipment_model_id", sa.Integer(), nullable=True),
        )
        op.execute(
            "ALTER TABLE public.supplier_equipment ADD CONSTRAINT fk_supplier_equipment_equipment_model "
            "FOREIGN KEY (equipment_model_id) REFERENCES public.equipment_models(id)"
        )
    if "license_plate" not in supplier_equipment_cols:
        op.add_column(
            "supplier_equipment",
            sa.Column("license_plate", sa.String(length=50), nullable=True),
        )
    if "status" not in supplier_equipment_cols:
        op.add_column(
            "supplier_equipment",
            sa.Column("status", sa.String(length=20), nullable=True),
        )
        op.execute("UPDATE public.supplier_equipment SET status = 'available' WHERE status IS NULL")

    op.execute("CREATE INDEX IF NOT EXISTS ix_supplier_equipment_model_id ON public.supplier_equipment (equipment_model_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_supplier_equipment_license_plate ON public.supplier_equipment (license_plate)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_supplier_equipment_status ON public.supplier_equipment (status)")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_supplier_equipment_model_license_active "
        "ON public.supplier_equipment (supplier_id, equipment_model_id, license_plate) "
        "WHERE is_active = true AND equipment_model_id IS NOT NULL AND license_plate IS NOT NULL"
    )

    work_order_cols = {c["name"] for c in inspector.get_columns("work_orders")}
    if "requested_equipment_model_id" not in work_order_cols:
        op.add_column(
            "work_orders",
            sa.Column("requested_equipment_model_id", sa.Integer(), nullable=True),
        )
        op.execute(
            "ALTER TABLE public.work_orders ADD CONSTRAINT fk_work_orders_requested_equipment_model "
            "FOREIGN KEY (requested_equipment_model_id) REFERENCES public.equipment_models(id)"
        )

    op.execute("CREATE INDEX IF NOT EXISTS ix_work_orders_requested_equipment_model_id ON public.work_orders (requested_equipment_model_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_work_orders_requested_equipment_model_id")
    op.execute("ALTER TABLE public.work_orders DROP CONSTRAINT IF EXISTS fk_work_orders_requested_equipment_model")
    op.execute("ALTER TABLE public.work_orders DROP COLUMN IF EXISTS requested_equipment_model_id")

    op.execute("DROP INDEX IF EXISTS ux_supplier_equipment_model_license_active")
    op.execute("DROP INDEX IF EXISTS ix_supplier_equipment_status")
    op.execute("DROP INDEX IF EXISTS ix_supplier_equipment_license_plate")
    op.execute("DROP INDEX IF EXISTS ix_supplier_equipment_model_id")
    op.execute("ALTER TABLE public.supplier_equipment DROP CONSTRAINT IF EXISTS fk_supplier_equipment_equipment_model")
    op.execute("ALTER TABLE public.supplier_equipment DROP COLUMN IF EXISTS status")
    op.execute("ALTER TABLE public.supplier_equipment DROP COLUMN IF EXISTS license_plate")
    op.execute("ALTER TABLE public.supplier_equipment DROP COLUMN IF EXISTS equipment_model_id")

    op.execute("DROP TABLE IF EXISTS public.equipment_models")
