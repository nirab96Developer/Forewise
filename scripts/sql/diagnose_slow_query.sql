-- =============================================================================
-- KKL Forest Management System - Slow Query Diagnostics
-- Run this BEFORE creating indexes to understand the problem
-- =============================================================================

SET NOCOUNT ON;

PRINT '================================================================';
PRINT '   WORK ORDERS PERFORMANCE DIAGNOSTICS';
PRINT '   Run Time: ' + CONVERT(VARCHAR, GETDATE(), 120);
PRINT '================================================================';
PRINT '';

-- -----------------------------------------------------------------------------
-- 1. TABLE SIZES
-- -----------------------------------------------------------------------------
PRINT '=== 1. TABLE ROW COUNTS ===';

SELECT 'work_orders' AS table_name, COUNT(*) AS row_count FROM dbo.work_orders
UNION ALL
SELECT 'projects', COUNT(*) FROM dbo.projects
UNION ALL
SELECT 'worklogs', COUNT(*) FROM dbo.worklogs
UNION ALL
SELECT 'users', COUNT(*) FROM dbo.users
UNION ALL
SELECT 'suppliers', COUNT(*) FROM dbo.suppliers
ORDER BY row_count DESC;

PRINT '';

-- -----------------------------------------------------------------------------
-- 2. MISSING INDEX SUGGESTIONS (SQL Server built-in)
-- -----------------------------------------------------------------------------
PRINT '=== 2. MISSING INDEX SUGGESTIONS FROM SQL SERVER ===';

SELECT TOP 10
    OBJECT_NAME(mid.object_id) AS table_name,
    migs.avg_user_impact AS avg_improvement_pct,
    migs.user_seeks + migs.user_scans AS total_requests,
    mid.equality_columns,
    mid.inequality_columns,
    mid.included_columns
FROM sys.dm_db_missing_index_group_stats migs
JOIN sys.dm_db_missing_index_groups mig ON migs.group_handle = mig.index_group_handle
JOIN sys.dm_db_missing_index_details mid ON mig.index_handle = mid.index_handle
WHERE mid.database_id = DB_ID()
  AND OBJECT_NAME(mid.object_id) IN ('work_orders', 'projects', 'worklogs', 'activity_logs')
ORDER BY migs.avg_user_impact DESC;

PRINT '';

-- -----------------------------------------------------------------------------
-- 3. CURRENT INDEX USAGE STATS
-- -----------------------------------------------------------------------------
PRINT '=== 3. CURRENT INDEX USAGE (work_orders) ===';

SELECT 
    i.name AS index_name,
    i.type_desc,
    ius.user_seeks,
    ius.user_scans,
    ius.user_lookups,
    ius.user_updates,
    ius.last_user_seek,
    ius.last_user_scan
FROM sys.indexes i
LEFT JOIN sys.dm_db_index_usage_stats ius 
    ON i.object_id = ius.object_id AND i.index_id = ius.index_id AND ius.database_id = DB_ID()
WHERE i.object_id = OBJECT_ID('dbo.work_orders')
ORDER BY ius.user_seeks DESC;

PRINT '';

-- -----------------------------------------------------------------------------
-- 4. EXECUTION PLAN HINT (show what query does)
-- -----------------------------------------------------------------------------
PRINT '=== 4. TYPICAL API QUERY EXECUTION PLAN ===';
PRINT 'Run this in SSMS with "Include Actual Execution Plan" enabled:';
PRINT '';
PRINT 'SELECT TOP 50';
PRINT '    wo.id, wo.order_number, wo.status, wo.priority, wo.created_at,';
PRINT '    wo.project_id, p.name AS project_name';
PRINT 'FROM dbo.work_orders wo';
PRINT 'LEFT JOIN dbo.projects p ON wo.project_id = p.id';
PRINT 'ORDER BY wo.created_at DESC;';
PRINT '';

-- -----------------------------------------------------------------------------
-- 5. TABLE FRAGMENTATION
-- -----------------------------------------------------------------------------
PRINT '=== 5. INDEX FRAGMENTATION ===';

SELECT 
    OBJECT_NAME(ips.object_id) AS table_name,
    i.name AS index_name,
    ips.index_type_desc,
    ips.avg_fragmentation_in_percent,
    ips.page_count
FROM sys.dm_db_index_physical_stats(DB_ID(), OBJECT_ID('dbo.work_orders'), NULL, NULL, 'LIMITED') ips
JOIN sys.indexes i ON ips.object_id = i.object_id AND ips.index_id = i.index_id
WHERE ips.page_count > 0
ORDER BY ips.avg_fragmentation_in_percent DESC;

PRINT '';

-- -----------------------------------------------------------------------------
-- 6. WAIT STATISTICS (what is SQL Server waiting on?)
-- -----------------------------------------------------------------------------
PRINT '=== 6. TOP WAIT TYPES (last hour) ===';

SELECT TOP 10
    wait_type,
    wait_time_ms / 1000.0 AS wait_time_seconds,
    waiting_tasks_count
FROM sys.dm_os_wait_stats
WHERE wait_type NOT IN (
    'CLR_SEMAPHORE', 'LAZYWRITER_SLEEP', 'RESOURCE_QUEUE', 'SLEEP_TASK',
    'SLEEP_SYSTEMTASK', 'SQLTRACE_BUFFER_FLUSH', 'WAITFOR', 'LOGMGR_QUEUE',
    'CHECKPOINT_QUEUE', 'REQUEST_FOR_DEADLOCK_SEARCH', 'XE_TIMER_EVENT',
    'BROKER_TO_FLUSH', 'BROKER_TASK_STOP', 'CLR_MANUAL_EVENT',
    'CLR_AUTO_EVENT', 'DISPATCHER_QUEUE_SEMAPHORE', 'FT_IFTS_SCHEDULER_IDLE_WAIT',
    'XE_DISPATCHER_WAIT', 'XE_DISPATCHER_JOIN'
)
ORDER BY wait_time_ms DESC;

PRINT '';

-- -----------------------------------------------------------------------------
-- 7. QUICK FIX TEST - Run with NOLOCK to check if locking is the issue
-- -----------------------------------------------------------------------------
PRINT '=== 7. TEST WITH NOLOCK (bypass locking) ===';
PRINT 'If this runs fast, locking/blocking is the issue:';
PRINT '';

SET STATISTICS TIME ON;

SELECT TOP 50 
    wo.id,
    wo.order_number,
    wo.status,
    wo.priority,
    wo.created_at,
    wo.project_id
FROM dbo.work_orders wo WITH (NOLOCK)
ORDER BY wo.created_at DESC;

SET STATISTICS TIME OFF;

PRINT '';
PRINT '================================================================';
PRINT '   DIAGNOSTICS COMPLETE';
PRINT '================================================================';
PRINT '';
PRINT 'NEXT STEPS:';
PRINT '1. If fragmentation > 30%: REBUILD indexes';
PRINT '2. If Missing Index suggestions: Run create_work_orders_indexes.sql';
PRINT '3. If NOLOCK query was fast: Check for blocking transactions';
PRINT '4. If still slow with indexes: Check execution plan in SSMS';
PRINT '';

