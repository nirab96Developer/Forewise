# app/services/__init__.py
"""Services module initialization."""

from app.services.activity_log_service import ActivityLogService
from app.services.area_service import AreaService
# Auth and User Services
from app.services.auth_service import AuthService
from app.services.balance_release_service import BalanceReleaseService
from app.services.budget_service import BudgetService
# System Services
from app.services.calendar_service import CalendarService
from app.services.daily_report_service import DailyReportService
from app.services.equipment_assignment_service import \
    EquipmentAssignmentService
from app.services.equipment_maintenance_service import \
    EquipmentMaintenanceService
from app.services.equipment_scan_service import EquipmentScanService
# Equipment Services
from app.services.equipment_service import EquipmentService
from app.services.file_service import FileService
# Financial Services
# from app.services.invoice_service import InvoiceService
from app.services.location_service import LocationService
from app.services.milestone_service import MilestoneService
# Support Services
from app.services.notification_service import NotificationService
# from app.services.payment_service import PaymentService
from app.services.permission_service import PermissionService
from app.services.project_assignment_service import ProjectAssignmentService
# Project Services
from app.services.project_service import ProjectService
# Organization Services
from app.services.region_service import RegionService
from app.services.report_service import ReportService
from app.services.role_service import RoleService
from app.services.supplier_rotation_service import SupplierRotationService
# Supplier Services
from app.services.supplier_service import SupplierService
from app.services.support_ticket_service import SupportTicketService
# from app.services.system_schedule_service import SystemScheduleService
from app.services.user_service import UserService
from app.services.work_order_service import WorkOrderService
# Worklog and Reporting Services
from app.services.worklog_service import WorklogService

__all__ = [
    # Auth and User
    "AuthService",
    "UserService",
    "RoleService",
    "PermissionService",
    # Organization
    "RegionService",
    "AreaService",
    "LocationService",
    # Project
    "ProjectService",
    "ProjectAssignmentService",
    "MilestoneService",
    # Equipment
    "EquipmentService",
    "EquipmentAssignmentService",
    "EquipmentScanService",
    "EquipmentMaintenanceService",
    # Supplier
    "SupplierService",
    "SupplierRotationService",
    "WorkOrderService",
    # Worklog and Reporting
    "WorklogService",
    "DailyReportService",
    "ReportService",
    # Financial
    "InvoiceService",
    "PaymentService",
    "BudgetService",
    "BalanceReleaseService",
    # Support
    "NotificationService",
    "SupportTicketService",
    "FileService",
    "ActivityLogService",
    # System
    "CalendarService",
    "SystemScheduleService",
]


# Service instances factory
def get_service(service_name: str):
    """Get service instance by name."""
    service_map = {
        "auth": AuthService,
        "user": UserService,
        "role": RoleService,
        "permission": PermissionService,
        "region": RegionService,
        "area": AreaService,
        "location": LocationService,
        "project": ProjectService,
        "project_assignment": ProjectAssignmentService,
        "milestone": MilestoneService,
        "equipment": EquipmentService,
        "equipment_assignment": EquipmentAssignmentService,
        "equipment_scan": EquipmentScanService,
        "equipment_maintenance": EquipmentMaintenanceService,
        "supplier": SupplierService,
        "supplier_rotation": SupplierRotationService,
        "work_order": WorkOrderService,
        "worklog": WorklogService,
        "daily_report": DailyReportService,
        "report": ReportService,
        "invoice": InvoiceService,
        "payment": PaymentService,
        "budget": BudgetService,
        "balance_release": BalanceReleaseService,
        "notification": NotificationService,
        "support_ticket": SupportTicketService,
        "file": FileService,
        "activity_log": ActivityLogService,
        "calendar": CalendarService,
        # "system_schedule": SystemScheduleService,
    }

    service_class = service_map.get(service_name)
    if not service_class:
        raise ValueError(f"Service '{service_name}' not found")

    return service_class()


# Dependency injection helpers
class ServiceContainer:
    """Service container for dependency injection."""

    _instances = {}

    @classmethod
    def get(cls, service_class):
        """Get or create service instance."""
        if service_class not in cls._instances:
            cls._instances[service_class] = service_class()
        return cls._instances[service_class]

    @classmethod
    def reset(cls):
        """Reset all service instances."""
        cls._instances.clear()


# Version info
__version__ = "1.0.0"
