-- ============================================================================
-- Verification Script - Check all migrations
-- תאריך: 2026-01-10
-- ============================================================================

USE [KKLForest];
GO

PRINT '========================================';
PRINT 'Migration Verification';
PRINT '========================================';
PRINT '';

-- 1. Check UNIQUE constraints
PRINT 'Checking UNIQUE constraints...';
SELECT 
    'UNIQUE' as type,
    OBJECT_NAME(i.object_id) as table_name,
    i.name as constraint_name,
    'OK' as status
FROM sys.indexes i
WHERE i.is_unique = 1
AND OBJECT_SCHEMA_NAME(i.object_id) = 'dbo'
AND i.name LIKE 'UQ_%'
ORDER BY table_name;

-- 2. Check created_at/updated_at are NOT NULL
PRINT '';
PRINT 'Checking NOT NULL timestamps...';
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'dbo'
AND COLUMN_NAME IN ('created_at', 'updated_at')
AND IS_NULLABLE = 'YES'
ORDER BY TABLE_NAME, COLUMN_NAME;

-- 3. Check DEFAULT constraints
PRINT '';
PRINT 'Checking DEFAULT constraints...';
SELECT 
    OBJECT_NAME(dc.parent_object_id) as table_name,
    COL_NAME(dc.parent_object_id, dc.parent_column_id) as column_name,
    dc.name as constraint_name
FROM sys.default_constraints dc
WHERE OBJECT_SCHEMA_NAME(dc.parent_object_id) = 'dbo'
AND dc.name LIKE 'DF_%'
ORDER BY table_name, column_name;

-- 4. Check triggers
PRINT '';
PRINT 'Checking triggers...';
SELECT 
    OBJECT_NAME(parent_id) as table_name,
    name as trigger_name,
    'OK' as status
FROM sys.triggers
WHERE parent_class = 1
AND OBJECT_SCHEMA_NAME(parent_id) = 'dbo'
AND name LIKE 'trg_%_updated_at'
ORDER BY table_name;

PRINT '';
PRINT '✅ Verification complete!';
PRINT '';
GO
