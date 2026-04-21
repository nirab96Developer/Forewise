"""
Worklog model - דיווחי עבודה
TRANSACTIONS category (created_at, updated_at, is_active - NO deleted_at/version)
"""

from __future__ import annotations

from datetime import datetime, date, time
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Date, Time, ForeignKey, Integer, String, Unicode, Numeric, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.work_order import WorkOrder
    from app.models.user import User
    from app.models.project import Project
    from app.models.equipment import Equipment
    from app.models.activity_type import ActivityType


class Worklog(Base):
    """
    Worklog model - דיווח עבודה
    Table: worklogs (46 columns)
    Category: TRANSACTIONS (created_at, updated_at, is_active - NO deleted_at/version)
    
    Represents a work log entry submitted by supplier/user.
    """
    __tablename__ = "worklogs"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Business Identifier
    report_number: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True,
        comment="מספר דוח"
    )
    
    report_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="סוג דוח"
    )

    # Foreign Keys (6)
    work_order_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('work_orders.id'), nullable=True, index=True,
        comment="הזמנת עבודה"
    )
    
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('users.id'), nullable=True, index=True,
        comment="משתמש מדווח"
    )
    
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('projects.id'), nullable=True, index=True,
        comment="פרויקט"
    )
    
    equipment_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('equipment.id'), nullable=True, index=True,
        comment="ציוד"
    )
    
    activity_type_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('activity_types.id'), nullable=True, index=True,
        comment="סוג פעילות"
    )
    
    status: Mapped[Optional[str]] = mapped_column(
        Unicode(50), ForeignKey('worklog_statuses.code'), nullable=True, index=True,
        comment="סטטוס"
    )
    
    area_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True,
        comment="אזור (no FK in DB)"
    )
    
    supplier_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True,
        comment="ספק (no FK in DB)"
    )
    
    equipment_type_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="סוג ציוד (no FK in DB)"
    )

    # Date & Time
    report_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True,
        comment="תאריך הדוח"
    )
    
    start_time: Mapped[Optional[time]] = mapped_column(
        Time, nullable=True,
        comment="שעת התחלה"
    )
    
    end_time: Mapped[Optional[time]] = mapped_column(
        Time, nullable=True,
        comment="שעת סיום"
    )

    # Hours
    work_hours: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False,
        comment="שעות עבודה"
    )
    
    break_hours: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="שעות הפסקה"
    )
    
    total_hours: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="סה\"כ שעות"
    )

    # Work Details
    work_type: Mapped[Optional[str]] = mapped_column(
        Unicode(100), nullable=True,
        comment="סוג עבודה"
    )
    
    equipment_type: Mapped[Optional[str]] = mapped_column(
        Unicode(100), nullable=True,
        comment="סוג ציוד (legacy)"
    )
    
    activity_description: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="תיאור פעילות"
    )

    # Standard/Non-Standard
    is_standard: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True,
        comment="האם עבודה תקנית"
    )
    
    non_standard_reason: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="סיבה לעבודה לא תקנית"
    )

    # Approval
    approved_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="אושר על ידי (no FK in DB)"
    )
    
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="מתי אושר"
    )

    # Submission
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="מתי הוגש"
    )
    
    submitted_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="הוגש על ידי (no FK in DB)"
    )
    
    rejection_reason: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="סיבת דחייה"
    )

    # Workflow Flags
    sent_to_supplier: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True,
        comment="נשלח לספק"
    )
    
    sent_to_supplier_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    
    sent_to_accountant: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True,
        comment="נשלח לחשב"
    )
    
    sent_to_accountant_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    
    sent_to_area_manager: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True,
        comment="נשלח למנהל אזור"
    )
    
    sent_to_area_manager_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    # Equipment Scanning
    equipment_scanned: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True,
        comment="האם ציוד נסרק"
    )
    
    scan_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="מתי נסרק"
    )

    # Financial Snapshot
    hourly_rate_snapshot: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="תעריף שעתי (snapshot)"
    )
    
    rate_source: Mapped[Optional[str]] = mapped_column(
        Unicode(50), nullable=True,
        comment="מקור התעריף"
    )
    
    rate_source_name: Mapped[Optional[str]] = mapped_column(
        Unicode(100), nullable=True,
        comment="שם מקור התעריף"
    )
    
    cost_before_vat: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="עלות לפני מע\"מ"
    )
    
    vat_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=0.18,
        comment="שיעור מע\"מ"
    )
    
    cost_with_vat: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="עלות כולל מע\"מ"
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="הערות"
    )

    # Free-form JSON metadata (scan_flags, hours summary, etc.)
    metadata_json: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="מטא-דאטה ב-JSON (scan_flags, hours_summary)"
    )

    # Audit - TRANSACTIONS category (inherited from Base but not BaseModel!)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text('SYSUTCDATETIME()'),
        comment="נוצר ב"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text('SYSUTCDATETIME()'),
        comment="עודכן ב (trigger auto-updates)"
    )
    
    is_active: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, default=True,
        comment="פעיל"
    )
    
    # Note: NO deleted_at, NO version (TRANSACTIONS category)

    # Overnight / segments
    is_overnight: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    overnight_nights: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    overnight_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True, default=0)
    overnight_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True, default=0)
    net_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True, default=0)
    paid_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True, default=0)
    pdf_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    pdf_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships - one-way only
    work_order: Mapped[Optional["WorkOrder"]] = relationship("WorkOrder", lazy="select", foreign_keys="[Worklog.work_order_id]")
    user: Mapped[Optional["User"]] = relationship("User", lazy="select", foreign_keys="[Worklog.user_id]")
    project: Mapped[Optional["Project"]] = relationship("Project", lazy="select", foreign_keys="[Worklog.project_id]")
    equipment: Mapped[Optional["Equipment"]] = relationship("Equipment", lazy="select", foreign_keys="[Worklog.equipment_id]")
    activity_type: Mapped[Optional["ActivityType"]] = relationship("ActivityType", lazy="select", foreign_keys="[Worklog.activity_type_id]")

    # Properties
    @property
    def display_name(self) -> str:
        """Display name"""
        return f"Worklog {self.report_number} - {self.report_date}"

    def __repr__(self):
        return f"<Worklog(id={self.id}, report_number={self.report_number}, date={self.report_date})>"
