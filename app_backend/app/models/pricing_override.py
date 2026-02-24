"""Pricing override model for custom supplier/project pricing"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class PricingOverride(Base):
    """Override default pricing for specific suppliers/projects/equipment"""
    __tablename__ = "pricing_overrides"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    equipment_type_id = Column(Integer, ForeignKey("equipment_types.id"), nullable=True)
    rate_type = Column(String(50), nullable=False)  # 'hourly', 'daily', 'equipment', etc.
    rate_value = Column(Float, nullable=False)
    currency = Column(String(10), default='ILS')
    effective_from = Column(DateTime, nullable=True)
    effective_to = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(String(500), nullable=True)
    
    # Relationships
    supplier = relationship("Supplier", foreign_keys=[supplier_id])
    project = relationship("Project", foreign_keys=[project_id])
    
    def __repr__(self):
        return f"<PricingOverride {self.rate_type}: {self.rate_value} {self.currency}>"
