-- ============================================================================
-- Migration 08: Fix DEFAULT Constraints
-- Corrected Script - No USE, No GO (for Azure SQL)
-- ============================================================================

DECLARE 
    @schema sysname,
    @table sysname,
    @column sysname,
    @df_name sysname,
    @sql nvarchar(max);

PRINT '========================================';
PRINT 'Fixing DEFAULT Constraints';
PRINT '========================================';
PRINT '';

DECLARE cur CURSOR FAST_FORWARD FOR
SELECT 
    s.name,
    t.name,
    c.name
FROM sys.tables t
JOIN sys.schemas s ON s.schema_id = t.schema_id
JOIN sys.columns c ON c.object_id = t.object_id
WHERE c.name IN ('created_at', 'updated_at')
  AND t.is_ms_shipped = 0
  AND s.name = 'dbo';

OPEN cur;
FETCH NEXT FROM cur INTO @schema, @table, @column;

WHILE @@FETCH_STATUS = 0
BEGIN
    -- מציאת DEFAULT קיים
    SELECT @df_name = dc.name
    FROM sys.default_constraints dc
    JOIN sys.columns c 
        ON c.object_id = dc.parent_object_id
       AND c.column_id = dc.parent_column_id
    WHERE dc.parent_object_id = OBJECT_ID(QUOTENAME(@schema) + '.' + QUOTENAME(@table))
      AND c.name = @column;

    -- מחיקת DEFAULT קיים
    IF @df_name IS NOT NULL
    BEGIN
        SET @sql = N'ALTER TABLE '
                 + QUOTENAME(@schema) + '.' + QUOTENAME(@table)
                 + N' DROP CONSTRAINT ' + QUOTENAME(@df_name) + ';';
        EXEC (@sql);
        PRINT '  Dropped: ' + @df_name + ' from ' + @table + '.' + @column;
    END

    -- הוספת DEFAULT חדש
    SET @sql = N'ALTER TABLE '
             + QUOTENAME(@schema) + '.' + QUOTENAME(@table)
             + N' ADD CONSTRAINT DF_' + @table + '_' + @column
             + N' DEFAULT SYSUTCDATETIME() FOR ' + QUOTENAME(@column) + ';';

    BEGIN TRY
        EXEC (@sql);
        PRINT '  ✅ DF_' + @table + '_' + @column + ' created';
    END TRY
    BEGIN CATCH
        PRINT '  ⚠️  ' + @table + '.' + @column + ': ' + ERROR_MESSAGE();
    END CATCH

    SET @df_name = NULL;
    FETCH NEXT FROM cur INTO @schema, @table, @column;
END

CLOSE cur;
DEALLOCATE cur;

PRINT '';
PRINT '✅ DEFAULTs fixed successfully!';

