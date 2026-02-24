-- ============================================================================
-- Auto-Generated Triggers for updated_at
-- תאריך: 2026-01-10
-- ============================================================================
-- Triggers created: 50
-- ============================================================================

USE [KKLForest];
GO

PRINT '========================================';
PRINT 'Creating updated_at Triggers';
PRINT '========================================';
PRINT '';


-- 1. activity_logs
PRINT 'Creating trigger for activity_logs...';
GO

CREATE OR ALTER TRIGGER trg_activity_logs_updated_at
ON dbo.activity_logs
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'activity_logs' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.activity_logs t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 2. activity_types
PRINT 'Creating trigger for activity_types...';
GO

CREATE OR ALTER TRIGGER trg_activity_types_updated_at
ON dbo.activity_types
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'activity_types' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.activity_types t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 3. areas
PRINT 'Creating trigger for areas...';
GO

CREATE OR ALTER TRIGGER trg_areas_updated_at
ON dbo.areas
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'areas' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.areas t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 4. audit_logs
PRINT 'Creating trigger for audit_logs...';
GO

CREATE OR ALTER TRIGGER trg_audit_logs_updated_at
ON dbo.audit_logs
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'audit_logs' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.audit_logs t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 5. balance_releases
PRINT 'Creating trigger for balance_releases...';
GO

CREATE OR ALTER TRIGGER trg_balance_releases_updated_at
ON dbo.balance_releases
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'balance_releases' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.balance_releases t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 6. budget_allocations
PRINT 'Creating trigger for budget_allocations...';
GO

CREATE OR ALTER TRIGGER trg_budget_allocations_updated_at
ON dbo.budget_allocations
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'budget_allocations' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.budget_allocations t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 7. budget_items
PRINT 'Creating trigger for budget_items...';
GO

CREATE OR ALTER TRIGGER trg_budget_items_updated_at
ON dbo.budget_items
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'budget_items' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.budget_items t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 8. budget_transfers
PRINT 'Creating trigger for budget_transfers...';
GO

CREATE OR ALTER TRIGGER trg_budget_transfers_updated_at
ON dbo.budget_transfers
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'budget_transfers' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.budget_transfers t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 9. budget_tx
PRINT 'Creating trigger for budget_tx...';
GO

CREATE OR ALTER TRIGGER trg_budget_tx_updated_at
ON dbo.budget_tx
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'budget_tx' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.budget_tx t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 10. budgets
PRINT 'Creating trigger for budgets...';
GO

CREATE OR ALTER TRIGGER trg_budgets_updated_at
ON dbo.budgets
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'budgets' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.budgets t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 11. conflict_logs
PRINT 'Creating trigger for conflict_logs...';
GO

CREATE OR ALTER TRIGGER trg_conflict_logs_updated_at
ON dbo.conflict_logs
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'conflict_logs' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.conflict_logs t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 12. daily_work_reports
PRINT 'Creating trigger for daily_work_reports...';
GO

CREATE OR ALTER TRIGGER trg_daily_work_reports_updated_at
ON dbo.daily_work_reports
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'daily_work_reports' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.daily_work_reports t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 13. departments
PRINT 'Creating trigger for departments...';
GO

CREATE OR ALTER TRIGGER trg_departments_updated_at
ON dbo.departments
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'departments' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.departments t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 14. equipment
PRINT 'Creating trigger for equipment...';
GO

CREATE OR ALTER TRIGGER trg_equipment_updated_at
ON dbo.equipment
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'equipment' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.equipment t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 15. equipment_assignments
PRINT 'Creating trigger for equipment_assignments...';
GO

CREATE OR ALTER TRIGGER trg_equipment_assignments_updated_at
ON dbo.equipment_assignments
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'equipment_assignments' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.equipment_assignments t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 16. equipment_categories
PRINT 'Creating trigger for equipment_categories...';
GO

CREATE OR ALTER TRIGGER trg_equipment_categories_updated_at
ON dbo.equipment_categories
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'equipment_categories' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.equipment_categories t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 17. equipment_maintenance
PRINT 'Creating trigger for equipment_maintenance...';
GO

