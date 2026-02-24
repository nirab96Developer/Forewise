-- ===========================================================================
-- Migration 01: Fix Timestamps - created_at/updated_at NOT NULL + DEFAULT
-- ===========================================================================
-- Description: 
--   1. Backfill NULL values with SYSUTCDATETIME()
--   2. Add DEFAULT SYSUTCDATETIME() constraints
--   3. ALTER COLUMN to NOT NULL
--
-- Generated from: migration_decisions.json
-- Date: 2026-01-10
-- ===========================================================================

BEGIN TRANSACTION;

PRINT 'Starting Migration 01: Fix Timestamps';
PRINT '======================================';

-- ===========================================================================
-- SECTION 1: Backfill NULL values
-- ===========================================================================
PRINT '';
PRINT 'SECTION 1: Backfilling NULL values...';

-- Users (needs NOT NULL)
UPDATE dbo.users SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
UPDATE dbo.users SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;

-- Departments
UPDATE dbo.departments SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
UPDATE dbo.departments SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;

-- Equipment
UPDATE dbo.equipment SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
UPDATE dbo.equipment SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;

-- Locations
UPDATE dbo.locations SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
UPDATE dbo.locations SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;

-- Permissions
UPDATE dbo.permissions SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
UPDATE dbo.permissions SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;

-- Pricing Overrides
UPDATE dbo.pricing_overrides SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
UPDATE dbo.pricing_overrides SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;

-- Projects (needs NOT NULL on updated_at)
UPDATE dbo.projects SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;

-- Regions
UPDATE dbo.regions SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
UPDATE dbo.regions SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;

-- Roles
UPDATE dbo.roles SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
UPDATE dbo.roles SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;

-- Suppliers
UPDATE dbo.suppliers SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
UPDATE dbo.suppliers SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;

-- Support Ticket Comments
UPDATE dbo.support_ticket_comments SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
UPDATE dbo.support_ticket_comments SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;

-- Supplier Equipment
UPDATE dbo.supplier_equipment SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
UPDATE dbo.supplier_equipment SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;

-- Work Orders
UPDATE dbo.work_orders SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
UPDATE dbo.work_orders SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;

-- Activity Types
UPDATE dbo.activity_types SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
UPDATE dbo.activity_types SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;

-- Equipment Types (needs NOT NULL on updated_at)
UPDATE dbo.equipment_types SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;

-- Supplier Rejection Reasons
UPDATE dbo.supplier_rejection_reasons SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
UPDATE dbo.supplier_rejection_reasons SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;

-- Work Order Statuses
UPDATE dbo.work_order_statuses SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
UPDATE dbo.work_order_statuses SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;

-- Worklog Statuses (needs NOT NULL on updated_at)
UPDATE dbo.worklog_statuses SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;

-- Report Runs (needs NOT NULL on updated_at)
UPDATE dbo.report_runs SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;

-- Worklog Segments
UPDATE dbo.worklog_segments SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
UPDATE dbo.worklog_segments SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;

-- Worklog Standards
UPDATE dbo.worklog_standards SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
UPDATE dbo.worklog_standards SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;

-- Worklogs
UPDATE dbo.worklogs SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
UPDATE dbo.worklogs SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;

-- Junction/Logs/Temporal tables
UPDATE dbo.role_permissions SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
UPDATE dbo.supplier_constraint_logs SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
UPDATE dbo.work_order_coordination_logs SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
UPDATE dbo.notification_types SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
UPDATE dbo.notifications SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
UPDATE dbo.supplier_rotation_queue SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;

-- System tables
UPDATE dbo.system_messages SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
UPDATE dbo.system_messages SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;
UPDATE dbo.system_notification_types SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;
UPDATE dbo.system_rates SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
UPDATE dbo.system_rates SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;
UPDATE dbo.system_settings SET created_at = SYSUTCDATETIME() WHERE created_at IS NULL;
UPDATE dbo.system_settings SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;
UPDATE dbo.system_ui_sections SET updated_at = SYSUTCDATETIME() WHERE updated_at IS NULL;

PRINT '✓ Backfill completed';

-- ===========================================================================
-- SECTION 2: Add DEFAULT constraints
-- ===========================================================================
PRINT '';
PRINT 'SECTION 2: Adding DEFAULT constraints...';

-- Helper: Add DEFAULT if not exists
DECLARE @sql NVARCHAR(MAX);
DECLARE @table_name NVARCHAR(128);
DECLARE @column_name NVARCHAR(128);

