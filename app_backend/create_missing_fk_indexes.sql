-- ============================================================================
-- יצירת אינדקסים חסרים ל-Foreign Keys
-- נוצר אוטומטית מתוך db_integrity_report.json
-- ============================================================================
-- התחלת טרנזקציה
BEGIN TRANSACTION;

-- Areas
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.areas') AND name = 'IX_areas_manager_id')
    CREATE NONCLUSTERED INDEX IX_areas_manager_id ON dbo.areas(manager_id);

-- Balance Releases  
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.balance_releases') AND name = 'IX_balance_releases_approved_by')
    CREATE NONCLUSTERED INDEX IX_balance_releases_approved_by ON dbo.balance_releases(approved_by);

-- Budget Allocations
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.budget_allocations') AND name = 'IX_budget_allocations_approved_by')
    CREATE NONCLUSTERED INDEX IX_budget_allocations_approved_by ON dbo.budget_allocations(approved_by);

-- Budget Transfers
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.budget_transfers') AND name = 'IX_budget_transfers_approved_by')
    CREATE NONCLUSTERED INDEX IX_budget_transfers_approved_by ON dbo.budget_transfers(approved_by);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.budget_transfers') AND name = 'IX_budget_transfers_requested_by')
    CREATE NONCLUSTERED INDEX IX_budget_transfers_requested_by ON dbo.budget_transfers(requested_by);

-- Budgets
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.budgets') AND name = 'IX_budgets_created_by')
    CREATE NONCLUSTERED INDEX IX_budgets_created_by ON dbo.budgets(created_by);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.budgets') AND name = 'IX_budgets_parent_budget_id')
    CREATE NONCLUSTERED INDEX IX_budgets_parent_budget_id ON dbo.budgets(parent_budget_id);

-- Conflict Logs
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.conflict_logs') AND name = 'IX_conflict_logs_resolved_by_id')
    CREATE NONCLUSTERED INDEX IX_conflict_logs_resolved_by_id ON dbo.conflict_logs(resolved_by_id);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.conflict_logs') AND name = 'IX_conflict_logs_sync_queue_id')
    CREATE NONCLUSTERED INDEX IX_conflict_logs_sync_queue_id ON dbo.conflict_logs(sync_queue_id);

-- Departments
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.departments') AND name = 'IX_departments_manager_id')
    CREATE NONCLUSTERED INDEX IX_departments_manager_id ON dbo.departments(manager_id);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.departments') AND name = 'IX_departments_parent_department_id')
    CREATE NONCLUSTERED INDEX IX_departments_parent_department_id ON dbo.departments(parent_department_id);

-- Equipment
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.equipment') AND name = 'IX_equipment_type_id')
    CREATE NONCLUSTERED INDEX IX_equipment_type_id ON dbo.equipment(type_id);

-- Equipment Assignments
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.equipment_assignments') AND name = 'IX_equipment_assignments_assigned_by')
    CREATE NONCLUSTERED INDEX IX_equipment_assignments_assigned_by ON dbo.equipment_assignments(assigned_by);

-- Equipment Maintenance
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.equipment_maintenance') AND name = 'IX_equipment_maintenance_performed_by')
    CREATE NONCLUSTERED INDEX IX_equipment_maintenance_performed_by ON dbo.equipment_maintenance(performed_by);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.equipment_maintenance') AND name = 'IX_equipment_maintenance_scheduled_by')
    CREATE NONCLUSTERED INDEX IX_equipment_maintenance_scheduled_by ON dbo.equipment_maintenance(scheduled_by);

-- Equipment Scans
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.equipment_scans') AND name = 'IX_equipment_scans_location_id')
    CREATE NONCLUSTERED INDEX IX_equipment_scans_location_id ON dbo.equipment_scans(location_id);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.equipment_scans') AND name = 'IX_equipment_scans_work_order_id')
    CREATE NONCLUSTERED INDEX IX_equipment_scans_work_order_id ON dbo.equipment_scans(work_order_id);

-- Files
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.files') AND name = 'IX_files_uploaded_by')
    CREATE NONCLUSTERED INDEX IX_files_uploaded_by ON dbo.files(uploaded_by);

