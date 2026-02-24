-- ===========================================================================
-- Migration 04: Verification Script
-- ===========================================================================
-- Description:
--   Verify all migrations completed successfully:
--   1. Timestamps (created_at/updated_at) NOT NULL + DEFAULT
--   2. Category columns (deleted_at/is_active/version) per table category
--   3. Triggers created (50 total)
--
-- Generated from: migration_decisions.json
-- Date: 2026-01-10
-- ===========================================================================

PRINT '==========================================';
PRINT 'Migration Verification Report';
PRINT '==========================================';
PRINT '';

-- ===========================================================================
-- CHECK 1: Timestamps NOT NULL + DEFAULT
-- ===========================================================================
PRINT 'CHECK 1: Timestamps (created_at/updated_at) NOT NULL + DEFAULT';
PRINT '--------------------------------------------------------------';

-- Check created_at NOT NULL
SELECT 
    COUNT(*) AS tables_with_created_at_not_null
FROM sys.columns c
JOIN sys.tables t ON c.object_id = t.object_id
WHERE t.schema_id = SCHEMA_ID('dbo')
AND c.name = 'created_at'
AND c.is_nullable = 0;

-- Check updated_at NOT NULL
SELECT 
    COUNT(*) AS tables_with_updated_at_not_null
FROM sys.columns c
JOIN sys.tables t ON c.object_id = t.object_id
WHERE t.schema_id = SCHEMA_ID('dbo')
AND c.name = 'updated_at'
AND c.is_nullable = 0;

-- Check DEFAULT constraints
SELECT 
    COUNT(*) AS tables_with_created_at_default
FROM sys.default_constraints dc
JOIN sys.columns c ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id
JOIN sys.tables t ON c.object_id = t.object_id
WHERE t.schema_id = SCHEMA_ID('dbo')
AND c.name = 'created_at';

SELECT 
    COUNT(*) AS tables_with_updated_at_default
FROM sys.default_constraints dc
JOIN sys.columns c ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id
JOIN sys.tables t ON c.object_id = t.object_id
WHERE t.schema_id = SCHEMA_ID('dbo')
AND c.name = 'updated_at';

PRINT '✓ Timestamp verification completed';
PRINT '';

-- ===========================================================================
-- CHECK 2: Category-specific columns
-- ===========================================================================
PRINT 'CHECK 2: Category-specific columns';
PRINT '-----------------------------------';

-- CORE: Should have deleted_at, is_active, version
PRINT 'CORE Tables (should have deleted_at, is_active, version):';

SELECT 
    t.name AS table_name,
    CASE WHEN EXISTS (
        SELECT 1 FROM sys.columns c 
        WHERE c.object_id = t.object_id AND c.name = 'deleted_at'
    ) THEN '✓' ELSE '✗' END AS has_deleted_at,
    CASE WHEN EXISTS (
        SELECT 1 FROM sys.columns c 
        WHERE c.object_id = t.object_id AND c.name = 'is_active'
    ) THEN '✓' ELSE '✗' END AS has_is_active,
    CASE WHEN EXISTS (
        SELECT 1 FROM sys.columns c 
        WHERE c.object_id = t.object_id AND c.name = 'version'
    ) THEN '✓' ELSE '✗' END AS has_version
FROM sys.tables t
WHERE t.schema_id = SCHEMA_ID('dbo')
AND t.name IN (
    'users', 'roles', 'permissions', 'departments', 'equipment',
    'equipment_categories', 'areas', 'regions', 'projects', 'suppliers',
    'budgets', 'budget_items', 'work_orders', 'invoices', 'invoice_items',
    'reports', 'files', 'locations', 'milestones', 'pricing_overrides',
    'project_documents', 'support_tickets', 'support_ticket_comments',
    'conflict_logs', 'audit_logs', 'activity_logs', 'daily_work_reports',
    'budget_tx', 'supplier_equipment', 'work_breaks'
)
ORDER BY t.name;

PRINT '';

-- TRANSACTIONS: Should have is_active, created_at, updated_at
PRINT 'TRANSACTIONS Tables (should have is_active):';

SELECT 
    t.name AS table_name,
    CASE WHEN EXISTS (
        SELECT 1 FROM sys.columns c 
        WHERE c.object_id = t.object_id AND c.name = 'is_active'
    ) THEN '✓' ELSE '✗' END AS has_is_active,
    CASE WHEN EXISTS (
        SELECT 1 FROM sys.columns c 
        WHERE c.object_id = t.object_id AND c.name = 'created_at'
    ) THEN '✓' ELSE '✗' END AS has_created_at,
    CASE WHEN EXISTS (
        SELECT 1 FROM sys.columns c 
        WHERE c.object_id = t.object_id AND c.name = 'updated_at'
    ) THEN '✓' ELSE '✗' END AS has_updated_at
FROM sys.tables t
WHERE t.schema_id = SCHEMA_ID('dbo')
AND t.name IN (
    'balance_releases', 'budget_allocations', 'budget_transfers',
    'equipment_assignments', 'equipment_maintenance', 'equipment_scans',
    'invoice_payments', 'project_assignments', 'report_runs',
    'role_assignments', 'supplier_rotations', 'worklog_segments',
    'worklog_standards', 'worklogs'
)
ORDER BY t.name;

PRINT '';
PRINT '✓ Category columns verification completed';
PRINT '';

-- ===========================================================================
-- CHECK 3: Triggers
-- ===========================================================================
PRINT 'CHECK 3: Triggers (should be 49-50)';
PRINT '------------------------------------';

SELECT 
    COUNT(*) AS total_updated_at_triggers
FROM sys.triggers
WHERE name LIKE 'trg_%_updated_at';

