# app/models/__init__.py
"""
CRITICAL: The order of imports matters!
This file resolves all circular dependencies by importing models in the correct order.
"""

# Step 1: Import base
from app.models.base import Base, BaseModel, AuditMixin, TimestampMixin, metadata

# Step 2: Import ALL models (this creates the classes)
# Import them but don't use them yet
import app.models.user
import app.models.project  
import app.models.permission
import app.models.activity_log
import app.models.role
import app.models.role_permission
import app.models.role_assignment
import app.models.session
import app.models.otp_token
import app.models.device_token
import app.models.region
import app.models.area
import app.models.department
import app.models.location
import app.models.supplier
import app.models.supplier_equipment
import app.models.equipment
import app.models.equipment_model
import app.models.equipment_type
import app.models.system_rate
import app.models.pricing_override
import app.models.activity_type
import app.models.work_order_coordination_log  # Must be imported before work_order
import app.models.work_order
import app.models.worklog_segment  # Must be before worklog
import app.models.worklog
import app.models.invoice
import app.models.supplier_constraint_log  # Must be imported before supplier_constraint_reason
import app.models.supplier_constraint_reason
import app.models.supplier_rejection_reason
import app.models.budget_item  # After budget
import app.models.budget_transfer
import app.models.supplier_invitation  # Fair rotation invitations
import app.models.forest  # PostGIS forest polygons
import app.models.project_assignment  # Project user assignments

# Step 3: NOW import the actual classes for use
from app.models.user import User
from app.models.project import Project
from app.models.permission import Permission
from app.models.activity_log import ActivityLog
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.role_assignment import RoleAssignment
from app.models.session import Session
from app.models.otp_token import OTPToken
from app.models.device_token import DeviceToken
from app.models.region import Region
from app.models.area import Area
from app.models.department import Department
from app.models.location import Location
from app.models.supplier import Supplier
from app.models.supplier_equipment import SupplierEquipment
from app.models.equipment import Equipment
from app.models.equipment_model import EquipmentModel
from app.models.equipment_type import EquipmentType
from app.models.system_rate import SystemRate
from app.models.pricing_override import PricingOverride
from app.models.activity_type import ActivityType
from app.models.work_order_coordination_log import WorkOrderCoordinationLog
from app.models.work_order import WorkOrder
from app.models.worklog_segment import WorklogSegment
from app.models.worklog import Worklog
from app.models.worklog_status import WorklogStatus
from app.models.work_order_status import WorkOrderStatus
from app.models.budget import Budget
from app.models.budget_item import BudgetItem
from app.models.invoice import Invoice
from app.models.supplier_constraint_log import SupplierConstraintLog  # Must be imported before SupplierConstraintReason
from app.models.supplier_constraint_reason import SupplierConstraintReason
from app.models.supplier_rejection_reason import SupplierRejectionReason
from app.models.supplier_invitation import SupplierInvitation
from app.models.forest import Forest
from app.models.project_assignment import ProjectAssignment

# Step 4: Export everything
__all__ = [
    'Base',
    'BaseModel',
    'AuditMixin',
    'TimestampMixin',
    'metadata',
    'User',
    'Project',
    'Permission',
    'ActivityLog',
    'Role',
    'RolePermission',
    'RoleAssignment',
    'Session',
    'OTPToken',
    'Region',
    'Area',
    'Department',
    'Location',
    'Supplier',
    'Equipment',
    'EquipmentModel',
    'EquipmentType',
    'SystemRate',
    'PricingOverride',
    'ActivityType',
    'WorkOrderCoordinationLog',
    'WorkOrder',
    'WorklogSegment',
    'Worklog',
    'WorklogStatus',
    'WorkOrderStatus',
    'Budget',
    'BudgetItem',
    'Invoice',
    'SupplierConstraintReason',
    'SupplierConstraintLog',
    'SupplierRejectionReason',
    'SupplierInvitation',
    'Forest',
    'ProjectAssignment',
]