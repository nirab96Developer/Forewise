# DB Migrations - Architecture Decisions

**Created**: 2026-01-10  
**Based on**: `migration_decisions.json`, `FINAL_DECISION_TABLE.md`

---

## Overview

These migrations implement the architecture decisions for audit columns across all 67 business tables.

### Goals

1. **Timestamps**: `created_at`/`updated_at` NOT NULL + DEFAULT SYSUTCDATETIME()
2. **Auto-update**: Triggers for `updated_at` (50 tables: CORE + TRANSACTIONS + LOOKUP)
3. **Category columns**: Add missing columns per table category
   - CORE: `deleted_at`, `is_active`, `version`
   - TRANSACTIONS: `is_active`
   - LOOKUP: `is_active`

---

## Migration Files

### 01_fix_timestamps.sql ✅

**Purpose**: Fix all timestamp columns

**Actions**:
1. Backfill NULL values with SYSUTCDATETIME()
2. Add DEFAULT constraints
3. ALTER COLUMN to NOT NULL

**Affects**: All business tables with `created_at`/`updated_at`

**Runtime**: ~30 seconds

---

### 02_add_missing_columns.sql ✅

**Purpose**: Add category-specific columns

**Actions**:
- CORE tables (30): Add `deleted_at`, `is_active`, `version` where missing
- TRANSACTIONS tables (14): Add `is_active`, `created_at`, `updated_at` where missing

**Affects**: 39 tables with missing columns

**Runtime**: ~10 seconds

---

### 03_create_triggers.sql ✅

**Purpose**: Auto-update `updated_at` on every UPDATE

**Actions**:
- Create trigger `trg_{table}_updated_at` for 50 tables
- CORE: 29 triggers
- TRANSACTIONS: 14 triggers
- LOOKUP: 6 triggers

**Why not all tables?**
- JUNCTION: `role_permissions` - simple link, no updates
- LOGS: `supplier_constraint_logs`, `work_order_coordination_logs` - append-only
- TEMPORAL: `sessions`, `otp_tokens`, etc. - no updates needed
- SYSTEM: Left as-is

**Runtime**: ~15 seconds

---

### 04_verification.sql ✅

**Purpose**: Verify all migrations succeeded

**Checks**:
1. Timestamps NOT NULL + DEFAULT
2. Category columns exist per table
3. Triggers created (should be 49-50)

**Outputs**: Detailed report with summary

**Runtime**: ~5 seconds

---

## How to Run

### Option A: Python Script (Recommended)

```bash
cd /root/kkl-forest/app_backend
python3 run_migrations.py
```

This will:
- Run all 4 migrations in order
- Show output from each
- Report overall success/failure
- Show verification results

### Option B: Manual SQL Execution

```bash
# Connect to DB
sqlcmd -S localhost -U sa -P 'YourStrong@Passw0rd' -d KKLForest

# Run each file
:r migrations/01_fix_timestamps.sql
:r migrations/02_add_missing_columns.sql
:r migrations/03_create_triggers.sql
:r migrations/04_verification.sql
```

---

## Expected Results

### After Migration 01
- All `created_at`/`updated_at` are NOT NULL
- All have DEFAULT SYSUTCDATETIME()
- ~50 tables affected

### After Migration 02
- CORE tables (30): All have `deleted_at`, `is_active`, `version`
- TRANSACTIONS (14): All have `is_active`, `created_at`, `updated_at`
- 39 tables modified

### After Migration 03
- 50 triggers created
- `updated_at` auto-updates on every UPDATE

### After Migration 04 (Verification)
```
CORE Tables Complete: 30/30
TRANSACTIONS Tables Complete: 14/14
LOOKUP Tables Complete: 6/6
Triggers Created: 50/50

✅ ALL MIGRATIONS COMPLETED SUCCESSFULLY!
```

---

## Rollback (If Needed)

⚠️ **No automated rollback provided!**

If you need to rollback:

1. **Triggers**: Easy - just DROP them
   ```sql
   DROP TRIGGER trg_{table}_updated_at;
   ```

