"""F-1 Phase 1 — normalize permissions table to lowercase only.

Revision ID: b5c6d7e8f9a0
Revises: a3b4c5d6e7f8
Create Date: 2026-04-27

Background
----------
LIVE_VERIFICATION_REPORT.md identified F-1 (CRITICAL): the
permissions table holds 134 lowercase + 50 UPPERCASE active rows.
Roles hold uppercase grants alongside lowercase grants. Because
`user_has_permission()` does a case-insensitive match, the
uppercase rows silently grant effective access to the lowercase
codes the routers check. PERMISSIONS_MATRIX.md (lowercase) is
therefore an inaccurate map of actual production access.

This migration normalizes the table to lowercase ONLY. It
preserves effective access exactly — the case-insensitive matching
already counted uppercase as lowercase, so collapsing them to
lowercase rows is a pure data hygiene change with no policy
change.

Two cases:
1. HAS_TWIN UPPERCASE (e.g. BUDGETS.CREATE alongside
   budgets.create): pre-merge any role grants from the uppercase
   row into the lowercase row, then deactivate the uppercase row.
2. NO_TWIN UPPERCASE (e.g. WORKLOGS.APPROVE with no lowercase
   counterpart): rename the code in place to lowercase. Role
   grants stay attached.

After this migration:
- Zero active UPPERCASE permission codes.
- Zero case-insensitive duplicates.
- Per-role effective permission set is identical to before
  (verified by an embedded assertion query at the end of upgrade()).

Out of scope (Phase 2 — separate PR after manual audit):
Revoking specific perm grants per documented policy
(e.g. WORK_MANAGER should not have worklogs.approve).
That is F-2; a separate PR per F1_MIGRATION_PLAN.md.

Idempotent — running twice is a no-op (first pass cleans up,
second pass finds nothing to do).
"""
from alembic import op


