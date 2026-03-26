# app/models/base.py
"""
Base models for SQLAlchemy with standardized audit columns
"""
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy import MetaData, DateTime, Integer, Boolean, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional

# Metadata for all tables
metadata = MetaData(
    naming_convention={
        "ix": "IX_%(table_name)s_%(column_0_name)s",
        "uq": "UQ_%(table_name)s_%(column_0_name)s",
        "ck": "CK_%(table_name)s_%(constraint_name)s",
        "fk": "FK_%(table_name)s_%(column_0_name)s",
        "pk": "PK_%(table_name)s"
    }
)

class Base(DeclarativeBase):
    """Base class for all models"""
    metadata = metadata
    __abstract__ = True


class BaseModel(Base):
    """
    Base model with standard audit columns matching DB structure.
    
AFTER MIGRATIONS (2026-01-11):
    - created_at, updated_at: NOT NULL + DEFAULT SYSUTCDATETIME() (all tables)
    - updated_at: Auto-updated by DB triggers (48 triggers created)
    - deleted_at, is_active, version: Optional (not all tables have these)
    
    CORE tables (30): Have all 5 columns (created_at, updated_at, deleted_at, is_active, version)
    TRANSACTIONS tables (14): Have created_at, updated_at, is_active
    LOOKUP tables (6): Have created_at, updated_at, is_active
    
    Override in specific models if table doesn't have deleted_at/is_active/version.
    
    Note: created_by_id and updated_by_id are NOT included by default.
    """
    __abstract__ = True
    
    # Timestamp fields - NOW NOT NULL in DB (after migrations!)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text('SYSUTCDATETIME()'),
        comment="תאריך יצירה"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text('SYSUTCDATETIME()'),
        comment="תאריך עדכון אחרון (DB trigger updates automatically)"
    )
    
    # Soft delete support - NOT IN ALL TABLES!
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
        comment="תאריך מחיקה (soft delete)",
        deferred=True  # Lazy load
    )
    
    # Active flag - NOT IN ALL TABLES!
    is_active: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        default=True,
        comment="האם הרשומה פעילה",
        deferred=True  # Lazy load
    )
    
    # Version for optimistic locking - NOT IN ALL TABLES!
    version: Mapped[Optional[int]] = mapped_column(
        Integer,
        default=1,
        nullable=True,
        comment="גרסה (optimistic locking)",
        deferred=True  # Lazy load
    )
    
    # Helper methods
    @property
    def is_deleted(self) -> bool:
        """Check if record is soft-deleted"""
        return self.deleted_at is not None
    
    def soft_delete(self) -> None:
        """Soft delete the record"""
        self.deleted_at = datetime.utcnow()
        self.is_active = False
    
    def restore(self) -> None:
        """Restore soft-deleted record"""
        self.deleted_at = None
        self.is_active = True


class AuditableModel(BaseModel):
    """
    Extended model with created_by_id and updated_by_id.
    Use this for tables that track who created/updated records.
    
    Currently MOST tables don't have these columns,
    so use BaseModel by default and AuditableModel only where needed.
    """
    __abstract__ = True
    
    created_by_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", name="FK_%(table_name)s_created_by"),
        nullable=True,
        comment="מזהה משתמש יוצר"
    )
    
    updated_by_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", name="FK_%(table_name)s_updated_by"),
        nullable=True,
        comment="מזהה משתמש מעדכן"
    )


# Compatibility aliases
class AuditMixin:
    """Mixin for audit fields (deprecated - use BaseModel)"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TimestampMixin:
    """Mixin for timestamp fields (deprecated - use BaseModel)"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None