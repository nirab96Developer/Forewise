"""Biometric credential model for WebAuthn/Face ID/Touch ID"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, LargeBinary
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class BiometricCredential(Base):
    """Store WebAuthn credentials for biometric authentication"""
    __tablename__ = "biometric_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    credential_id = Column(String(512), unique=True, nullable=False)
    public_key = Column(LargeBinary, nullable=False)  # COSE public key
    sign_count = Column(Integer, default=0)
    device_name = Column(String(255), nullable=True)  # "iPhone 15", "MacBook Pro", etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    # Relationship
    user = relationship("User", back_populates="biometric_credentials")

    def __repr__(self):
        return f"<BiometricCredential {self.credential_id[:20]}... for user {self.user_id}>"
