# /root/app_backend/app/schemas/support_ticket.py - חדש
"""Support ticket schemas - Aligned with database model."""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel as PydanticBaseModel, ConfigDict, Field


class TicketPriority(str, Enum):
    """Ticket priority enum - matches model."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class TicketStatus(str, Enum):
    """Ticket status enum - matches model."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_USER = "waiting_for_user"
    WAITING_FOR_SUPPLIER = "waiting_for_supplier"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class TicketType(str, Enum):
    """Ticket type enum - matches model."""

    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    TECHNICAL_ISSUE = "technical_issue"
    USER_TRAINING = "user_training"
    SYSTEM_ACCESS = "system_access"
    DATA_ISSUE = "data_issue"
    OTHER = "other"


class SupportTicketBase(PydanticBaseModel):
    """Base support ticket schema."""

    title: str = Field(..., min_length=1, max_length=200, description="Ticket title")
    description: str = Field(..., min_length=1, description="Ticket description")

    # Classification
    type: TicketType = Field(..., description="Ticket type")
    priority: TicketPriority = Field(
        TicketPriority.NORMAL, description="Priority level"
    )

    # Categorization
    category: Optional[str] = Field(None, max_length=100, description="Category")
    tags: Optional[List[str]] = Field(None, description="Tags")

    # Time tracking
    estimated_resolution_time: Optional[int] = Field(
        None, ge=0, description="Estimated hours"
    )
    due_date: Optional[datetime] = Field(None, description="Due date")


class SupportTicketCreate(SupportTicketBase):
    """Create support ticket schema.

    Wave 7.I — `user_id` is now Optional and **ignored by the handler**.
    The router unconditionally sets `user_id=current_user.id` so a caller
    can never spoof another user. The field stays in the schema only
    for backwards-compat with any client that still sends it; new
    callers should omit it.
    """

    user_id: Optional[int] = Field(
        None, gt=0,
        description="DEPRECATED — ignored by server, always overridden with current_user.id",
    )
    status: TicketStatus = TicketStatus.OPEN
    custom_metadata_json: Optional[Dict[str, Any]] = None


class SupportTicketUpdate(PydanticBaseModel):
    """Update support ticket schema."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    type: Optional[TicketType] = None
    priority: Optional[TicketPriority] = None
    status: Optional[TicketStatus] = None
    assigned_to_id: Optional[int] = Field(None, gt=0)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    estimated_resolution_time: Optional[int] = Field(None, ge=0)
    actual_resolution_time: Optional[int] = Field(None, ge=0)
    due_date: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    user_feedback: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    is_active: Optional[bool] = None


class SupportTicketResponse(SupportTicketBase):
    """Support ticket response schema."""

    id: int
    ticket_number: str
    user_id: int
    status: TicketStatus

    # Assignment
    assigned_to_id: Optional[int] = None

    # Time tracking
    actual_resolution_time: Optional[int] = None

    # Dates
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    # Resolution
    resolution_notes: Optional[str] = None
    user_feedback: Optional[str] = None
    rating: Optional[int] = None

    # Additional - stored as JSON string in DB, parsed on read
    custom_metadata_json: Optional[Any] = None

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    # Computed
    is_open: bool = False
    is_resolved: bool = False
    is_closed: bool = False
    is_overdue: bool = False
    days_open: int = 0

    # From relationships
    user_name: Optional[str] = None
    assigned_to_name: Optional[str] = None
    comments_count: int = 0

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context):
        """Calculate computed fields."""
        self.is_open = self.status in [
            TicketStatus.OPEN,
            TicketStatus.IN_PROGRESS,
            TicketStatus.WAITING_FOR_USER,
            TicketStatus.WAITING_FOR_SUPPLIER,
        ]
        self.is_resolved = self.status == TicketStatus.RESOLVED
        self.is_closed = self.status == TicketStatus.CLOSED
        if self.due_date:
            self.is_overdue = datetime.utcnow() > self.due_date
        if self.created_at:
            self.days_open = int(
                (datetime.utcnow() - self.created_at).total_seconds() / 86400
            )


class CommentCreate(PydanticBaseModel):
    """Comment create schema."""
    
    model_config = ConfigDict(from_attributes=True)

    ticket_id: int = Field(..., gt=0, description="Support ticket ID")
    content: str = Field(..., min_length=1, max_length=2000, description="Comment content")
    is_internal: bool = Field(False, description="Internal comment flag")
    attachments: Optional[List[str]] = Field(None, description="Attachment URLs")


class TicketCreate(PydanticBaseModel):
    """Ticket create schema."""
    
    model_config = ConfigDict(from_attributes=True)

    title: str = Field(..., min_length=1, max_length=200, description="Ticket title")
    description: str = Field(..., min_length=1, description="Ticket description")
    type: TicketType = Field(TicketType.OTHER, description="Ticket type")
    priority: TicketPriority = Field(TicketPriority.NORMAL, description="Ticket priority")
    category: Optional[str] = Field(None, max_length=100, description="Ticket category")
    user_id: int = Field(..., gt=0, description="User creating ticket")
    assigned_to_id: Optional[int] = Field(None, gt=0, description="Assigned user")
    due_date: Optional[datetime] = Field(None, description="Due date")
    custom_metadata_json: Optional[Dict[str, Any]] = None


class TicketUpdate(PydanticBaseModel):
    """Ticket update schema."""
    
    model_config = ConfigDict(from_attributes=True)

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    type: Optional[TicketType] = None
    priority: Optional[TicketPriority] = None
    status: Optional[TicketStatus] = None
    category: Optional[str] = Field(None, max_length=100)
    assigned_to_id: Optional[int] = Field(None, gt=0)
    due_date: Optional[datetime] = None
    resolution: Optional[str] = Field(None, max_length=1000)
    custom_metadata_json: Optional[Dict[str, Any]] = None


class TicketComment(PydanticBaseModel):
    """Ticket comment schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    content: str = Field(..., min_length=1, max_length=2000)
    is_internal: bool = False
    created_by_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # From relationships
    created_by_name: Optional[str] = None


class TicketEscalation(PydanticBaseModel):
    """Ticket escalation schema."""
    
    reason: str = Field(..., min_length=1, max_length=500, description="Escalation reason")
    priority: TicketPriority = Field(..., description="New priority level")
    assign_to_id: Optional[int] = Field(None, description="Assign to specific user")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")


class TicketStatistics(PydanticBaseModel):
    """Ticket statistics schema."""
    
    total_tickets: int = 0
    open_tickets: int = 0
    in_progress_tickets: int = 0
    resolved_tickets: int = 0
    closed_tickets: int = 0
    
    # By priority
    low_priority: int = 0
    normal_priority: int = 0
    high_priority: int = 0
    urgent_priority: int = 0
    critical_priority: int = 0
    
    # By type
    bug_tickets: int = 0
    feature_requests: int = 0
    technical_issues: int = 0
    user_training: int = 0
    system_access: int = 0
    data_issues: int = 0
    other_tickets: int = 0
    
    # Response metrics
    avg_response_time_hours: float = 0.0
    avg_resolution_time_hours: float = 0.0
    resolution_rate: float = 0.0
    
    # Time period
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


# Alias for compatibility
TicketResponse = SupportTicketResponse