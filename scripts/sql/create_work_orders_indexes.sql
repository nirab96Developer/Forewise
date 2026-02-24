-- =============================================================================
-- KKL Forest Management System - Work Orders Performance Optimization
-- SQL Server Index Creation & Performance Testing Script
-- =============================================================================
-- 
-- IMPORTANT: Run on production during low-traffic hours
-- Always backup before running DDL commands
--
-- Created: 2026-01-17
-- =============================================================================

-- -----------------------------------------------------------------------------
-- STEP 1: Enable Statistics for Performance Analysis
-- -----------------------------------------------------------------------------
SET STATISTICS IO ON;
SET STATISTICS TIME ON;

-- -----------------------------------------------------------------------------
-- STEP 2: Check Current Table Structure
-- -----------------------------------------------------------------------------
PRINT '=== Work Orders Table Structure ===';

SELECT 
    c.name AS column_name,
    t.name AS data_type,
    c.max_length,
    c.is_nullable,
    c.is_identity
FROM sys.columns c
JOIN sys.types t ON c.user_type_id = t.user_type_id
WHERE c.object_id = OBJECT_ID('dbo.work_orders')
ORDER BY c.column_id;

-- Check existing indexes
PRINT '';
PRINT '=== Existing Indexes on work_orders ===';

SELECT 
    i.name AS index_name,
    i.type_desc AS index_type,
    i.is_unique,
    i.is_primary_key,
    STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) AS columns
FROM sys.indexes i
JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
WHERE i.object_id = OBJECT_ID('dbo.work_orders')
GROUP BY i.name, i.type_desc, i.is_unique, i.is_primary_key
ORDER BY i.name;

-- -----------------------------------------------------------------------------
-- STEP 3: Baseline Performance Test (BEFORE indexes)
-- -----------------------------------------------------------------------------
PRINT '';
PRINT '=== BASELINE QUERY PERFORMANCE (Before Indexes) ===';
PRINT 'Running test query...';

-- Test query that mimics the API call
SELECT TOP 50 
    wo.id,
    wo.order_number,
    wo.status,
    wo.priority,
    wo.created_at,
    wo.project_id,
    p.name AS project_name,
    p.code AS project_code
FROM dbo.work_orders wo
LEFT JOIN dbo.projects p ON wo.project_id = p.id
ORDER BY wo.created_at DESC;

-- Note the IO and TIME statistics from the output

-- -----------------------------------------------------------------------------
-- STEP 4: Create Optimized Indexes
-- -----------------------------------------------------------------------------
PRINT '';
PRINT '=== CREATING INDEXES ===';

-- Index 1: Status filter (most common filter)
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.work_orders') AND name = 'IX_work_orders_status')
BEGIN
    PRINT 'Creating IX_work_orders_status...';
    CREATE NONCLUSTERED INDEX IX_work_orders_status 
    ON dbo.work_orders (status)
    INCLUDE (id, order_number, project_id, priority, created_at);
    PRINT 'IX_work_orders_status created successfully.';
END
ELSE
    PRINT 'IX_work_orders_status already exists.';

-- Index 2: Project ID (for project-specific work orders)
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.work_orders') AND name = 'IX_work_orders_project_id')
BEGIN
    PRINT 'Creating IX_work_orders_project_id...';
    CREATE NONCLUSTERED INDEX IX_work_orders_project_id 
    ON dbo.work_orders (project_id)
    INCLUDE (id, order_number, status, priority, created_at);
    PRINT 'IX_work_orders_project_id created successfully.';
END
ELSE
    PRINT 'IX_work_orders_project_id already exists.';

-- Index 3: Created_at DESC (for default ordering by newest first)
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.work_orders') AND name = 'IX_work_orders_created_at_desc')
BEGIN
    PRINT 'Creating IX_work_orders_created_at_desc...';
    CREATE NONCLUSTERED INDEX IX_work_orders_created_at_desc 
    ON dbo.work_orders (created_at DESC)
    INCLUDE (id, order_number, status, project_id, priority);
    PRINT 'IX_work_orders_created_at_desc created successfully.';
END
ELSE
    PRINT 'IX_work_orders_created_at_desc already exists.';

-- Index 4: Composite index for common filter + order pattern
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.work_orders') AND name = 'IX_work_orders_status_created')
BEGIN
    PRINT 'Creating IX_work_orders_status_created...';
    CREATE NONCLUSTERED INDEX IX_work_orders_status_created 
    ON dbo.work_orders (status, created_at DESC)
    INCLUDE (id, order_number, project_id, priority);
    PRINT 'IX_work_orders_status_created created successfully.';
END
ELSE
    PRINT 'IX_work_orders_status_created already exists.';

-- Index 5: Priority (for urgency filtering)
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.work_orders') AND name = 'IX_work_orders_priority')
BEGIN
    PRINT 'Creating IX_work_orders_priority...';
    CREATE NONCLUSTERED INDEX IX_work_orders_priority 
    ON dbo.work_orders (priority)
    INCLUDE (id, order_number, status, project_id, created_at);
    PRINT 'IX_work_orders_priority created successfully.';
END
ELSE
    PRINT 'IX_work_orders_priority already exists.';

-- Index 6: Supplier ID (for supplier-specific queries)
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.work_orders') AND name = 'IX_work_orders_supplier_id')
BEGIN
    PRINT 'Creating IX_work_orders_supplier_id...';
    CREATE NONCLUSTERED INDEX IX_work_orders_supplier_id 
    ON dbo.work_orders (supplier_id)
    INCLUDE (id, order_number, status, project_id, created_at)
    WHERE supplier_id IS NOT NULL;
    PRINT 'IX_work_orders_supplier_id created successfully.';
