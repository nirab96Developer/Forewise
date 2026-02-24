-- ===========================================================================
-- Migration 03: Create updated_at Triggers
-- ===========================================================================
-- Description:
--   Create triggers to automatically update updated_at on every UPDATE
--   Only for: CORE + TRANSACTIONS + LOOKUP tables (50 total)
--
-- Generated from: migration_decisions.json (needs_trigger: true)
-- Date: 2026-01-10
-- ===========================================================================

BEGIN TRANSACTION;

PRINT 'Starting Migration 03: Create Triggers';
PRINT '=======================================';
PRINT '';
PRINT 'Creating 50 triggers for updated_at auto-update...';
PRINT '';

-- ===========================================================================
-- CORE Tables (29 triggers)
-- ===========================================================================

-- activity_logs
CREATE OR ALTER TRIGGER trg_activity_logs_updated_at
ON dbo.activity_logs
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.activity_logs
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- areas
CREATE OR ALTER TRIGGER trg_areas_updated_at
ON dbo.areas
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.areas
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- audit_logs
CREATE OR ALTER TRIGGER trg_audit_logs_updated_at
ON dbo.audit_logs
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.audit_logs
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- budget_items
CREATE OR ALTER TRIGGER trg_budget_items_updated_at
ON dbo.budget_items
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.budget_items
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- budget_tx
CREATE OR ALTER TRIGGER trg_budget_tx_updated_at
ON dbo.budget_tx
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.budget_tx
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- budgets
CREATE OR ALTER TRIGGER trg_budgets_updated_at
ON dbo.budgets
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.budgets
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- conflict_logs
CREATE OR ALTER TRIGGER trg_conflict_logs_updated_at
ON dbo.conflict_logs
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.conflict_logs
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- daily_work_reports
CREATE OR ALTER TRIGGER trg_daily_work_reports_updated_at
ON dbo.daily_work_reports
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.daily_work_reports
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- departments
CREATE OR ALTER TRIGGER trg_departments_updated_at
ON dbo.departments
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.departments
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- equipment
CREATE OR ALTER TRIGGER trg_equipment_updated_at
ON dbo.equipment
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.equipment
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- equipment_categories
CREATE OR ALTER TRIGGER trg_equipment_categories_updated_at
ON dbo.equipment_categories
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.equipment_categories
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- files
CREATE OR ALTER TRIGGER trg_files_updated_at
ON dbo.files
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.files
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- invoice_items
CREATE OR ALTER TRIGGER trg_invoice_items_updated_at
ON dbo.invoice_items
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.invoice_items
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- invoices
CREATE OR ALTER TRIGGER trg_invoices_updated_at
ON dbo.invoices
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.invoices
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- locations
CREATE OR ALTER TRIGGER trg_locations_updated_at
ON dbo.locations
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.locations
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- milestones
CREATE OR ALTER TRIGGER trg_milestones_updated_at
ON dbo.milestones
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.milestones
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- permissions
CREATE OR ALTER TRIGGER trg_permissions_updated_at
ON dbo.permissions
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.permissions
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- pricing_overrides
CREATE OR ALTER TRIGGER trg_pricing_overrides_updated_at
ON dbo.pricing_overrides
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.pricing_overrides
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- project_documents
CREATE OR ALTER TRIGGER trg_project_documents_updated_at
ON dbo.project_documents
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.project_documents
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- projects
CREATE OR ALTER TRIGGER trg_projects_updated_at
ON dbo.projects
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.projects
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- regions
CREATE OR ALTER TRIGGER trg_regions_updated_at
ON dbo.regions
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.regions
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- reports
CREATE OR ALTER TRIGGER trg_reports_updated_at
ON dbo.reports
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.reports
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- roles
CREATE OR ALTER TRIGGER trg_roles_updated_at
ON dbo.roles
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.roles
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- supplier_equipment
CREATE OR ALTER TRIGGER trg_supplier_equipment_updated_at
ON dbo.supplier_equipment
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.supplier_equipment
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- suppliers
CREATE OR ALTER TRIGGER trg_suppliers_updated_at
ON dbo.suppliers
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.suppliers
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- support_ticket_comments
CREATE OR ALTER TRIGGER trg_support_ticket_comments_updated_at
ON dbo.support_ticket_comments
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.support_ticket_comments
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- support_tickets
CREATE OR ALTER TRIGGER trg_support_tickets_updated_at
ON dbo.support_tickets
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.support_tickets
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- users
CREATE OR ALTER TRIGGER trg_users_updated_at
ON dbo.users
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.users
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- work_breaks
CREATE OR ALTER TRIGGER trg_work_breaks_updated_at
ON dbo.work_breaks
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.work_breaks
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- work_orders
CREATE OR ALTER TRIGGER trg_work_orders_updated_at
ON dbo.work_orders
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.work_orders
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

