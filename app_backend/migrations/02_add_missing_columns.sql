-- ===========================================================================
-- Migration 02: Add Missing Columns Per Category
-- ===========================================================================
-- Description:
--   Add missing audit columns based on table category:
--   - CORE: deleted_at, is_active, version
--   - TRANSACTIONS: is_active, created_at, updated_at
--   - LOOKUP: (all have what they need)
--
-- Generated from: migration_decisions.json
-- Date: 2026-01-10
-- ===========================================================================

BEGIN TRANSACTION;

PRINT 'Starting Migration 02: Add Missing Columns';
PRINT '==========================================';

-- ===========================================================================
-- CORE Tables - Need deleted_at, is_active, version
-- ===========================================================================
PRINT '';
PRINT 'SECTION 1: CORE Tables - Adding missing columns...';

-- areas: missing deleted_at
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.areas') AND name = 'deleted_at')
BEGIN
    ALTER TABLE dbo.areas ADD deleted_at datetime2 NULL;
    PRINT '  ✓ areas: Added deleted_at';
END

-- budget_tx: missing is_active, updated_at, version, deleted_at
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.budget_tx') AND name = 'updated_at')
BEGIN
    ALTER TABLE dbo.budget_tx ADD updated_at datetime2 NULL DEFAULT SYSUTCDATETIME();
    PRINT '  ✓ budget_tx: Added updated_at';
END

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.budget_tx') AND name = 'is_active')
BEGIN
    ALTER TABLE dbo.budget_tx ADD is_active bit NULL DEFAULT 1;
    PRINT '  ✓ budget_tx: Added is_active';
END

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.budget_tx') AND name = 'version')
BEGIN
    ALTER TABLE dbo.budget_tx ADD version int NOT NULL DEFAULT 1;
    PRINT '  ✓ budget_tx: Added version';
END

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.budget_tx') AND name = 'deleted_at')
BEGIN
    ALTER TABLE dbo.budget_tx ADD deleted_at datetime2 NULL;
    PRINT '  ✓ budget_tx: Added deleted_at';
END

-- pricing_overrides: missing deleted_at, version
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.pricing_overrides') AND name = 'deleted_at')
BEGIN
    ALTER TABLE dbo.pricing_overrides ADD deleted_at datetime2 NULL;
    PRINT '  ✓ pricing_overrides: Added deleted_at';
END

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.pricing_overrides') AND name = 'version')
BEGIN
    ALTER TABLE dbo.pricing_overrides ADD version int NOT NULL DEFAULT 1;
    PRINT '  ✓ pricing_overrides: Added version';
END

-- projects: missing deleted_at, version
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.projects') AND name = 'deleted_at')
BEGIN
    ALTER TABLE dbo.projects ADD deleted_at datetime2 NULL;
    PRINT '  ✓ projects: Added deleted_at';
END

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.projects') AND name = 'version')
BEGIN
    ALTER TABLE dbo.projects ADD version int NOT NULL DEFAULT 1;
    PRINT '  ✓ projects: Added version';
END

-- regions: missing is_active, deleted_at
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.regions') AND name = 'is_active')
BEGIN
    ALTER TABLE dbo.regions ADD is_active bit NULL DEFAULT 1;
    PRINT '  ✓ regions: Added is_active';
END

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.regions') AND name = 'deleted_at')
BEGIN
    ALTER TABLE dbo.regions ADD deleted_at datetime2 NULL;
    PRINT '  ✓ regions: Added deleted_at';
END

-- supplier_equipment: missing deleted_at, version
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.supplier_equipment') AND name = 'deleted_at')
BEGIN
    ALTER TABLE dbo.supplier_equipment ADD deleted_at datetime2 NULL;
    PRINT '  ✓ supplier_equipment: Added deleted_at';
END

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.supplier_equipment') AND name = 'version')
BEGIN
    ALTER TABLE dbo.supplier_equipment ADD version int NOT NULL DEFAULT 1;
    PRINT '  ✓ supplier_equipment: Added version';
END

-- suppliers: missing deleted_at
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.suppliers') AND name = 'deleted_at')
BEGIN
    ALTER TABLE dbo.suppliers ADD deleted_at datetime2 NULL;
    PRINT '  ✓ suppliers: Added deleted_at';
END

-- support_ticket_comments: missing is_active, deleted_at, version
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.support_ticket_comments') AND name = 'is_active')
BEGIN
    ALTER TABLE dbo.support_ticket_comments ADD is_active bit NULL DEFAULT 1;
    PRINT '  ✓ support_ticket_comments: Added is_active';
END

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.support_ticket_comments') AND name = 'deleted_at')
BEGIN
    ALTER TABLE dbo.support_ticket_comments ADD deleted_at datetime2 NULL;
    PRINT '  ✓ support_ticket_comments: Added deleted_at';
END

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.support_ticket_comments') AND name = 'version')
BEGIN
    ALTER TABLE dbo.support_ticket_comments ADD version int NOT NULL DEFAULT 1;
    PRINT '  ✓ support_ticket_comments: Added version';
END

