# app/models/work_order_coordination_log.py
# מודל יומן תיאום הזמנות - Work Order Coordination Log

from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.work_order import WorkOrder
    from app.models.user import User
    from app.models.supplier import Supplier


class WorkOrderCoordinationLog(BaseModel):
    """
    Work Order Coordination Log - יומן פעולות תיאום
    
    מתעד את כל הפעולות של מנהל תיאום הזמנות:
    - CALL: שיחה עם ספק
    - RESEND: שליחה מחדש
    - ESCALATE: הסלמה
    - NOTE: הערה כללית
    - MOVE_NEXT: העברה לספק הבא
    - STATUS_UPDATE: עדכון סטטוס
    """

    __tablename__ = "work_order_coordination_logs"
    __table_args__ = {"extend_existing": True}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    work_order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("work_orders.id"), nullable=False
    )
    created_by_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    old_supplier_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("suppliers.id"), nullable=True
    )
    new_supplier_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("suppliers.id"), nullable=True
    )

    # Action Details
    action_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # CALL, RESEND, ESCALATE, NOTE, MOVE_NEXT, STATUS_UPDATE
    
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    work_order: Mapped["WorkOrder"] = relationship(
        "WorkOrder", 
    )
    created_by: Mapped["User"] = relationship(
        "User", foreign_keys=[created_by_user_id]
    )
    old_supplier: Mapped[Optional["Supplier"]] = relationship(
        "Supplier", foreign_keys=[old_supplier_id]
    )
    new_supplier: Mapped[Optional["Supplier"]] = relationship(
        "Supplier", foreign_keys=[new_supplier_id]
    )

    def __repr__(self):
        return f"<CoordinationLog(id={self.id}, order={self.work_order_id}, action='{self.action_type}')>"