END
ELSE
    PRINT 'IX_work_orders_supplier_id already exists.';

-- Index 7: Order number (for direct lookups)
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.work_orders') AND name = 'IX_work_orders_order_number')
BEGIN
    PRINT 'Creating IX_work_orders_order_number...';
    CREATE NONCLUSTERED INDEX IX_work_orders_order_number 
    ON dbo.work_orders (order_number)
    INCLUDE (id, status, project_id, created_at);
    PRINT 'IX_work_orders_order_number created successfully.';
END
ELSE
    PRINT 'IX_work_orders_order_number already exists.';

-- -----------------------------------------------------------------------------
-- STEP 5: Update Statistics
-- -----------------------------------------------------------------------------
PRINT '';
PRINT '=== UPDATING STATISTICS ===';
UPDATE STATISTICS dbo.work_orders;
PRINT 'Statistics updated.';

-- -----------------------------------------------------------------------------
-- STEP 6: Post-Index Performance Test (AFTER indexes)
-- -----------------------------------------------------------------------------
PRINT '';
PRINT '=== POST-INDEX QUERY PERFORMANCE ===';
PRINT 'Running test query again...';

-- Same test query to compare
SELECT TOP 50 
    wo.id,
    wo.order_number,
    wo.status,
    wo.priority,
    wo.created_at,
    wo.project_id,
    p.name AS project_name,
    p.code AS project_code
FROM dbo.work_orders wo
LEFT JOIN dbo.projects p ON wo.project_id = p.id
ORDER BY wo.created_at DESC;

-- Compare the IO and TIME statistics with the baseline

-- -----------------------------------------------------------------------------
-- STEP 7: Verify Index Usage
-- -----------------------------------------------------------------------------
PRINT '';
PRINT '=== VERIFY INDEX CREATION ===';

SELECT 
    i.name AS index_name,
    i.type_desc AS index_type,
    i.is_unique,
    STATS_DATE(i.object_id, i.index_id) AS stats_date,
    STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) AS key_columns,
    (SELECT STRING_AGG(c2.name, ', ') 
     FROM sys.index_columns ic2 
     JOIN sys.columns c2 ON ic2.object_id = c2.object_id AND ic2.column_id = c2.column_id
     WHERE ic2.object_id = i.object_id AND ic2.index_id = i.index_id AND ic2.is_included_column = 1) AS included_columns
FROM sys.indexes i
JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id AND ic.is_included_column = 0
JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
WHERE i.object_id = OBJECT_ID('dbo.work_orders')
  AND i.name LIKE 'IX_%'
GROUP BY i.name, i.type_desc, i.is_unique, i.object_id, i.index_id
ORDER BY i.name;

-- -----------------------------------------------------------------------------
-- STEP 8: Check Index Size/Space
-- -----------------------------------------------------------------------------
PRINT '';
PRINT '=== INDEX SIZE INFORMATION ===';

SELECT 
    i.name AS index_name,
    SUM(s.used_page_count) * 8 / 1024.0 AS size_mb,
    SUM(s.row_count) AS row_count
FROM sys.dm_db_partition_stats s
JOIN sys.indexes i ON s.object_id = i.object_id AND s.index_id = i.index_id
WHERE s.object_id = OBJECT_ID('dbo.work_orders')
GROUP BY i.name
ORDER BY size_mb DESC;

-- -----------------------------------------------------------------------------
-- STEP 9: Additional Tables to Consider Indexing
-- -----------------------------------------------------------------------------
PRINT '';
PRINT '=== ADDITIONAL RECOMMENDED INDEXES ===';

-- Projects table (for JOIN performance)
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.projects') AND name = 'IX_projects_code')
BEGIN
    PRINT 'Creating IX_projects_code on projects...';
    CREATE NONCLUSTERED INDEX IX_projects_code 
    ON dbo.projects (code)
    INCLUDE (id, name, status);
    PRINT 'IX_projects_code created successfully.';
END

-- Worklogs table (common queries)
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.worklogs') AND name = 'IX_worklogs_work_order_id')
BEGIN
    PRINT 'Creating IX_worklogs_work_order_id on worklogs...';
    CREATE NONCLUSTERED INDEX IX_worklogs_work_order_id 
    ON dbo.worklogs (work_order_id)
    INCLUDE (id, user_id, status, created_at);
    PRINT 'IX_worklogs_work_order_id created successfully.';
END

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.worklogs') AND name = 'IX_worklogs_project_id')
BEGIN
    PRINT 'Creating IX_worklogs_project_id on worklogs...';
    CREATE NONCLUSTERED INDEX IX_worklogs_project_id 
    ON dbo.worklogs (project_id)
    INCLUDE (id, work_order_id, user_id, status, created_at);
    PRINT 'IX_worklogs_project_id created successfully.';
END

-- Activity logs table
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.activity_logs') AND name = 'IX_activity_logs_created_at')
BEGIN
    PRINT 'Creating IX_activity_logs_created_at on activity_logs...';
    CREATE NONCLUSTERED INDEX IX_activity_logs_created_at 
    ON dbo.activity_logs (created_at DESC)
    INCLUDE (id, user_id, action, entity_type, entity_id);
    PRINT 'IX_activity_logs_created_at created successfully.';
END

PRINT '';
PRINT '=== INDEX CREATION COMPLETE ===';
PRINT 'Please compare the BEFORE and AFTER statistics to verify improvement.';
PRINT '';
PRINT 'Expected improvement: Query time should drop from 45+ seconds to < 1 second';
PRINT '';

-- Disable statistics output
SET STATISTICS IO OFF;
SET STATISTICS TIME OFF;

-- =============================================================================
-- END OF SCRIPT
-- =============================================================================

