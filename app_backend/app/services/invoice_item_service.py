"""
InvoiceItem Service
"""

from typing import Optional, List, Tuple
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_

from app.models.invoice_item import InvoiceItem
from app.models.invoice import Invoice
from app.schemas.invoice_item import InvoiceItemCreate, InvoiceItemUpdate, InvoiceItemSearch
from app.services.base_service import BaseService
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException


class InvoiceItemService(BaseService[InvoiceItem]):
    """InvoiceItem Service - CORE"""
    
    def __init__(self):
        super().__init__(InvoiceItem)
    
    def create(self, db: Session, data: InvoiceItemCreate, current_user_id: int) -> InvoiceItem:
        """Create invoice item"""
        # Validate FK: invoice_id
        invoice = db.query(Invoice).filter_by(id=data.invoice_id).first()
        if not invoice:
            raise ValidationException(f"Invoice {data.invoice_id} not found")
        if not invoice.is_active:
            raise ValidationException(f"Invoice {data.invoice_id} is not active")
        
        # Create
        item_dict = data.model_dump(exclude_unset=True)
        item_dict["total_price"] = item_dict.get("total")
        item = InvoiceItem(**item_dict)
        
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    
    def update(self, db: Session, item_id: int, data: InvoiceItemUpdate, current_user_id: int) -> InvoiceItem:
        """Update invoice item"""
        item = self.get_by_id_or_404(db, item_id)
        
        # Version check
        if data.version is not None and item.version != data.version:
            raise DuplicateException("Invoice item was modified by another user")
        
        update_dict = data.model_dump(exclude_unset=True, exclude={'version'})
        
        for field, value in update_dict.items():
            setattr(item, field, value)

        if "total" in update_dict:
            item.total_price = update_dict["total"]

        # Legacy DB compatibility: ensure updated_at advances even without DB trigger.
        item.updated_at = datetime.utcnow()
        
        if item.version is not None:
            item.version += 1
        
        db.commit()
        db.refresh(item)
        return item
    
    def list(self, db: Session, search: InvoiceItemSearch) -> Tuple[List[InvoiceItem], int]:
        """List invoice items"""
        query = self._base_query(db, include_deleted=search.include_deleted)
        
        if search.q:
            term = f"%{search.q}%"
            query = query.where(or_(
                InvoiceItem.description.ilike(term),
                InvoiceItem.item_code.ilike(term)
            ))
        
        if search.invoice_id:
            query = query.where(InvoiceItem.invoice_id == search.invoice_id)
        if search.worklog_id:
            query = query.where(InvoiceItem.worklog_id == search.worklog_id)
        if search.is_active is not None:
            query = query.where(InvoiceItem.is_active == search.is_active)
        
        total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0
        
        sort_col = getattr(InvoiceItem, search.sort_by, InvoiceItem.line_number)
        query = query.order_by(sort_col.desc() if search.sort_desc else sort_col.asc())
        
        offset = (search.page - 1) * search.page_size
        items = db.execute(query.offset(offset).limit(search.page_size)).scalars().all()
        
        return items, total
