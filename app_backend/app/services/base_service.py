"""
Base Service - שירות בסיס עם תמיכה ב-soft delete
"""

from datetime import datetime
from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_
from sqlalchemy.exc import IntegrityError

from app.models.base import BaseModel
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException

T = TypeVar('T', bound=BaseModel)


class BaseService(Generic[T]):
    """
    Base service with CRUD operations and soft delete support.
    
    Features:
    - Automatic soft delete filtering (if deleted_at column exists)
    - Optimistic locking support (if version column exists)
    - Common CRUD operations
    - Pagination helpers
    
    Usage:
        class UserService(BaseService[User]):
            def __init__(self):
                super().__init__(User)
    """
    
    def __init__(self, model: Type[T]):
        """
        Initialize base service.
        
        Args:
            model: SQLAlchemy model class
        """
        self.model = model
        self._has_deleted_at = hasattr(model, 'deleted_at')
        self._has_version = hasattr(model, 'version')
        self._has_is_active = hasattr(model, 'is_active')
    
    def _base_query(self, db: Session, include_deleted: bool = False):
        """
        Get base query with soft delete filtering.
        
        Args:
            db: Database session
            include_deleted: If True, include soft-deleted records
        
        Returns:
            Query for non-deleted records (or all if include_deleted=True)
        """
        query = select(self.model)
        
        # Filter soft-deleted if column exists and include_deleted=False
        if self._has_deleted_at and not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))
        
        return query
    
    def get_by_id(
        self,
        db: Session,
        id: Any,
        include_deleted: bool = False
    ) -> Optional[T]:
        """
        Get record by ID.
        
        Args:
            db: Database session
            id: Record ID
            include_deleted: If True, include soft-deleted records
        
        Returns:
            Record or None if not found
        """
        query = self._base_query(db, include_deleted).where(self.model.id == id)
        return db.execute(query).scalar_one_or_none()
    
    def get_by_id_or_404(
        self,
        db: Session,
        id: Any,
        include_deleted: bool = False
    ) -> T:
        """
        Get record by ID or raise NotFoundException.
        
        Args:
            db: Database session
            id: Record ID
            include_deleted: If True, include soft-deleted records
        
        Returns:
            Record
        
        Raises:
            NotFoundException: If record not found
        """
        record = self.get_by_id(db, id, include_deleted)
        if not record:
            raise NotFoundException(f"{self.model.__name__} with id {id} not found")
        return record
    
    def list(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        **filters
    ) -> List[T]:
        """
        List records with pagination and filtering.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_deleted: If True, include soft-deleted records
            order_by: Column name to order by (default: id)
            order_desc: If True, order descending
            **filters: Additional filters (column_name=value)
        
        Returns:
            List of records
        """
        query = self._base_query(db, include_deleted)
        
        # Apply filters
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                query = query.where(getattr(self.model, key) == value)
        
        # Order
        if order_by and hasattr(self.model, order_by):
            order_col = getattr(self.model, order_by)
            query = query.order_by(order_col.desc() if order_desc else order_col.asc())
        else:
            query = query.order_by(self.model.id.asc())
        
        # Paginate
        query = query.offset(skip).limit(limit)
        
        return db.execute(query).scalars().all()
    
    def count(
        self,
        db: Session,
        include_deleted: bool = False,
        **filters
    ) -> int:
        """
        Count records with filtering.
        
        Args:
            db: Database session
            include_deleted: If True, include soft-deleted records
            **filters: Additional filters
        
        Returns:
            Count of records
        """
        query = select(func.count(self.model.id))
        
        # Soft delete filter
        if self._has_deleted_at and not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))
        
        # Apply filters
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                query = query.where(getattr(self.model, key) == value)
        
        return db.execute(query).scalar() or 0
    
    def create(
        self,
        db: Session,
        obj_in: Dict[str, Any],
        commit: bool = True
    ) -> T:
        """
        Create new record.
        
        Args:
            db: Database session
            obj_in: Dictionary of field values
            commit: If True, commit transaction
        
        Returns:
            Created record
        
        Raises:
            ValidationException: If data is invalid
            DuplicateException: If unique constraint violated
        """
        try:
            record = self.model(**obj_in)
            db.add(record)
            
            if commit:
                db.commit()
                db.refresh(record)
            else:
                db.flush()
            
            return record
        
        except IntegrityError as e:
            db.rollback()
            raise DuplicateException(f"Record already exists or constraint violated: {str(e)}")
        except Exception as e:
            db.rollback()
            raise ValidationException(f"Failed to create record: {str(e)}")
    
    def update(
        self,
        db: Session,
        id: Any,
        obj_in: Dict[str, Any],
        commit: bool = True
    ) -> T:
        """
        Update record.
        
        Args:
            db: Database session
            id: Record ID
            obj_in: Dictionary of fields to update
            commit: If True, commit transaction
        
        Returns:
            Updated record
        
        Raises:
            NotFoundException: If record not found
            DuplicateException: If version mismatch (optimistic locking)
            ValidationException: If update fails
        """
        record = self.get_by_id_or_404(db, id)
        
        # Handle optimistic locking
        if self._has_version and 'version' in obj_in:
            current_version = obj_in.pop('version')
            if record.version != current_version:
                raise DuplicateException(
                    f"Record was modified by another user. "
                    f"Expected version {current_version}, got {record.version}"
                )
        
        try:
            # Update fields
            for field, value in obj_in.items():
                if hasattr(record, field):
                    setattr(record, field, value)
            
            # Increment version if exists
            if self._has_version:
                record.version = (record.version or 0) + 1
            
            if commit:
                db.commit()
                db.refresh(record)
            else:
                db.flush()
            
            return record
        
        except IntegrityError as e:
            db.rollback()
            raise DuplicateException(f"Update violates constraint: {str(e)}")
        except Exception as e:
            db.rollback()
            raise ValidationException(f"Failed to update record: {str(e)}")
    
    def soft_delete(
        self,
        db: Session,
        id: Any,
        commit: bool = True
    ) -> T:
        """
        Soft delete record (set deleted_at timestamp).
        
        Args:
            db: Database session
            id: Record ID
            commit: If True, commit transaction
        
        Returns:
            Soft-deleted record
        
        Raises:
            NotFoundException: If record not found
            ValidationException: If table doesn't support soft delete
        """
        if not self._has_deleted_at:
            raise ValidationException(f"{self.model.__name__} doesn't support soft delete")
        
        record = self.get_by_id_or_404(db, id)
        
        # Set deleted_at
        record.deleted_at = datetime.utcnow()
        
        # Set is_active = False if column exists
        if self._has_is_active:
            record.is_active = False
        
        if commit:
            db.commit()
            db.refresh(record)
        else:
            db.flush()
        
        return record
    
    def restore(
        self,
        db: Session,
        id: Any,
        commit: bool = True
    ) -> T:
        """
        Restore soft-deleted record.
        
        Args:
            db: Database session
            id: Record ID
            commit: If True, commit transaction
        
        Returns:
            Restored record
        
        Raises:
            NotFoundException: If record not found
        """
        if not self._has_deleted_at:
            raise ValidationException(f"{self.model.__name__} doesn't support soft delete")
        
        record = self.get_by_id(db, id, include_deleted=True)
        if not record:
            raise NotFoundException(f"{self.model.__name__} with id {id} not found")
        
        # Restore
        record.deleted_at = None
        
        if self._has_is_active:
            record.is_active = True
        
        if commit:
            db.commit()
            db.refresh(record)
        else:
            db.flush()
        
        return record
    
    def hard_delete(
        self,
        db: Session,
        id: Any,
        commit: bool = True
    ) -> None:
        """
        Permanently delete record from database.
        
        ⚠️ USE WITH CAUTION! This cannot be undone.
        
        Args:
            db: Database session
            id: Record ID
            commit: If True, commit transaction
        
        Raises:
            NotFoundException: If record not found
        """
        record = self.get_by_id(db, id, include_deleted=True)
        if not record:
            raise NotFoundException(f"{self.model.__name__} with id {id} not found")
        
        db.delete(record)
        
        if commit:
            db.commit()
        else:
            db.flush()
    
    def exists(
        self,
        db: Session,
        id: Any,
        include_deleted: bool = False
    ) -> bool:
        """
        Check if record exists.
        
        Args:
            db: Database session
            id: Record ID
            include_deleted: If True, include soft-deleted records
        
        Returns:
            True if record exists
        """
        return self.get_by_id(db, id, include_deleted) is not None

