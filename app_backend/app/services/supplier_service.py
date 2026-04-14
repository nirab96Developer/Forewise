"""
Supplier Service - לוגיקה עסקית לספקים
"""

from typing import Optional, List, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_

from app.models.supplier import Supplier
from app.models.supplier_equipment import SupplierEquipment
from app.models.equipment_model import EquipmentModel
from app.models.work_order import WorkOrder
from app.schemas.supplier import (
    SupplierCreate,
    SupplierUpdate,
    SupplierSearch,
    SupplierStatistics,
    SupplierBrief,
    SupplierEquipmentCreate,
    SupplierEquipmentUpdate,
)
from app.services.base_service import BaseService
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException


class SupplierService(BaseService[Supplier]):
    """
    Supplier Service - שירות ספקים
    
    Business rules:
    1. UNIQUE: name (case-insensitive)
    2. UNIQUE: code (if provided)
    3. UNIQUE: tax_id (if provided)
    4. Cannot delete if has active work orders
    """
    
    def __init__(self):
        super().__init__(Supplier)
    
    def create(
        self,
        db: Session,
        data: SupplierCreate,
        current_user_id: int
    ) -> Supplier:
        """Create new supplier with UNIQUE validation"""
        # Validate UNIQUE: name (case-insensitive)
        existing = db.query(Supplier).filter(
            func.lower(Supplier.name) == func.lower(data.name),
            Supplier.deleted_at.is_(None)
        ).first()
        if existing:
            raise DuplicateException(f"Supplier with name '{data.name}' already exists")
        
        # Validate UNIQUE: code
        if data.code:
            existing = db.query(Supplier).filter(
                Supplier.code == data.code,
                Supplier.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Supplier with code '{data.code}' already exists")
        
        # Validate UNIQUE: tax_id
        if data.tax_id:
            existing = db.query(Supplier).filter(
                Supplier.tax_id == data.tax_id,
                Supplier.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Supplier with tax_id '{data.tax_id}' already exists")
        
        # Create
        supplier_dict = data.model_dump(exclude_unset=True)
        supplier = Supplier(**supplier_dict)
        
        db.add(supplier)
        db.commit()
        db.refresh(supplier)
        
        return supplier
    
    def update(
        self,
        db: Session,
        supplier_id: int,
        data: SupplierUpdate,
        current_user_id: int
    ) -> Supplier:
        """Update supplier with version check and UNIQUE validation"""
        supplier = self.get_by_id_or_404(db, supplier_id)
        
        # Version check
        if data.version is not None and supplier.version != data.version:
            raise DuplicateException(
                f"Supplier was modified by another user. "
                f"Expected version {data.version}, current is {supplier.version}"
            )
        
        update_dict = data.model_dump(exclude_unset=True, exclude={'version'})
        
        # Validate UNIQUE: name (if changed)
        if 'name' in update_dict and update_dict['name'] and update_dict['name'] != supplier.name:
            existing = db.query(Supplier).filter(
                func.lower(Supplier.name) == func.lower(update_dict['name']),
                Supplier.id != supplier_id,
                Supplier.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Supplier with name '{update_dict['name']}' already exists")
        
        # Validate UNIQUE: code (if changed)
        if 'code' in update_dict and update_dict['code'] and update_dict['code'] != supplier.code:
            existing = db.query(Supplier).filter(
                Supplier.code == update_dict['code'],
                Supplier.id != supplier_id,
                Supplier.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Supplier with code '{update_dict['code']}' already exists")
        
        # Validate UNIQUE: tax_id (if changed)
        if 'tax_id' in update_dict and update_dict['tax_id'] and update_dict['tax_id'] != supplier.tax_id:
            existing = db.query(Supplier).filter(
                Supplier.tax_id == update_dict['tax_id'],
                Supplier.id != supplier_id,
                Supplier.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Supplier with tax_id '{update_dict['tax_id']}' already exists")
        
        # Update
        for field, value in update_dict.items():
            setattr(supplier, field, value)
        
        if supplier.version is not None:
            supplier.version += 1
        
        db.commit()
        db.refresh(supplier)
        
        return supplier
    
    def list(
        self,
        db: Session,
        search: SupplierSearch
    ) -> Tuple[List[Supplier], int]:
        """List suppliers with filters"""
        query = self._base_query(db, include_deleted=False)
        
        # Free text search
        if search.q:
            search_term = f"%{search.q}%"
            query = query.where(
                or_(
                    Supplier.name.ilike(search_term),
                    Supplier.code.ilike(search_term),
                    Supplier.tax_id.ilike(search_term)
                )
            )
        
        # Filters
        if search.supplier_type:
            query = query.where(Supplier.supplier_type == search.supplier_type.value)
        
        if search.is_active is not None:
            query = query.where(Supplier.is_active == search.is_active)
        
        if search.min_rating:
            query = query.where(Supplier.rating >= search.min_rating)
        
        if search.region_id:
            query = query.where(Supplier.region_id == search.region_id)
        
        if search.area_id:
            query = query.where(Supplier.area_id == search.area_id)
        
        # Count
        total = db.execute(
            select(func.count()).select_from(query.subquery())
        ).scalar() or 0
        
        # Sort
        sort_column = getattr(Supplier, search.sort_by, Supplier.name)
        if search.sort_desc:
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Paginate
        offset = (search.page - 1) * search.page_size
        query = query.offset(offset).limit(search.page_size)
        
        suppliers = db.execute(query).scalars().all()
        
        return suppliers, total
    
    def soft_delete(
        self,
        db: Session,
        supplier_id: int,
        current_user_id: int
    ) -> Supplier:
        """
        Soft delete supplier
        
        Business rule: Check no active work orders
        """
        self.get_by_id_or_404(db, supplier_id)
        
        # Business rule: Cannot delete if has active work orders
        active_work_orders = db.query(WorkOrder).filter(
            WorkOrder.supplier_id == supplier_id,
            or_(
                WorkOrder.status.is_(None),
                WorkOrder.status.notin_(['COMPLETED', 'REJECTED', 'CANCELLED']),
            ),
            WorkOrder.deleted_at.is_(None)
        ).count()
        
        if active_work_orders > 0:
            raise ValidationException(
                f"Cannot delete supplier with {active_work_orders} active work orders. "
                "Complete or cancel them first."
            )
        
        # Soft delete
        deleted = super().soft_delete(db, supplier_id, commit=True)
        
        return deleted
    
    def restore(
        self,
        db: Session,
        supplier_id: int,
        current_user_id: int
    ) -> Supplier:
        """Restore soft-deleted supplier"""
        restored = super().restore(db, supplier_id, commit=True)
        return restored
    
    def get_by_code(
        self,
        db: Session,
        code: str,
        include_deleted: bool = False
    ) -> Optional[Supplier]:
        """Get supplier by code"""
        query = select(Supplier).where(Supplier.code == code)
        
        if not include_deleted:
            query = query.where(Supplier.deleted_at.is_(None))
        
        return db.execute(query).scalar_one_or_none()
    
    def get_statistics(
        self,
        db: Session,
        filters: Optional[dict] = None
    ) -> SupplierStatistics:
        """Get supplier statistics"""
        query = select(Supplier).where(Supplier.deleted_at.is_(None))
        
        # Apply filters
        if filters:
            if filters.get('supplier_type'):
                query = query.where(Supplier.supplier_type == filters['supplier_type'])
        
        # Get all suppliers
        all_suppliers = db.execute(query).scalars().all()
        
        # Calculate statistics
        stats = SupplierStatistics(
            total=len(all_suppliers),
            active_count=sum(1 for s in all_suppliers if s.is_active),
            average_rating=None
        )
        
        # By type
        by_type = {}
        for s in all_suppliers:
            if s.supplier_type:
                by_type[s.supplier_type] = by_type.get(s.supplier_type, 0) + 1
        stats.by_type = by_type
        
        # Average rating
        ratings = [s.rating for s in all_suppliers if s.rating is not None]
        if ratings:
            stats.average_rating = Decimal(str(sum(ratings) / len(ratings)))
        
        # Top rated (top 5)
        top = sorted(
            [s for s in all_suppliers if s.rating is not None],
            key=lambda x: x.rating,
            reverse=True
        )[:5]
        
        stats.top_rated = [
            SupplierBrief(
                id=s.id,
                name=s.name,
                code=s.code,
                supplier_type=s.supplier_type,
                is_active=s.is_active,
                rating=s.rating
            )
            for s in top
        ]
        
        return stats

    def list_supplier_equipment(self, db: Session, supplier_id: int) -> List[SupplierEquipment]:
        """List active equipment inventory rows for supplier."""
        self.get_by_id_or_404(db, supplier_id)
        rows = (
            db.query(SupplierEquipment)
            .filter(
                SupplierEquipment.supplier_id == supplier_id,
                SupplierEquipment.is_active == True,
            )
            .order_by(SupplierEquipment.id.asc())
            .all()
        )
        return rows

    def add_supplier_equipment(
        self,
        db: Session,
        supplier_id: int,
        data: SupplierEquipmentCreate,
    ) -> SupplierEquipment:
        """Attach equipment model + license plate to supplier."""
        self.get_by_id_or_404(db, supplier_id)

        model = db.query(EquipmentModel).filter(EquipmentModel.id == data.equipment_model_id).first()
        if not model or not model.is_active:
            raise ValidationException(f"Equipment model {data.equipment_model_id} not found or inactive")

        normalized_plate = data.license_plate.strip().upper()
        if not normalized_plate:
            raise ValidationException("license_plate is required")

        duplicate = (
            db.query(SupplierEquipment.id)
            .filter(
                SupplierEquipment.supplier_id == supplier_id,
                func.upper(SupplierEquipment.license_plate) == normalized_plate,
                SupplierEquipment.is_active == True,
            )
            .first()
        )
        if duplicate:
            raise DuplicateException("Supplier already has this license plate")

        row = SupplierEquipment(
            supplier_id=supplier_id,
            equipment_model_id=data.equipment_model_id,
            # Keep legacy category for compatibility where model has category.
            equipment_category_id=model.category_id,
            license_plate=normalized_plate,
            status=data.status.value,
            quantity_available=data.quantity_available,
            hourly_rate=data.hourly_rate,
            is_active=True,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def update_supplier_equipment(
        self,
        db: Session,
        supplier_id: int,
        supplier_equipment_id: int,
        data: SupplierEquipmentUpdate,
    ) -> SupplierEquipment:
        """Update supplier equipment row status/availability/rates."""
        row = (
            db.query(SupplierEquipment)
            .filter(
                SupplierEquipment.id == supplier_equipment_id,
                SupplierEquipment.supplier_id == supplier_id,
                SupplierEquipment.is_active == True,
            )
            .first()
        )
        if not row:
            raise NotFoundException("Supplier equipment not found")

        update_dict = data.model_dump(exclude_unset=True)
        if "status" in update_dict and update_dict["status"] is not None:
            row.status = update_dict["status"].value
        if "quantity_available" in update_dict and update_dict["quantity_available"] is not None:
            row.quantity_available = update_dict["quantity_available"]
        if "hourly_rate" in update_dict and update_dict["hourly_rate"] is not None:
            row.hourly_rate = update_dict["hourly_rate"]

        db.commit()
        db.refresh(row)
        return row

# Alias methods for backward-compat with older router 
    def list_with_filters(self, db, filters):
        return self.list(db, filters)

    def create_supplier(self, db, data):
        return self.create(db, data)

    def update_supplier(self, db, supplier_id, data):
        return self.update(db, supplier_id, data, current_user_id=None)


# Module-level singleton instance
supplier_service = SupplierService()
