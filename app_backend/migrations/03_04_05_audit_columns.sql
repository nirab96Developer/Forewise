-- ============================================================================
-- Migrations 03-05: Audit Columns (Add + Defaults + NOT NULL)
-- תאריך: 2026-01-10
-- ============================================================================
-- Combined for efficiency - runs in correct order
-- ============================================================================

USE [KKLForest];
GO

PRINT '========================================';
PRINT 'Migrations 03-05: Audit Columns';
PRINT '========================================';
PRINT '';

BEGIN TRANSACTION;

BEGIN TRY

    -- ========================================================================
    -- Migration 03: ADD COLUMN (missing columns by category)
    -- ========================================================================
    
    PRINT 'Migration 03: Adding missing columns...';
    PRINT '';
    
    -- CORE Tables - need deleted_at, is_active, version
    
    -- areas - missing deleted_at
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'areas' AND COLUMN_NAME = 'deleted_at')
    BEGIN
        ALTER TABLE dbo.areas ADD deleted_at datetime2 NULL;
        PRINT '  ✅ areas.deleted_at added';
    END
    
    -- projects - missing deleted_at, version
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'projects' AND COLUMN_NAME = 'deleted_at')
    BEGIN
        ALTER TABLE dbo.projects ADD deleted_at datetime2 NULL;
        PRINT '  ✅ projects.deleted_at added';
    END
    
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'projects' AND COLUMN_NAME = 'version')
    BEGIN
        ALTER TABLE dbo.projects ADD version int NOT NULL DEFAULT 1;
        PRINT '  ✅ projects.version added';
    END
    
    -- regions - missing is_active, deleted_at
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'regions' AND COLUMN_NAME = 'is_active')
    BEGIN
        ALTER TABLE dbo.regions ADD is_active bit NULL DEFAULT 1;
        PRINT '  ✅ regions.is_active added';
    END
    
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'regions' AND COLUMN_NAME = 'deleted_at')
    BEGIN
        ALTER TABLE dbo.regions ADD deleted_at datetime2 NULL;
        PRINT '  ✅ regions.deleted_at added';
    END
    
    -- suppliers - missing deleted_at
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'suppliers' AND COLUMN_NAME = 'deleted_at')
    BEGIN
        ALTER TABLE dbo.suppliers ADD deleted_at datetime2 NULL;
        PRINT '  ✅ suppliers.deleted_at added';
    END
    
    -- work_orders - missing is_active, deleted_at
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'work_orders' AND COLUMN_NAME = 'is_active')
    BEGIN
        ALTER TABLE dbo.work_orders ADD is_active bit NULL DEFAULT 1;
        PRINT '  ✅ work_orders.is_active added';
    END
    
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'work_orders' AND COLUMN_NAME = 'deleted_at')
    BEGIN
        ALTER TABLE dbo.work_orders ADD deleted_at datetime2 NULL;
        PRINT '  ✅ work_orders.deleted_at added';
    END
    
    -- worklogs - missing is_active
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'worklogs' AND COLUMN_NAME = 'is_active')
    BEGIN
        ALTER TABLE dbo.worklogs ADD is_active bit NULL DEFAULT 1;
        PRINT '  ✅ worklogs.is_active added';
    END
    
    -- TRANSACTIONS Tables - need is_active, created_at, updated_at
    
    -- budget_transfers - missing everything!
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'budget_transfers' AND COLUMN_NAME = 'created_at')
    BEGIN
        ALTER TABLE dbo.budget_transfers ADD created_at datetime2 NULL DEFAULT SYSUTCDATETIME();
        PRINT '  ✅ budget_transfers.created_at added';
    END
    
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'budget_transfers' AND COLUMN_NAME = 'updated_at')
    BEGIN
        ALTER TABLE dbo.budget_transfers ADD updated_at datetime2 NULL DEFAULT SYSUTCDATETIME();
        PRINT '  ✅ budget_transfers.updated_at added';
    END
    
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'budget_transfers' AND COLUMN_NAME = 'is_active')
    BEGIN
        ALTER TABLE dbo.budget_transfers ADD is_active bit NULL DEFAULT 1;
        PRINT '  ✅ budget_transfers.is_active added';
    END
    
    -- role_assignments - missing created_at, updated_at
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'role_assignments' AND COLUMN_NAME = 'created_at')
    BEGIN
        ALTER TABLE dbo.role_assignments ADD created_at datetime2 NULL DEFAULT SYSUTCDATETIME();
        PRINT '  ✅ role_assignments.created_at added';
    END
    
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'role_assignments' AND COLUMN_NAME = 'updated_at')
    BEGIN
        ALTER TABLE dbo.role_assignments ADD updated_at datetime2 NULL DEFAULT SYSUTCDATETIME();
        PRINT '  ✅ role_assignments.updated_at added';
    END
    
    -- report_runs, project_assignments, worklog_segments, worklog_standards - missing is_active
    DECLARE @tables_need_is_active TABLE (table_name NVARCHAR(128));
    INSERT INTO @tables_need_is_active VALUES 
        ('report_runs'), ('project_assignments'), ('worklog_segments'), ('worklog_standards');
    
    DECLARE @table NVARCHAR(128);
    DECLARE table_cursor CURSOR FOR SELECT table_name FROM @tables_need_is_active;
    OPEN table_cursor;
    FETCH NEXT FROM table_cursor INTO @table;
    
    WHILE @@FETCH_STATUS = 0
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = @table AND COLUMN_NAME = 'is_active')
        BEGIN
            DECLARE @sql NVARCHAR(MAX) = 'ALTER TABLE dbo.' + @table + ' ADD is_active bit NULL DEFAULT 1;';
            EXEC sp_executesql @sql;
            PRINT '  ✅ ' + @table + '.is_active added';
        END
        FETCH NEXT FROM table_cursor INTO @table;
    END
    
    CLOSE table_cursor;
    DEALLOCATE table_cursor;
    
    PRINT '';
    
    -- ========================================================================
    -- Migration 04: ADD DEFAULT Constraints
    -- ========================================================================
    
    PRINT 'Migration 04: Adding DEFAULT constraints...';
    PRINT '';
    
    -- Add defaults for created_at and updated_at on ALL business tables
    -- Only if they don't already have a default
    
    DECLARE @add_defaults TABLE (
        table_name NVARCHAR(128),
        column_name NVARCHAR(128)
    );
    
    -- Find columns without defaults
    INSERT INTO @add_defaults
    SELECT 
        c.TABLE_NAME,
        c.COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS c
    LEFT JOIN sys.default_constraints dc 
        ON dc.parent_object_id = OBJECT_ID(c.TABLE_SCHEMA + '.' + c.TABLE_NAME)
        AND dc.parent_column_id = COLUMNPROPERTY(OBJECT_ID(c.TABLE_SCHEMA + '.' + c.TABLE_NAME), c.COLUMN_NAME, 'ColumnId')
    WHERE c.TABLE_SCHEMA = 'dbo'
    AND c.COLUMN_NAME IN ('created_at', 'updated_at')
    AND dc.object_id IS NULL
    AND c.TABLE_NAME NOT IN ('alembic_version');  -- Exclude system tables
    
    DECLARE @df_table NVARCHAR(128), @df_column NVARCHAR(128), @df_sql NVARCHAR(MAX);
    DECLARE default_cursor CURSOR FOR SELECT table_name, column_name FROM @add_defaults;
    OPEN default_cursor;
    FETCH NEXT FROM default_cursor INTO @df_table, @df_column;
    
    WHILE @@FETCH_STATUS = 0
    BEGIN
        SET @df_sql = 'ALTER TABLE dbo.' + @df_table + 
                     ' ADD CONSTRAINT DF_' + @df_table + '_' + @df_column + 
                     ' DEFAULT SYSUTCDATETIME() FOR ' + @df_column + ';';
        
        BEGIN TRY
            EXEC sp_executesql @df_sql;
            PRINT '  ✅ DF_' + @df_table + '_' + @df_column;
        END TRY
        BEGIN CATCH
            PRINT '  ⚠️  DF_' + @df_table + '_' + @df_column + ' - ' + ERROR_MESSAGE();
        END CATCH
        
        FETCH NEXT FROM default_cursor INTO @df_table, @df_column;
    END
    
    CLOSE default_cursor;
    DEALLOCATE default_cursor;
    
    PRINT '';
    
    -- ========================================================================
    -- Migration 05: ALTER COLUMN to NOT NULL
    -- ========================================================================
    
    PRINT 'Migration 05: Altering created_at/updated_at to NOT NULL...';
    PRINT '';
    
    -- Get all tables with created_at or updated_at that are still nullable
    DECLARE @alter_tables TABLE (
        table_name NVARCHAR(128),
        column_name NVARCHAR(128)
    );
    
    INSERT INTO @alter_tables
    SELECT TABLE_NAME, COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'dbo'
    AND COLUMN_NAME IN ('created_at', 'updated_at')
    AND IS_NULLABLE = 'YES'
    AND TABLE_NAME NOT IN ('alembic_version', 'system_settings', 'system_messages', 
                           'system_schedules', 'system_notification_types', 'system_rates',
                           'system_schedule_runs', 'system_ui_sections');  -- Skip SYSTEM tables
    
    DECLARE @alt_table NVARCHAR(128), @alt_column NVARCHAR(128), @alt_sql NVARCHAR(MAX);
    DECLARE alter_cursor CURSOR FOR SELECT table_name, column_name FROM @alter_tables;
    OPEN alter_cursor;
    FETCH NEXT FROM alter_cursor INTO @alt_table, @alt_column;
    
    WHILE @@FETCH_STATUS = 0
    BEGIN
        -- Verify no NULLs exist
        DECLARE @null_count INT;
        SET @alt_sql = 'SELECT @count = COUNT(*) FROM dbo.' + @alt_table + ' WHERE ' + @alt_column + ' IS NULL';
        EXEC sp_executesql @alt_sql, N'@count INT OUTPUT', @null_count OUTPUT;
        
        IF @null_count > 0
        BEGIN
            PRINT '  ⚠️  ' + @alt_table + '.' + @alt_column + ' still has ' + CAST(@null_count AS NVARCHAR(10)) + ' NULLs - skipping';
        END
        ELSE
        BEGIN
            SET @alt_sql = 'ALTER TABLE dbo.' + @alt_table + ' ALTER COLUMN ' + @alt_column + ' datetime2 NOT NULL;';
            
            BEGIN TRY
                EXEC sp_executesql @alt_sql;
                PRINT '  ✅ ' + @alt_table + '.' + @alt_column + ' → NOT NULL';
            END TRY
            BEGIN CATCH
                PRINT '  ❌ ' + @alt_table + '.' + @alt_column + ' - ' + ERROR_MESSAGE();
            END CATCH
        END
        
        FETCH NEXT FROM alter_cursor INTO @alt_table, @alt_column;
    END
    
    CLOSE alter_cursor;
    DEALLOCATE alter_cursor;
    
    COMMIT TRANSACTION;
    
    PRINT '';
    PRINT '✅ Migrations 03-05 completed successfully!';
    PRINT '';

END TRY
BEGIN CATCH
    ROLLBACK TRANSACTION;
    
    PRINT '';
    PRINT '❌ Migrations 03-05 failed!';
    PRINT 'Error: ' + ERROR_MESSAGE();
    PRINT '';
    
    THROW;
END CATCH

GO

