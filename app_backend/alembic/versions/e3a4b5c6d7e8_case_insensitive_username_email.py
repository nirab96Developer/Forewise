"""case-insensitive username + email + unique indexes

Revision ID: e3a4b5c6d7e8
Revises: d2f3e4a5b6c7
Create Date: 2026-04-18

Login (password) endpoints now compare username/email case-insensitively (so
``nira``, ``NIRA`` and ``Nira`` resolve to the same user). Two database-level
changes are required to keep this safe:

1. **Backfill** — collapse all existing usernames/emails to lowercase. If a
   collision shows up (e.g. both ``Nira`` and ``nira``), we keep the row with
   the smaller id and append ``__dup<id>`` to the duplicate(s) so the unique
   constraint can be applied. This lets the migration succeed; you should then
   reach out to the duplicate owners and delete/merge the conflicting rows
   manually (we can't do that automatically — passwords differ).
2. **Unique indexes** on ``lower(username)`` and ``lower(email)`` so the
   database itself prevents future case-only duplicates.

Idempotent — safe to re-run.
"""

from alembic import op
import sqlalchemy as sa


revision = "e3a4b5c6d7e8"
down_revision = "d2f3e4a5b6c7"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name  # postgresql / mssql / sqlite ...

    # ── Step 1: backfill duplicates that would block the unique index ──
    # For each lowercase value with >1 row, keep MIN(id) untouched and rename
    # the rest to "<original>__dup<id>" so they become unique without losing
    # the row.
    for col in ("username", "email"):
        op.execute(sa.text(f"""
            UPDATE users
               SET {col} = {col} || '__dup' || CAST(id AS VARCHAR)
             WHERE id IN (
                 SELECT u.id
                 FROM users u
                 JOIN (
                     SELECT LOWER({col}) AS lc, MIN(id) AS keep_id
                     FROM users
                     WHERE {col} IS NOT NULL AND {col} <> ''
                     GROUP BY LOWER({col})
                     HAVING COUNT(*) > 1
                 ) d ON LOWER(u.{col}) = d.lc
                 WHERE u.id <> d.keep_id
             )
        """))

    # ── Step 2: lowercase every value that's left ──
    op.execute("UPDATE users SET email    = LOWER(email)    WHERE email    IS NOT NULL")
    op.execute("UPDATE users SET username = LOWER(username) WHERE username IS NOT NULL")

    # ── Step 3: functional unique indexes ──
    if dialect == "postgresql":
        op.execute("DROP INDEX IF EXISTS ux_users_lower_email")
        op.execute("DROP INDEX IF EXISTS ux_users_lower_username")
        op.execute("CREATE UNIQUE INDEX ux_users_lower_email    ON users (LOWER(email))    WHERE email    IS NOT NULL")
        op.execute("CREATE UNIQUE INDEX ux_users_lower_username ON users (LOWER(username)) WHERE username IS NOT NULL")
    elif dialect == "mssql":
        # SQL Server: filtered unique index using a computed column expression.
        # Functional indexes need a persisted computed column; create one if missing.
        op.execute("""
            IF NOT EXISTS (
                SELECT 1 FROM sys.computed_columns
                WHERE object_id = OBJECT_ID('users') AND name = 'email_lower'
            )
            BEGIN
                ALTER TABLE users ADD email_lower    AS LOWER(email)    PERSISTED;
                ALTER TABLE users ADD username_lower AS LOWER(username) PERSISTED;
            END
        """)
        op.execute("""
            IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'ux_users_lower_email')
                CREATE UNIQUE INDEX ux_users_lower_email    ON users (email_lower)    WHERE email_lower    IS NOT NULL;
        """)
        op.execute("""
            IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'ux_users_lower_username')
                CREATE UNIQUE INDEX ux_users_lower_username ON users (username_lower) WHERE username_lower IS NOT NULL;
        """)
    else:
        # Generic fallback (sqlite tests etc.) — non-functional but enforces uniqueness on the lowercase values we just stored.
        op.create_index("ux_users_lower_email",    "users", ["email"],    unique=True)
        op.create_index("ux_users_lower_username", "users", ["username"], unique=True)


def downgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.execute("DROP INDEX IF EXISTS ux_users_lower_email")
        op.execute("DROP INDEX IF EXISTS ux_users_lower_username")
    elif dialect == "mssql":
        op.execute("IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'ux_users_lower_email') DROP INDEX ux_users_lower_email ON users;")
        op.execute("IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'ux_users_lower_username') DROP INDEX ux_users_lower_username ON users;")
    else:
        op.drop_index("ux_users_lower_email",    table_name="users")
        op.drop_index("ux_users_lower_username", table_name="users")
