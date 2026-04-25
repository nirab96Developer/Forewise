"""
SystemRate schemas
"""

from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class SystemRateBase(BaseModel):
    """Base schema for system rate.

    Cleanup #1 (post-Wave 7) — added the `rate_code` / `rate_name`
    fields that the model has always had but the schema was missing.
    The router used to call `data.code.upper()` / `SystemRate.code`
    against fields that don't exist; an admin POST/PATCH would
    AttributeError before it ever hit the DB.
    """
    rate_code: str = Field(..., max_length=50, description="Unique business code, uppercased on save")
    rate_name: str = Field(..., max_length=255, description="Display name")
    rate_type: str = Field(..., max_length=50)
    rate_value: Decimal = Field(..., ge=0)
    description: Optional[str] = None


class SystemRateCreate(SystemRateBase):
    """Schema for creating system rate."""
    pass


class SystemRateUpdate(BaseModel):
    """Schema for updating system rate."""
    rate_code: Optional[str] = Field(None, max_length=50)
    rate_name: Optional[str] = Field(None, max_length=255)
    rate_type: Optional[str] = Field(None, max_length=50)
    rate_value: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class SystemRateResponse(SystemRateBase):
    """Schema for system rate response"""
    id: int
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
