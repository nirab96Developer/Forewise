"""System rate model for pricing configuration"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from datetime import datetime

from app.models.base import Base


class SystemRate(Base):
    """System-wide default rates for equipment and services"""
    __tablename__ = "system_rates"
    
    id = Column(Integer, primary_key=True, index=True)
    rate_type = Column(String(50), nullable=False)  # 'hourly', 'daily', 'equipment', etc.
    rate_code = Column(String(50), nullable=False, unique=True)
    rate_name = Column(String(255), nullable=False)
    rate_value = Column(Float, nullable=False, default=0)
    currency = Column(String(10), default='ILS')
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SystemRate {self.rate_code}: {self.rate_value} {self.currency}>"
