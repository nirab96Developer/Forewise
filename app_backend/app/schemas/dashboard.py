# src/schemas/dashboard.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
from enum import Enum

class AlertType(str, Enum):
    PROJECT_OVERDUE = "project_overdue"
    EQUIPMENT_MAINTENANCE = "equipment_maintenance"
    SUPPLIER_RESPONSE = "supplier_response"
    BUDGET_EXCEEDED = "budget_exceeded"

class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ActivityType(str, Enum):
    WORK_LOG = "work_log"
    EQUIPMENT_SCAN = "equipment_scan"
    WORK_ORDER = "work_order"
    PROJECT_UPDATE = "project_update"

class DashboardSummaryResponse(BaseModel):
    active_projects_count: int
    avg_progress_pct: float
    hours_month_total: float
    open_alerts_count: int
    can_report_hours: bool
    can_create_order: bool
    can_scan_equipment: bool
    can_open_ticket: bool

class DashboardStatsResponse(BaseModel):
    total_projects: int
    active_projects: int
    completed_projects: int
    pending_work_orders: int
    total_equipment: int
    available_equipment: int
    total_suppliers: int
    active_suppliers: int
    monthly_hours: int
    weekly_hours: int

class DashboardProjectResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    status: str
    priority: str
    progress_percentage: float
    days_remaining: int
    is_overdue: bool
    budget_utilization: float
    team_size: int
    last_activity: str
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    allocated_budget: Optional[float] = None
    spent_budget: Optional[float] = None

class DashboardAlertResponse(BaseModel):
    id: int
    type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    project_id: Optional[int] = None
    work_order_id: Optional[int] = None
    equipment_id: Optional[int] = None
    supplier_id: Optional[int] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    action_required: bool

class DashboardActivityResponse(BaseModel):
    id: int
    type: ActivityType
    title: str
    description: str
    user_name: str
    project_name: Optional[str] = None
    created_at: datetime
    location: Optional[str] = None

class MapProjectData(BaseModel):
    id: int
    name: str
    status: str
    lat: float
    lng: float
    progress: float

class MapEquipmentData(BaseModel):
    id: int
    equipment_number: str
    type: str
    lat: float
    lng: float
    project_name: str

class MapSupplierData(BaseModel):
    id: int
    company_name: str
    lat: float
    lng: float
    active_orders: int

class MapDataResponse(BaseModel):
    projects: List[MapProjectData]
    equipment: List[MapEquipmentData]
    suppliers: List[MapSupplierData]

class HoursDataResponse(BaseModel):
    date: str
    hours: int

class ActiveEquipmentResponse(BaseModel):
    id: int
    equipment_number: str
    equipment_type: str
    project_name: str
    location: str
    status: str
    last_scan: str

class ActiveSupplierResponse(BaseModel):
    id: int
    company_name: str
    contact_person: str
    phone: str
    email: str
    active_orders: int
    last_order_date: str
    rating: float


