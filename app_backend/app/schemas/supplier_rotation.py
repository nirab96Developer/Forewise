# /root/app_backend/app/schemas/supplier_rotation.py - חדש
"""Supplier rotation schemas - Aligned with database model."""
from datetime import date, datetime
from enum import Enum
from typing import Optional, List, Dict

from pydantic import BaseModel, ConfigDict, Field


class RotationStatus(str, Enum):
    """Rotation status - matches model."""

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class SupplierRotationBase(BaseModel):
    """Base supplier rotation schema."""

    supplier_id: int = Field(..., gt=0, description="Supplier ID")

    # Rotation details
    rotation_date: date = Field(..., description="Rotation date")
    priority: int = Field(1, ge=1, le=100, description="Priority level")
    sequence_number: int = Field(0, ge=0, description="Sequence number")

    # Equipment type
    equipment_type: Optional[str] = Field(
        None, max_length=50, description="Equipment type"
    )

    # Additional
    notes: Optional[str] = Field(None, description="Notes")


class SupplierRotationCreate(SupplierRotationBase):
    """Create supplier rotation schema."""

    status: RotationStatus = RotationStatus.PENDING


class SupplierRotationUpdate(BaseModel):
    """Update supplier rotation schema."""

    rotation_date: Optional[date] = None
    priority: Optional[int] = Field(None, ge=1, le=100)
    sequence_number: Optional[int] = Field(None, ge=0)
    status: Optional[RotationStatus] = None
    equipment_type: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierRotationResponse(SupplierRotationBase):
    """Supplier rotation response schema."""

    id: int
    status: RotationStatus

    # Usage tracking
    last_used_date: Optional[date] = None
    usage_count: int = 0
    skip_count: int = 0

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    # Computed
    days_since_last_use: Optional[int] = None
    is_available: bool = False

    # From relationships
    supplier_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context):
        """Calculate computed fields."""
        if self.last_used_date:
            self.days_since_last_use = (date.today() - self.last_used_date).days
        self.is_available = self.is_active and self.status == RotationStatus.PENDING


class SupplierRotationFilter(BaseModel):
    """Filter for supplier rotations."""

    supplier_id: Optional[int] = None
    status: Optional[RotationStatus] = None
    statuses: Optional[List[RotationStatus]] = None
    equipment_type: Optional[str] = None
    min_priority: Optional[int] = None
    max_priority: Optional[int] = None
    is_available: Optional[bool] = None


# Alias for compatibility
RotationCreate = SupplierRotationCreate
RotationResponse = SupplierRotationResponse
RotationUpdate = SupplierRotationUpdate


class RotationHistory(BaseModel):
    """Rotation history schema."""
    
    id: int
    supplier_id: int
    rotation_date: date
    status: RotationStatus
    equipment_type: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    
    # From relationships
    supplier_name: Optional[str] = None


class RotationQueueResponse(BaseModel):
    """Rotation queue response schema."""
    
    queue_id: int
    supplier_id: int
    supplier_name: Optional[str] = None
    equipment_type: Optional[str] = None
    priority: int
    sequence_number: int
    estimated_date: Optional[date] = None
    status: RotationStatus
    notes: Optional[str] = None
    
    # Statistics
    days_in_queue: int = 0
    usage_count: int = 0
    last_used_date: Optional[date] = None
    
    # Computed
    is_available: bool = False
    is_overdue: bool = False


class RotationStatistics(BaseModel):
    """Rotation statistics schema."""
    
    total_rotations: int = 0
    active_rotations: int = 0
    completed_rotations: int = 0
    overdue_rotations: int = 0
    
    # By status
    by_status: Dict[str, int] = Field(default_factory=dict)
    
    # By equipment type
    by_equipment_type: Dict[str, int] = Field(default_factory=dict)
    
    # Performance metrics
    average_days_in_queue: float = 0.0
    average_usage_count: float = 0.0
    
    # Top suppliers
    top_suppliers: List[dict] = Field(default_factory=list)


class SupplierPerformance(BaseModel):
    """Supplier performance schema."""
    
    supplier_id: int
    supplier_name: Optional[str] = None
    
    # Rotation metrics
    total_rotations: int = 0
    completed_rotations: int = 0
    overdue_rotations: int = 0
    
    # Performance scores
    reliability_score: float = 0.0
    efficiency_score: float = 0.0
    quality_score: float = 0.0
    overall_score: float = 0.0
    
    # Usage statistics
    average_days_in_queue: float = 0.0
    average_usage_count: float = 0.0
    last_used_date: Optional[date] = None
    
    # Equipment types
    equipment_types: List[str] = Field(default_factory=list)