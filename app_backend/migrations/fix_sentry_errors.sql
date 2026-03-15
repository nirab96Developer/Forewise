-- Migration: Fix Sentry errors (March 2026)
-- Run on production DB: kkl_forest_prod

-- 1. Add deleted_at to budget_transfers (ProgrammingError fix)
ALTER TABLE budget_transfers ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;

-- 2. Add deleted_at to areas (N+1 query fix)  
ALTER TABLE areas ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;

-- 3. Add deleted_at to regions (N+1 query fix)
ALTER TABLE regions ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;

-- 4. Add deleted_at to budgets (N+1 query fix)
ALTER TABLE budgets ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;

-- 5. Add is_active to invoices if missing (N+1 query fix)
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- 6. Add is_active to equipment if missing (N+1 query fix)
ALTER TABLE equipment ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- 7. Add rotation_date to supplier_rotations if missing (TypeError fix)
ALTER TABLE supplier_rotations ADD COLUMN IF NOT EXISTS rotation_date DATE;

-- 8. Verify invoice_items.line_number allows NULL as fallback
-- (IntegrityError fix — some code paths don't set line_number)
ALTER TABLE invoice_items ALTER COLUMN line_number DROP NOT NULL;