2. **Columns**: Harder - may have data
   ```sql
   ALTER TABLE {table} DROP COLUMN deleted_at;
   ALTER TABLE {table} DROP COLUMN is_active;
   ALTER TABLE {table} DROP COLUMN version;
   ```

3. **NOT NULL**: Can revert
   ```sql
   ALTER TABLE {table} ALTER COLUMN created_at datetime2 NULL;
   ```

4. **DEFAULT**: Easy
   ```sql
   ALTER TABLE {table} DROP CONSTRAINT DF_{table}_created_at;
   ```

**Recommendation**: Take DB backup before running!

---

## Impact on Code

### Before Migration

```python
class BaseModel(Base):
    # Everything nullable
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    # Some tables missing deleted_at, is_active, version
```

### After Migration

```python
class BaseModel(Base):
    # NOT NULL with server defaults
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.sysutcdatetime()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.sysutcdatetime()
        # Trigger handles updates - no onupdate needed!
    )
    
    # Optional - not all tables have these
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=True)
    version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=1)
```

### Category-Specific Models

**CORE** (has all):
```python
class User(BaseModel):
    # Inherits: created_at, updated_at, deleted_at, is_active, version
    pass
```

**TRANSACTIONS** (no deleted_at/version):
```python
class Worklog(BaseModel):
    # Inherits: created_at, updated_at, is_active
    # Override to remove non-existent columns
    deleted_at: Mapped[None] = None  # type: ignore
    version: Mapped[None] = None  # type: ignore
```

**JUNCTION** (only created_at):
```python
class RolePermission(Base):  # Not BaseModel!
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.sysutcdatetime()
    )
```

---

## Testing

After running migrations, test:

1. **INSERT** - timestamps auto-populate
   ```sql
   INSERT INTO users (email, full_name, password_hash) VALUES (...);
   SELECT created_at, updated_at FROM users WHERE id = ...;
   -- Should be current time
   ```

2. **UPDATE** - updated_at auto-updates
   ```sql
   UPDATE users SET full_name = 'New Name' WHERE id = ...;
   SELECT updated_at FROM users WHERE id = ...;
   -- Should be > created_at
   ```

3. **Soft Delete** - works on CORE tables
   ```python
   user = db.query(User).filter_by(id=1).first()
   user.deleted_at = datetime.utcnow()
   db.commit()
   ```

4. **Optimistic Locking** - works on CORE tables
   ```python
   User.__mapper_args__ = {"version_id_col": "version"}
   # Now concurrent updates will fail with StaleDataError
   ```

---

## Files Created

```
migrations/
├── README.md                    # This file
├── 01_fix_timestamps.sql        # Timestamps NOT NULL + DEFAULT
├── 02_add_missing_columns.sql   # Category columns
├── 03_create_triggers.sql       # 50 updated_at triggers
└── 04_verification.sql          # Verification report

../
├── run_migrations.py            # Python runner script
├── migration_decisions.json     # Source of truth (input)
└── FINAL_DECISION_TABLE.md      # Human-readable decisions
```

---

## Troubleshooting

### Error: Column has NULL values
**Cause**: Migration 01 backfill didn't run or failed  
**Fix**: Manually backfill before running:
```sql
UPDATE {table} SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
```

### Error: Trigger already exists
**Cause**: Re-running migration 03  
**Fix**: Safe - we use `CREATE OR ALTER TRIGGER`

### Error: DEFAULT constraint already exists
**Cause**: Re-running migration 01  
**Fix**: Safe - we check `IF NOT EXISTS` before adding

### Verification shows incomplete
**Cause**: Migration partially failed  
**Fix**: Re-run the specific migration that failed

---

## Support

**Questions?** Check:
1. `migration_decisions.json` - What was decided
2. `FINAL_DECISION_TABLE.md` - Category rules
3. `DB_MODELS_CORRECTED_SUMMARY.md` - Full architecture doc

**Problems?** 
- Check verification output
- Review error messages in each migration
- Ensure DB connection is working

---

**Last Updated**: 2026-01-10  
**Status**: ✅ Ready to run  
**Tested**: No (needs DB execution)
