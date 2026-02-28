"""DeviceToken — persistent trusted-device record for biometric re-login."""

import uuid
from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, ForeignKey, text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base


class DeviceToken(Base):
    __tablename__ = "device_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(128), nullable=False, unique=True, index=True)
    device_id = Column(UUID(as_uuid=True), nullable=False)
    device_name = Column(String(255))
    device_os = Column(String(100))
    is_active = Column(Boolean, nullable=False, default=True)
    last_used_at = Column(DateTime)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=text("NOW()"))

    user = relationship("User", back_populates="device_tokens", lazy="select")