-- Tables that need created_at DEFAULT
DECLARE table_cursor CURSOR FOR
SELECT table_name FROM (VALUES
    ('users'), ('roles'), ('permissions'), ('departments'), ('equipment'),
    ('locations'), ('regions'), ('suppliers'), ('projects'), ('work_orders'),
    ('activity_types'), ('equipment_types'), ('supplier_rejection_reasons'),
    ('work_order_statuses'), ('worklog_statuses'), ('worklogs'),
    ('role_permissions'), ('supplier_constraint_logs'), ('work_order_coordination_logs'),
    ('notification_types'), ('notifications'), ('supplier_rotation_queue'),
    ('system_messages'), ('system_rates'), ('system_settings')
) AS t(table_name);

OPEN table_cursor;
FETCH NEXT FROM table_cursor INTO @table_name;

WHILE @@FETCH_STATUS = 0
BEGIN
    -- Add DEFAULT for created_at if not exists
    IF NOT EXISTS (
        SELECT 1 FROM sys.default_constraints 
        WHERE parent_object_id = OBJECT_ID('dbo.' + @table_name)
        AND COL_NAME(parent_object_id, parent_column_id) = 'created_at'
    )
    BEGIN
        SET @sql = N'ALTER TABLE dbo.' + QUOTENAME(@table_name) + 
                   N' ADD CONSTRAINT DF_' + @table_name + N'_created_at DEFAULT SYSUTCDATETIME() FOR created_at';
        EXEC sp_executesql @sql;
        PRINT '  Added DEFAULT to ' + @table_name + '.created_at';
    END

    -- Add DEFAULT for updated_at if column exists
    IF EXISTS (
        SELECT 1 FROM sys.columns
        WHERE object_id = OBJECT_ID('dbo.' + @table_name)
        AND name = 'updated_at'
    ) AND NOT EXISTS (
        SELECT 1 FROM sys.default_constraints
        WHERE parent_object_id = OBJECT_ID('dbo.' + @table_name)
        AND COL_NAME(parent_object_id, parent_column_id) = 'updated_at'
    )
    BEGIN
        SET @sql = N'ALTER TABLE dbo.' + QUOTENAME(@table_name) +
                   N' ADD CONSTRAINT DF_' + @table_name + N'_updated_at DEFAULT SYSUTCDATETIME() FOR updated_at';
        EXEC sp_executesql @sql;
        PRINT '  Added DEFAULT to ' + @table_name + '.updated_at';
    END

    FETCH NEXT FROM table_cursor INTO @table_name;
END

CLOSE table_cursor;
DEALLOCATE table_cursor;

PRINT '✓ DEFAULT constraints added';

-- ===========================================================================
-- SECTION 3: ALTER COLUMN to NOT NULL (careful - already backfilled!)
-- ===========================================================================
PRINT '';
PRINT 'SECTION 3: Altering columns to NOT NULL...';

-- Note: Only alter columns that should be NOT NULL per migration_decisions.json

-- Users
ALTER TABLE dbo.users ALTER COLUMN created_at datetime2 NOT NULL;
ALTER TABLE dbo.users ALTER COLUMN updated_at datetime2 NOT NULL;

-- Departments
ALTER TABLE dbo.departments ALTER COLUMN created_at datetime2 NOT NULL;
ALTER TABLE dbo.departments ALTER COLUMN updated_at datetime2 NOT NULL;

-- Equipment
ALTER TABLE dbo.equipment ALTER COLUMN created_at datetime2 NOT NULL;
ALTER TABLE dbo.equipment ALTER COLUMN updated_at datetime2 NOT NULL;

-- Locations
ALTER TABLE dbo.locations ALTER COLUMN created_at datetime2 NOT NULL;
ALTER TABLE dbo.locations ALTER COLUMN updated_at datetime2 NOT NULL;

-- Permissions
ALTER TABLE dbo.permissions ALTER COLUMN created_at datetime2 NOT NULL;
ALTER TABLE dbo.permissions ALTER COLUMN updated_at datetime2 NOT NULL;

-- Pricing Overrides
ALTER TABLE dbo.pricing_overrides ALTER COLUMN created_at datetime2 NOT NULL;
ALTER TABLE dbo.pricing_overrides ALTER COLUMN updated_at datetime2 NOT NULL;

-- Projects (only updated_at)
ALTER TABLE dbo.projects ALTER COLUMN updated_at datetime2 NOT NULL;

-- Regions
ALTER TABLE dbo.regions ALTER COLUMN created_at datetime2 NOT NULL;
ALTER TABLE dbo.regions ALTER COLUMN updated_at datetime2 NOT NULL;

-- Roles
ALTER TABLE dbo.roles ALTER COLUMN created_at datetime2 NOT NULL;
ALTER TABLE dbo.roles ALTER COLUMN updated_at datetime2 NOT NULL;

-- Suppliers
ALTER TABLE dbo.suppliers ALTER COLUMN created_at datetime2 NOT NULL;
ALTER TABLE dbo.suppliers ALTER COLUMN updated_at datetime2 NOT NULL;

