/* ============================================================
   create_work_orders_indexes_optimized.sql
   
   תפור לפי ה-SQLAlchemy Query האמיתי של work_order_service.py
   
   בעיות שזוהו:
   1. deleted_at לא מאונדקס (כל query מסנן IS NULL)
   2. created_at לא מאונדקס (ORDER BY הדיפולטי)
   3. אין Covering Indexes (כל שורה = Key Lookup יקר)
   
   פתרון: אינדקסים מורכבים עם INCLUDE לביטול Lookups
   ============================================================ */

SET NOCOUNT ON;

PRINT '================================================================';
PRINT '   WORK ORDERS OPTIMIZED INDEX CREATION';
PRINT '   Run Time: ' + CONVERT(VARCHAR, GETDATE(), 120);
PRINT '================================================================';
PRINT '';

-- STEP 1: Check current state
PRINT '=== BEFORE: Current indexes on work_orders ===';
SELECT 
    i.name AS index_name,
    i.type_desc,
    (SELECT STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal)
     FROM sys.index_columns ic 
     JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
     WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id AND ic.is_included_column = 0
    ) AS key_columns,
    (SELECT STRING_AGG(c.name, ', ')
     FROM sys.index_columns ic 
     JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
     WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id AND ic.is_included_column = 1
    ) AS included_columns
FROM sys.indexes i
WHERE i.object_id = OBJECT_ID('dbo.work_orders')
ORDER BY i.type_desc, i.name;

PRINT '';
PRINT '=== Creating optimized indexes... ===';
PRINT '';