PRINT '✓ CORE triggers created (29)';

-- ===========================================================================
-- TRANSACTIONS Tables (15 triggers)
-- ===========================================================================

-- balance_releases
CREATE OR ALTER TRIGGER trg_balance_releases_updated_at
ON dbo.balance_releases
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.balance_releases
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- budget_allocations
CREATE OR ALTER TRIGGER trg_budget_allocations_updated_at
ON dbo.budget_allocations
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.budget_allocations
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- budget_transfers
CREATE OR ALTER TRIGGER trg_budget_transfers_updated_at
ON dbo.budget_transfers
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.budget_transfers
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- equipment_assignments
CREATE OR ALTER TRIGGER trg_equipment_assignments_updated_at
ON dbo.equipment_assignments
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.equipment_assignments
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- equipment_maintenance
CREATE OR ALTER TRIGGER trg_equipment_maintenance_updated_at
ON dbo.equipment_maintenance
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.equipment_maintenance
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- equipment_scans
CREATE OR ALTER TRIGGER trg_equipment_scans_updated_at
ON dbo.equipment_scans
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.equipment_scans
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- invoice_payments
CREATE OR ALTER TRIGGER trg_invoice_payments_updated_at
ON dbo.invoice_payments
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.invoice_payments
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- project_assignments
CREATE OR ALTER TRIGGER trg_project_assignments_updated_at
ON dbo.project_assignments
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.project_assignments
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- report_runs
CREATE OR ALTER TRIGGER trg_report_runs_updated_at
ON dbo.report_runs
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.report_runs
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- role_assignments
CREATE OR ALTER TRIGGER trg_role_assignments_updated_at
ON dbo.role_assignments
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.role_assignments
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- supplier_rotations
CREATE OR ALTER TRIGGER trg_supplier_rotations_updated_at
ON dbo.supplier_rotations
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.supplier_rotations
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- worklog_segments
CREATE OR ALTER TRIGGER trg_worklog_segments_updated_at
ON dbo.worklog_segments
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.worklog_segments
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- worklog_standards
CREATE OR ALTER TRIGGER trg_worklog_standards_updated_at
ON dbo.worklog_standards
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.worklog_standards
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- worklogs
CREATE OR ALTER TRIGGER trg_worklogs_updated_at
ON dbo.worklogs
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.worklogs
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

PRINT '✓ TRANSACTIONS triggers created (14)';

-- ===========================================================================
-- LOOKUP Tables (6 triggers)
-- ===========================================================================

-- activity_types
CREATE OR ALTER TRIGGER trg_activity_types_updated_at
ON dbo.activity_types
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.activity_types
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- equipment_types
CREATE OR ALTER TRIGGER trg_equipment_types_updated_at
ON dbo.equipment_types
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.equipment_types
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- supplier_constraint_reasons
CREATE OR ALTER TRIGGER trg_supplier_constraint_reasons_updated_at
ON dbo.supplier_constraint_reasons
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.supplier_constraint_reasons
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- supplier_rejection_reasons
CREATE OR ALTER TRIGGER trg_supplier_rejection_reasons_updated_at
ON dbo.supplier_rejection_reasons
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.supplier_rejection_reasons
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- work_order_statuses
CREATE OR ALTER TRIGGER trg_work_order_statuses_updated_at
ON dbo.work_order_statuses
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.work_order_statuses
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- worklog_statuses
CREATE OR ALTER TRIGGER trg_worklog_statuses_updated_at
ON dbo.worklog_statuses
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.worklog_statuses
    SET updated_at = SYSUTCDATETIME()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

PRINT '✓ LOOKUP triggers created (6)';

-- ===========================================================================
-- COMMIT
-- ===========================================================================
COMMIT TRANSACTION;

PRINT '';
PRINT '=======================================';
PRINT '✅ Migration 03 completed successfully!';
PRINT '=======================================';
PRINT '';
PRINT 'Summary:';
PRINT '  - CORE: 29 triggers';
PRINT '  - TRANSACTIONS: 14 triggers';
PRINT '  - LOOKUP: 6 triggers';
PRINT '  - TOTAL: 49 triggers';
PRINT '';
PRINT 'updated_at will now update automatically on every UPDATE!';
PRINT '';
PRINT 'Next: Run 04_verification.sql';
