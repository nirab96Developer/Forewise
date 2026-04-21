"""
WorkOrder model - הזמנות עבודה
CORE entity with full audit columns and state machine
"""

from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Unicode, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.supplier import Supplier
    from app.models.equipment import Equipment
    from app.models.equipment_model import EquipmentModel
    from app.models.location import Location
    from app.models.user import User


class WorkOrder(BaseModel):
    """
    WorkOrder model - הזמנת עבודה
    Table: work_orders
    Category: CORE (has created_at, updated_at, deleted_at, is_active, version)

    Live state machine:
        PENDING                                    (created by Work Manager)
          ↓ send-to-supplier
        DISTRIBUTING                               (sent to Supplier via portal)
          ↓ supplier accepts
        SUPPLIER_ACCEPTED_PENDING_COORDINATOR      (Coordinator must approve)
          ↓ coordinator approve
        APPROVED_AND_SENT
          ↓ scan-equipment / confirm-equipment
        IN_PROGRESS
          ↓ close
        COMPLETED

    Branch states:
        REJECTED              — rejected by Coordinator or Supplier (terminal)
        CANCELLED             — cancelled by Admin                  (terminal)
        EXPIRED               — supplier didn't respond in 3h       (terminal)
        STOPPED               — equipment removed mid-flight        (terminal)
        NEEDS_RE_COORDINATION — wrong equipment scanned, back to coordinator
    """
    __tablename__ = "work_orders"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Business Identifier - UNIQUE!
    order_number: Mapped[int] = mapped_column(
        Integer, nullable=False, unique=True, index=True,
        comment="מספר הזמנה ייחודי"
    )

    # Basic Information
    title: Mapped[Optional[str]] = mapped_column(
        Unicode(200), nullable=True,
        comment="כותרת ההזמנה"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="תיאור מפורט"
    )

    # Foreign Keys - Organization
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('projects.id'), nullable=True, index=True,
        comment="פרויקט"
    )
    
    location_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('locations.id'), nullable=True, index=True,
        comment="מיקום"
    )
    
    created_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('users.id'), nullable=True, index=True,
        comment="נוצר על ידי"
    )

    # Foreign Keys - Supplier & Equipment
    supplier_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('suppliers.id'), nullable=True, index=True,
        comment="ספק"
    )
    
    equipment_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('equipment.id'), nullable=True, index=True,
        comment="ציוד (required when APPROVED/ACTIVE)"
    )
    
    equipment_type: Mapped[Optional[str]] = mapped_column(
        Unicode(100), nullable=True,
        comment="סוג ציוד (legacy - use equipment_id)"
    )

    equipment_license_plate: Mapped[Optional[str]] = mapped_column(
        Unicode(20), nullable=True,
        comment="מספר רישוי כלי (מתמלא אוטומטית בסריקה/אישור ספק)"
    )

    requested_equipment_model_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("equipment_models.id"), nullable=True, index=True,
        comment="דגם כלי מבוקש להזמנה"
    )

    # Status & Priority
    status: Mapped[Optional[str]] = mapped_column(
        Unicode(50), ForeignKey('work_order_statuses.code'), nullable=True, index=True,
        comment=(
            "סטטוס (UPPERCASE): PENDING, DISTRIBUTING, "
            "SUPPLIER_ACCEPTED_PENDING_COORDINATOR, APPROVED_AND_SENT, "
            "IN_PROGRESS, COMPLETED, REJECTED, CANCELLED, EXPIRED, STOPPED, "
            "NEEDS_RE_COORDINATION"
        )
    )
    
    priority: Mapped[Optional[str]] = mapped_column(
        Unicode(20), nullable=True, index=True,
        comment="עדיפות: LOW, MEDIUM, HIGH, URGENT"
    )

    # Work Dates
    work_start_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True,
        comment="תאריך התחלה מתוכנן"
    )
    
    work_end_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True,
        comment="תאריך סיום מתוכנן"
    )

    # Portal/Token for Supplier
    portal_token: Mapped[Optional[str]] = mapped_column(
        Unicode(255), nullable=True, unique=True, index=True,
        comment="טוקן לכניסת ספק בפורטל"
    )
    
    portal_token_expires: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="תוקף טוקן (old)"
    )
    
    portal_expiry: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="תוקף טוקן"
    )
    
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="תוקף טוקן"
    )
    
    response_received_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="מתי התקבלה תשובה מהספק"
    )
    
    supplier_response_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="מתי הספק הגיב"
    )

    # Work Details - Hours
    estimated_hours: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="שעות משוערות"
    )
    
    actual_hours: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="שעות בפועל"
    )

    # Financial
    hourly_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="תעריף שעתי"
    )
    
    total_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="סכום כולל משוער"
    )
    
    frozen_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=0,
        comment="סכום מוקפא בתקציב"
    )
    
    charged_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=0,
        comment="סכום שחויב בפועל"
    )
    
    remaining_frozen: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True, default=0,
        comment="יתרת סכום מוקפא"
    )

    days: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="מספר ימי עבודה"
    )
    
    overnight_nights: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="מספר לינות"
    )
    
    has_overnight: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="האם כולל לינת שטח"
    )
    
    allocation_method: Mapped[Optional[str]] = mapped_column(
        Unicode(20), nullable=True, default='FAIR_ROTATION',
        comment="שיטת הקצאה: FAIR_ROTATION / MANUAL"
    )

    # Supplier Constraints/Rejection
    constraint_reason_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('supplier_constraint_reasons.id'), nullable=True,
        comment="סיבת אילוץ ספק"
    )
    
    constraint_notes: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="הערות אילוץ"
    )
    
    rejection_reason_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('supplier_rejection_reasons.id'), nullable=True,
        comment="סיבת דחייה"
    )
    
    rejection_notes: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="הערות דחייה"
    )
    
    is_forced_selection: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, default=False,
        comment="האם בחירת ספק כפויה (עקוף rotation)"
    )

    # Overnight guard (שמירת לילה)
    requires_guard: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="האם נדרשת שמירת לילה"
    )
    guard_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="מספר לילות שמירה"
    )

    # Relationships - Enabled for eager loading optimization
    project: Mapped[Optional["Project"]] = relationship(
        "Project", 
        lazy="noload",  # Don't load by default, use joinedload() in queries
        foreign_keys=[project_id]
    )
    supplier: Mapped[Optional["Supplier"]] = relationship(
        "Supplier", 
        lazy="noload",
        foreign_keys=[supplier_id]
    )
    equipment: Mapped[Optional["Equipment"]] = relationship(
        "Equipment", 
        lazy="noload",
        foreign_keys=[equipment_id]
    )
    requested_equipment_model: Mapped[Optional["EquipmentModel"]] = relationship(
        "EquipmentModel",
        lazy="noload",
        foreign_keys=[requested_equipment_model_id]
    )
    location: Mapped[Optional["Location"]] = relationship(
        "Location", 
        lazy="noload",
        foreign_keys=[location_id]
    )
    created_by: Mapped[Optional["User"]] = relationship(
        "User", 
        lazy="noload",
        foreign_keys=[created_by_id]
    )

    # Properties - Display only, no business logic!
    @property
    def display_name(self) -> str:
        """Display name for UI"""
        return f"WO-{self.order_number}: {self.title or 'ללא כותרת'}"

    @property
    def is_pending(self) -> bool:
        """Check if status is PENDING"""
        return self.status == 'PENDING'

    @property
    def is_approved(self) -> bool:
        """Check if status is APPROVED_AND_SENT (post-coordinator approval)."""
        return self.status == 'APPROVED_AND_SENT'

    @property
    def is_in_progress(self) -> bool:
        """Check if work has started (equipment scanned)."""
        return self.status == 'IN_PROGRESS'

    @property
    def is_status_active(self) -> bool:
        """DEPRECATED: legacy 'ACTIVE' status; use is_in_progress instead.
        Kept temporarily for any caller still on the old name."""
        return self.status in ('ACTIVE', 'IN_PROGRESS')

    @property
    def is_completed(self) -> bool:
        """Check if status is COMPLETED"""
        return self.status == 'COMPLETED'

    @property
    def is_rejected(self) -> bool:
        """Check if status is REJECTED"""
        return self.status == 'REJECTED'

    @property
    def is_cancelled(self) -> bool:
        """Check if status is CANCELLED"""
        return self.status == 'CANCELLED'

    @property
    def is_closed(self) -> bool:
        """Check if work order is closed (completed, rejected, or cancelled)"""
        return self.status in ('COMPLETED', 'REJECTED', 'CANCELLED')

    def __repr__(self):
        return f"<WorkOrder(id={self.id}, order_number={self.order_number}, status='{self.status}')>"
