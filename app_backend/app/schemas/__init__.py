# app/schemas/__init__.py
"""Schemas package - All Pydantic schemas."""

# Auth & Token
from .auth import *
from .token import *
from .session import *
from .otp_token import *
from .token_blacklist import *

# User & Permissions
from .user import *
from .role import *
from .permission import *
from .role_permission import *

# Organization
from .region import *
from .area import *
from .department import *
from .location import *

# Projects
from .project import *
from .project_assignment import *
from .project_document import *
from .milestone import *

# Budget
from .budget import *
from .budget_item import *
from .budget_allocation import *
from .budget_transfer import *
from .balance_release import *

# Equipment
from .equipment import *
from .equipment_category import *
from .equipment_assignment import *
from .equipment_scan import *
from .equipment_maintenance import *

# Suppliers
from .supplier import *
from .supplier_rotation import *
from .supplier_constraint_log import *

# Work Management
from .work_order import *
from .work_report import *
from .worklog import *
from .worklog_segment import *
from .work_break import *
from .daily_work_report import *

# Finance - Temporarily commented out due to circular imports
# from .invoice import *
# from .invoice_item import *
# from .invoice_payment import *

# Support
from .support_ticket import *
from .support_ticket_comment import *

# Common
from .base import *
from .common import *
from .file import *
from .notification import *
from .system_message import *

# Reports & Scheduling
from .report import *
from .report_run import *
from .report_run_summary import *
# from .system_schedule import *
# from .system_schedule_run import *

# Audit
from .audit_log import *
from .activity_log import *

__version__ = "1.0.0"
