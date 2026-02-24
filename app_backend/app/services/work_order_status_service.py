"""
Work Order Status Service - לוגיקה עסקית לסטטוסי הזמנות עבודה
"""
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models.work_order_status import WorkOrderStatus
from app.services.base_service import BaseService
from app.core.exceptions import NotFoundException, DuplicateException


class WorkOrderStatusService(BaseService[WorkOrderStatus]):
    """Work Order Status service"""
    
    def __init__(self):
        super().__init__(WorkOrderStatus)
    
    def get_by_code(self, db: Session, code: str) -> Optional[WorkOrderStatus]:
        """Get status by code"""
        return db.query(WorkOrderStatus).filter(WorkOrderStatus.code == code).first()
    
    def list_with_filters(
        self,
        db: Session,
        q: Optional[str] = None,
        is_active: Optional[bool] = True,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "display_order",
        sort_desc: bool = False
    ) -> Tuple[List[WorkOrderStatus], int]:
        """List statuses with filters"""
        query = db.query(WorkOrderStatus)
        
        # Search
        if q:
            query = query.filter(
                or_(
                    WorkOrderStatus.name.ilike(f"%{q}%"),
                    WorkOrderStatus.code.ilike(f"%{q}%"),
                    WorkOrderStatus.description.ilike(f"%{q}%")
                )
            )
        
        # Active filter
        if is_active is not None:
            query = query.filter(WorkOrderStatus.is_active == is_active)
        
        # Count
        total = query.count()
        
        # Sort
        if hasattr(WorkOrderStatus, sort_by):
            order_col = getattr(WorkOrderStatus, sort_by)
            query = query.order_by(order_col.desc() if sort_desc else order_col.asc())
        
        # Paginate
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        
        return items, total
    
    def create_status(
        self,
        db: Session,
        code: str,
        name: str,
        description: Optional[str] = None,
        is_active: bool = True,
        display_order: int = 0
    ) -> WorkOrderStatus:
        """Create new status"""
        # Validate unique code
        if self.get_by_code(db, code):
            raise DuplicateException(f"Status with code '{code}' already exists")
        
        status = WorkOrderStatus(
            code=code,
            name=name,
            description=description,
            is_active=is_active,
            display_order=display_order
        )
        
        db.add(status)
        db.commit()
        db.refresh(status)
        
        return status
    
    def update_status(
        self,
        db: Session,
        status_id: int,
        data: Dict[str, Any]
    ) -> WorkOrderStatus:
        """Update status"""
        status = self.get_by_id(db, status_id)
        if not status:
            raise NotFoundException(f"Status {status_id} not found")
        
        # Check unique code if changing
        if 'code' in data and data['code'] != status.code:
            existing = self.get_by_code(db, data['code'])
            if existing:
                raise DuplicateException(f"Status with code '{data['code']}' already exists")
        
        for key, value in data.items():
            if hasattr(status, key) and value is not None:
                setattr(status, key, value)
        
        db.commit()
        db.refresh(status)
        
        return status
    
    def deactivate(self, db: Session, status_id: int) -> WorkOrderStatus:
        """Deactivate status"""
        status = self.get_by_id(db, status_id)
        if not status:
            raise NotFoundException(f"Status {status_id} not found")
        
        status.is_active = False
        db.commit()
        db.refresh(status)
        
        return status
    
    def activate(self, db: Session, status_id: int) -> WorkOrderStatus:
        """Activate status"""
        status = self.get_by_id(db, status_id)
        if not status:
            raise NotFoundException(f"Status {status_id} not found")
        
        status.is_active = True
        db.commit()
        db.refresh(status)
        
        return status
    
    def get_statistics(self, db: Session) -> Dict[str, Any]:
        """Get status statistics"""
        total = db.query(func.count(WorkOrderStatus.id)).scalar() or 0
        active = db.query(func.count(WorkOrderStatus.id)).filter(
            WorkOrderStatus.is_active == True
        ).scalar() or 0
        
        return {
            "total": total,
            "active": active,
            "inactive": total - active
        }


# Singleton
work_order_status_service = WorkOrderStatusService()
