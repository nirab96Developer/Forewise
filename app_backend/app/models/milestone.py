"""
Milestone model - אבני דרך בפרויקט
SYNCED WITH DB - 17.11.2025
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import date

from sqlalchemy import Integer, String, Text, Boolean, Date, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class Milestone(BaseModel):
    """Milestone model - אבן דרך - SYNCED WITH DB"""

    __tablename__ = "milestones"

    __table_args__ = {"extend_existing": True}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys - DB: int, NO / int, YES
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    assigned_to: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    # Basic info - DB: nvarchar(200), NO
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Dates - DB: date, NO / date, NO / date, YES
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    completed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Progress - DB: float, NO / int, NO
    progress_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)

    # Status - DB: nvarchar(20), NO
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    # Dependencies - DB: int, YES
    depends_on_milestone_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("milestones.id"), nullable=True
    )

    # Additional - DB: nvarchar(-1), YES
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deliverables: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # DB: bit, NO
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Relationships
    # project: Mapped["Project"] = relationship("Project")
    # assigned_user: Mapped[Optional["User"]] = relationship("User")

    def __repr__(self):
        return f"<Milestone(id={self.id}, name='{self.name}', status='{self.status}')>"
