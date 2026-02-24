-- ============================================================================
-- Migration 02: Backfill NULL values in created_at/updated_at
-- Auto-Generated
-- תאריך: 2026-01-10
-- ============================================================================
-- חייב לרוץ לפני ALTER COLUMN ל-NOT NULL!
-- ============================================================================

USE [KKLForest];
GO

PRINT '========================================';
PRINT 'Migration 02: Backfill Timestamps';
PRINT '========================================';
PRINT '';

DECLARE @now datetime2 = SYSUTCDATETIME();
PRINT 'Current timestamp: ' + CAST(@now AS NVARCHAR(50));
PRINT '';

BEGIN TRANSACTION;

BEGIN TRY

    PRINT 'Backfilling created_at and updated_at...';
    PRINT '';
    
    -- activity_logs
    UPDATE dbo.activity_logs SET created_at = @now WHERE created_at IS NULL;
    PRINT '  activity_logs.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.activity_logs SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  activity_logs.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- activity_types
    UPDATE dbo.activity_types SET created_at = @now WHERE created_at IS NULL;
    PRINT '  activity_types.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.activity_types SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  activity_types.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- areas
    UPDATE dbo.areas SET created_at = @now WHERE created_at IS NULL;
    PRINT '  areas.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.areas SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  areas.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- audit_logs
    UPDATE dbo.audit_logs SET created_at = @now WHERE created_at IS NULL;
    PRINT '  audit_logs.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.audit_logs SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  audit_logs.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- balance_releases
    UPDATE dbo.balance_releases SET created_at = @now WHERE created_at IS NULL;
    PRINT '  balance_releases.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.balance_releases SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  balance_releases.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- budget_allocations
    UPDATE dbo.budget_allocations SET created_at = @now WHERE created_at IS NULL;
    PRINT '  budget_allocations.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.budget_allocations SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  budget_allocations.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- budget_items
    UPDATE dbo.budget_items SET created_at = @now WHERE created_at IS NULL;
    PRINT '  budget_items.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.budget_items SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  budget_items.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- budget_transfers
    UPDATE dbo.budget_transfers SET created_at = @now WHERE created_at IS NULL;
    PRINT '  budget_transfers.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.budget_transfers SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  budget_transfers.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- budget_tx
    UPDATE dbo.budget_tx SET created_at = @now WHERE created_at IS NULL;
    PRINT '  budget_tx.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.budget_tx SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  budget_tx.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- budgets
    UPDATE dbo.budgets SET created_at = @now WHERE created_at IS NULL;
    PRINT '  budgets.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.budgets SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  budgets.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- conflict_logs
    UPDATE dbo.conflict_logs SET created_at = @now WHERE created_at IS NULL;
    PRINT '  conflict_logs.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.conflict_logs SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  conflict_logs.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- daily_work_reports
    UPDATE dbo.daily_work_reports SET created_at = @now WHERE created_at IS NULL;
    PRINT '  daily_work_reports.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.daily_work_reports SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  daily_work_reports.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- departments
    UPDATE dbo.departments SET created_at = @now WHERE created_at IS NULL;
    PRINT '  departments.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.departments SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  departments.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- equipment
    UPDATE dbo.equipment SET created_at = @now WHERE created_at IS NULL;
    PRINT '  equipment.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.equipment SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  equipment.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- equipment_assignments
    UPDATE dbo.equipment_assignments SET created_at = @now WHERE created_at IS NULL;
    PRINT '  equipment_assignments.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.equipment_assignments SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  equipment_assignments.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- equipment_categories
    UPDATE dbo.equipment_categories SET created_at = @now WHERE created_at IS NULL;
    PRINT '  equipment_categories.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.equipment_categories SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  equipment_categories.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- equipment_maintenance
    UPDATE dbo.equipment_maintenance SET created_at = @now WHERE created_at IS NULL;
    PRINT '  equipment_maintenance.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.equipment_maintenance SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  equipment_maintenance.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- equipment_scans
    UPDATE dbo.equipment_scans SET created_at = @now WHERE created_at IS NULL;
    PRINT '  equipment_scans.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.equipment_scans SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  equipment_scans.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- equipment_types
    UPDATE dbo.equipment_types SET created_at = @now WHERE created_at IS NULL;
    PRINT '  equipment_types.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.equipment_types SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  equipment_types.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- files
    UPDATE dbo.files SET created_at = @now WHERE created_at IS NULL;
    PRINT '  files.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.files SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  files.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- invoice_items
    UPDATE dbo.invoice_items SET created_at = @now WHERE created_at IS NULL;
    PRINT '  invoice_items.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.invoice_items SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  invoice_items.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- invoice_payments
    UPDATE dbo.invoice_payments SET created_at = @now WHERE created_at IS NULL;
    PRINT '  invoice_payments.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.invoice_payments SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  invoice_payments.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- invoices
    UPDATE dbo.invoices SET created_at = @now WHERE created_at IS NULL;
    PRINT '  invoices.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.invoices SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  invoices.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- locations
    UPDATE dbo.locations SET created_at = @now WHERE created_at IS NULL;
    PRINT '  locations.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.locations SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  locations.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- milestones
    UPDATE dbo.milestones SET created_at = @now WHERE created_at IS NULL;
    PRINT '  milestones.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.milestones SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  milestones.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- notification_types
    UPDATE dbo.notification_types SET created_at = @now WHERE created_at IS NULL;
    PRINT '  notification_types.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.notification_types SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  notification_types.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- notifications
    UPDATE dbo.notifications SET created_at = @now WHERE created_at IS NULL;
    PRINT '  notifications.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.notifications SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  notifications.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- otp_tokens
    UPDATE dbo.otp_tokens SET created_at = @now WHERE created_at IS NULL;
    PRINT '  otp_tokens.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.otp_tokens SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  otp_tokens.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- permissions
    UPDATE dbo.permissions SET created_at = @now WHERE created_at IS NULL;
    PRINT '  permissions.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.permissions SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  permissions.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- pricing_overrides
    UPDATE dbo.pricing_overrides SET created_at = @now WHERE created_at IS NULL;
    PRINT '  pricing_overrides.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.pricing_overrides SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  pricing_overrides.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- project_assignments
    UPDATE dbo.project_assignments SET created_at = @now WHERE created_at IS NULL;
    PRINT '  project_assignments.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.project_assignments SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  project_assignments.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- project_documents
    UPDATE dbo.project_documents SET created_at = @now WHERE created_at IS NULL;
    PRINT '  project_documents.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.project_documents SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  project_documents.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- projects
    UPDATE dbo.projects SET created_at = @now WHERE created_at IS NULL;
    PRINT '  projects.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.projects SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  projects.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- regions
    UPDATE dbo.regions SET created_at = @now WHERE created_at IS NULL;
    PRINT '  regions.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.regions SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  regions.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- report_runs
    UPDATE dbo.report_runs SET created_at = @now WHERE created_at IS NULL;
    PRINT '  report_runs.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.report_runs SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  report_runs.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- reports
    UPDATE dbo.reports SET created_at = @now WHERE created_at IS NULL;
    PRINT '  reports.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.reports SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  reports.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- role_assignments
    UPDATE dbo.role_assignments SET created_at = @now WHERE created_at IS NULL;
    PRINT '  role_assignments.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.role_assignments SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  role_assignments.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- role_permissions
    UPDATE dbo.role_permissions SET created_at = @now WHERE created_at IS NULL;
    PRINT '  role_permissions.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.role_permissions SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  role_permissions.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- roles
    UPDATE dbo.roles SET created_at = @now WHERE created_at IS NULL;
    PRINT '  roles.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.roles SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  roles.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- sessions
    UPDATE dbo.sessions SET created_at = @now WHERE created_at IS NULL;
    PRINT '  sessions.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.sessions SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  sessions.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- supplier_constraint_logs
    UPDATE dbo.supplier_constraint_logs SET created_at = @now WHERE created_at IS NULL;
    PRINT '  supplier_constraint_logs.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.supplier_constraint_logs SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  supplier_constraint_logs.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- supplier_constraint_reasons
    UPDATE dbo.supplier_constraint_reasons SET created_at = @now WHERE created_at IS NULL;
    PRINT '  supplier_constraint_reasons.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.supplier_constraint_reasons SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  supplier_constraint_reasons.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- supplier_equipment
    UPDATE dbo.supplier_equipment SET created_at = @now WHERE created_at IS NULL;
    PRINT '  supplier_equipment.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.supplier_equipment SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  supplier_equipment.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- supplier_rejection_reasons
    UPDATE dbo.supplier_rejection_reasons SET created_at = @now WHERE created_at IS NULL;
    PRINT '  supplier_rejection_reasons.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.supplier_rejection_reasons SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  supplier_rejection_reasons.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- supplier_rotation_queue
    UPDATE dbo.supplier_rotation_queue SET created_at = @now WHERE created_at IS NULL;
    PRINT '  supplier_rotation_queue.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.supplier_rotation_queue SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  supplier_rotation_queue.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- supplier_rotations
    UPDATE dbo.supplier_rotations SET created_at = @now WHERE created_at IS NULL;
    PRINT '  supplier_rotations.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.supplier_rotations SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  supplier_rotations.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- suppliers
    UPDATE dbo.suppliers SET created_at = @now WHERE created_at IS NULL;
    PRINT '  suppliers.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.suppliers SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  suppliers.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- support_ticket_comments
    UPDATE dbo.support_ticket_comments SET created_at = @now WHERE created_at IS NULL;
    PRINT '  support_ticket_comments.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.support_ticket_comments SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  support_ticket_comments.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- support_tickets
    UPDATE dbo.support_tickets SET created_at = @now WHERE created_at IS NULL;
    PRINT '  support_tickets.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.support_tickets SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  support_tickets.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- sync_queue
    UPDATE dbo.sync_queue SET created_at = @now WHERE created_at IS NULL;
    PRINT '  sync_queue.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.sync_queue SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  sync_queue.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- token_blacklist
    UPDATE dbo.token_blacklist SET created_at = @now WHERE created_at IS NULL;
    PRINT '  token_blacklist.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.token_blacklist SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  token_blacklist.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- users
    UPDATE dbo.users SET created_at = @now WHERE created_at IS NULL;
    PRINT '  users.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.users SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  users.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- work_breaks
    UPDATE dbo.work_breaks SET created_at = @now WHERE created_at IS NULL;
    PRINT '  work_breaks.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.work_breaks SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  work_breaks.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- work_order_coordination_logs
    UPDATE dbo.work_order_coordination_logs SET created_at = @now WHERE created_at IS NULL;
    PRINT '  work_order_coordination_logs.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.work_order_coordination_logs SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  work_order_coordination_logs.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- work_order_statuses
    UPDATE dbo.work_order_statuses SET created_at = @now WHERE created_at IS NULL;
    PRINT '  work_order_statuses.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.work_order_statuses SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  work_order_statuses.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- work_orders
    UPDATE dbo.work_orders SET created_at = @now WHERE created_at IS NULL;
    PRINT '  work_orders.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.work_orders SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  work_orders.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- worklog_segments
    UPDATE dbo.worklog_segments SET created_at = @now WHERE created_at IS NULL;
    PRINT '  worklog_segments.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.worklog_segments SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  worklog_segments.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- worklog_standards
    UPDATE dbo.worklog_standards SET created_at = @now WHERE created_at IS NULL;
    PRINT '  worklog_standards.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.worklog_standards SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  worklog_standards.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- worklog_statuses
    UPDATE dbo.worklog_statuses SET created_at = @now WHERE created_at IS NULL;
    PRINT '  worklog_statuses.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.worklog_statuses SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  worklog_statuses.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    -- worklogs
    UPDATE dbo.worklogs SET created_at = @now WHERE created_at IS NULL;
    PRINT '  worklogs.created_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    UPDATE dbo.worklogs SET updated_at = COALESCE(created_at, @now) WHERE updated_at IS NULL;
    PRINT '  worklogs.updated_at: ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + ' rows';
    
    COMMIT TRANSACTION;
    
    PRINT '';
    PRINT '✅ Migration 02 completed successfully!';
    PRINT 'All created_at and updated_at NULLs have been backfilled.';
    PRINT '';

END TRY
BEGIN CATCH
    ROLLBACK TRANSACTION;
    
    PRINT '';
    PRINT '❌ Migration 02 failed!';
    PRINT 'Error: ' + ERROR_MESSAGE();
    PRINT '';
    
    THROW;
END CATCH

GO
