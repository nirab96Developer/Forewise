# /root/app_backend/app/schemas/base.py - מתוקן
"""Base schemas with common mixins and utilities."""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrderDirection(str, Enum):
    """Sort order direction."""

    ASC = "asc"
    DESC = "desc"


class ResponseStatus(str, Enum):
    """Response status codes."""

    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


T = TypeVar("T")


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields - matches model."""

    created_at: datetime
    updated_at: Optional[datetime] = None


class AuditMixin(TimestampMixin):
    """Mixin for audit fields - matches model."""

    created_by_id: Optional[int] = None
    updated_by_id: Optional[int] = None

    # From joins
    created_by_name: Optional[str] = None
    updated_by_name: Optional[str] = None


class SoftDeleteMixin(BaseModel):
    """Soft delete fields - matches model."""

    is_active: bool = True
    deleted_at: Optional[datetime] = None
    deleted_by_id: Optional[int] = None


class MetadataMixin(BaseModel):
    """Metadata and tags - matches model."""

    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tags: Optional[List[str]] = Field(default_factory=list)
    notes: Optional[str] = None


class BaseModel(BaseModel):
    """Base model with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        validate_assignment=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
        },
    )


class BaseResponse(BaseModel):
    """Base response with all mixins."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BaseResponseWithAudit(BaseResponse, AuditMixin, SoftDeleteMixin, MetadataMixin):
    """Base response with full audit trail."""

    pass


# PaginationParams moved to app.schemas.common to avoid conflicts


class FilterParams(BaseModel):
    """Base filter parameters."""

    search: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None
    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None

    @field_validator("created_to")
    @classmethod
    def validate_date_range(cls, v, info):
        """Validate that created_to is after created_from."""
        if v and info.data.get("created_from"):
            if v < info.data["created_from"]:
                raise ValueError("created_to must be after created_from")
        return v


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    status: ResponseStatus = ResponseStatus.SUCCESS
    message: Optional[str] = None
    data: Optional[T] = None
    errors: Optional[List[Dict[str, Any]]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    items: List[T] = []
    total: int = 0
    page: int = 1
    per_page: int = 20
    pages: int = 0
    has_next: bool = False
    has_prev: bool = False

    def set_pagination(self, page: int, per_page: int, total: int):
        """Calculate pagination metadata."""
        self.page = page
        self.per_page = per_page
        self.total = total
        self.pages = (total + per_page - 1) // per_page if per_page > 0 else 0
        self.has_next = page * per_page < total
        self.has_prev = page > 1
