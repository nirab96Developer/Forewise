-- =====================================================
-- סקריפט אבחון מקיף למערכת Forest Management
-- PostgreSQL Database Diagnostic Script
-- =====================================================

-- 1. מידע כללי על מסד הנתונים
SELECT 
    current_database() as "Database Name",
    version() as "PostgreSQL Version",
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public') as "Total Tables",
    (SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public') as "Total Views",
    (SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema = 'public') as "Total Functions";

-- 2. רשימת טבלאות עם מספר רשומות
SELECT 
    t.table_name as "Table Name",
    COALESCE(s.n_tup_ins - s.n_tup_del, 0) as "Record Count"
FROM information_schema.tables t
LEFT JOIN pg_stat_user_tables s ON t.table_name = s.relname
WHERE t.table_schema = 'public' AND t.table_type = 'BASE TABLE'
ORDER BY t.table_name;

-- 3. משתמשים במערכת
SELECT 
    COUNT(*) as "Total Users",
    SUM(CASE WHEN is_active = true THEN 1 ELSE 0 END) as "Active Users",
    SUM(CASE WHEN is_locked = true THEN 1 ELSE 0 END) as "Locked Users",
    COUNT(DISTINCT role_id) as "Different Roles",
    COUNT(DISTINCT department_id) as "Different Departments",
    COUNT(DISTINCT region_id) as "Different Regions",
    COUNT(DISTINCT area_id) as "Different Areas"
FROM users;

-- רשימת משתמשים
SELECT 
    id,
    username,
    email,
    full_name,
    phone,
    role_id,
    department_id,
    region_id,
    area_id,
    is_active,
    is_locked,
    created_at
FROM users
ORDER BY id;

-- 4. פרויקטים במערכת
SELECT 
    COUNT(*) as "Total Projects",
    COUNT(DISTINCT region_id) as "Regions with Projects",
    COUNT(DISTINCT area_id) as "Areas with Projects",
    COUNT(DISTINCT manager_id) as "Different Managers"
FROM projects;

-- פרויקטים לפי סטטוס
SELECT 
    COALESCE(status, 'NULL') as "Status",
    COUNT(*) as "Count"
FROM projects
GROUP BY status
ORDER BY "Count" DESC;

-- פרויקטים לפי עדיפות
SELECT 
    COALESCE(priority, 'NULL') as "Priority",
    COUNT(*) as "Count"
FROM projects
GROUP BY priority
ORDER BY "Count" DESC;

-- רשימת פרויקטים
SELECT 
    id,
    code,
    name,
    status,
    priority,
    region_id,
    area_id,
    manager_id,
    budget_id,
    start_date,
    end_date
FROM projects
ORDER BY id
LIMIT 20;

-- 5. ציוד במערכת
SELECT 
    COUNT(*) as "Total Equipment",
    COUNT(DISTINCT category_id) as "Equipment Categories",
    COUNT(DISTINCT CASE WHEN status = 'available' THEN id END) as "Available",
    COUNT(DISTINCT CASE WHEN status = 'in_use' THEN id END) as "In Use",
    COUNT(DISTINCT CASE WHEN status = 'maintenance' THEN id END) as "In Maintenance"
FROM equipment;

-- ציוד לפי קטגוריה
SELECT 
    category_id,
    COUNT(*) as "Count"
FROM equipment
GROUP BY category_id
ORDER BY "Count" DESC;

-- 6. ספקים במערכת
SELECT 
    COUNT(*) as "Total Suppliers",
    SUM(CASE WHEN is_active = true THEN 1 ELSE 0 END) as "Active Suppliers"
FROM suppliers;

-- רשימת ספקים
SELECT 
    id,
    name,
    contact_name,
    phone,
    email,
    is_active
FROM suppliers
ORDER BY id
LIMIT 20;

-- 7. הזמנות עבודה
SELECT 
    COUNT(*) as "Total Work Orders",
    COUNT(DISTINCT project_id) as "Projects with Orders",
    COUNT(DISTINCT supplier_id) as "Suppliers with Orders",
    COUNT(DISTINCT equipment_id) as "Equipment in Orders"
FROM work_orders;

-- הזמנות לפי סטטוס
SELECT 
    COALESCE(status, 'NULL') as "Status",
    COUNT(*) as "Count"
FROM work_orders
GROUP BY status
ORDER BY "Count" DESC;

-- 8. דיווחי שעות
SELECT 
    COUNT(*) as "Total Worklogs",
    SUM(total_hours) as "Total Hours Reported",
    AVG(total_hours) as "Average Hours per Log",
    COUNT(DISTINCT user_id) as "Users Reporting",
    COUNT(DISTINCT work_order_id) as "Work Orders with Logs"
FROM worklogs;

-- 9. תקציבים
SELECT 
    COUNT(*) as "Total Budgets",
    SUM(total_amount) as "Total Budget Amount",
    SUM(allocated_amount) as "Total Allocated",
    SUM(spent_amount) as "Total Spent",
    SUM(available_amount) as "Total Available"
FROM budgets;

-- 10. בדיקת אינדקסים
SELECT 
    t.table_name as "Table Name",
    i.indexname as "Index Name",
    i.indexdef as "Index Definition"
FROM information_schema.tables t
LEFT JOIN pg_indexes i ON t.table_name = i.tablename
WHERE t.table_schema = 'public' AND t.table_type = 'BASE TABLE'
ORDER BY t.table_name, i.indexname;

-- 11. בדיקת Foreign Keys
SELECT 
    tc.constraint_name as "FK Name",
    tc.table_name as "Parent Table",
    kcu.column_name as "Parent Column",
    ccu.table_name as "Referenced Table",
    ccu.column_name as "Referenced Column"
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name, tc.constraint_name;

-- 12. בעיות פוטנציאליות
-- בדיקת ערכי NULL בשדות חשובים
SELECT 'Users with NULL password_hash' as "Issue", COUNT(*) as "Count"
FROM users WHERE password_hash IS NULL
UNION ALL
SELECT 'Users with NULL email', COUNT(*)
FROM users WHERE email IS NULL
UNION ALL
SELECT 'Projects with NULL status', COUNT(*)
FROM projects WHERE status IS NULL
UNION ALL
SELECT 'Projects with NULL priority', COUNT(*)
FROM projects WHERE priority IS NULL;

-- בדיקת ערכי Priority
SELECT DISTINCT priority as "Priority", COUNT(*) as "Count"
FROM projects
GROUP BY priority
ORDER BY priority;

-- בדיקת ערכי Status
SELECT DISTINCT status as "Status", COUNT(*) as "Count"
FROM projects
GROUP BY status
ORDER BY status;

