# app/schemas/common.py
"""Common response schemas for consistent API responses."""

from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    success: bool = True
    data: T
    message: Optional[str] = None

class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for SQL query."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit for SQL query."""
        return self.page_size
    
    @property
    def skip(self) -> int:
        """Get skip for SQL query (alias for offset)."""
        return self.offset
    
    @property
    def per_page(self) -> int:
        """Get per_page (alias for page_size for backward compatibility)."""
        return self.page_size

class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")

class ErrorResponse(BaseModel):
    """Error response schema."""
    success: bool = False
    error: dict = Field(..., description="Error details")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid input data",
                    "details": {
                        "field": "email",
                        "issue": "Invalid email format"
                    }
                }
            }
        }

class SuccessResponse(BaseModel):
    """Simple success response."""
    success: bool = True
    message: str = Field(..., description="Success message")
    data: Optional[Any] = None

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment name")
    database: str = Field(..., description="Database connection status")