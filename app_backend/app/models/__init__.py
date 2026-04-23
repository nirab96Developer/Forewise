# app/models/__init__.py
"""
CRITICAL: The order of imports matters!
This file resolves all circular dependencies by importing models in the correct order.
"""

# Step 1: Import base
from app.models.base import Base, BaseModel, AuditMixin, TimestampMixin, metadata

# Step 2: Import ALL models (this creates the classes and registers tables in
# Base.metadata so Alembic autogenerate, create_all() and FK resolution all
# work. Lazy imports inside service code are NOT enough — they only register
# the table after the first request hits that code path, which breaks
# `alembic check` and any greenfield bootstrap.)
import app.models.user
import app.models.project
import app.models.project_assignment
import app.models.permission
import app.models.activity_log
import app.models.activity_type
import app.models.audit_log
import app.models.role
import app.models.role_permission
import app.models.role_assignment
import app.models.session
import app.models.otp_token
import app.models.device_token
import app.models.token_blacklist
import app.models.biometric_credential
import app.models.notification
import app.models.region
import app.models.area
import app.models.department
import app.models.location
import app.models.forest
import app.models.file
import app.models.milestone
import app.models.report
import app.models.report_run
import app.models.support_ticket
import app.models.support_ticket_comment
import app.models.sync_queue
import app.models.daily_work_report
import app.models.supplier
import app.models.supplier_equipment
import app.models.supplier_invitation
import app.models.supplier_constraint_log  # before supplier_constraint_reason
import app.models.supplier_constraint_reason
import app.models.supplier_rejection_reason
import app.models.supplier_rotation
import app.models.equipment_category  # referenced by equipment_models.category_id FK
import app.models.equipment_type
import app.models.equipment_model
import app.models.equipment
import app.models.equipment_assignment
import app.models.equipment_maintenance
import app.models.equipment_scan
import app.models.system_rate
import app.models.work_order_coordination_log  # before work_order
import app.models.work_order
import app.models.worklog_segment  # before worklog
import app.models.worklog
import app.models.invoice
import app.models.invoice_item
import app.models.invoice_payment
import app.models.invoice_work_order  # N:N invoice ↔ work_order
import app.models.budget
import app.models.budget_item  # after budget
import app.models.budget_commitment  # after budget, work_order, invoice
import app.models.budget_transfer
import app.models.balance_release

# Step 3: NOW import the actual classes for use
from app.models.user import User
from app.models.project import Project
from app.models.project_assignment import ProjectAssignment
from app.models.permission import Permission
from app.models.activity_log import ActivityLog
from app.models.activity_type import ActivityType
from app.models.audit_log import AuditLog
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.role_assignment import RoleAssignment
from app.models.session import Session
from app.models.otp_token import OTPToken
from app.models.device_token import DeviceToken
from app.models.token_blacklist import TokenBlacklist
from app.models.biometric_credential import BiometricCredential
from app.models.notification import Notification
from app.models.region import Region
from app.models.area import Area
from app.models.department import Department
from app.models.location import Location
from app.models.forest import Forest
from app.models.file import File
from app.models.milestone import Milestone
from app.models.report import Report
from app.models.report_run import ReportRun
from app.models.support_ticket import SupportTicket
from app.models.support_ticket_comment import SupportTicketComment
from app.models.sync_queue import SyncQueue
from app.models.daily_work_report import DailyWorkReport
from app.models.supplier import Supplier
from app.models.supplier_equipment import SupplierEquipment
from app.models.supplier_invitation import SupplierInvitation
from app.models.supplier_constraint_log import SupplierConstraintLog
from app.models.supplier_constraint_reason import SupplierConstraintReason
from app.models.supplier_rejection_reason import SupplierRejectionReason
from app.models.supplier_rotation import SupplierRotation
from app.models.equipment_category import EquipmentCategory
from app.models.equipment_type import EquipmentType
from app.models.equipment_model import EquipmentModel
from app.models.equipment import Equipment
from app.models.equipment_assignment import EquipmentAssignment
from app.models.equipment_maintenance import EquipmentMaintenance
from app.models.equipment_scan import EquipmentScan
from app.models.system_rate import SystemRate
from app.models.work_order_coordination_log import WorkOrderCoordinationLog
from app.models.work_order import WorkOrder
from app.models.worklog_segment import WorklogSegment
from app.models.worklog import Worklog
from app.models.worklog_status import WorklogStatus
from app.models.work_order_status import WorkOrderStatus
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.invoice_payment import InvoicePayment
from app.models.invoice_work_order import InvoiceWorkOrder
from app.models.budget import Budget
from app.models.budget_item import BudgetItem
from app.models.budget_commitment import BudgetCommitment
from app.models.budget_transfer import BudgetTransfer
from app.models.balance_release import BalanceRelease

# Step 4: Export everything
__all__ = [
    # Base
    'Base', 'BaseModel', 'AuditMixin', 'TimestampMixin', 'metadata',
    # Identity / Auth
    'User', 'Permission', 'Role', 'RolePermission', 'RoleAssignment',
    'Session', 'OTPToken', 'DeviceToken', 'TokenBlacklist',
    'BiometricCredential', 'Notification',
    # Org / Geo
    'Region', 'Area', 'Department', 'Location', 'Forest',
    'Project', 'ProjectAssignment',
    # Supplier domain
    'Supplier', 'SupplierEquipment', 'SupplierInvitation',
    'SupplierRotation', 'SupplierConstraintLog', 'SupplierConstraintReason',
    'SupplierRejectionReason',
    # Equipment domain
    'EquipmentCategory', 'EquipmentType', 'EquipmentModel', 'Equipment',
    'EquipmentAssignment', 'EquipmentMaintenance', 'EquipmentScan',
    # Work execution
    'WorkOrder', 'WorkOrderCoordinationLog', 'WorkOrderStatus',
    'Worklog', 'WorklogSegment', 'WorklogStatus',
    'ActivityLog', 'ActivityType', 'AuditLog', 'DailyWorkReport',
    # Financial
    'SystemRate',
    'Budget', 'BudgetItem', 'BudgetCommitment', 'BudgetTransfer',
    'BalanceRelease',
    'Invoice', 'InvoiceItem', 'InvoicePayment', 'InvoiceWorkOrder',
    # Misc
    'File', 'Milestone', 'Report', 'ReportRun',
    'SupportTicket', 'SupportTicketComment', 'SyncQueue',
]