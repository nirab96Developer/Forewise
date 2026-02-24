"""
Budget model - תקציבים
CORE entity with self-referential hierarchy
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import Date, ForeignKey, Integer, Numeric, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.budget_item import BudgetItem


class Budget(BaseModel):
    """
    Budget model - תקציב
    Table: budgets (25 columns)
    Category: CORE (has all audit columns)
    
    Self-referential hierarchy with parent_budget_id.
    """
    __tablename__ = "budgets"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Basic Information
    name: Mapped[str] = mapped_column(
        Unicode(200), nullable=False, index=True,
        comment="שם התקציב"
    )
    
    code: Mapped[Optional[str]] = mapped_column(
        Unicode(50), nullable=True, unique=True, index=True,
        comment="קוד תקציב"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="תיאור"
    )

    # Classification
    budget_type: Mapped[str] = mapped_column(
        Unicode(50), nullable=False,
        comment="סוג תקציב"
    )
    
    status: Mapped[str] = mapped_column(
        Unicode(50), nullable=False, default='DRAFT',
        comment="סטטוס: DRAFT, ACTIVE, CLOSED"
    )

    # Foreign Keys
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('users.id'), nullable=True, index=True,
        comment="נוצר על ידי"
    )
    
    parent_budget_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('budgets.id'), nullable=True, index=True,
        comment="תקציב אב (היררכיה)"
    )

    # Organization (no FK in DB - references only)
    region_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True,
        comment="אזור (no FK)"
    )
    
    area_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True,
        comment="תת-אזור (no FK)"
    )
    
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True,
        comment="פרויקט (no FK)"
    )

    # Amounts
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False,
        comment="סכום כולל"
    )
    
    allocated_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="סכום שהוקצה"
    )
    
    spent_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="סכום שהוצא"
    )
    
    committed_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="סכום מחויב"
    )

    # Time Period
    fiscal_year: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="שנת כספים"
    )
    
    start_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True,
        comment="תאריך התחלה"
    )
    
    end_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True,
        comment="תאריך סיום"
    )

    # Additional
    notes: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="הערות"
    )
    
    metadata_json: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="מטא-דאטה"
    )

    # Audit columns inherited from BaseModel:
    # created_at, updated_at, deleted_at, is_active, version

    # Relationships - one-way only
    created_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by],
        lazy="select"
    )
    
    parent_budget: Mapped[Optional["Budget"]] = relationship(
        "Budget",
        remote_side=[id],
        foreign_keys=[parent_budget_id],
        lazy="select"
    )
    
    items: Mapped[List["BudgetItem"]] = relationship(
        "BudgetItem",
        foreign_keys="BudgetItem.budget_id",
        lazy="select",
        overlaps="budget"
    )

    # Properties
    @property
    def display_name(self) -> str:
        return f"{self.code}: {self.name}" if self.code else self.name

    @property
    def remaining_amount(self) -> Decimal:
        """Calculate remaining budget"""
        return self.total_amount - (self.spent_amount or 0) - (self.committed_amount or 0)

    def __repr__(self):
        return f"<Budget(id={self.id}, code='{self.code}', name='{self.name}')>"
