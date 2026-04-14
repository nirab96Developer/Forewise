"""
File model - קבצים
SYNCED WITH DB - 17.11.2025
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import datetime

from sqlalchemy import Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

if TYPE_CHECKING:
    pass


class File(BaseModel):
    """File model - קובץ - SYNCED WITH DB"""

    __tablename__ = "files"

    __table_args__ = {"extend_existing": True}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # File details - DB: nvarchar(255), NO
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)

    # Storage - DB: nvarchar(500), NO / nvarchar(500), YES
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Ownership - DB: int, YES
    uploaded_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    # Entity association - DB: nvarchar(50), YES / int, YES
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Metadata - DB: nvarchar(-1), YES / nvarchar(500), YES
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Status - DB: bit, NO
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Timestamps - DB: datetime2, NO
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationships
    # uploader: Mapped[Optional["User"]] = relationship("User")

    def __repr__(self):
        return f"<File(id={self.id}, filename='{self.filename}')>"
