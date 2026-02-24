# app/schemas/project_status.py
"""Project status update schemas."""
from typing import Optional

from pydantic import BaseModel, Field


class ProjectStatusUpdate(BaseModel):
    """Project status update schema."""
    
    status: str = Field(..., description="New project status")
    reason: Optional[str] = Field(None, description="Reason for status change")
    notes: Optional[str] = Field(None, description="Additional notes")