-- Invoice Payments
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.invoice_payments') AND name = 'IX_invoice_payments_processed_by')
    CREATE NONCLUSTERED INDEX IX_invoice_payments_processed_by ON dbo.invoice_payments(processed_by);

-- Invoices
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.invoices') AND name = 'IX_invoices_created_by')
    CREATE NONCLUSTERED INDEX IX_invoices_created_by ON dbo.invoices(created_by);

-- Locations
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.locations') AND name = 'IX_locations_area_id')
    CREATE NONCLUSTERED INDEX IX_locations_area_id ON dbo.locations(area_id);

-- Milestones
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.milestones') AND name = 'IX_milestones_assigned_to')
    CREATE NONCLUSTERED INDEX IX_milestones_assigned_to ON dbo.milestones(assigned_to);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.milestones') AND name = 'IX_milestones_depends_on_milestone_id')
    CREATE NONCLUSTERED INDEX IX_milestones_depends_on_milestone_id ON dbo.milestones(depends_on_milestone_id);

-- OTP Tokens
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.otp_tokens') AND name = 'IX_otp_tokens_user_id')
    CREATE NONCLUSTERED INDEX IX_otp_tokens_user_id ON dbo.otp_tokens(user_id);

-- Project Assignments
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.project_assignments') AND name = 'IX_project_assignments_approved_by_id')
    CREATE NONCLUSTERED INDEX IX_project_assignments_approved_by_id ON dbo.project_assignments(approved_by_id);

-- Project Documents
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.project_documents') AND name = 'IX_project_documents_approved_by')
    CREATE NONCLUSTERED INDEX IX_project_documents_approved_by ON dbo.project_documents(approved_by);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.project_documents') AND name = 'IX_project_documents_file_id')
    CREATE NONCLUSTERED INDEX IX_project_documents_file_id ON dbo.project_documents(file_id);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.project_documents') AND name = 'IX_project_documents_uploaded_by')
    CREATE NONCLUSTERED INDEX IX_project_documents_uploaded_by ON dbo.project_documents(uploaded_by);

-- Regions
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.regions') AND name = 'IX_regions_manager_id')
    CREATE NONCLUSTERED INDEX IX_regions_manager_id ON dbo.regions(manager_id);

-- Report Runs
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.report_runs') AND name = 'IX_report_runs_parent_run_id')
    CREATE NONCLUSTERED INDEX IX_report_runs_parent_run_id ON dbo.report_runs(parent_run_id);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.report_runs') AND name = 'IX_report_runs_triggered_by_id')
    CREATE NONCLUSTERED INDEX IX_report_runs_triggered_by_id ON dbo.report_runs(triggered_by_id);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.report_runs') AND name = 'IX_report_runs_run_by')
    CREATE NONCLUSTERED INDEX IX_report_runs_run_by ON dbo.report_runs(run_by);

-- Reports
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.reports') AND name = 'IX_reports_created_by_id')
    CREATE NONCLUSTERED INDEX IX_reports_created_by_id ON dbo.reports(created_by_id);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.reports') AND name = 'IX_reports_owner_id')
    CREATE NONCLUSTERED INDEX IX_reports_owner_id ON dbo.reports(owner_id);

-- Role Assignments
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.role_assignments') AND name = 'IX_role_assignments_assigned_by')
    CREATE NONCLUSTERED INDEX IX_role_assignments_assigned_by ON dbo.role_assignments(assigned_by);

-- Supplier Constraint Logs
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.supplier_constraint_logs') AND name = 'IX_supplier_constraint_logs_approved_by')
    CREATE NONCLUSTERED INDEX IX_supplier_constraint_logs_approved_by ON dbo.supplier_constraint_logs(approved_by);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.supplier_constraint_logs') AND name = 'IX_supplier_constraint_logs_created_by')
    CREATE NONCLUSTERED INDEX IX_supplier_constraint_logs_created_by ON dbo.supplier_constraint_logs(created_by);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.supplier_constraint_logs') AND name = 'IX_supplier_constraint_logs_constraint_reason_id')
    CREATE NONCLUSTERED INDEX IX_supplier_constraint_logs_constraint_reason_id ON dbo.supplier_constraint_logs(constraint_reason_id);