CREATE OR ALTER TRIGGER trg_equipment_maintenance_updated_at
ON dbo.equipment_maintenance
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'equipment_maintenance' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.equipment_maintenance t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 18. equipment_scans
PRINT 'Creating trigger for equipment_scans...';
GO

CREATE OR ALTER TRIGGER trg_equipment_scans_updated_at
ON dbo.equipment_scans
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'equipment_scans' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.equipment_scans t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 19. equipment_types
PRINT 'Creating trigger for equipment_types...';
GO

CREATE OR ALTER TRIGGER trg_equipment_types_updated_at
ON dbo.equipment_types
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'equipment_types' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.equipment_types t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 20. files
PRINT 'Creating trigger for files...';
GO

CREATE OR ALTER TRIGGER trg_files_updated_at
ON dbo.files
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'files' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.files t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 21. invoice_items
PRINT 'Creating trigger for invoice_items...';
GO

CREATE OR ALTER TRIGGER trg_invoice_items_updated_at
ON dbo.invoice_items
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'invoice_items' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.invoice_items t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 22. invoice_payments
PRINT 'Creating trigger for invoice_payments...';
GO

CREATE OR ALTER TRIGGER trg_invoice_payments_updated_at
ON dbo.invoice_payments
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'invoice_payments' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.invoice_payments t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 23. invoices
PRINT 'Creating trigger for invoices...';
GO

CREATE OR ALTER TRIGGER trg_invoices_updated_at
ON dbo.invoices
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'invoices' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.invoices t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 24. locations
PRINT 'Creating trigger for locations...';
GO

CREATE OR ALTER TRIGGER trg_locations_updated_at
ON dbo.locations
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'locations' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.locations t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 25. milestones
PRINT 'Creating trigger for milestones...';
GO

CREATE OR ALTER TRIGGER trg_milestones_updated_at
ON dbo.milestones
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'milestones' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.milestones t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 26. permissions
PRINT 'Creating trigger for permissions...';
GO

CREATE OR ALTER TRIGGER trg_permissions_updated_at
ON dbo.permissions
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'permissions' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.permissions t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 27. pricing_overrides
PRINT 'Creating trigger for pricing_overrides...';
GO

CREATE OR ALTER TRIGGER trg_pricing_overrides_updated_at
ON dbo.pricing_overrides
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'pricing_overrides' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.pricing_overrides t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 28. project_assignments
PRINT 'Creating trigger for project_assignments...';
GO

CREATE OR ALTER TRIGGER trg_project_assignments_updated_at
ON dbo.project_assignments
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'project_assignments' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.project_assignments t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 29. project_documents
PRINT 'Creating trigger for project_documents...';
GO

CREATE OR ALTER TRIGGER trg_project_documents_updated_at
ON dbo.project_documents
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'project_documents' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.project_documents t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 30. projects
PRINT 'Creating trigger for projects...';
GO

CREATE OR ALTER TRIGGER trg_projects_updated_at
ON dbo.projects
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'projects' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.projects t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 31. regions
PRINT 'Creating trigger for regions...';
GO

CREATE OR ALTER TRIGGER trg_regions_updated_at
ON dbo.regions
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'regions' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.regions t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 32. report_runs
PRINT 'Creating trigger for report_runs...';
GO

CREATE OR ALTER TRIGGER trg_report_runs_updated_at
ON dbo.report_runs
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'report_runs' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.report_runs t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 33. reports
PRINT 'Creating trigger for reports...';
GO

CREATE OR ALTER TRIGGER trg_reports_updated_at
ON dbo.reports
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'reports' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.reports t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 34. role_assignments
PRINT 'Creating trigger for role_assignments...';
GO

CREATE OR ALTER TRIGGER trg_role_assignments_updated_at
ON dbo.role_assignments
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'role_assignments' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.role_assignments t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 35. roles
PRINT 'Creating trigger for roles...';
GO

CREATE OR ALTER TRIGGER trg_roles_updated_at
ON dbo.roles
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'roles' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.roles t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 36. supplier_constraint_reasons
PRINT 'Creating trigger for supplier_constraint_reasons...';
GO