BEGIN TRY
    BEGIN TRAN;

    -- =====================================================================
    -- INDEX 1: DEFAULT LIST QUERY (הכי חשוב!)
    -- Pattern: WHERE deleted_at IS NULL ORDER BY created_at DESC
    -- COVERING: Returns all columns needed for list without Key Lookup
    -- =====================================================================
    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_work_orders_list_default' AND object_id = OBJECT_ID('dbo.work_orders'))
    BEGIN
        PRINT 'Creating IX_work_orders_list_default (deleted_at, created_at DESC)...';
        CREATE NONCLUSTERED INDEX IX_work_orders_list_default
        ON dbo.work_orders (deleted_at, created_at DESC)
        INCLUDE (
            id, order_number, title, status, priority, 
            project_id, supplier_id, equipment_id, location_id,
            work_start_date, work_end_date, is_active
        );
        PRINT '  ✓ Created IX_work_orders_list_default';
    END
    ELSE
        PRINT '  - IX_work_orders_list_default already exists';

    -- =====================================================================
    -- INDEX 2: FILTER BY STATUS (very common)
    -- Pattern: WHERE deleted_at IS NULL AND status = 'X' ORDER BY created_at DESC
    -- =====================================================================
    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_work_orders_status_list' AND object_id = OBJECT_ID('dbo.work_orders'))
    BEGIN
        PRINT 'Creating IX_work_orders_status_list (status, deleted_at, created_at)...';
        CREATE NONCLUSTERED INDEX IX_work_orders_status_list
        ON dbo.work_orders (status, deleted_at, created_at DESC)
        INCLUDE (
            id, order_number, title, priority, 
            project_id, supplier_id, is_active
        );
        PRINT '  ✓ Created IX_work_orders_status_list';
    END
    ELSE
        PRINT '  - IX_work_orders_status_list already exists';

    -- =====================================================================
    -- INDEX 3: FILTER BY PROJECT (project page)
    -- Pattern: WHERE project_id = X AND deleted_at IS NULL ORDER BY created_at DESC
    -- =====================================================================
    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_work_orders_project_list' AND object_id = OBJECT_ID('dbo.work_orders'))
    BEGIN
        PRINT 'Creating IX_work_orders_project_list (project_id, deleted_at, created_at)...';
        CREATE NONCLUSTERED INDEX IX_work_orders_project_list
        ON dbo.work_orders (project_id, deleted_at, created_at DESC)
        INCLUDE (
            id, order_number, title, status, priority, 
            supplier_id, is_active, work_start_date
        );
        PRINT '  ✓ Created IX_work_orders_project_list';
    END
    ELSE
        PRINT '  - IX_work_orders_project_list already exists';

    -- =====================================================================
    -- INDEX 4: FILTER BY SUPPLIER (supplier queries)
    -- Pattern: WHERE supplier_id = X AND deleted_at IS NULL
    -- =====================================================================
    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_work_orders_supplier_list' AND object_id = OBJECT_ID('dbo.work_orders'))
    BEGIN
        PRINT 'Creating IX_work_orders_supplier_list (supplier_id, deleted_at, created_at)...';
        CREATE NONCLUSTERED INDEX IX_work_orders_supplier_list
        ON dbo.work_orders (supplier_id, deleted_at, created_at DESC)
        INCLUDE (
            id, order_number, title, status, priority, project_id
        )
        WHERE supplier_id IS NOT NULL;
        PRINT '  ✓ Created IX_work_orders_supplier_list';
    END
    ELSE
        PRINT '  - IX_work_orders_supplier_list already exists';

    -- =====================================================================
    -- INDEX 5: COUNT QUERY OPTIMIZATION
    -- The service runs a separate COUNT(*) query - make it fast
    -- =====================================================================
    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_work_orders_count' AND object_id = OBJECT_ID('dbo.work_orders'))
    BEGIN
        PRINT 'Creating IX_work_orders_count (deleted_at, status, project_id)...';
        CREATE NONCLUSTERED INDEX IX_work_orders_count
        ON dbo.work_orders (deleted_at, status, project_id)
        INCLUDE (id);
        PRINT '  ✓ Created IX_work_orders_count';
    END
    ELSE
        PRINT '  - IX_work_orders_count already exists';

    -- =====================================================================
    -- INDEX 6: PRIORITY FILTERING
    -- Pattern: WHERE priority = 'URGENT' AND deleted_at IS NULL
    -- =====================================================================
    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_work_orders_priority_list' AND object_id = OBJECT_ID('dbo.work_orders'))
    BEGIN
        PRINT 'Creating IX_work_orders_priority_list (priority, deleted_at, created_at)...';
        CREATE NONCLUSTERED INDEX IX_work_orders_priority_list
        ON dbo.work_orders (priority, deleted_at, created_at DESC)
        INCLUDE (
            id, order_number, title, status, project_id
        );
        PRINT '  ✓ Created IX_work_orders_priority_list';
    END
    ELSE
        PRINT '  - IX_work_orders_priority_list already exists';

    -- =====================================================================
    -- INDEX 7: DATE RANGE FILTERING
    -- Pattern: WHERE work_start_date BETWEEN X AND Y
    -- =====================================================================
    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_work_orders_date_range' AND object_id = OBJECT_ID('dbo.work_orders'))
    BEGIN
        PRINT 'Creating IX_work_orders_date_range (work_start_date, deleted_at)...';
        CREATE NONCLUSTERED INDEX IX_work_orders_date_range
        ON dbo.work_orders (work_start_date, deleted_at)
        INCLUDE (
            id, order_number, status, project_id, priority
        );
        PRINT '  ✓ Created IX_work_orders_date_range';
    END
    ELSE
        PRINT '  - IX_work_orders_date_range already exists';

    -- =====================================================================
    -- INDEX 8: PORTAL TOKEN LOOKUP (already has UNIQUE, but ensure covering)
    -- Pattern: WHERE portal_token = 'X'
    -- =====================================================================
    -- Note: portal_token already has a unique index, skip if exists

    -- =====================================================================
    -- UPDATE STATISTICS
    -- =====================================================================
    PRINT '';
    PRINT '=== Updating statistics... ===';
    UPDATE STATISTICS dbo.work_orders WITH FULLSCAN;
    PRINT '  ✓ Statistics updated';

    COMMIT TRAN;

    PRINT '';
    PRINT '=== AFTER: New indexes on work_orders ===';
    SELECT 
        i.name AS index_name,
        i.type_desc,
        (SELECT STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal)
         FROM sys.index_columns ic 
         JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
         WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id AND ic.is_included_column = 0
        ) AS key_columns
    FROM sys.indexes i
    WHERE i.object_id = OBJECT_ID('dbo.work_orders')
      AND i.name LIKE 'IX_%'
    ORDER BY i.name;

END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRAN;
    DECLARE @msg NVARCHAR(4000) = ERROR_MESSAGE();
    DECLARE @line INT = ERROR_LINE();
    RAISERROR('Index creation failed at line %d: %s', 16, 1, @line, @msg);
END CATCH;

-- =====================================================================
-- PERFORMANCE TEST QUERY (copy and run with SET STATISTICS IO/TIME ON)
-- =====================================================================
PRINT '';
PRINT '=== TEST: Run this with STATISTICS to compare before/after ===';
PRINT '';
PRINT 'SET STATISTICS IO ON;';
PRINT 'SET STATISTICS TIME ON;';
PRINT '';
PRINT 'SELECT TOP 50';
PRINT '    wo.id, wo.order_number, wo.title, wo.status, wo.priority,';
PRINT '    wo.created_at, wo.project_id, wo.supplier_id';
PRINT 'FROM dbo.work_orders wo';
PRINT 'WHERE wo.deleted_at IS NULL';
PRINT 'ORDER BY wo.created_at DESC;';
PRINT '';
PRINT '-- Expected: < 1 second, < 1000 logical reads';
PRINT '';

PRINT '================================================================';
PRINT '   INDEX CREATION COMPLETE';
PRINT '================================================================';

