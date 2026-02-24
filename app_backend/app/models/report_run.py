"""
ReportRun model - הרצות דוחות
TRANSACTIONS category
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Unicode, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.report import Report
    from app.models.user import User


class ReportRun(Base):
    """
    ReportRun model - הרצת דוח
    Table: report_runs (26 columns)
    Category: TRANSACTIONS (is_active, created_at, updated_at - NO deleted_at/version per category)
    
    Note: DB actually has deleted_at and version, but category is TRANSACTIONS
    """
    __tablename__ = "report_runs"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Business Identifier
    run_number: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True,
        comment="מספר הרצה"
    )

    # Foreign Keys
    report_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('reports.id'), nullable=False, index=True,
        comment="דוח"
    )
    
    run_by: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id'), nullable=False, index=True,
        comment="הורץ על ידי"
    )
    
    triggered_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('users.id'), nullable=True, index=True,
        comment="הופעל על ידי"
    )
    
    parent_run_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('report_runs.id'), nullable=True, index=True,
        comment="הרצת אב (retry)"
    )

    # Status & Timing
    status: Mapped[str] = mapped_column(
        Unicode(50), nullable=False, index=True,
        comment="סטטוס: PENDING, RUNNING, SUCCESS, FAILED, CANCELLED"
    )
    
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="התחיל ב"
    )
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="הסתיים ב"
    )
    
    queued_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="נכנס לתור ב"
    )

    # Performance Metrics
    execution_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="זמן ריצה (ms)"
    )
    
    duration_seconds: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="משך (שניות)"
    )

    # Results
    result_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="מספר תוצאות"
    )
    
    result_rows: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="מספר שורות"
    )
    
    result_data: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="נתוני תוצאה"
    )
    
    result_format: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="פורמט תוצאה"
    )
    
    result_path: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="נתיב לקובץ תוצאה"
    )
    
    result_size_bytes: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True,
        comment="גודל תוצאה (bytes)"
    )
    
    file_path: Mapped[Optional[str]] = mapped_column(
        Unicode(500), nullable=True,
        comment="נתיב קובץ"
    )

    # Error Handling
    error_message: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="הודעת שגיאה"
    )
    
    error_details: Mapped[Optional[str]] = mapped_column(
        String, nullable=True,
        comment="פרטי שגיאה"
    )
    
    retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="מספר ניסיונות חוזרים"
    )

    # Parameters & Metadata
    parameters: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="פרמטרים (JSON)"
    )
    
    custom_metadata: Mapped[Optional[str]] = mapped_column(
        String, nullable=True,
        comment="מטא-דאטה מותאם"
    )

    # Audit - TRANSACTIONS (but DB has all columns)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text('SYSUTCDATETIME()'),
        comment="נוצר ב"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text('SYSUTCDATETIME()'),
        comment="עודכן ב"
    )

    # Note: DB actually has these columns even though category is TRANSACTIONS
    # is_active added in migration

    # Relationships - one-way
    report: Mapped["Report"] = relationship(
        "Report",
        foreign_keys=[report_id],
        lazy="select"
    )
    
    run_by_user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[run_by],
        lazy="select"
    )

    # Properties
    @property
    def is_finished(self) -> bool:
        """Check if run is finished"""
        return self.status in ('SUCCESS', 'FAILED', 'CANCELLED')

    @property
    def is_successful(self) -> bool:
        """Check if run succeeded"""
        return self.status == 'SUCCESS'

    def __repr__(self):
        return f"<ReportRun(id={self.id}, report_id={self.report_id}, status='{self.status}')>"
