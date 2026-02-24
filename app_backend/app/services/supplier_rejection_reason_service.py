"""
Supplier Rejection Reason Service - לוגיקה עסקית לסיבות דחיית ספק
"""
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models.supplier_rejection_reason import SupplierRejectionReason
from app.services.base_service import BaseService
from app.core.exceptions import NotFoundException, DuplicateException


class SupplierRejectionReasonService(BaseService[SupplierRejectionReason]):
    """Supplier Rejection Reason service"""
    
    def __init__(self):
        super().__init__(SupplierRejectionReason)
    
    def get_by_code(self, db: Session, code: str) -> Optional[SupplierRejectionReason]:
        """Get reason by code"""
        return db.query(SupplierRejectionReason).filter(
            SupplierRejectionReason.code == code
        ).first()
    
    def list_with_filters(
        self,
        db: Session,
        q: Optional[str] = None,
        category: Optional[str] = None,
        requires_approval: Optional[bool] = None,
        is_active: Optional[bool] = True,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "display_order",
        sort_desc: bool = False
    ) -> Tuple[List[SupplierRejectionReason], int]:
        """List reasons with filters"""
        query = db.query(SupplierRejectionReason)
        
        # Search
        if q:
            query = query.filter(
                or_(
                    SupplierRejectionReason.name.ilike(f"%{q}%"),
                    SupplierRejectionReason.code.ilike(f"%{q}%"),
                    SupplierRejectionReason.description.ilike(f"%{q}%")
                )
            )
        
        # Category filter
        if category:
            query = query.filter(SupplierRejectionReason.category == category)
        
        # Requires approval filter
        if requires_approval is not None:
            query = query.filter(SupplierRejectionReason.requires_approval == requires_approval)
        
        # Active filter
        if is_active is not None:
            query = query.filter(SupplierRejectionReason.is_active == is_active)
        
        # Count
        total = query.count()
        
        # Sort
        if hasattr(SupplierRejectionReason, sort_by):
            order_col = getattr(SupplierRejectionReason, sort_by)
            query = query.order_by(order_col.desc() if sort_desc else order_col.asc())
        
        # Paginate
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        
        return items, total
    
    def create_reason(
        self,
        db: Session,
        code: str,
        name: str,
        description: Optional[str] = None,
        category: str = "OPERATIONAL",
        is_active: bool = True,
        requires_additional_text: bool = False,
        requires_approval: bool = False,
        display_order: int = 0
    ) -> SupplierRejectionReason:
        """Create new reason"""
        # Validate unique code
        if self.get_by_code(db, code):
            raise DuplicateException(f"Reason with code '{code}' already exists")
        
        reason = SupplierRejectionReason(
            code=code,
            name=name,
            description=description,
            category=category,
            is_active=is_active,
            requires_additional_text=requires_additional_text,
            requires_approval=requires_approval,
            display_order=display_order,
            usage_count=0
        )
        
        db.add(reason)
        db.commit()
        db.refresh(reason)
        
        return reason
    
    def update_reason(
        self,
        db: Session,
        reason_id: int,
        data: Dict[str, Any]
    ) -> SupplierRejectionReason:
        """Update reason"""
        reason = self.get_by_id(db, reason_id)
        if not reason:
            raise NotFoundException(f"Reason {reason_id} not found")
        
        # Check unique code if changing
        if 'code' in data and data['code'] != reason.code:
            existing = self.get_by_code(db, data['code'])
            if existing:
                raise DuplicateException(f"Reason with code '{data['code']}' already exists")
        
        for key, value in data.items():
            if hasattr(reason, key) and value is not None:
                setattr(reason, key, value)
        
        db.commit()
        db.refresh(reason)
        
        return reason
    
    def deactivate(self, db: Session, reason_id: int) -> SupplierRejectionReason:
        """Deactivate reason"""
        reason = self.get_by_id(db, reason_id)
        if not reason:
            raise NotFoundException(f"Reason {reason_id} not found")
        
        reason.is_active = False
        db.commit()
        db.refresh(reason)
        
        return reason
    
    def activate(self, db: Session, reason_id: int) -> SupplierRejectionReason:
        """Activate reason"""
        reason = self.get_by_id(db, reason_id)
        if not reason:
            raise NotFoundException(f"Reason {reason_id} not found")
        
        reason.is_active = True
        db.commit()
        db.refresh(reason)
        
        return reason
    
    def increment_usage(self, db: Session, reason_id: int) -> SupplierRejectionReason:
        """Increment usage count"""
        reason = self.get_by_id(db, reason_id)
        if not reason:
            raise NotFoundException(f"Reason {reason_id} not found")
        
        reason.usage_count = (reason.usage_count or 0) + 1
        db.commit()
        db.refresh(reason)
        
        return reason
    
    def get_statistics(self, db: Session) -> Dict[str, Any]:
        """Get reason statistics"""
        total = db.query(func.count(SupplierRejectionReason.id)).scalar() or 0
        active = db.query(func.count(SupplierRejectionReason.id)).filter(
            SupplierRejectionReason.is_active == True
        ).scalar() or 0
        
        # By category
        by_category = db.query(
            SupplierRejectionReason.category,
            func.count(SupplierRejectionReason.id)
        ).group_by(SupplierRejectionReason.category).all()
        
        return {
            "total": total,
            "active": active,
            "inactive": total - active,
            "by_category": {cat or "uncategorized": count for cat, count in by_category}
        }


# Singleton
supplier_rejection_reason_service = SupplierRejectionReasonService()
