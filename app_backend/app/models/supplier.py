"""Supplier model."""

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app.models.base import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), nullable=False, unique=True)
    name = Column(String(200), nullable=False)
    contact_name = Column(String(200))
    contact_phone = Column(String(50))
    contact_email = Column(String(200))
    phone = Column(String(50))
    email = Column(String(200))
    address = Column(String(500))
    tax_id = Column(String(50))
    bank_account = Column(String(100))
    supplier_type = Column(String(50))
    rating = Column(Numeric(3, 2))
    region_id = Column(Integer, ForeignKey("regions.id"), index=True)
    area_id = Column(Integer, ForeignKey("areas.id"), index=True)
    is_active = Column(Boolean, default=True)
    total_jobs = Column(Integer, default=0)
    active_area_ids = Column(ARRAY(Integer), default=[])
    active_region_ids = Column(ARRAY(Integer), default=[])
    total_assignments = Column(Integer, default=0)
    total_skips = Column(Integer, default=0)
    priority_score = Column(Integer, default=0)
    average_response_time = Column(Float)
    last_selected = Column(DateTime)
    metadata_json = Column(String)
    created_at = Column(DateTime, server_default=text("NOW()"))
    updated_at = Column(DateTime, server_default=text("NOW()"))
    deleted_at = Column(DateTime)
    version = Column(Integer, default=1)

    region = relationship("Region", lazy="select")
    area = relationship("Area", lazy="select")
    equipment = relationship("SupplierEquipment", back_populates="supplier", cascade="all, delete-orphan", lazy="select")
