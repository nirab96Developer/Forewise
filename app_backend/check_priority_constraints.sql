-- Check existing constraints and defaults
SELECT 
    cc.name as constraint_name,
    cc.definition,
    cc.is_disabled
FROM sys.check_constraints cc
WHERE cc.parent_object_id = OBJECT_ID('dbo.projects')
AND cc.name LIKE '%priority%';

SELECT 
    dc.name as default_name,
    dc.definition,
    c.name as column_name
FROM sys.default_constraints dc
JOIN sys.columns c ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id
WHERE dc.parent_object_id = OBJECT_ID('dbo.projects')
AND c.name = 'priority';

-- Check current priority values
SELECT 
    priority,
    COUNT(*) as count
FROM dbo.projects 
GROUP BY priority
ORDER BY priority;

