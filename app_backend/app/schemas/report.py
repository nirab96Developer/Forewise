"""
Report schemas
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ReportType(str, Enum):
    """Report type enum"""
    FINANCIAL = "FINANCIAL"
    OPERATIONAL = "OPERATIONAL"
    ANALYTICAL = "ANALYTICAL"
    CUSTOM = "CUSTOM"


class ReportStatus(str, Enum):
    """Report status enum"""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class ReportBase(BaseModel):
    """Base report"""
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    type: ReportType = Field(..., description="סוג דוח")
    status: ReportStatus = Field(ReportStatus.DRAFT)


class ReportCreate(ReportBase):
    """Create report"""
    code: str = Field(..., max_length=50, description="קוד ייחודי")
    template_path: Optional[str] = Field(None, max_length=500)
    parameters: Optional[str] = None
    is_scheduled: bool = Field(False)
    schedule_cron: Optional[str] = Field(None, max_length=100)
    requires_approval: bool = Field(False)
    max_execution_time: int = Field(300, ge=1)
    owner_id: Optional[int] = None

    @field_validator('code')
    @classmethod
    def normalize_code(cls, v: str) -> str:
        """Normalize code"""
        return v.strip().upper()

    @field_validator('schedule_cron')
    @classmethod
    def validate_cron(cls, v: Optional[str], info) -> Optional[str]:
        """Validate cron if scheduled"""
        if info.data.get('is_scheduled') and not v:
            raise ValueError("schedule_cron required when is_scheduled=True")
        return v


class ReportUpdate(BaseModel):
    """Update report"""
    name: Optional[str] = Field(None, max_length=200)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    type: Optional[ReportType] = None
    status: Optional[ReportStatus] = None
    template_path: Optional[str] = None
    parameters: Optional[str] = None
    is_scheduled: Optional[bool] = None
    schedule_cron: Optional[str] = None
    requires_approval: Optional[bool] = None
    max_execution_time: Optional[int] = Field(None, ge=1)
    owner_id: Optional[int] = None
    version: Optional[int] = None


class ReportResponse(ReportBase):
    """Report response"""
    id: int
    code: str
    template_path: Optional[str] = None
    parameters: Optional[str] = None
    is_scheduled: bool
    schedule_cron: Optional[str] = None
    last_run: Optional[datetime] = None
    requires_approval: bool
    max_execution_time: int
    created_by_id: int
    owner_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    is_active: bool
    version: int
    
    model_config = ConfigDict(from_attributes=True)


class ReportBrief(BaseModel):
    """Brief report"""
    id: int
    code: str
    name: str
    type: str
    status: str
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


class ReportList(BaseModel):
    """List response"""
    items: List[ReportResponse]
    total: int
    page: int = 1
    page_size: int = 50
    total_pages: int = 1


class ReportSearch(BaseModel):
    """Search filters"""
    q: Optional[str] = None
    type: Optional[ReportType] = None
    status: Optional[ReportStatus] = None
    owner_id: Optional[int] = None
    is_scheduled: Optional[bool] = None
    is_active: Optional[bool] = None
    include_deleted: bool = Field(False)
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
    sort_by: str = Field("name")
    sort_desc: bool = Field(False)


class ReportStatistics(BaseModel):
    """Statistics"""
    total: int = 0
    by_type: dict[str, int] = {}
    by_status: dict[str, int] = {}
    scheduled_count: int = 0
