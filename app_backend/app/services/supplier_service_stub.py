"""SupplierService — stub restored from backup context."""

from sqlalchemy.orm import Session
from app.models.supplier import Supplier


class SupplierService:
    def get(self, db: Session, supplier_id: int):
        return db.query(Supplier).filter(Supplier.id == supplier_id, Supplier.is_active == True).first()

    def list(self, db: Session, area_id: int = None, region_id: int = None, is_active: bool = True):
        q = db.query(Supplier).filter(Supplier.is_active == is_active)
        if area_id:
            q = q.filter(Supplier.area_id == area_id)
        if region_id:
            q = q.filter(Supplier.region_id == region_id)
        return q.all()
