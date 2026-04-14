"""Application exceptions"""
import logging
from typing import Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

logger = logging.getLogger(__name__)


class APIException(HTTPException):
    """Base API exception"""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "Internal server error",
        headers: Optional[Dict[str, str]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        logger.warning(f"{self.__class__.__name__}: {detail}")


class ValidationException(APIException):
    """Validation error"""

    def __init__(
        self, detail: str = "Validation error", field_errors: Optional[Dict] = None
    ):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
        self.field_errors = field_errors


class NotFoundException(APIException):
    """Resource not found"""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UnauthorizedException(APIException):
    """Unauthorized access"""

    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(APIException):
    """Forbidden access"""

    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class PermissionDeniedException(APIException):
    """Permission denied exception."""

    def __init__(self, detail: str = "Permission denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class DuplicateException(APIException):
    """Duplicate record exception."""

    def __init__(self, detail: str = "Record already exists"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class BusinessException(APIException):
    """Business logic error"""

    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class BusinessLogicException(APIException):
    """Business logic exception."""

    def __init__(self, detail: str = "Business logic error"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class AuthenticationException(APIException):
    """Authentication exception."""

    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class InvalidTokenException(APIException):
    """Invalid token exception."""

    def __init__(self, detail: str = "Invalid token"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class TokenExpiredException(APIException):
    """Token expired exception."""

    def __init__(self, detail: str = "Token has expired"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class InsufficientPermissionsException(APIException):
    """Insufficient permissions exception."""

    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class DatabaseException(APIException):
    """Database error"""

    def __init__(
        self,
        detail: str = "Database error",
        original_error: Optional[SQLAlchemyError] = None,
    ):
        if original_error and isinstance(original_error, IntegrityError):
            if "duplicate" in str(original_error).lower():
                detail = "Record already exists"
            elif "foreign key" in str(original_error).lower():
                detail = "Cannot delete - related records exist"
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail
        )


# Aliases for compatibility
BusinessRuleViolation = BusinessException
ResourceNotFound = NotFoundException
DuplicateResource = DuplicateException
InsufficientPermissions = InsufficientPermissionsException

# Export
__all__ = [
    "APIException",
    "ValidationException",
    "NotFoundException",
    "UnauthorizedException",
    "ForbiddenException",
    "PermissionDeniedException",
    "DuplicateException",
    "BusinessException",
    "BusinessLogicException",
    "AuthenticationException",
    "InvalidTokenException",
    "TokenExpiredException",
    "InsufficientPermissionsException",
    "DatabaseException",
    "BusinessRuleViolation",
    "ResourceNotFound",
    "DuplicateResource",
    "InsufficientPermissions",
]


# ==================== Custom Base Exception ====================


class CustomException(Exception):
    """Base custom exception class."""

    def __init__(
        self, detail: str, status_code: int = 400, error_code: Optional[str] = None
    ):
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code or "CUSTOM_ERROR"
        super().__init__(self.detail)
