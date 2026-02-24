# /root/app_backend/app/schemas/equipment_maintenance.py - חדש
"""Equipment maintenance schemas - Aligned with database model."""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MaintenanceType(str, Enum):
    """Maintenance type enum - matches model."""

    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    EMERGENCY = "emergency"
    INSPECTION = "inspection"
    REPAIR = "repair"
    SERVICE = "service"


class MaintenanceStatus(str, Enum):
    """Maintenance status enum - matches model."""

    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class EquipmentMaintenanceBase(BaseModel):
    """Base equipment maintenance schema."""

    equipment_id: int = Field(..., gt=0, description="Equipment ID")
    maintenance_type: MaintenanceType = Field(..., description="Type of maintenance")

    # Description
    title: str = Field(
        ..., min_length=1, max_length=200, description="Maintenance title"
    )
    description: Optional[str] = Field(None, description="Detailed description")

    # Schedule
    scheduled_date: date = Field(..., description="Scheduled maintenance date")

    # Estimates
    estimated_hours: Optional[int] = Field(
        None, ge=0, description="Estimated work hours"
    )
    estimated_cost: Optional[Decimal] = Field(None, ge=0, description="Estimated cost")

    # Details
    parts_replaced: Optional[str] = Field(
        None, description="Parts replaced during maintenance"
    )
    next_maintenance_date: Optional[date] = Field(
        None, description="Next scheduled maintenance"
    )
    notes: Optional[str] = Field(None, description="Additional notes")

    @field_validator("estimated_cost")
    @classmethod
    def validate_cost(cls, v):
        """Ensure cost is not negative."""
        if v is not None and v < 0:
            raise ValueError("Cost cannot be negative")
        return v


class EquipmentMaintenanceCreate(EquipmentMaintenanceBase):
    """Create equipment maintenance schema."""

    status: MaintenanceStatus = MaintenanceStatus.SCHEDULED


class EquipmentMaintenanceUpdate(BaseModel):
    """Update equipment maintenance schema."""

    maintenance_type: Optional[MaintenanceType] = None
    status: Optional[MaintenanceStatus] = None
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    scheduled_date: Optional[date] = None
    start_date: Optional[date] = None
    completion_date: Optional[date] = None
    estimated_hours: Optional[int] = Field(None, ge=0)
    actual_hours: Optional[int] = Field(None, ge=0)
    estimated_cost: Optional[Decimal] = Field(None, ge=0)
    actual_cost: Optional[Decimal] = Field(None, ge=0)
    performed_by_id: Optional[int] = Field(None, gt=0)
    parts_replaced: Optional[str] = None
    next_maintenance_date: Optional[date] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class EquipmentMaintenanceResponse(EquipmentMaintenanceBase):
    """Equipment maintenance response schema."""

    id: int
    status: MaintenanceStatus

    # Actual tracking
    start_date: Optional[date] = None
    completion_date: Optional[date] = None
    actual_hours: int = 0
    actual_cost: Decimal = Decimal("0")

    # Performed by
    performed_by_id: Optional[int] = None

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    # Computed properties
    is_overdue: bool = False
    is_completed: bool = False
    duration_days: Optional[int] = None

    # From relationships
    equipment_name: Optional[str] = None
    equipment_code: Optional[str] = None
    performed_by_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context):
        """Calculate computed fields."""
        self.is_overdue = (
            date.today() > self.scheduled_date
            and self.status == MaintenanceStatus.SCHEDULED
        )
        self.is_completed = self.status == MaintenanceStatus.COMPLETED
        if self.start_date and self.completion_date:
            self.duration_days = (self.completion_date - self.start_date).days


class EquipmentMaintenanceFilter(BaseModel):
    """Filter for equipment maintenance."""

    equipment_id: Optional[int] = None
    equipment_ids: Optional[List[int]] = None
    maintenance_type: Optional[MaintenanceType] = None
    maintenance_types: Optional[List[MaintenanceType]] = None
    status: Optional[MaintenanceStatus] = None
    statuses: Optional[List[MaintenanceStatus]] = None
    performed_by_id: Optional[int] = None
    scheduled_date_from: Optional[date] = None
    scheduled_date_to: Optional[date] = None
    is_overdue: Optional[bool] = None
    is_completed: Optional[bool] = None
    min_cost: Optional[Decimal] = None
    max_cost: Optional[Decimal] = None


class EquipmentMaintenanceSummary(BaseModel):
    """Equipment maintenance summary statistics."""

    total_maintenance: int = 0

    # By status
    scheduled_count: int = 0
    in_progress_count: int = 0
    completed_count: int = 0
    cancelled_count: int = 0
    overdue_count: int = 0

    # By type
    by_type: dict = Field(default_factory=dict)

    # Costs
    total_estimated_cost: Decimal = Decimal("0")
    total_actual_cost: Decimal = Decimal("0")
    cost_variance: Decimal = Decimal("0")

    # Hours
    total_estimated_hours: int = 0
    total_actual_hours: int = 0

    # Metrics
    average_duration_days: float = 0.0
    completion_rate: float = 0.0


# Alias for compatibility
MaintenanceCreate = EquipmentMaintenanceCreate
MaintenanceUpdate = EquipmentMaintenanceUpdate
MaintenanceResponse = EquipmentMaintenanceResponse