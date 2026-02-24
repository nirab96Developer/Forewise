"""Maintenance schemas - Aligned with database model."""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel as PydanticBaseModel, ConfigDict, Field, field_validator


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


class MaintenanceBase(PydanticBaseModel):
    """Base maintenance schema."""
    
    model_config = ConfigDict(from_attributes=True)

    equipment_id: int = Field(..., gt=0, description="Equipment ID")
    maintenance_type: MaintenanceType = Field(..., description="Type of maintenance")
    title: str = Field(..., min_length=1, max_length=200, description="Maintenance title")
    description: Optional[str] = Field(None, description="Detailed description")
    scheduled_date: date = Field(..., description="Scheduled maintenance date")
    estimated_hours: Optional[int] = Field(None, ge=0, description="Estimated work hours")
    estimated_cost: Optional[Decimal] = Field(None, ge=0, description="Estimated cost")
    priority: int = Field(1, ge=1, le=5, description="Priority level (1-5)")
    status: MaintenanceStatus = Field(MaintenanceStatus.SCHEDULED, description="Maintenance status")

    @field_validator("scheduled_date")
    @classmethod
    def validate_scheduled_date(cls, v):
        """Validate scheduled date."""
        if v < date.today():
            raise ValueError("Scheduled date cannot be in the past")
        return v


class MaintenanceCreate(MaintenanceBase):
    """Create maintenance schema."""

    assigned_to_id: int = Field(..., gt=0, description="User assigned to maintenance")
    created_by_id: int = Field(..., gt=0, description="User who created maintenance")


class MaintenanceUpdate(PydanticBaseModel):
    """Update maintenance schema."""
    
    model_config = ConfigDict(from_attributes=True)

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    scheduled_date: Optional[date] = None
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    estimated_hours: Optional[int] = Field(None, ge=0)
    actual_hours: Optional[int] = Field(None, ge=0)
    estimated_cost: Optional[Decimal] = Field(None, ge=0)
    actual_cost: Optional[Decimal] = Field(None, ge=0)
    priority: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[MaintenanceStatus] = None
    notes: Optional[str] = Field(None, max_length=1000)
    assigned_to_id: Optional[int] = Field(None, gt=0)

    @field_validator("scheduled_date")
    @classmethod
    def validate_scheduled_date(cls, v):
        """Validate scheduled date."""
        if v is not None and v < date.today():
            raise ValueError("Scheduled date cannot be in the past")
        return v


class MaintenanceResponse(MaintenanceBase):
    """Maintenance response schema."""

    id: int
    assigned_to_id: int
    created_by_id: int
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    actual_hours: Optional[int] = None
    actual_cost: Optional[Decimal] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # From relationships
    equipment_name: Optional[str] = None
    assigned_to_name: Optional[str] = None
    created_by_name: Optional[str] = None


class MaintenanceStatistics(PydanticBaseModel):
    """Maintenance statistics schema."""

    total_maintenance: int = 0
    scheduled_maintenance: int = 0
    in_progress_maintenance: int = 0
    completed_maintenance: int = 0
    overdue_maintenance: int = 0

    # By type
    by_type: dict = Field(default_factory=dict)

    # By status
    by_status: dict = Field(default_factory=dict)

    # Costs
    total_estimated_cost: Decimal = Decimal("0")
    total_actual_cost: Decimal = Decimal("0")

    # Hours
    total_estimated_hours: int = 0
    total_actual_hours: int = 0

    # Metrics
    average_duration_days: float = 0.0
    completion_rate: float = 0.0


class MaintenanceCost(PydanticBaseModel):
    """Maintenance cost schema."""
    
    model_config = ConfigDict(from_attributes=True)

    maintenance_id: int
    cost_type: str  # labor, parts, materials, etc.
    description: str
    amount: Decimal
    quantity: Optional[int] = 1
    unit_cost: Optional[Decimal] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MaintenanceHistory(PydanticBaseModel):
    """Maintenance history schema."""
    
    model_config = ConfigDict(from_attributes=True)

    maintenance_id: int
    action: str  # created, updated, completed, cancelled, etc.
    description: str
    performed_by_id: int
    performed_at: datetime = Field(default_factory=datetime.utcnow)
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None


class MaintenanceSchedule(PydanticBaseModel):
    """Maintenance schedule schema."""

    model_config = ConfigDict(from_attributes=True)

    equipment_id: int
    maintenance_type: MaintenanceType
    frequency_days: int = Field(..., ge=1, description="Frequency in days")
    next_due_date: date
    is_active: bool = True
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
