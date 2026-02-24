# app/schemas/project_document.py
"""Project document schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DocumentType(str, Enum):
    """Document type."""
    CONTRACT = "contract"
    PERMIT = "permit"
    PLAN = "plan"
    REPORT = "report"
    INVOICE = "invoice"
    PHOTO = "photo"
    DRAWING = "drawing"
    SPECIFICATION = "specification"
    CORRESPONDENCE = "correspondence"
    OTHER = "other"


class DocumentStatus(str, Enum):
    """Document status."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class ProjectDocumentBase(BaseModel):
    """Base project document schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    project_id: int = Field(..., gt=0)
    file_id: int = Field(..., gt=0)
    document_type: DocumentType
    document_date: Optional[datetime] = None
    version: str = Field("1.0", max_length=20)
    requires_approval: bool = False
    is_public: bool = False


class ProjectDocumentCreate(ProjectDocumentBase):
    """Create project document."""
    uploaded_by: int = Field(..., gt=0)


class ProjectDocumentUpdate(BaseModel):
    """Update project document."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    document_type: Optional[DocumentType] = None
    document_date: Optional[datetime] = None
    version: Optional[str] = Field(None, max_length=20)
    status: Optional[DocumentStatus] = None
    is_public: Optional[bool] = None


class ProjectDocumentApprove(BaseModel):
    """Approve/reject document."""
    action: str = Field(..., pattern="^(approve|reject)$")
    reason: Optional[str] = None


class ProjectDocumentResponse(ProjectDocumentBase):
    """Project document response."""
    id: int
    status: DocumentStatus
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    uploaded_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # From relationships
    project_name: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_mime_type: Optional[str] = None
    uploader_name: Optional[str] = None
    approver_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
