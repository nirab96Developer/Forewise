# app/schemas/work_order_coordination_log.py
# Pydantic schemas for Work Order Coordination Logs

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


# Action types
ActionType = Literal["CALL", "RESEND", "ESCALATE", "NOTE", "MOVE_NEXT", "STATUS_UPDATE"]


class CoordinationLogBase(BaseModel):
    """Base schema for coordination logs"""
    action_type: ActionType = Field(..., description="Type of coordination action")
    note: Optional[str] = Field(None, description="Notes or description of the action")


class CoordinationLogCreate(CoordinationLogBase):
    """Schema for creating a coordination log"""
    work_order_id: int = Field(..., description="Work order ID")
    previous_supplier_id: Optional[int] = Field(None, description="Previous supplier ID (for MOVE_NEXT)")
    new_supplier_id: Optional[int] = Field(None, description="New supplier ID (for MOVE_NEXT)")


class CoordinationLogResponse(CoordinationLogBase):
    """Schema for coordination log response"""
    id: int
    work_order_id: int
    created_by_user_id: int
    previous_supplier_id: Optional[int] = None
    new_supplier_id: Optional[int] = None
    created_at: datetime
    
    # From relationships
    created_by_name: Optional[str] = None
    previous_supplier_name: Optional[str] = None
    new_supplier_name: Optional[str] = None
    action_type_display: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class CoordinationLogListResponse(BaseModel):
    """Schema for list of coordination logs"""
    items: list[CoordinationLogResponse]
    total: int

