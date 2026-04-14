# /root/app_backend/app/schemas/support_ticket_comment.py - חדש
"""Support ticket comment schemas - Aligned with database model."""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class CommentType(str, Enum):
    """Comment type enum - matches model."""

    USER_COMMENT = "user_comment"
    SUPPORT_COMMENT = "support_comment"
    SYSTEM_COMMENT = "system_comment"
    INTERNAL_NOTE = "internal_note"


class SupportTicketCommentBase(BaseModel):
    """Base support ticket comment schema."""

    ticket_id: int = Field(..., gt=0, description="Ticket ID")
    content: str = Field(..., min_length=1, description="Comment content")
    type: CommentType = Field(CommentType.USER_COMMENT, description="Comment type")
    is_internal: bool = Field(False, description="Is internal note")
    parent_comment_id: Optional[int] = Field(
        None, gt=0, description="Parent comment ID for replies"
    )


class SupportTicketCommentCreate(SupportTicketCommentBase):
    """Create support ticket comment schema."""

    user_id: int = Field(..., gt=0, description="User ID")
    custom_metadata_json: Optional[Dict[str, Any]] = None


class SupportTicketCommentUpdate(BaseModel):
    """Update support ticket comment schema."""

    content: Optional[str] = Field(None, min_length=1)
    type: Optional[CommentType] = None
    is_internal: Optional[bool] = None
    custom_metadata_json: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class SupportTicketCommentResponse(SupportTicketCommentBase):
    """Support ticket comment response schema."""

    id: int
    user_id: int
    custom_metadata_json: Optional[Dict[str, Any]] = None

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    # Computed
    is_reply: bool = False
    is_support_comment: bool = False
    is_internal_note: bool = False

    # From relationships
    user_name: Optional[str] = None
    replies_count: int = 0

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context):
        """Calculate computed fields."""
        self.is_reply = self.parent_comment_id is not None
        self.is_support_comment = self.type == CommentType.SUPPORT_COMMENT
        self.is_internal_note = self.type == CommentType.INTERNAL_NOTE


class SupportTicketCommentFilter(BaseModel):
    """Filter for support ticket comments."""

    ticket_id: Optional[int] = None
    user_id: Optional[int] = None
    type: Optional[CommentType] = None
    is_internal: Optional[bool] = None
    is_reply: Optional[bool] = None
    parent_comment_id: Optional[int] = None