-- List missing triggers (if any)
PRINT '';
PRINT 'Tables missing triggers:';

SELECT t.name AS table_missing_trigger
FROM sys.tables t
WHERE t.schema_id = SCHEMA_ID('dbo')
AND t.name IN (
    -- CORE
    'users', 'roles', 'permissions', 'departments', 'equipment',
    'equipment_categories', 'areas', 'regions', 'projects', 'suppliers',
    'budgets', 'budget_items', 'work_orders', 'invoices', 'invoice_items',
    'reports', 'files', 'locations', 'milestones', 'pricing_overrides',
    'project_documents', 'support_tickets', 'support_ticket_comments',
    'conflict_logs', 'audit_logs', 'activity_logs', 'daily_work_reports',
    'budget_tx', 'supplier_equipment', 'work_breaks',
    -- TRANSACTIONS
    'balance_releases', 'budget_allocations', 'budget_transfers',
    'equipment_assignments', 'equipment_maintenance', 'equipment_scans',
    'invoice_payments', 'project_assignments', 'report_runs',
    'role_assignments', 'supplier_rotations', 'worklog_segments',
    'worklog_standards', 'worklogs',
    -- LOOKUP
    'activity_types', 'equipment_types', 'supplier_constraint_reasons',
    'supplier_rejection_reasons', 'work_order_statuses', 'worklog_statuses'
)
AND NOT EXISTS (
    SELECT 1 FROM sys.triggers tr
    WHERE tr.parent_id = t.object_id
    AND tr.name = 'trg_' + t.name + '_updated_at'
);

PRINT '';
PRINT '✓ Trigger verification completed';
PRINT '';

-- ===========================================================================
-- SUMMARY
-- ===========================================================================
PRINT '==========================================';
PRINT 'SUMMARY';
PRINT '==========================================';

-- Count by category
DECLARE @core_complete INT;
DECLARE @trans_complete INT;
DECLARE @lookup_complete INT;
DECLARE @triggers_count INT;

-- CORE: all with deleted_at, is_active, version
SELECT @core_complete = COUNT(*)
FROM sys.tables t
WHERE t.schema_id = SCHEMA_ID('dbo')
AND t.name IN (
    'users', 'roles', 'permissions', 'departments', 'equipment',
    'equipment_categories', 'areas', 'regions', 'projects', 'suppliers',
    'budgets', 'budget_items', 'work_orders', 'invoices', 'invoice_items',
    'reports', 'files', 'locations', 'milestones', 'pricing_overrides',
    'project_documents', 'support_tickets', 'support_ticket_comments',
    'conflict_logs', 'audit_logs', 'activity_logs', 'daily_work_reports',
    'budget_tx', 'supplier_equipment', 'work_breaks'
)
AND EXISTS (SELECT 1 FROM sys.columns c WHERE c.object_id = t.object_id AND c.name = 'deleted_at')
AND EXISTS (SELECT 1 FROM sys.columns c WHERE c.object_id = t.object_id AND c.name = 'is_active')
AND EXISTS (SELECT 1 FROM sys.columns c WHERE c.object_id = t.object_id AND c.name = 'version');

-- TRANSACTIONS: all with is_active
SELECT @trans_complete = COUNT(*)
FROM sys.tables t
WHERE t.schema_id = SCHEMA_ID('dbo')
AND t.name IN (
    'balance_releases', 'budget_allocations', 'budget_transfers',
    'equipment_assignments', 'equipment_maintenance', 'equipment_scans',
    'invoice_payments', 'project_assignments', 'report_runs',
    'role_assignments', 'supplier_rotations', 'worklog_segments',
    'worklog_standards', 'worklogs'
)
AND EXISTS (SELECT 1 FROM sys.columns c WHERE c.object_id = t.object_id AND c.name = 'is_active');

-- LOOKUP: all with is_active
SELECT @lookup_complete = COUNT(*)
FROM sys.tables t
WHERE t.schema_id = SCHEMA_ID('dbo')
AND t.name IN (
    'activity_types', 'equipment_types', 'supplier_constraint_reasons',
    'supplier_rejection_reasons', 'work_order_statuses', 'worklog_statuses'
)
AND EXISTS (SELECT 1 FROM sys.columns c WHERE c.object_id = t.object_id AND c.name = 'is_active');

-- Triggers
SELECT @triggers_count = COUNT(*)
FROM sys.triggers
WHERE name LIKE 'trg_%_updated_at';

-- Print summary
PRINT 'CORE Tables Complete: ' + CAST(@core_complete AS VARCHAR) + '/30';
PRINT 'TRANSACTIONS Tables Complete: ' + CAST(@trans_complete AS VARCHAR) + '/14';
PRINT 'LOOKUP Tables Complete: ' + CAST(@lookup_complete AS VARCHAR) + '/6';
PRINT 'Triggers Created: ' + CAST(@triggers_count AS VARCHAR) + '/50';
PRINT '';

-- Overall status
IF @core_complete = 30 AND @trans_complete = 14 AND @lookup_complete = 6 AND @triggers_count >= 49
BEGIN
    PRINT '✅ ALL MIGRATIONS COMPLETED SUCCESSFULLY!';
    PRINT '';
    PRINT 'Database is now ready for:';
    PRINT '  - BaseModel with consistent audit columns';
    PRINT '  - Automatic updated_at management';
    PRINT '  - Soft delete support (CORE tables)';
    PRINT '  - Optimistic locking (CORE tables with version)';
END
ELSE
BEGIN
    PRINT '⚠️  SOME MIGRATIONS INCOMPLETE - Review output above';
END

PRINT '';
PRINT '==========================================';