-- Supplier Rotation Queue
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.supplier_rotation_queue') AND name = 'IX_supplier_rotation_queue_area_id')
    CREATE NONCLUSTERED INDEX IX_supplier_rotation_queue_area_id ON dbo.supplier_rotation_queue(area_id);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.supplier_rotation_queue') AND name = 'IX_supplier_rotation_queue_equipment_category_id')
    CREATE NONCLUSTERED INDEX IX_supplier_rotation_queue_equipment_category_id ON dbo.supplier_rotation_queue(equipment_category_id);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.supplier_rotation_queue') AND name = 'IX_supplier_rotation_queue_supplier_id')
    CREATE NONCLUSTERED INDEX IX_supplier_rotation_queue_supplier_id ON dbo.supplier_rotation_queue(supplier_id);

-- Support Tickets
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.support_tickets') AND name = 'IX_support_tickets_created_by_id')
    CREATE NONCLUSTERED INDEX IX_support_tickets_created_by_id ON dbo.support_tickets(created_by_id);

-- System Messages
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.system_messages') AND name = 'IX_system_messages_created_by')
    CREATE NONCLUSTERED INDEX IX_system_messages_created_by ON dbo.system_messages(created_by);

-- System Schedules
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.system_schedules') AND name = 'IX_system_schedules_created_by')
    CREATE NONCLUSTERED INDEX IX_system_schedules_created_by ON dbo.system_schedules(created_by);

-- Token Blacklist
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.token_blacklist') AND name = 'IX_token_blacklist_blacklisted_by_id')
    CREATE NONCLUSTERED INDEX IX_token_blacklist_blacklisted_by_id ON dbo.token_blacklist(blacklisted_by_id);

-- Users
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.users') AND name = 'IX_users_manager_id')
    CREATE NONCLUSTERED INDEX IX_users_manager_id ON dbo.users(manager_id);

-- Work Order Coordination Logs
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.work_order_coordination_logs') AND name = 'IX_work_order_coordination_logs_new_supplier_id')
    CREATE NONCLUSTERED INDEX IX_work_order_coordination_logs_new_supplier_id ON dbo.work_order_coordination_logs(new_supplier_id);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.work_order_coordination_logs') AND name = 'IX_work_order_coordination_logs_previous_supplier_id')
    CREATE NONCLUSTERED INDEX IX_work_order_coordination_logs_previous_supplier_id ON dbo.work_order_coordination_logs(previous_supplier_id);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.work_order_coordination_logs') AND name = 'IX_work_order_coordination_logs_created_by_user_id')
    CREATE NONCLUSTERED INDEX IX_work_order_coordination_logs_created_by_user_id ON dbo.work_order_coordination_logs(created_by_user_id);

-- Work Orders
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.work_orders') AND name = 'IX_work_orders_constraint_reason_id')
    CREATE NONCLUSTERED INDEX IX_work_orders_constraint_reason_id ON dbo.work_orders(constraint_reason_id);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.work_orders') AND name = 'IX_work_orders_rejection_reason_id')
    CREATE NONCLUSTERED INDEX IX_work_orders_rejection_reason_id ON dbo.work_orders(rejection_reason_id);

-- Worklog Segments
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.worklog_segments') AND name = 'IX_worklog_segments_worklog_id')
    CREATE NONCLUSTERED INDEX IX_worklog_segments_worklog_id ON dbo.worklog_segments(worklog_id);

-- Worklogs
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.worklogs') AND name = 'IX_worklogs_activity_type_id')
    CREATE NONCLUSTERED INDEX IX_worklogs_activity_type_id ON dbo.worklogs(activity_type_id);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.worklogs') AND name = 'IX_worklogs_equipment_id')
    CREATE NONCLUSTERED INDEX IX_worklogs_equipment_id ON dbo.worklogs(equipment_id);

-- Commit
COMMIT TRANSACTION;

PRINT 'הושלמה יצירת אינדקסים חסרים ל-Foreign Keys!';

