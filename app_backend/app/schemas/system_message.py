# /root/app_backend/app/schemas/system_message.py - חדש
"""System message schemas - Aligned with database model."""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class MessageType(str, Enum):
    """Message type enum - matches model."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    UPDATE = "update"
    ANNOUNCEMENT = "announcement"
    SYSTEM = "system"


class MessagePriority(str, Enum):
    """Message priority enum - matches model."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class MessageStatus(str, Enum):
    """Message status enum - matches model."""

    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class SystemMessageBase(BaseModel):
    """Base system message schema."""

    title: str = Field(..., min_length=1, max_length=200, description="Message title")
    content: str = Field(..., min_length=1, description="Message content")

    # Classification
    type: MessageType = Field(..., description="Message type")
    priority: MessagePriority = Field(MessagePriority.NORMAL, description="Priority")

    # Schedule
    start_date: datetime = Field(..., description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")

    # Targeting
    is_global: bool = Field(True, description="Is global message")
    target_roles: Optional[List[str]] = Field(None, description="Target roles")
    target_regions: Optional[List[int]] = Field(None, description="Target region IDs")
    target_areas: Optional[List[int]] = Field(None, description="Target area IDs")

    # Acknowledgment
    requires_acknowledgment: bool = Field(False, description="Requires acknowledgment")


class SystemMessageCreate(SystemMessageBase):
    """Create system message schema."""

    created_by_id: int = Field(..., gt=0, description="Creator ID")
    status: MessageStatus = MessageStatus.DRAFT
    custom_metadata_json: Optional[Dict[str, Any]] = None


class SystemMessageUpdate(BaseModel):
    """Update system message schema."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    type: Optional[MessageType] = None
    priority: Optional[MessagePriority] = None
    status: Optional[MessageStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_global: Optional[bool] = None
    target_roles: Optional[List[str]] = None
    target_regions: Optional[List[int]] = None
    target_areas: Optional[List[int]] = None
    requires_acknowledgment: Optional[bool] = None
    is_active: Optional[bool] = None


class SystemMessageResponse(SystemMessageBase):
    """System message response schema."""

    id: int
    status: MessageStatus
    created_by_id: int
    approved_by_id: Optional[int] = None
    acknowledgment_count: int = 0
    custom_metadata_json: Optional[Dict[str, Any]] = None

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    # Computed
    is_message_active: bool = False
    is_expired: bool = False
    is_urgent: bool = False
    is_high_priority: bool = False

    # From relationships
    created_by_name: Optional[str] = None
    approved_by_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context):
        """Calculate computed fields."""
        now = datetime.utcnow()
        self.is_message_active = (
            self.status == MessageStatus.ACTIVE
            and self.start_date <= now
            and (not self.end_date or now <= self.end_date)
        )
        self.is_expired = self.end_date and now > self.end_date
        self.is_urgent = self.priority == MessagePriority.URGENT
        self.is_high_priority = self.priority in [
            MessagePriority.HIGH,
            MessagePriority.URGENT,
        ]
