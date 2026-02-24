-- Create meaningful indexes for better performance
-- SQL Server specific syntax

-- Projects indexes
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_projects_status_region_created_at')
BEGIN
    CREATE NONCLUSTERED INDEX IX_projects_status_region_created_at
    ON dbo.projects (status, region_id, created_at)
    INCLUDE (id, name, priority, manager_id);
    PRINT 'Created IX_projects_status_region_created_at';
END
ELSE
BEGIN
    PRINT 'IX_projects_status_region_created_at already exists';
END

-- Worklogs indexes
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_worklogs_project_id_report_date')
BEGIN
    CREATE NONCLUSTERED INDEX IX_worklogs_project_id_report_date
    ON dbo.worklogs (project_id, report_date)
    INCLUDE (id, user_id, total_hours, status);
    PRINT 'Created IX_worklogs_project_id_report_date';
END
ELSE
BEGIN
    PRINT 'IX_worklogs_project_id_report_date already exists';
END

-- Work Orders indexes
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_work_orders_status_created_at')
BEGIN
    CREATE NONCLUSTERED INDEX IX_work_orders_status_created_at
    ON dbo.work_orders (status, created_at)
    INCLUDE (id, project_id, supplier_id, priority);
    PRINT 'Created IX_work_orders_status_created_at';
END
ELSE
BEGIN
    PRINT 'IX_work_orders_status_created_at already exists';
END

-- Equipment Assignments indexes
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_equipment_assignments_equipment_id_from_to')
BEGIN
    CREATE NONCLUSTERED INDEX IX_equipment_assignments_equipment_id_from_to
    ON dbo.equipment_assignments (equipment_id, start_date, end_date)
    INCLUDE (id, project_id, status);
    PRINT 'Created IX_equipment_assignments_equipment_id_from_to';
END
ELSE
BEGIN
    PRINT 'IX_equipment_assignments_equipment_id_from_to already exists';
END

-- Users indexes for authentication
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_users_email_active')
BEGIN
    CREATE NONCLUSTERED INDEX IX_users_email_active
    ON dbo.users (email, is_active)
    INCLUDE (id, username, full_name, role_id);
    PRINT 'Created IX_users_email_active';
END
ELSE
BEGIN
    PRINT 'IX_users_email_active already exists';
END

-- Sessions indexes
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_sessions_user_id_active')
BEGIN
    CREATE NONCLUSTERED INDEX IX_sessions_user_id_active
    ON dbo.sessions (user_id, is_active)
    INCLUDE (id, session_id, expires_at);
    PRINT 'Created IX_sessions_user_id_active';
END
ELSE
BEGIN
    PRINT 'IX_sessions_user_id_active already exists';
END

-- Budget Allocations indexes
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_budget_allocations_budget_status')
BEGIN
    CREATE NONCLUSTERED INDEX IX_budget_allocations_budget_status
    ON dbo.budget_allocations (budget_id, status)
    INCLUDE (id, amount, allocation_date, approved_at);
    PRINT 'Created IX_budget_allocations_budget_status';
END
ELSE
BEGIN
    PRINT 'IX_budget_allocations_budget_status already exists';
END

-- Equipment indexes
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_equipment_type_status')
BEGIN
    CREATE NONCLUSTERED INDEX IX_equipment_type_status
    ON dbo.equipment (equipment_type, status)
    INCLUDE (id, name, code, location_id);
    PRINT 'Created IX_equipment_type_status';
END
ELSE
BEGIN
    PRINT 'IX_equipment_type_status already exists';
END

-- Suppliers indexes
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_suppliers_status_rating')
BEGIN
    CREATE NONCLUSTERED INDEX IX_suppliers_status_rating
    ON dbo.suppliers (is_active, rating)
    INCLUDE (id, name, email);
    PRINT 'Created IX_suppliers_status_rating';
END
ELSE
BEGIN
    PRINT 'IX_suppliers_status_rating already exists';
END

-- Activity Logs indexes
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_activity_logs_user_id_created_at')
BEGIN
    CREATE NONCLUSTERED INDEX IX_activity_logs_user_id_created_at
    ON dbo.activity_logs (user_id, created_at)
    INCLUDE (id, activity_type, details);
    PRINT 'Created IX_activity_logs_user_id_created_at';
END
ELSE
BEGIN
    PRINT 'IX_activity_logs_user_id_created_at already exists';
END

-- Check index usage statistics
SELECT 
    i.name as index_name,
    s.user_seeks,
    s.user_scans,
    s.user_lookups,
    s.user_updates
FROM sys.indexes i
LEFT JOIN sys.dm_db_index_usage_stats s ON i.object_id = s.object_id AND i.index_id = s.index_id
WHERE i.name LIKE 'IX_%'
ORDER BY i.name;

PRINT 'Index creation completed';
