"""equipment hierarchy cleanup (Phase 3)

Revision ID: b9c0d1e2f3a4
Revises: a8b9c0d1e2f3
Create Date: 2026-04-22

Phase 3 of the model-restructure roadmap.

Originally planned as "merge equipment_types into equipment_categories
because they look like duplicates". A deeper audit showed the design is
actually a legitimate 3-level hierarchy:

    equipment_categories  (top-level grouping, includes sub-variants)
            ↓
    equipment_types  (mid-level type, FK → equipment_categories.category_id)
            ↓
    equipment_models  (specific model, FK → equipment_types.equipment_type_id
                       and legacy FK → equipment_categories.category_id)

The hierarchy is structurally intact (all 12 equipment_types rows have a
populated category_id). The actual problems were narrower:

1. Typo: equipment_types.id=2 "מחפרון זרוע טלסקפי" vs equipment_categories
   "מחפרון זרוע טלסקופי" (same word, missing ו). This is what made the
   Phase 1.3 name-match backfill miss 6 of 16 models.

2. equipment.category_id is sparsely populated (272 of 1026 rows). With
   the type→category link in place we can derive category_id from type_id
   for free, so dashboards can group by category without having to JOIN
   through equipment_types every time.

3. After the typo fix, re-run the Phase 1.3 name-match backfill so the
   remaining models pick up their equipment_type_id.

Idempotent — safe to re-run.
"""

from alembic import op


revision = "b9c0d1e2f3a4"
down_revision = "a8b9c0d1e2f3"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Fix the typo. (Quoted exactly so re-running is a no-op once fixed.)
    op.execute("""
        UPDATE equipment_types
        SET name = N'מחפרון זרוע טלסקופי'
        WHERE id = 2 AND name = N'מחפרון זרוע טלסקפי'
    """)

    # 2. Backfill equipment.category_id from equipment.type_id via the
    #    type→category hierarchy. Only touch rows missing a category.
    op.execute("""
        UPDATE equipment e
        SET category_id = et.category_id
        FROM equipment_types et
        WHERE et.id = e.type_id
          AND e.category_id IS NULL
          AND et.category_id IS NOT NULL
    """)

    # 3. Re-run the Phase 1.3 name-match backfill on equipment_models.
    #    Previously caught 10/16 models; with the typo fixed we expect to
    #    pick up the "מחפרון זרוע טלסקופי" variant. The 5 משאית-מים
    #    sub-variants (categories C158/159/162/163) intentionally remain
    #    NULL — they have no type counterpart and are leaf-only categories.
    op.execute("""
        UPDATE equipment_models m
        SET equipment_type_id = et.id
        FROM equipment_categories ec
        JOIN equipment_types et ON et.name = ec.name
        WHERE m.category_id = ec.id
          AND m.equipment_type_id IS NULL
    """)


def downgrade():
    # Restoring a typo and clearing inferred FKs would only confuse readers.
    pass
