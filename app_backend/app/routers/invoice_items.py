"""
InvoiceItems Router
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.schemas.invoice_item import (
    InvoiceItemCreate, InvoiceItemUpdate, InvoiceItemResponse,
    InvoiceItemList, InvoiceItemSearch
)
from app.services.invoice_item_service import InvoiceItemService
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException

router = APIRouter(prefix="/invoice-items", tags=["Invoice Items"])
invoice_item_service = InvoiceItemService()


@router.get("", response_model=InvoiceItemList)
def list_invoice_items(
    search: Annotated[InvoiceItemSearch, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """List invoice items"""
    require_permission(current_user, "invoice_items.read")
    items, total = invoice_item_service.list(db, search)
    total_pages = (total + search.page_size - 1) // search.page_size if total > 0 else 1
    return InvoiceItemList(items=items, total=total, page=search.page, page_size=search.page_size, total_pages=total_pages)


@router.get("/{item_id}", response_model=InvoiceItemResponse)
def get_invoice_item(
    item_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get invoice item"""
    require_permission(current_user, "invoice_items.read")
    item = invoice_item_service.get_by_id_or_404(db, item_id)
    return item


@router.post("", response_model=InvoiceItemResponse, status_code=status.HTTP_201_CREATED)
def create_invoice_item(
    data: InvoiceItemCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Create invoice item"""
    require_permission(current_user, "invoice_items.create")
    try:
        item = invoice_item_service.create(db, data, current_user.id)
        return item
    except (ValidationException, DuplicateException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{item_id}", response_model=InvoiceItemResponse)
def update_invoice_item(
    item_id: int,
    data: InvoiceItemUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Update invoice item"""
    require_permission(current_user, "invoice_items.update")
    try:
        item = invoice_item_service.update(db, item_id, data, current_user.id)
        return item
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValidationException, DuplicateException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice_item(
    item_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Delete invoice item"""
    require_permission(current_user, "invoice_items.delete")
    try:
        invoice_item_service.soft_delete(db, item_id, current_user.id)
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{item_id}/restore", response_model=InvoiceItemResponse)
def restore_invoice_item(
    item_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Restore invoice item"""
    require_permission(current_user, "invoice_items.restore")
    item = invoice_item_service.restore(db, item_id, current_user.id)
    return item
