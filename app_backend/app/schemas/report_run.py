"""
ReportRun schemas
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class ReportRunStatus(str, Enum):
    """Report run status"""
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ResultFormat(str, Enum):
    """Result format"""
    JSON = "JSON"
    CSV = "CSV"
    EXCEL = "EXCEL"
    PDF = "PDF"


class ReportRunBase(BaseModel):
    """Base report run"""
    status: ReportRunStatus = Field(ReportRunStatus.PENDING)


class ReportRunCreate(ReportRunBase):
    """Create report run"""
    report_id: int = Field(..., description="דוח")
    parameters: Optional[str] = None


class ReportRunUpdate(BaseModel):
    """Update report run"""
    status: Optional[ReportRunStatus] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = Field(None, ge=0)
    result_count: Optional[int] = Field(None, ge=0)
    result_data: Optional[str] = None
    error_message: Optional[str] = None
    result_format: Optional[ResultFormat] = None
    result_path: Optional[str] = None


class ReportRunResponse(ReportRunBase):
    """Report run response"""
    id: int
    run_number: int
    report_id: int
    run_by: int
    triggered_by_id: Optional[int] = None
    parent_run_id: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    queued_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    duration_seconds: Optional[int] = None
    result_count: Optional[int] = None
    result_rows: Optional[int] = None
    result_data: Optional[str] = None
    result_format: Optional[str] = None
    result_path: Optional[str] = None
    result_size_bytes: Optional[int] = None
    file_path: Optional[str] = None
    error_message: Optional[str] = None
    error_details: Optional[str] = None
    retry_count: int
    parameters: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ReportRunBrief(BaseModel):
    """Brief run"""
    id: int
    run_number: int
    report_id: int
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result_count: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class ReportRunList(BaseModel):
    """List response"""
    items: List[ReportRunResponse]
    total: int
    page: int = 1
    page_size: int = 50
    total_pages: int = 1


class ReportRunSearch(BaseModel):
    """Search filters"""
    report_id: Optional[int] = Field(None, description="סינון לפי דוח")
    status: Optional[ReportRunStatus] = None
    run_by: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
    sort_by: str = Field("created_at")
    sort_desc: bool = Field(True)


class ReportRunStatistics(BaseModel):
    """Statistics"""
    total: int = 0
    by_status: dict[str, int] = {}
    success_count: int = 0
    failed_count: int = 0
    avg_execution_time_ms: Optional[int] = None