-- Support Ticket Comments
ALTER TABLE dbo.support_ticket_comments ALTER COLUMN created_at datetime2 NOT NULL;
ALTER TABLE dbo.support_ticket_comments ALTER COLUMN updated_at datetime2 NOT NULL;

-- Supplier Equipment
ALTER TABLE dbo.supplier_equipment ALTER COLUMN created_at datetime2 NOT NULL;
ALTER TABLE dbo.supplier_equipment ALTER COLUMN updated_at datetime2 NOT NULL;

-- Work Orders
ALTER TABLE dbo.work_orders ALTER COLUMN created_at datetime2 NOT NULL;
ALTER TABLE dbo.work_orders ALTER COLUMN updated_at datetime2 NOT NULL;

-- Activity Types
ALTER TABLE dbo.activity_types ALTER COLUMN created_at datetime2 NOT NULL;
ALTER TABLE dbo.activity_types ALTER COLUMN updated_at datetime2 NOT NULL;

-- Equipment Types (only updated_at)
ALTER TABLE dbo.equipment_types ALTER COLUMN updated_at datetime2 NOT NULL;

-- Supplier Rejection Reasons
ALTER TABLE dbo.supplier_rejection_reasons ALTER COLUMN created_at datetime2 NOT NULL;
ALTER TABLE dbo.supplier_rejection_reasons ALTER COLUMN updated_at datetime2 NOT NULL;

-- Work Order Statuses
ALTER TABLE dbo.work_order_statuses ALTER COLUMN created_at datetime2 NOT NULL;
ALTER TABLE dbo.work_order_statuses ALTER COLUMN updated_at datetime2 NOT NULL;

-- Worklog Statuses (only updated_at)
ALTER TABLE dbo.worklog_statuses ALTER COLUMN updated_at datetime2 NOT NULL;

-- Report Runs (only updated_at)
ALTER TABLE dbo.report_runs ALTER COLUMN updated_at datetime2 NOT NULL;

-- Worklog Segments
ALTER TABLE dbo.worklog_segments ALTER COLUMN created_at datetime2 NOT NULL;
ALTER TABLE dbo.worklog_segments ALTER COLUMN updated_at datetime2 NOT NULL;

-- Worklog Standards
ALTER TABLE dbo.worklog_standards ALTER COLUMN created_at datetime2 NOT NULL;
ALTER TABLE dbo.worklog_standards ALTER COLUMN updated_at datetime2 NOT NULL;

-- Worklogs
ALTER TABLE dbo.worklogs ALTER COLUMN created_at datetime2 NOT NULL;
ALTER TABLE dbo.worklogs ALTER COLUMN updated_at datetime2 NOT NULL;

-- Junction/Logs tables (created_at only)
ALTER TABLE dbo.role_permissions ALTER COLUMN created_at datetime2 NOT NULL;
ALTER TABLE dbo.supplier_constraint_logs ALTER COLUMN created_at datetime2 NOT NULL;
ALTER TABLE dbo.work_order_coordination_logs ALTER COLUMN created_at datetime2 NOT NULL;

-- Temporal tables
ALTER TABLE dbo.notification_types ALTER COLUMN created_at datetime2 NOT NULL;
ALTER TABLE dbo.notifications ALTER COLUMN created_at datetime2 NOT NULL;
ALTER TABLE dbo.supplier_rotation_queue ALTER COLUMN created_at datetime2 NOT NULL;

-- System tables
ALTER TABLE dbo.system_messages ALTER COLUMN created_at datetime2 NOT NULL;
ALTER TABLE dbo.system_messages ALTER COLUMN updated_at datetime2 NOT NULL;
ALTER TABLE dbo.system_notification_types ALTER COLUMN updated_at datetime2 NOT NULL;
ALTER TABLE dbo.system_rates ALTER COLUMN created_at datetime2 NOT NULL;
ALTER TABLE dbo.system_rates ALTER COLUMN updated_at datetime2 NOT NULL;
ALTER TABLE dbo.system_settings ALTER COLUMN created_at datetime2 NOT NULL;
ALTER TABLE dbo.system_settings ALTER COLUMN updated_at datetime2 NOT NULL;
ALTER TABLE dbo.system_ui_sections ALTER COLUMN updated_at datetime2 NOT NULL;

PRINT '✓ All required columns altered to NOT NULL';

-- ===========================================================================
-- COMMIT
-- ===========================================================================
COMMIT TRANSACTION;

PRINT '';
PRINT '======================================';
PRINT '✅ Migration 01 completed successfully!';
PRINT '======================================';
PRINT '';
PRINT 'Summary:';
PRINT '  - Backfilled NULL timestamps';
PRINT '  - Added DEFAULT SYSUTCDATETIME() constraints';
PRINT '  - Altered columns to NOT NULL';
PRINT '';
PRINT 'Next: Run 02_add_missing_columns.sql';