CREATE OR ALTER TRIGGER trg_supplier_constraint_reasons_updated_at
ON dbo.supplier_constraint_reasons
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'supplier_constraint_reasons' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.supplier_constraint_reasons t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 37. supplier_equipment
PRINT 'Creating trigger for supplier_equipment...';
GO

CREATE OR ALTER TRIGGER trg_supplier_equipment_updated_at
ON dbo.supplier_equipment
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'supplier_equipment' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.supplier_equipment t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 38. supplier_rejection_reasons
PRINT 'Creating trigger for supplier_rejection_reasons...';
GO

CREATE OR ALTER TRIGGER trg_supplier_rejection_reasons_updated_at
ON dbo.supplier_rejection_reasons
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'supplier_rejection_reasons' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.supplier_rejection_reasons t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 39. supplier_rotations
PRINT 'Creating trigger for supplier_rotations...';
GO

CREATE OR ALTER TRIGGER trg_supplier_rotations_updated_at
ON dbo.supplier_rotations
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'supplier_rotations' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.supplier_rotations t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 40. suppliers
PRINT 'Creating trigger for suppliers...';
GO

CREATE OR ALTER TRIGGER trg_suppliers_updated_at
ON dbo.suppliers
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'suppliers' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.suppliers t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 41. support_ticket_comments
PRINT 'Creating trigger for support_ticket_comments...';
GO

CREATE OR ALTER TRIGGER trg_support_ticket_comments_updated_at
ON dbo.support_ticket_comments
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'support_ticket_comments' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.support_ticket_comments t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 42. support_tickets
PRINT 'Creating trigger for support_tickets...';
GO

CREATE OR ALTER TRIGGER trg_support_tickets_updated_at
ON dbo.support_tickets
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'support_tickets' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.support_tickets t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 43. users
PRINT 'Creating trigger for users...';
GO

CREATE OR ALTER TRIGGER trg_users_updated_at
ON dbo.users
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.users t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 44. work_breaks
PRINT 'Creating trigger for work_breaks...';
GO

CREATE OR ALTER TRIGGER trg_work_breaks_updated_at
ON dbo.work_breaks
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'work_breaks' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.work_breaks t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 45. work_order_statuses
PRINT 'Creating trigger for work_order_statuses...';
GO

CREATE OR ALTER TRIGGER trg_work_order_statuses_updated_at
ON dbo.work_order_statuses
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'work_order_statuses' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.work_order_statuses t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 46. work_orders
PRINT 'Creating trigger for work_orders...';
GO

CREATE OR ALTER TRIGGER trg_work_orders_updated_at
ON dbo.work_orders
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'work_orders' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.work_orders t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 47. worklog_segments
PRINT 'Creating trigger for worklog_segments...';
GO

CREATE OR ALTER TRIGGER trg_worklog_segments_updated_at
ON dbo.worklog_segments
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'worklog_segments' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.worklog_segments t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 48. worklog_standards
PRINT 'Creating trigger for worklog_standards...';
GO

CREATE OR ALTER TRIGGER trg_worklog_standards_updated_at
ON dbo.worklog_standards
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'worklog_standards' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.worklog_standards t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 49. worklog_statuses
PRINT 'Creating trigger for worklog_statuses...';
GO

CREATE OR ALTER TRIGGER trg_worklog_statuses_updated_at
ON dbo.worklog_statuses
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'worklog_statuses' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.worklog_statuses t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


-- 50. worklogs
PRINT 'Creating trigger for worklogs...';
GO

CREATE OR ALTER TRIGGER trg_worklogs_updated_at
ON dbo.worklogs
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'worklogs' AND COLUMN_NAME = 'updated_at')
    BEGIN
        UPDATE t
        SET t.updated_at = SYSUTCDATETIME()
        FROM dbo.worklogs t
        INNER JOIN inserted i ON t.id = i.id
        WHERE t.id IN (SELECT id FROM inserted);
    END
END
GO


PRINT '';
PRINT '✅ All triggers created successfully!';
PRINT 'Total triggers: 50';
PRINT '';
GO
