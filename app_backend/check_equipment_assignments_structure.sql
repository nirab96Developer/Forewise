-- Check equipment_assignments table structure
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'equipment_assignments'
ORDER BY ORDINAL_POSITION;