revision = "b5c6d7e8f9a0"
down_revision = "a3b4c5d6e7f8"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()

    # ------------------------------------------------------------------
    # Snapshot per-role effective access BEFORE the migration. We keep
    # this as a temp table so we can compare it post-migration inside
    # the same transaction. Rollback if the comparison fails.
    # ------------------------------------------------------------------
    bind.exec_driver_sql("""
        CREATE TEMP TABLE _f1_pre_snapshot AS
        SELECT r.code AS role_code, LOWER(p.code) AS perm_code
        FROM role_permissions rp
        JOIN permissions p ON p.id = rp.permission_id AND p.is_active = true
        JOIN roles r ON r.id = rp.role_id;
    """)

    # ------------------------------------------------------------------
    # Case 1: HAS_TWIN UPPERCASE perms.
    # For each pair (upper, lower) where lower.code = LOWER(upper.code):
    #   Step 1a: copy any role grants from upper → lower (skip duplicates).
    #   Step 1b: delete the uppercase role_permissions rows.
    #   Step 1c: deactivate the uppercase permission row.
    # ------------------------------------------------------------------
    bind.exec_driver_sql("""
        WITH twins AS (
            SELECT u.id AS upper_id, l.id AS lower_id
            FROM permissions u
            JOIN permissions l
                 ON l.code = LOWER(u.code) AND l.code != u.code
            WHERE u.is_active = true
              AND u.code = UPPER(u.code)
              AND u.code != LOWER(u.code)
        )
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT DISTINCT rp.role_id, t.lower_id
        FROM role_permissions rp
        JOIN twins t ON t.upper_id = rp.permission_id
        WHERE NOT EXISTS (
            SELECT 1 FROM role_permissions rp2
            WHERE rp2.role_id = rp.role_id
              AND rp2.permission_id = t.lower_id
        );
    """)

    bind.exec_driver_sql("""
        DELETE FROM role_permissions
        WHERE permission_id IN (
            SELECT u.id FROM permissions u
            WHERE u.is_active = true
              AND u.code = UPPER(u.code)
              AND u.code != LOWER(u.code)
              AND EXISTS (
                  SELECT 1 FROM permissions l
                  WHERE l.code = LOWER(u.code) AND l.code != u.code
              )
        );
    """)

    bind.exec_driver_sql("""
        UPDATE permissions
        SET is_active = false
        WHERE is_active = true
          AND code = UPPER(code)
          AND code != LOWER(code)
          AND EXISTS (
              SELECT 1 FROM permissions l
              WHERE l.code = LOWER(permissions.code) AND l.code != permissions.code
          );
    """)

    # ------------------------------------------------------------------
    # Case 2: NO_TWIN UPPERCASE perms.
    # No lowercase counterpart — just rename the code in place. Role
    # grants stay attached because we're only updating permissions.code.
    # ------------------------------------------------------------------
    bind.exec_driver_sql("""
        UPDATE permissions
        SET code = LOWER(code)
        WHERE is_active = true
          AND code = UPPER(code)
          AND code != LOWER(code);
    """)

    # ------------------------------------------------------------------
    # Assertion: zero active UPPERCASE perms remain.
    # ------------------------------------------------------------------
    rows = bind.exec_driver_sql("""
        SELECT COUNT(*) FROM permissions
        WHERE is_active = true AND code != LOWER(code);
    """).fetchone()
    if rows[0] > 0:
        raise RuntimeError(
            f"F-1 migration failed: {rows[0]} active UPPERCASE perms remain. "
            "Migration aborted (transaction will rollback)."
        )

    # ------------------------------------------------------------------
    # Assertion: no two active perms share a LOWER(code).
    # ------------------------------------------------------------------
    rows = bind.exec_driver_sql("""
        SELECT LOWER(code), COUNT(*)
        FROM permissions WHERE is_active = true
        GROUP BY LOWER(code) HAVING COUNT(*) > 1
        LIMIT 5;
    """).fetchall()
    if rows:
        raise RuntimeError(
            f"F-1 migration failed: duplicate active perms by LOWER(code): {rows}. "
            "Aborting."
        )

    # ------------------------------------------------------------------
    # Assertion: per-role effective access is preserved.
    # Compare _f1_pre_snapshot to the equivalent post-migration view.
    # ------------------------------------------------------------------
    diff = bind.exec_driver_sql("""
        WITH post AS (
            SELECT r.code AS role_code, LOWER(p.code) AS perm_code
            FROM role_permissions rp
            JOIN permissions p ON p.id = rp.permission_id AND p.is_active = true
            JOIN roles r ON r.id = rp.role_id
        ),
        pre_distinct AS (SELECT DISTINCT role_code, perm_code FROM _f1_pre_snapshot),
        post_distinct AS (SELECT DISTINCT role_code, perm_code FROM post),
        lost AS (
            SELECT role_code, perm_code FROM pre_distinct
            EXCEPT SELECT role_code, perm_code FROM post_distinct
        ),
        gained AS (
            SELECT role_code, perm_code FROM post_distinct
            EXCEPT SELECT role_code, perm_code FROM pre_distinct
        )
        SELECT 'lost' AS kind, role_code, perm_code FROM lost
        UNION ALL
        SELECT 'gained', role_code, perm_code FROM gained
        LIMIT 20;
    """).fetchall()
    if diff:
        details = "\n  ".join(f"{r.kind}: {r.role_code} / {r.perm_code}" for r in diff)
        raise RuntimeError(
            f"F-1 migration failed: per-role effective access changed:\n  {details}\n"
            "Aborting (transaction will rollback)."
        )

    # ------------------------------------------------------------------
    # Optional: also clean up the same uppercase pattern on inactive rows
    # so a future re-activation can't reintroduce the duplicate. We just
    # delete any inactive uppercase rows that have an active lowercase
    # twin — they are pure clutter at this point.
    # ------------------------------------------------------------------
    bind.exec_driver_sql("""
        DELETE FROM permissions
        WHERE is_active = false
          AND code = UPPER(code)
          AND code != LOWER(code)
          AND EXISTS (
              SELECT 1 FROM permissions l
              WHERE l.code = LOWER(permissions.code)
                AND l.code != permissions.code
                AND l.is_active = true
          );
    """)

    # Drop the temp snapshot (it would be auto-dropped at end of session
    # anyway, but explicit is nice).
    bind.exec_driver_sql("DROP TABLE IF EXISTS _f1_pre_snapshot;")


def downgrade():
    """No automatic downgrade — this is a data cleanup. Restore from
    the pg_dump backup taken before the migration if rollback is
    needed (see backups/permissions_pre_f1_*.sql)."""
    raise RuntimeError(
        "F-1 Phase 1 has no automatic downgrade. To revert, restore "
        "from backups/permissions_pre_f1_*.sql."
    )
