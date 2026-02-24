"""
Equipment Service - לוגיקה עסקית לציוד
Handles all business logic for equipment management
"""

from datetime import datetime, date
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func

from app.models.equipment import Equipment
from app.models.equipment_type import EquipmentType
from app.models.equipment_category import EquipmentCategory
from app.models.supplier import Supplier
from app.models.location import Location
from app.models.equipment_assignment import EquipmentAssignment
from app.schemas.equipment import (
    EquipmentCreate,
    EquipmentUpdate,
    EquipmentSearch,
    EquipmentStatistics
)
from app.services.base_service import BaseService
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException


class EquipmentService(BaseService[Equipment]):
    """
    Equipment Service - שירות ציוד
    
    Business rules:
    1. Unique constraints: code, license_plate, qr_code
    2. FK validation: type_id, category_id, supplier_id
    3. Cannot delete if has active assignments
    4. Status transitions validation
    """
    
    def __init__(self):
        super().__init__(Equipment)
    
    def create(
        self,
        db: Session,
        data: EquipmentCreate,
        current_user_id: Optional[int] = None
    ) -> Equipment:
        """
        Create new equipment
        
        Args:
            db: Database session
            data: Equipment creation data
            current_user_id: ID of user creating equipment
        
        Returns:
            Created equipment
        
        Raises:
            ValidationError: If validation fails
            ConflictError: If unique constraint violated
        """
        # Validate FK: type_id
        if data.type_id:
            type_obj = db.query(EquipmentType).filter_by(id=data.type_id).first()
            if not type_obj:
                raise ValidationException(f"Equipment type {data.type_id} not found")
            if not type_obj.is_active:
                raise ValidationException(f"Equipment type {data.type_id} is not active")
        
        # Validate FK: category_id (no FK in DB, but validate if provided)
        if data.category_id:
            category = db.query(EquipmentCategory).filter_by(id=data.category_id).first()
            if not category:
                raise ValidationException(f"Equipment category {data.category_id} not found")
            if not category.is_active:
                raise ValidationException(f"Equipment category {data.category_id} is not active")
        
        # Validate FK: supplier_id (no FK in DB, but validate if provided)
        if data.supplier_id:
            supplier = db.query(Supplier).filter_by(id=data.supplier_id).first()
            if not supplier:
                raise ValidationException(f"Supplier {data.supplier_id} not found")
            if not supplier.is_active:
                raise ValidationException(f"Supplier {data.supplier_id} is not active")
        
        # Validate FK: location_id (no FK in DB, but validate if provided)
        if data.location_id:
            location = db.query(Location).filter_by(id=data.location_id).first()
            if not location:
                raise ValidationException(f"Location {data.location_id} not found")
        
        # Check UNIQUE constraints
        if data.code:
            existing = db.query(Equipment).filter(
                Equipment.code == data.code,
                Equipment.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Equipment with code '{data.code}' already exists")
        
        if data.license_plate:
            existing = db.query(Equipment).filter(
                Equipment.license_plate == data.license_plate,
                Equipment.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Equipment with license plate '{data.license_plate}' already exists")
        
        if data.qr_code:
            existing = db.query(Equipment).filter(
                Equipment.qr_code == data.qr_code,
                Equipment.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Equipment with QR code '{data.qr_code}' already exists")
        
        # Business validation: maintenance dates
        if data.last_maintenance and data.next_maintenance:
            if data.next_maintenance < data.last_maintenance:
                raise ValidationException("next_maintenance must be after last_maintenance")
        
        # Create equipment directly
        equipment_dict = data.model_dump(exclude_unset=True)
        equipment = Equipment(**equipment_dict)
        
        db.add(equipment)
        db.commit()
        db.refresh(equipment)
        
        return equipment
    
    def update(
        self,
        db: Session,
        equipment_id: int,
        data: EquipmentUpdate,
        current_user_id: Optional[int] = None
    ) -> Equipment:
        """
        Update equipment
        
        Args:
            db: Database session
            equipment_id: Equipment ID
            data: Update data
            current_user_id: ID of user updating
        
        Returns:
            Updated equipment
        
        Raises:
            NotFoundError: If equipment not found
            ValidationError: If validation fails
            ConflictError: If unique constraint violated or version mismatch
        """
        # Get equipment
        equipment = self.get_by_id_or_404(db, equipment_id, include_deleted=False)
        
        # Version check for optimistic locking
        if data.version is not None and equipment.version != data.version:
            raise DuplicateException(
                f"Equipment was modified by another user. "
                f"Expected version {data.version}, current is {equipment.version}"
            )
        
        update_dict = data.model_dump(exclude_unset=True, exclude={'version'})
        
        # Validate FKs if changed
        if 'type_id' in update_dict and update_dict['type_id']:
            type_obj = db.query(EquipmentType).filter_by(id=update_dict['type_id']).first()
            if not type_obj:
                raise ValidationException(f"Equipment type {update_dict['type_id']} not found")
            if not type_obj.is_active:
                raise ValidationException(f"Equipment type {update_dict['type_id']} is not active")
        
        if 'category_id' in update_dict and update_dict['category_id']:
            category = db.query(EquipmentCategory).filter_by(id=update_dict['category_id']).first()
            if not category:
                raise ValidationException(f"Equipment category {update_dict['category_id']} not found")
        
        if 'supplier_id' in update_dict and update_dict['supplier_id']:
            supplier = db.query(Supplier).filter_by(id=update_dict['supplier_id']).first()
            if not supplier:
                raise ValidationException(f"Supplier {update_dict['supplier_id']} not found")
        
        # Check UNIQUE constraints if changed
        if 'code' in update_dict and update_dict['code'] and update_dict['code'] != equipment.code:
            existing = db.query(Equipment).filter(
                Equipment.code == update_dict['code'],
                Equipment.id != equipment_id,
                Equipment.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Equipment with code '{update_dict['code']}' already exists")
        
        if 'license_plate' in update_dict and update_dict['license_plate'] and update_dict['license_plate'] != equipment.license_plate:
            existing = db.query(Equipment).filter(
                Equipment.license_plate == update_dict['license_plate'],
                Equipment.id != equipment_id,
                Equipment.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Equipment with license plate '{update_dict['license_plate']}' already exists")
        
        if 'qr_code' in update_dict and update_dict['qr_code'] and update_dict['qr_code'] != equipment.qr_code:
            existing = db.query(Equipment).filter(
                Equipment.qr_code == update_dict['qr_code'],
                Equipment.id != equipment_id,
                Equipment.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Equipment with QR code '{update_dict['qr_code']}' already exists")
        
        # Update equipment
        for field, value in update_dict.items():
            setattr(equipment, field, value)
        
        # Increment version if exists
        if equipment.version is not None:
            equipment.version += 1
        
        db.commit()
        db.refresh(equipment)
        
        return equipment
    
    def list(
        self,
        db: Session,
        search: EquipmentSearch
    ) -> Tuple[List[Equipment], int]:
        """
        List equipment with filters and pagination
        
        Args:
            db: Database session
            search: Search filters
        
        Returns:
            Tuple of (equipment list, total count)
        """
        # Base query
        query = self._base_query(db, include_deleted=search.include_deleted)
        
        # Free text search
        if search.q:
            search_term = f"%{search.q}%"
            query = query.where(
                or_(
                    Equipment.name.ilike(search_term),
                    Equipment.code.ilike(search_term),
                    Equipment.license_plate.ilike(search_term),
                    Equipment.qr_code.ilike(search_term)
                )
            )
        
        # Filters
        if search.type_id:
            query = query.where(Equipment.type_id == search.type_id)
        
        if search.category_id:
            query = query.where(Equipment.category_id == search.category_id)
        
        if search.supplier_id:
            query = query.where(Equipment.supplier_id == search.supplier_id)
        
        if search.status:
            query = query.where(Equipment.status == search.status.value)
        
        if search.location_id:
            query = query.where(Equipment.location_id == search.location_id)
        
        if search.assigned_project_id:
            query = query.where(Equipment.assigned_project_id == search.assigned_project_id)
        
        if search.is_active is not None:
            query = query.where(Equipment.is_active == search.is_active)
        
        if search.needs_maintenance:
            # Equipment needs maintenance if next_maintenance date is today or past
            query = query.where(
                and_(
                    Equipment.next_maintenance.isnot(None),
                    Equipment.next_maintenance <= func.current_date()
                )
            )
        
        # Count total
        total = db.execute(
            select(func.count()).select_from(query.subquery())
        ).scalar() or 0
        
        # Sort
        sort_column = getattr(Equipment, search.sort_by, Equipment.name)
        if search.sort_desc:
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Paginate
        offset = (search.page - 1) * search.page_size
        query = query.offset(offset).limit(search.page_size)
        
        # Execute
        equipment_list = db.execute(query).scalars().all()
        
        return equipment_list, total
    
    def soft_delete(
        self,
        db: Session,
        equipment_id: int,
        current_user_id: Optional[int] = None
    ) -> Equipment:
        """
        Soft delete equipment
        
        Args:
            db: Database session
            equipment_id: Equipment ID
            current_user_id: ID of user deleting
        
        Returns:
            Soft-deleted equipment
        
        Raises:
            NotFoundError: If equipment not found
            ValidationError: If equipment has active assignments
        """
        equipment = self.get_by_id_or_404(db, equipment_id, include_deleted=False)
        
        # Business rule: Cannot delete if has active assignments
        active_assignments = db.query(EquipmentAssignment).filter(
            EquipmentAssignment.equipment_id == equipment_id,
            EquipmentAssignment.is_active == True,
            EquipmentAssignment.deleted_at.is_(None),
            or_(
                EquipmentAssignment.end_date.is_(None),
                EquipmentAssignment.end_date >= datetime.utcnow()
            )
        ).count()
        
        if active_assignments > 0:
            raise ValidationException(
                f"Cannot delete equipment with {active_assignments} active assignments. "
                "Please end assignments first."
            )
        
        # Soft delete using BaseService
        deleted = super().soft_delete(db, equipment_id, commit=True)
        
        return deleted
    
    def restore(
        self,
        db: Session,
        equipment_id: int,
        current_user_id: Optional[int] = None
    ) -> Equipment:
        """
        Restore soft-deleted equipment
        
        Args:
            db: Database session
            equipment_id: Equipment ID
            current_user_id: ID of user restoring
        
        Returns:
            Restored equipment
        """
        # Restore using BaseService
        restored = super().restore(db, equipment_id, commit=True)
        
        return restored
    
    def get_statistics(
        self,
        db: Session,
        filters: Optional[dict] = None
    ) -> EquipmentStatistics:
        """
        Get equipment statistics
        
        Args:
            db: Database session
            filters: Optional filters (type_id, category_id, etc.)
        
        Returns:
            Equipment statistics
        """
        # Base query (active only)
        query = select(Equipment).where(Equipment.deleted_at.is_(None))
        
        # Apply filters
        if filters:
            if filters.get('type_id'):
                query = query.where(Equipment.type_id == filters['type_id'])
            if filters.get('category_id'):
                query = query.where(Equipment.category_id == filters['category_id'])
        
        # Get all equipment
        all_equipment = db.execute(query).scalars().all()
        
        # Calculate statistics
        stats = EquipmentStatistics(
            total=len(all_equipment),
            available=sum(1 for e in all_equipment if e.status == 'available'),
            in_use=sum(1 for e in all_equipment if e.status == 'in_use'),
            maintenance=sum(1 for e in all_equipment if e.status == 'maintenance'),
            retired=sum(1 for e in all_equipment if e.status == 'retired'),
            needs_maintenance=sum(1 for e in all_equipment if e.needs_maintenance),
            total_value=sum(e.purchase_price or 0 for e in all_equipment)
        )
        
        # By type
        by_type = {}
        for e in all_equipment:
            if e.type_id:
                by_type[e.type_id] = by_type.get(e.type_id, 0) + 1
        stats.by_type = {str(k): v for k, v in by_type.items()}
        
        # By category
        by_category = {}
        for e in all_equipment:
            if e.category_id:
                by_category[e.category_id] = by_category.get(e.category_id, 0) + 1
        stats.by_category = {str(k): v for k, v in by_category.items()}
        
        return stats
    
    def assign_to_project(
        self,
        db: Session,
        equipment_id: int,
        project_id: int,
        current_user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        notes: Optional[str] = None
    ) -> EquipmentAssignment:
        """
        Assign equipment to project
        
        Args:
            db: Database session
            equipment_id: Equipment ID
            project_id: Project ID
            current_user_id: User performing assignment
            start_date: Assignment start date
            end_date: Assignment end date
            notes: Assignment notes
        
        Returns:
            Created assignment
        
        Raises:
            ValidationError: If validation fails
        """
        # Verify equipment exists and is available
        equipment = self.get_by_id_or_404(db, equipment_id)
        
        if equipment.status not in ('available', 'in_use'):
            raise ValidationException(f"Equipment status '{equipment.status}' cannot be assigned")
        
        # Create assignment
        assignment = EquipmentAssignment(
            equipment_id=equipment_id,
            project_id=project_id,
            assigned_by=current_user_id,
            start_date=start_date or datetime.utcnow(),
            end_date=end_date,
            notes=notes,
            is_active=True
        )
        
        db.add(assignment)
        
        # Update equipment status
        equipment.status = 'in_use'
        equipment.assigned_project_id = project_id
        
        db.commit()
        db.refresh(assignment)
        
        return assignment
    
    def get_by_code(
        self,
        db: Session,
        code: str,
        include_deleted: bool = False
    ) -> Optional[Equipment]:
        """
        Get equipment by code
        
        Args:
            db: Database session
            code: Equipment code
            include_deleted: Include soft-deleted
        
        Returns:
            Equipment or None
        """
        query = select(Equipment).where(Equipment.code == code)
        
        if not include_deleted:
            query = query.where(Equipment.deleted_at.is_(None))
        
        return db.execute(query).scalar_one_or_none()
    
    def get_by_license_plate(
        self,
        db: Session,
        license_plate: str,
        include_deleted: bool = False
    ) -> Optional[Equipment]:
        """
        Get equipment by license plate
        
        Args:
            db: Database session
            license_plate: License plate number
            include_deleted: Include soft-deleted
        
        Returns:
            Equipment or None
        """
        query = select(Equipment).where(Equipment.license_plate == license_plate)
        
        if not include_deleted:
            query = query.where(Equipment.deleted_at.is_(None))
        
        return db.execute(query).scalar_one_or_none()
    
    def get_by_qr_code(
        self,
        db: Session,
        qr_code: str,
        include_deleted: bool = False
    ) -> Optional[Equipment]:
        """
        Get equipment by QR code
        
        Args:
            db: Database session
            qr_code: QR code
            include_deleted: Include soft-deleted
        
        Returns:
            Equipment or None
        """
        query = select(Equipment).where(Equipment.qr_code == qr_code)
        
        if not include_deleted:
            query = query.where(Equipment.deleted_at.is_(None))
        
        return db.execute(query).scalar_one_or_none()
