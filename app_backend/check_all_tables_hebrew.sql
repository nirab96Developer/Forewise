-- =========================================================
-- בדיקה מקיפה של כל הטבלאות לבעיות בטקסט עברי
-- =========================================================

-- 1. בדיקת טבלת AREAS
SELECT 'AREAS' as TableName, COUNT(*) as ProblemsCount
FROM areas
WHERE name LIKE '%?%' OR description LIKE '%?%';

-- 2. בדיקת טבלת REGIONS
SELECT 'REGIONS' as TableName, COUNT(*) as ProblemsCount
FROM regions
WHERE name LIKE '%?%' OR description LIKE '%?%';

-- 3. בדיקת טבלת LOCATIONS
SELECT 'LOCATIONS' as TableName, COUNT(*) as ProblemsCount
FROM locations
WHERE name LIKE '%?%' OR description LIKE '%?%' OR address LIKE '%?%';

-- 4. בדיקת טבלת PROJECTS
SELECT 'PROJECTS' as TableName, COUNT(*) as ProblemsCount
FROM projects
WHERE name LIKE '%?%' OR description LIKE '%?%' OR objectives LIKE '%?%';

-- 5. בדיקת טבלת USERS
SELECT 'USERS' as TableName, COUNT(*) as ProblemsCount
FROM users
WHERE full_name LIKE '%?%' OR email LIKE '%?%' OR phone LIKE '%?%';

-- 6. בדיקת טבלת DEPARTMENTS
SELECT 'DEPARTMENTS' as TableName, COUNT(*) as ProblemsCount
FROM departments
WHERE name LIKE '%?%' OR description LIKE '%?%';

-- 7. בדיקת טבלת BUDGETS
SELECT 'BUDGETS' as TableName, COUNT(*) as ProblemsCount
FROM budgets
WHERE name LIKE '%?%' OR description LIKE '%?%';

-- 8. בדיקת טבלת WORK_ORDERS (אם קיימת)
IF OBJECT_ID('work_orders', 'U') IS NOT NULL
BEGIN
    SELECT 'WORK_ORDERS' as TableName, COUNT(*) as ProblemsCount
    FROM work_orders
    WHERE title LIKE '%?%' OR description LIKE '%?%';
END

-- 9. בדיקת טבלת SUPPLIERS (אם קיימת)
IF OBJECT_ID('suppliers', 'U') IS NOT NULL
BEGIN
    SELECT 'SUPPLIERS' as TableName, COUNT(*) as ProblemsCount
    FROM suppliers
    WHERE name LIKE '%?%' OR description LIKE '%?%' OR contact_name LIKE '%?%';
END

-- 10. בדיקת טבלת ROLES
SELECT 'ROLES' as TableName, COUNT(*) as ProblemsCount
FROM roles
WHERE name LIKE '%?%' OR description LIKE '%?%';

-- 11. בדיקת טבלת PERMISSIONS
SELECT 'PERMISSIONS' as TableName, COUNT(*) as ProblemsCount
FROM permissions
WHERE name LIKE '%?%' OR description LIKE '%?%';

-- 12. בדיקת טבלת REPORTS (אם קיימת)
IF OBJECT_ID('reports', 'U') IS NOT NULL
BEGIN
    SELECT 'REPORTS' as TableName, COUNT(*) as ProblemsCount
    FROM reports
    WHERE name LIKE '%?%' OR description LIKE '%?%';
END

-- 13. בדיקת טבלת WORKLOGS (אם קיימת)
IF OBJECT_ID('worklogs', 'U') IS NOT NULL
BEGIN
    SELECT 'WORKLOGS' as TableName, COUNT(*) as ProblemsCount
    FROM worklogs
    WHERE description LIKE '%?%' OR notes LIKE '%?%';
END

-- =========================================================
-- סיכום כללי - הצגת כל הרשומות עם בעיות
-- =========================================================

PRINT '===== DETAILED PROBLEMS LIST ====='

-- הצגת כל הבעיות בטבלת AREAS
IF EXISTS (SELECT 1 FROM areas WHERE name LIKE '%?%' OR description LIKE '%?%')
BEGIN
    PRINT 'AREAS with problems:'
    SELECT id, code, name, description
    FROM areas
    WHERE name LIKE '%?%' OR description LIKE '%?%'
    ORDER BY id;
END

-- הצגת כל הבעיות בטבלת PROJECTS
IF EXISTS (SELECT 1 FROM projects WHERE name LIKE '%?%' OR description LIKE '%?%')
BEGIN
    PRINT 'PROJECTS with problems:'
    SELECT TOP 20 id, code, name, description
    FROM projects
    WHERE name LIKE '%?%' OR description LIKE '%?%'
    ORDER BY id;
END

-- הצגת כל הבעיות בטבלת LOCATIONS
IF EXISTS (SELECT 1 FROM locations WHERE name LIKE '%?%' OR description LIKE '%?%')
BEGIN
    PRINT 'LOCATIONS with problems:'
    SELECT TOP 20 id, code, name, description
    FROM locations
    WHERE name LIKE '%?%' OR description LIKE '%?%'
    ORDER BY id;
END

-- =========================================================
-- בדיקה של כל העמודות מסוג טקסט בכל הטבלאות
-- =========================================================

DECLARE @sql NVARCHAR(MAX) = '';

SELECT @sql = @sql + 
    'SELECT ''' + TABLE_NAME + ''' as TableName, ''' + COLUMN_NAME + ''' as ColumnName, COUNT(*) as ProblemsCount ' +
    'FROM [' + TABLE_NAME + '] ' +
    'WHERE [' + COLUMN_NAME + '] LIKE ''%?%'' ' +
    'HAVING COUNT(*) > 0 ' +
    'UNION ALL '
FROM INFORMATION_SCHEMA.COLUMNS
WHERE DATA_TYPE IN ('nvarchar', 'varchar', 'text', 'ntext')
    AND TABLE_SCHEMA = 'dbo'
    AND TABLE_NAME NOT IN ('sysdiagrams');

-- הסרת ה-UNION ALL האחרון
IF LEN(@sql) > 10
BEGIN
    SET @sql = LEFT(@sql, LEN(@sql) - 10);
    PRINT 'Checking all text columns in all tables:';
    EXEC sp_executesql @sql;
END
