"""
ProjectAssignment model - שיוכי משתמשים לפרויקטים
SYNCED WITH DB - 17.11.2025
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import date
from decimal import Decimal

from sqlalchemy import Integer, String, Text, Boolean, Date, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

if TYPE_CHECKING:
    pass


class ProjectAssignment(BaseModel):
    """ProjectAssignment model - שיוך משתמש לפרויקט - SYNCED WITH DB"""

    __tablename__ = "project_assignments"

    __table_args__ = {'implicit_returning': False, 'extend_existing': True}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys - DB: int, NO / int, NO
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    # Role and status - DB: nvarchar(255), NO
    role: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(255), nullable=False)

    # Dates - DB: date, NO / date, YES
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Allocation - DB: int, NO / decimal, YES
    allocation_percentage: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    actual_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    # Permissions - DB: bit, NO
    can_approve_reports: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_manage_team: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_edit_budget: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Additional - DB: nvarchar(-1), YES
    responsibilities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Approval - DB: int, YES / date, YES
    approved_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationships
    # project: Mapped["Project"] = relationship("Project")
    # user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    # approved_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by_id])

    def __repr__(self):
        return f"<ProjectAssignment(id={self.id}, project_id={self.project_id}, user_id={self.user_id})>"
