"""
SupplierInvitation model - Fair Rotation Distribution
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import datetime

from sqlalchemy import Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.supplier import Supplier
    from app.models.work_order import WorkOrder
    from app.models.user import User


class SupplierInvitation(BaseModel):
    """
    SupplierInvitation - invitation to supplier for work order.
    
    Flow:
    1. Coordinator clicks send-to-suppliers on a WO
    2. System picks supplier via fair rotation
    3. Invitation created with unique token
    4. Supplier accepts or declines via portal
    5. If accepted -> WO status = SUPPLIER_ACCEPTED_PENDING_COORDINATOR
    6. Coordinator approves -> WO status = APPROVED_AND_SENT
    7. If declined -> next supplier in rotation gets invitation
    """
    __tablename__ = "supplier_invitations"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Links
    work_order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("work_orders.id"), nullable=False, index=True
    )
    supplier_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("suppliers.id"), nullable=False, index=True
    )
    invited_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )

    # Token for supplier portal access
    token: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    # Status: PENDING, VIEWED, ACCEPTED, DECLINED, EXPIRED, CANCELLED
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="PENDING", index=True
    )

    # Timestamps
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    viewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Supplier response
    response_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decline_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Rotation tracking
    rotation_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    def __repr__(self):
        return f"<SupplierInvitation(id={self.id}, wo={self.work_order_id}, supplier={self.supplier_id}, status={self.status})>"
