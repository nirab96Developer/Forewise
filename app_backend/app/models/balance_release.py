"""
BalanceRelease model - שחרורי יתרה מתקציב
SYNCED WITH DB - 17.11.2025
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import date
from decimal import Decimal

from sqlalchemy import Integer, String, Text, Boolean, Date, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.budget import Budget
    from app.models.user import User


class BalanceRelease(BaseModel):
    """BalanceRelease model - שחרור יתרה - SYNCED WITH DB"""

    __tablename__ = "balance_releases"

    __table_args__ = {'implicit_returning': False, 'extend_existing': True}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys - DB: int, NO / int, YES
    budget_id: Mapped[int] = mapped_column(Integer, ForeignKey("budgets.id"), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    # Release details - DB: nvarchar(255), NO / decimal, NO
    release_type: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Dates - DB: date, YES
    release_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    executed_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Status - DB: nvarchar(255), NO / bit, NO
    status: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Details - DB: nvarchar(-1), YES
    condition_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Actual amount - DB: decimal, YES
    actual_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)

    # Relationships
    # budget: Mapped["Budget"] = relationship("Budget")
    # creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])
    # approver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by])

    def __repr__(self):
        return f"<BalanceRelease(id={self.id}, budget_id={self.budget_id}, amount={self.amount})>"
