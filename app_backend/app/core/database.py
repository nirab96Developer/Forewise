# app/core/database.py
"""Database configuration"""
import logging
import time
from typing import Generator

import sentry_sdk
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Slow-query monitoring ─────────────────────────────────────────────────────
SLOW_QUERY_THRESHOLD_S = 0.5  # log + alert for queries slower than 500 ms

@event.listens_for(Engine, "before_cursor_execute")
def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault("query_start_time", []).append(time.monotonic())

@event.listens_for(Engine, "after_cursor_execute")
def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    elapsed = time.monotonic() - conn.info["query_start_time"].pop(-1)
    if elapsed > SLOW_QUERY_THRESHOLD_S:
        truncated = statement[:500]
        logger.warning("SLOW QUERY (%.2fs): %s", elapsed, truncated)
        try:
            sentry_sdk.capture_message(
                f"Slow DB query: {elapsed:.2f}s",
                level="warning",
                extras={"query": truncated, "duration_s": round(elapsed, 3)},
            )
        except Exception:
            pass  # sentry not configured — ignore

# Create engine with proper Unicode support for SQL Server
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=settings.DB_ECHO,
)

# Note: Hebrew/Unicode support is handled by using Unicode/UnicodeText types in models

# Create SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables"""
    from app.models.base_simple import Base  # Import Base from base_simple
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized")


def close_db() -> None:
    """Close database connections"""
    engine.dispose()
    logger.info("Database connections closed")


def check_connection() -> bool:
    """Check database connection"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


async def check_database_connection() -> bool:
    """Check database connection (async wrapper)"""
    return check_connection()


__all__ = [
    "engine",
    "SessionLocal",
    "get_db",
    "init_db",
    "close_db",
    "check_connection",
    "check_database_connection",
]
