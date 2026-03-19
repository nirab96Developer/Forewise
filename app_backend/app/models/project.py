"""Project model."""

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.orm import relationship
try:
    from geoalchemy2 import Geometry
    _has_geo = True
except ImportError:
    _has_geo = False

from app.models.base import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), nullable=False, unique=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    region_id = Column(Integer, ForeignKey("regions.id"), index=True)
    area_id = Column(Integer, ForeignKey("areas.id"), index=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"))
    manager_id = Column(Integer, ForeignKey("users.id"))
    location_id = Column(Integer, ForeignKey("locations.id"))
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    forest_id = Column(Integer)
    forest_polygon_id = Column(Integer)
    status = Column(String(50), default="active")
    start_date = Column(Date)
    end_date = Column(Date)
    is_active = Column(Boolean, default=True)
    budget = Column(Numeric(15, 2))
    scope = Column(Text)
    total_hours = Column(Numeric(10, 2))

    work_type = Column(String(100))
    execution_type = Column(String(100))
    contractor_name = Column(String(255))
    permit_required = Column(Boolean, default=False)
    notes = Column(Text)
    metadata_json = Column(Text)
    created_at = Column(DateTime, server_default=text("NOW()"))
    updated_at = Column(DateTime, server_default=text("NOW()"))
    deleted_at = Column(DateTime)
    version = Column(Integer, default=1)

    if _has_geo:
        location_geom = Column(Geometry("POINT", srid=4326))

    region = relationship("Region", lazy="select")
    area = relationship("Area", lazy="select")
    manager = relationship("User", foreign_keys=[manager_id], lazy="select")
    location = relationship("Location", foreign_keys=[location_id], lazy="select")
