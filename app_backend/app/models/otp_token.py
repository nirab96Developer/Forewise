"""OTPToken model — one-time password tokens for login / 2FA."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.orm import relationship
from app.models.base import Base


class OTPToken(Base):
    __tablename__ = "otp_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(64))            # plain code (legacy, kept for compat)
    token_hash = Column(String(128))      # sha256 of token (legacy)
    code_hash = Column(String(128))       # sha256 of 6-digit OTP (new spec)
    purpose = Column(String(50), nullable=False, default="login")
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime)
    is_used = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    attempts = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, server_default=text("NOW()"))
    updated_at = Column(DateTime, nullable=False, server_default=text("NOW()"), onupdate=text("NOW()"))
    deleted_at = Column(DateTime)
    version = Column(Integer, nullable=False, default=1)

    user = relationship("User", back_populates="otp_tokens")
