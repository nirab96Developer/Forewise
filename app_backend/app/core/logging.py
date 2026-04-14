"""
Simplified logging configuration for the application
"""
import logging
import sys
from pathlib import Path
from typing import Optional


from app.core.config import settings


def setup_logging(
    app_name: Optional[str] = None,
    environment: Optional[str] = None,
    log_level: Optional[str] = None,
):
    """
    Setup application logging with loguru

    Args:
        app_name: Application name
        environment: Runtime environment
        log_level: Log level
    """
    # Get settings
    app_name = app_name or settings.APP_NAME
    environment = environment or settings.ENVIRONMENT
    log_level = log_level or getattr(settings, "LOG_LEVEL", "INFO")

    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True, parents=True)

    # Remove default handler
    logger.remove()

    # Console format - simple and clean
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    # Add console handler with UTF-8 encoding
    logger.add(
        sys.stdout,
        format=console_format,
        level=log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )

    # File handler — all environments write to logs/app.log
    file_format = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"

    logger.add(
        logs_dir / "app.log",
        format=file_format,
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8",
        enqueue=True,
    )

    # Extra production log (compressed, long retention)
    if environment == "production":
        logger.add(
            logs_dir / f"{app_name}_{environment}.log",
            format=file_format,
            level=log_level,
            rotation="1 day",
            retention="30 days",
            compression="gz",
            encoding="utf-8",
            enqueue=True,
        )

    # Debug file in development
    if environment in ("development", "local"):
        logger.add(
            logs_dir / f"{app_name}_debug.log",
            format="{time} - {name} - {level} - {message}",
            level="DEBUG",
            rotation="100 MB",
            retention="7 days",
            encoding="utf-8",
        )

    # Intercept standard logging
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            # Get corresponding Loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # Find caller from where originated the logged message
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )

    # Setup basic config
    logging.basicConfig(handlers=[InterceptHandler()], level=0)

    # Redirect uvicorn and sqlalchemy logs
    for logger_name in [
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "fastapi",
        "sqlalchemy.engine",
    ]:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.propagate = False

    # Log startup
    logger.info(
        f"Logging initialized - App: {app_name}, Environment: {environment}, Level: {log_level}"
    )

    return logger


# Initialize logger
logger = setup_logging()


# Export functions for compatibility
def get_logger(name: str = None):
    """Get logger instance"""
    return logger.bind(name=name) if name else logger


# Context management functions
def set_user_id(user_id: int):
    """Set user ID in logging context"""
    logger.configure(extra={"user_id": user_id})


def set_request_id(request_id: str):
    """Set request ID in logging context"""
    logger.configure(extra={"request_id": request_id})


def get_request_id() -> str:
    """Get current request ID from logging context"""
    return logger.contextualize().get("request_id", "unknown")


# Convenience functions
debug = logger.debug
info = logger.info
warning = logger.warning
error = logger.error
critical = logger.critical
exception = logger.exception

# Export
__all__ = [
    "logger",
    "setup_logging",
    "get_logger",
    "set_user_id",
    "set_request_id",
    "get_request_id",
    "debug",
    "info",
    "warning",
    "error",
    "critical",
    "exception",
]
