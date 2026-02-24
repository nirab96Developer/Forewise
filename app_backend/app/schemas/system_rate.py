"""
SystemRate schemas
"""

from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class SystemRateBase(BaseModel):
    """Base schema for system rate"""
    rate_type: str = Field(..., max_length=50)
    rate_value: Decimal = Field(..., ge=0)
    description: Optional[str] = None


class SystemRateCreate(SystemRateBase):
    """Schema for creating system rate"""
    pass


class SystemRateUpdate(BaseModel):
    """Schema for updating system rate"""
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
