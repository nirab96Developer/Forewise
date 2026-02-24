-- Check activity_logs table structure
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'activity_logs'
ORDER BY ORDINAL_POSITION;

