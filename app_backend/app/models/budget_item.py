"""
BudgetItem model - פריטי תקציב
CORE entity
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, Numeric, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.budget import Budget


class BudgetItem(BaseModel):
    """
    BudgetItem model - פריט תקציב
    Table: budget_items (20 columns)
    Category: CORE
    
    Line item within a budget.
    """
    __tablename__ = "budget_items"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key - Budget (REQUIRED!)
    budget_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('budgets.id'), nullable=False, index=True,
        comment="תקציב"
    )

    # Basic Information
    item_name: Mapped[str] = mapped_column(
        Unicode(200), nullable=False,
        comment="שם הפריט"
    )
    
    item_code: Mapped[Optional[str]] = mapped_column(
        Unicode(50), nullable=True, index=True,
        comment="קוד פריט"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="תיאור"
    )

    # Classification
    item_type: Mapped[str] = mapped_column(
        Unicode(50), nullable=False,
        comment="סוג פריט"
    )
    
    category: Mapped[Optional[str]] = mapped_column(
        Unicode(50), nullable=True, index=True,
        comment="קטגוריה"
    )
    
    status: Mapped[str] = mapped_column(
        Unicode(50), nullable=False, default='PLANNED',
        comment="סטטוס: PLANNED, APPROVED, IN_USE, COMPLETED"
    )
    
    priority: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="עדיפות"
    )

    # Amounts
    planned_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False,
        comment="סכום מתוכנן"
    )
    
    approved_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="סכום מאושר"
    )
    
    committed_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="סכום מחויב"
    )
    
    actual_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="סכום בפועל"
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

    # Audit columns from BaseModel:
    # created_at, updated_at, deleted_at, is_active, version

    # Relationship
    budget: Mapped["Budget"] = relationship(
        "Budget",
        foreign_keys=[budget_id],
        lazy="select"
    )

    # Properties
    @property
    def remaining_amount(self) -> Decimal:
        """Calculate remaining from approved amount"""
        base = self.approved_amount or self.planned_amount
        return base - (self.actual_amount or 0) - (self.committed_amount or 0)

    def __repr__(self):
        return f"<BudgetItem(id={self.id}, name='{self.item_name}', budget_id={self.budget_id})>"