-- work_breaks: missing is_active, updated_at, version, deleted_at
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.work_breaks') AND name = 'updated_at')
BEGIN
    ALTER TABLE dbo.work_breaks ADD updated_at datetime2 NULL DEFAULT SYSUTCDATETIME();
    PRINT '  ✓ work_breaks: Added updated_at';
END

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.work_breaks') AND name = 'is_active')
BEGIN
    ALTER TABLE dbo.work_breaks ADD is_active bit NULL DEFAULT 1;
    PRINT '  ✓ work_breaks: Added is_active';
END

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.work_breaks') AND name = 'version')
BEGIN
    ALTER TABLE dbo.work_breaks ADD version int NOT NULL DEFAULT 1;
    PRINT '  ✓ work_breaks: Added version';
END

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.work_breaks') AND name = 'deleted_at')
BEGIN
    ALTER TABLE dbo.work_breaks ADD deleted_at datetime2 NULL;
    PRINT '  ✓ work_breaks: Added deleted_at';
END

-- work_orders: missing is_active, deleted_at
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.work_orders') AND name = 'is_active')
BEGIN
    ALTER TABLE dbo.work_orders ADD is_active bit NULL DEFAULT 1;
    PRINT '  ✓ work_orders: Added is_active';
END

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.work_orders') AND name = 'deleted_at')
BEGIN
    ALTER TABLE dbo.work_orders ADD deleted_at datetime2 NULL;
    PRINT '  ✓ work_orders: Added deleted_at';
END

PRINT '✓ CORE tables completed';

-- ===========================================================================
-- TRANSACTIONS Tables - Need is_active, created_at, updated_at
-- ===========================================================================
PRINT '';
PRINT 'SECTION 2: TRANSACTIONS Tables - Adding missing columns...';

-- budget_transfers: missing is_active, updated_at, created_at
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.budget_transfers') AND name = 'created_at')
BEGIN
    ALTER TABLE dbo.budget_transfers ADD created_at datetime2 NULL DEFAULT SYSUTCDATETIME();
    PRINT '  ✓ budget_transfers: Added created_at';
END

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.budget_transfers') AND name = 'updated_at')
BEGIN
    ALTER TABLE dbo.budget_transfers ADD updated_at datetime2 NULL DEFAULT SYSUTCDATETIME();
    PRINT '  ✓ budget_transfers: Added updated_at';
END

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.budget_transfers') AND name = 'is_active')
BEGIN
    ALTER TABLE dbo.budget_transfers ADD is_active bit NULL DEFAULT 1;
    PRINT '  ✓ budget_transfers: Added is_active';
END

-- project_assignments: missing is_active
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.project_assignments') AND name = 'is_active')
BEGIN
    ALTER TABLE dbo.project_assignments ADD is_active bit NULL DEFAULT 1;
    PRINT '  ✓ project_assignments: Added is_active';
END

-- report_runs: missing is_active
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.report_runs') AND name = 'is_active')
BEGIN
    ALTER TABLE dbo.report_runs ADD is_active bit NULL DEFAULT 1;
    PRINT '  ✓ report_runs: Added is_active';
END

-- role_assignments: missing updated_at, created_at
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.role_assignments') AND name = 'created_at')
BEGIN
    ALTER TABLE dbo.role_assignments ADD created_at datetime2 NULL DEFAULT SYSUTCDATETIME();
    PRINT '  ✓ role_assignments: Added created_at';
END

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.role_assignments') AND name = 'updated_at')
BEGIN
    ALTER TABLE dbo.role_assignments ADD updated_at datetime2 NULL DEFAULT SYSUTCDATETIME();
    PRINT '  ✓ role_assignments: Added updated_at';
END

-- worklog_segments: missing is_active
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.worklog_segments') AND name = 'is_active')
BEGIN
    ALTER TABLE dbo.worklog_segments ADD is_active bit NULL DEFAULT 1;
    PRINT '  ✓ worklog_segments: Added is_active';
END

-- worklog_standards: missing is_active
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.worklog_standards') AND name = 'is_active')
BEGIN
    ALTER TABLE dbo.worklog_standards ADD is_active bit NULL DEFAULT 1;
    PRINT '  ✓ worklog_standards: Added is_active';
END

-- worklogs: missing is_active
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.worklogs') AND name = 'is_active')
BEGIN
    ALTER TABLE dbo.worklogs ADD is_active bit NULL DEFAULT 1;
    PRINT '  ✓ worklogs: Added is_active';
END

PRINT '✓ TRANSACTIONS tables completed';

-- ===========================================================================
-- COMMIT
-- ===========================================================================
COMMIT TRANSACTION;

PRINT '';
PRINT '==========================================';
PRINT '✅ Migration 02 completed successfully!';
PRINT '==========================================';
PRINT '';
PRINT 'Summary:';
PRINT '  - CORE tables: Added deleted_at/is_active/version where missing';
PRINT '  - TRANSACTIONS tables: Added is_active/created_at/updated_at where missing';
PRINT '';
PRINT 'Next: Run 03_create_triggers.sql';
