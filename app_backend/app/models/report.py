"""
Report model - דוחות
CORE entity
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class Report(BaseModel):
    """
    Report model - דוח
    Table: reports (22 columns)
    Category: CORE
    """
    __tablename__ = "reports"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Business Identifier - UNIQUE
    code: Mapped[str] = mapped_column(
        Unicode(50), nullable=False, unique=True, index=True,
        comment="קוד דוח ייחודי"
    )
    
    name: Mapped[str] = mapped_column(
        Unicode(200), nullable=False, index=True,
        comment="שם הדוח"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="תיאור"
    )

    # Classification
    type: Mapped[str] = mapped_column(
        Unicode(50), nullable=False, index=True,
        comment="סוג דוח"
    )
    
    status: Mapped[str] = mapped_column(
        Unicode(50), nullable=False, index=True,
        comment="סטטוס"
    )

    # Template & Parameters
    template_path: Mapped[Optional[str]] = mapped_column(
        Unicode(500), nullable=True,
        comment="נתיב תבנית"
    )
    
    parameters: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="פרמטרים (JSON)"
    )

    # Scheduling
    is_scheduled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="האם מתוזמן"
    )
    
    schedule_cron: Mapped[Optional[str]] = mapped_column(
        Unicode(100), nullable=True,
        comment="ביטוי CRON"
    )
    
    last_run: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="הרצה אחרונה"
    )

    # Configuration
    requires_approval: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="דורש אישור"
    )
    
    max_execution_time: Mapped[int] = mapped_column(
        Integer, nullable=False, default=300,
        comment="זמן ריצה מקסימלי (שניות)"
    )

    # Ownership
    created_by_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id'), nullable=False, index=True,
        comment="נוצר על ידי"
    )
    
    owner_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('users.id'), nullable=True, index=True,
        comment="בעלים"
    )

    # Additional
    custom_metadata_json: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="מטא-דאטה מותאם"
    )
    
    metadata_json: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="מטא-דאטה"
    )

    # Audit from BaseModel: created_at, updated_at, deleted_at, is_active, version

    # Relationships - one-way
    created_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by_id],
        lazy="select"
    )
    
    owner: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[owner_id],
        lazy="select"
    )

    # Properties
    @property
    def display_name(self) -> str:
        return f"{self.code}: {self.name}"

    @property
    def is_ready_to_run(self) -> bool:
        """Check if report can be run"""
        return self.is_active and self.deleted_at is None and self.status == 'ACTIVE'

    def __repr__(self):
        return f"<Report(id={self.id}, code='{self.code}', name='{self.name}')>"
