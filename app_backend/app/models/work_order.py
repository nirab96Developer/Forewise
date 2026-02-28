"""
WorkOrder model - הזמנות עבודה
CORE entity with full audit columns and state machine
"""

from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Unicode, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.supplier import Supplier
    from app.models.equipment import Equipment
    from app.models.equipment_model import EquipmentModel
    from app.models.location import Location
    from app.models.user import User
    from app.models.work_order_status import WorkOrderStatus as WorkOrderStatusModel
    from app.models.supplier_constraint_reason import SupplierConstraintReason
    from app.models.supplier_rejection_reason import SupplierRejectionReason
    from app.models.worklog import Worklog


class WorkOrder(BaseModel):
    """
    WorkOrder model - הזמנת עבודה
    Table: work_orders
    Category: CORE (has created_at, updated_at, deleted_at, is_active, version)
    
    Represents a work order in the system with state machine:
    PENDING → APPROVED → ACTIVE → COMPLETED
    Can be REJECTED or CANCELLED at various stages.
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

    requested_equipment_model_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("equipment_models.id"), nullable=True, index=True,
        comment="דגם כלי מבוקש להזמנה"
    )

    # Status & Priority
    status: Mapped[Optional[str]] = mapped_column(
        Unicode(50), ForeignKey('work_order_statuses.code'), nullable=True, index=True,
        comment="סטטוס: PENDING, APPROVED, ACTIVE, COMPLETED, REJECTED, CANCELLED"
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
    
    # Note: remaining_frozen_amount is a COMPUTED COLUMN in DB - do not include!
    # remaining_frozen_amount = frozen_amount - charged_amount (computed by DB)

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
        """Check if status is APPROVED"""
        return self.status == 'APPROVED'

    @property
    def is_status_active(self) -> bool:
        """Check if status is ACTIVE (renamed to avoid conflict with BaseModel.is_active)"""
        return self.status == 'ACTIVE'

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
