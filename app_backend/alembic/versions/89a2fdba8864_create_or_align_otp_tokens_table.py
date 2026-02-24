"""create or align otp_tokens table

Revision ID: 89a2fdba8864
Revises: 6f56f7c618bf
Create Date: 2026-02-22 18:31:46.694972

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "89a2fdba8864"
down_revision: Union[str, None] = "6f56f7c618bf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "otp_tokens" not in inspector.get_table_names():
        op.execute(
            """
            CREATE TABLE IF NOT EXISTS public.otp_tokens (
                id integer NOT NULL,
                user_id integer NOT NULL,
                token varchar(255) NULL,
                token_hash varchar(128) NULL,
                purpose varchar(100) NOT NULL,
                expires_at timestamp without time zone NOT NULL,
                used_at timestamp without time zone NULL,
                is_used boolean NOT NULL DEFAULT false,
                is_active boolean NOT NULL DEFAULT true,
                created_at timestamp without time zone NOT NULL DEFAULT now(),
                updated_at timestamp without time zone NOT NULL DEFAULT now(),
                deleted_at timestamp without time zone NULL,
                version integer NOT NULL DEFAULT 1,
                CONSTRAINT pk_otp_tokens PRIMARY KEY (id),
                CONSTRAINT fk_otp_tokens_user FOREIGN KEY (user_id) REFERENCES public.users(id)
            );
            """
        )
        op.execute("CREATE SEQUENCE IF NOT EXISTS public.otp_tokens_id_seq")
        op.execute(
            "ALTER SEQUENCE public.otp_tokens_id_seq OWNED BY public.otp_tokens.id"
        )
        op.execute(
            "ALTER TABLE public.otp_tokens ALTER COLUMN id SET DEFAULT nextval('public.otp_tokens_id_seq')"
        )
        op.execute(
            "SELECT setval('public.otp_tokens_id_seq', COALESCE((SELECT MAX(id) FROM public.otp_tokens), 0) + 1, false)"
        )
    else:
        cols = {c["name"] for c in inspector.get_columns("otp_tokens")}
        if "token_hash" not in cols:
            op.add_column(
                "otp_tokens",
                sa.Column("token_hash", sa.String(length=128), nullable=True),
            )
        if "used_at" not in cols:
            op.add_column(
                "otp_tokens", sa.Column("used_at", sa.DateTime(), nullable=True)
            )
        if "deleted_at" not in cols:
            op.add_column(
                "otp_tokens", sa.Column("deleted_at", sa.DateTime(), nullable=True)
            )
        if "version" not in cols:
            op.add_column(
                "otp_tokens",
                sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            )
            op.execute("UPDATE otp_tokens SET version = 1 WHERE version IS NULL")
            op.alter_column(
                "otp_tokens", "version", server_default=None, existing_type=sa.Integer()
            )
        if "token" in cols:
            op.alter_column(
                "otp_tokens",
                "token",
                nullable=True,
                existing_type=sa.String(length=255),
            )

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_otp_tokens_user_purpose ON public.otp_tokens (user_id, purpose)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_otp_tokens_expires_at ON public.otp_tokens (expires_at)"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_otp_tokens_token_hash ON public.otp_tokens (token_hash) WHERE token_hash IS NOT NULL"
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
                  AND c.relname = 'otp_tokens'
                  AND t.tgname = 'trg_otp_tokens_set_updated_at'
            ) THEN
                CREATE TRIGGER trg_otp_tokens_set_updated_at
                BEFORE UPDATE ON public.otp_tokens
                FOR EACH ROW
                EXECUTE FUNCTION public.set_updated_at_timestamp();
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS public.otp_tokens")
