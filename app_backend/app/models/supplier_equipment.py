"""SupplierEquipment — equipment inventory per supplier."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, text
from sqlalchemy.orm import relationship
from app.models.base import Base


class SupplierEquipment(Base):
    __tablename__ = "supplier_equipment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    equipment_category_id = Column(Integer, ForeignKey("equipment_categories.id"), index=True)
    equipment_model_id = Column(Integer, ForeignKey("equipment_models.id"), index=True)
    license_plate = Column(String(50))
    status = Column(String(30), default="available")   # available / busy / inactive
    quantity_available = Column(Integer, default=1)
    hourly_rate = Column(Numeric(10, 2))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=text("NOW()"))

    supplier = relationship("Supplier", back_populates="equipment")
    equipment_model = relationship("EquipmentModel", lazy="select")
