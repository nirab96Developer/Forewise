# app/core/__init__.py
"""
Core Module Initialization
==========================
Central configuration, database, security, and utility modules
"""

from loguru import logger

# Config
from app.core.config import settings

# Database
from app.core.database import (
    SessionLocal,
    engine,
    get_db,
    init_db,
    close_db,
    check_connection,
    check_database_connection
)

# Security (only token and password functions)
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token
)

# Dependencies (user auth and permissions)
from app.core.dependencies import (
    get_current_user,
    get_current_active_user,
    admin_required,
    manager_required,
    PermissionChecker,
    CurrentUser,
    CurrentActiveUser,
    AdminUser,
    ManagerUser,
    DatabaseSession
)

# Exceptions
from app.core.exceptions import (
    APIException,
    ValidationException,
    NotFoundException,
    UnauthorizedException,
    ForbiddenException,
    PermissionDeniedException,
    DuplicateException,
    BusinessException,
    BusinessLogicException,
    AuthenticationException,
    InvalidTokenException,
    TokenExpiredException,
    InsufficientPermissionsException,
    DatabaseException,
    CustomException
)

# Optional imports with graceful fallback
try:
    from app.core.pagination import PageResponse, paginate_query
except ImportError:
    PageResponse = None
    paginate_query = None

try:
    from app.core.cache import (
        get_cache,
        set_cache,
        delete_cache,
        clear_cache_pattern,
        clear_all_cache,
        cache,
        init_redis,
        close_redis
    )
except ImportError:
    get_cache = None
    set_cache = None
    delete_cache = None
    clear_cache_pattern = None
    clear_all_cache = None
    cache = None
    init_redis = None
    close_redis = None

try:
    from app.core.email import send_email, EmailService
except ImportError:
    send_email = None
    EmailService = None

try:
    from app.core.logging import setup_logging
except ImportError:
    setup_logging = None

# Version info
__version__ = "1.0.0"
__author__ = "Forest Management System"

# Export all public items
__all__ = [
    # Config
    "settings",

    # Database
    "SessionLocal",
    "engine",
    "get_db",
    "init_db",
    "close_db",
    "check_connection",
    "check_database_connection",

    # Security (token and password)
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "create_refresh_token",
    "decode_token",

    # Dependencies (authentication)
    "get_current_user",
    "get_current_active_user",
    "admin_required",
    "manager_required",
    "PaginationParams",
    "PermissionChecker",
    "CurrentUser",
    "CurrentActiveUser",
    "AdminUser",
    "ManagerUser",
    "DatabaseSession",

    # Exceptions
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
    "CustomException",

    # Cache functions
    "get_cache",
    "set_cache",
    "delete_cache",
    "clear_cache_pattern",
    "clear_all_cache",
    "cache",
    "init_redis",
    "close_redis",

    # Optional modules
    "PageResponse",
    "paginate_query",
    "send_email",
    "EmailService",
    "setup_logging",

    # Logger
    "logger",

    # Version
    "__version__",
    "__author__",
]

# Log initialization
logger.info(f"Core module initialized - Version {__version__}")
