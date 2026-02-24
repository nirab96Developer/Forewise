# app/schemas/role_permission.py
"""Role-Permission association schemas."""

from typing import List

from pydantic import BaseModel, ConfigDict, Field


class RolePermissionCreate(BaseModel):
    """Assign permissions to role."""
    role_id: int = Field(..., gt=0)
    permission_ids: List[int] = Field(..., min_items=1)


class RolePermissionRemove(BaseModel):
    """Remove permissions from role."""
    role_id: int = Field(..., gt=0)
    permission_ids: List[int] = Field(..., min_items=1)


class RolePermissionResponse(BaseModel):
    """Role-permission response."""
    role_id: int
    permission_id: int
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class RolePermissionsUpdate(BaseModel):
    """Update all permissions for a role."""
    permission_ids: List[int] = Field(..., min_items=0)
