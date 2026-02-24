"""
InvoicePayments Router
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.schemas.invoice_payment import (
    InvoicePaymentCreate, InvoicePaymentUpdate, InvoicePaymentResponse,
    InvoicePaymentList, InvoicePaymentSearch
)
from app.services.invoice_payment_service import InvoicePaymentService
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException

router = APIRouter(prefix="/invoice-payments", tags=["Invoice Payments"])
invoice_payment_service = InvoicePaymentService()


@router.get("", response_model=InvoicePaymentList)
def list_invoice_payments(
    search: Annotated[InvoicePaymentSearch, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """List payments"""
    require_permission(current_user, "invoice_payments.read")
    payments, total = invoice_payment_service.list(db, search)
    total_pages = (total + search.page_size - 1) // search.page_size if total > 0 else 1
    return InvoicePaymentList(items=payments, total=total, page=search.page, page_size=search.page_size, total_pages=total_pages)


@router.get("/{payment_id}", response_model=InvoicePaymentResponse)
def get_invoice_payment(
    payment_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get payment"""
    require_permission(current_user, "invoice_payments.read")
    payment = invoice_payment_service.get_by_id(db, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment


@router.post("", response_model=InvoicePaymentResponse, status_code=status.HTTP_201_CREATED)
def create_invoice_payment(
    data: InvoicePaymentCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Create payment"""
    require_permission(current_user, "invoice_payments.create")
    try:
        payment = invoice_payment_service.create(db, data, current_user.id)
        return payment
    except (ValidationException, DuplicateException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{payment_id}", response_model=InvoicePaymentResponse)
def update_invoice_payment(
    payment_id: int,
    data: InvoicePaymentUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Update payment"""
    require_permission(current_user, "invoice_payments.update")
    try:
        payment = invoice_payment_service.update(db, payment_id, data, current_user.id)
        return payment
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValidationException, DuplicateException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{payment_id}/deactivate", response_model=InvoicePaymentResponse)
def deactivate_payment(
    payment_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Deactivate payment"""
    require_permission(current_user, "invoice_payments.delete")
    try:
        payment = invoice_payment_service.deactivate(db, payment_id, current_user.id)
        return payment
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{payment_id}/activate", response_model=InvoicePaymentResponse)
def activate_payment(
    payment_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Activate payment"""
    require_permission(current_user, "invoice_payments.restore")
    try:
        payment = invoice_payment_service.activate(db, payment_id, current_user.id)
        return payment
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
