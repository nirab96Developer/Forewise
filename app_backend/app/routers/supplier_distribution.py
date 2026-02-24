"""
Supplier Distribution Router - Fair Rotation + Distribution Flow
Endpoints for sending WOs to suppliers and handling responses.

Flow: Coordinator -> System picks supplier -> Portal -> Accept/Decline -> Final approve
"""
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.work_order import WorkOrder
from app.models.supplier import Supplier
from app.models.supplier_rotation import SupplierRotation
from app.models.supplier_invitation import SupplierInvitation
from app.services.work_order_service import WorkOrderService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/supplier-distribution", tags=["Supplier Distribution"])
work_order_service = WorkOrderService()


class DistributeRequest(BaseModel):
    work_order_id: int
    force_supplier_id: Optional[int] = None  # Override fair rotation


class SupplierResponseRequest(BaseModel):
    accepted: bool
    notes: Optional[str] = None
    decline_reason: Optional[str] = None


class CoordinatorApproveRequest(BaseModel):
    approved: bool
    notes: Optional[str] = None


@router.post("/distribute")
async def distribute_work_order(
    request: DistributeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Send work order to supplier via fair rotation.
    Coordinator clicks 'send to suppliers' -> system picks supplier -> creates invitation.
    """
    # Get WO
    wo = db.query(WorkOrder).filter(WorkOrder.id == request.work_order_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    if wo.status not in ("PENDING", "APPROVED"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot distribute WO in status {wo.status}. Must be PENDING or APPROVED."
        )
    
    # Cancel any existing pending invitations for this WO
    db.query(SupplierInvitation).filter(
        SupplierInvitation.work_order_id == wo.id,
        SupplierInvitation.status == "PENDING"
    ).update({"status": "CANCELLED"})
    
    # Pick supplier (single source of truth from WorkOrderService)
    if request.force_supplier_id:
        supplier = db.query(Supplier).filter(Supplier.id == request.force_supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
        if not work_order_service.supplier_has_required_tool(db, supplier.id, wo.requested_equipment_model_id):
            raise HTTPException(
                status_code=400,
                detail="Forced supplier must have the requested tool"
            )
        supplier_id = supplier.id
        rotation_pos = None
    else:
        supplier_id, rotation = work_order_service.select_next_supplier(
            db,
            wo,
            constraint_mode=bool(wo.is_forced_selection),
            exclude_supplier_ids=[wo.supplier_id] if wo.supplier_id else None,
        )
        rotation_pos = rotation.rotation_position if rotation else None
        if rotation:
            rotation.total_assignments = (rotation.total_assignments or 0) + 1
            rotation.last_assignment_date = datetime.utcnow().date()
    
    # Create invitation with token
    token = str(uuid.uuid4())
    invitation = SupplierInvitation(
        work_order_id=wo.id,
        supplier_id=supplier_id,
        invited_by_id=current_user.id,
        token=token,
        token_expires_at=datetime.utcnow() + timedelta(hours=48),
        status="PENDING",
        sent_at=datetime.utcnow(),
        rotation_position=rotation_pos,
    )
    db.add(invitation)
    
    # Update WO status
    wo.status = "DISTRIBUTING"
    wo.supplier_id = supplier_id
    
    db.commit()
    db.refresh(invitation)
    
    # Get supplier name
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    
    # Send email notification to supplier
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        supplier_email = getattr(supplier, 'email', None) or "avitbulnir@gmail.com"
        portal_url = f"http://167.99.228.10/supplier-portal/{token}"
        
        msg = MIMEMultipart()
        msg["Subject"] = f"הזמנת עבודה חדשה - {wo.title or wo.order_number}"
        msg["From"] = "noreply@kkl-forest.co.il"
        msg["To"] = supplier_email
        
        body = f"""
        <div dir="rtl" style="font-family:Arial,sans-serif;padding:20px">
            <h2 style="color:#047857">הזמנת עבודה חדשה</h2>
            <p>שלום {supplier.name if supplier else "ספק"},</p>
            <p>התקבלה הזמנת עבודה חדשה עבורך:</p>
            <ul>
                <li><b>מספר הזמנה:</b> {wo.order_number}</li>
                <li><b>כותרת:</b> {wo.title or "ללא"}</li>
            </ul>
            <p>לצפייה ואישור ההזמנה:</p>
            <a href="{portal_url}" style="display:inline-block;padding:12px 24px;background:#047857;color:#fff;text-decoration:none;border-radius:8px;font-weight:bold">
                כניסה לפורטל ספקים
            </a>
            <p style="color:#6b7280;font-size:12px;margin-top:20px">הזמנה זו תפוג תוך 48 שעות.</p>
        </div>
        """
        msg.attach(MIMEText(body, "html"))
        
        # Try sending via local SMTP or configured SMTP
        try:
            smtp = smtplib.SMTP("localhost", 25, timeout=5)
            smtp.send_message(msg)
            smtp.quit()
            logger.info(f"Email sent to {supplier_email} for WO {wo.order_number}")
        except Exception:
            logger.warning(f"SMTP not available, email not sent to {supplier_email}")
    except Exception as e:
        logger.warning(f"Email notification failed: {e}")
    
    return {
        "success": True,
        "invitation_id": invitation.id,
        "supplier_id": supplier_id,
        "supplier_name": supplier.name if supplier else f"Supplier #{supplier_id}",
        "token": token,
        "portal_url": f"/supplier-portal/{token}",
        "expires_at": invitation.token_expires_at.isoformat() if invitation.token_expires_at else None,
        "work_order_status": "DISTRIBUTING",
    }


@router.post("/respond/{token}")
async def supplier_respond(
    token: str,
    request: SupplierResponseRequest,
    db: Session = Depends(get_db),
):
    """
    Supplier responds to invitation (accept/decline).
    Public endpoint - authenticated via token.
    """
    invitation = db.query(SupplierInvitation).filter(
        SupplierInvitation.token == token
    ).first()
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    if invitation.status != "PENDING" and invitation.status != "VIEWED":
        raise HTTPException(status_code=400, detail=f"Invitation already {invitation.status}")
    
    if invitation.token_expires_at and invitation.token_expires_at < datetime.utcnow():
        invitation.status = "EXPIRED"
        db.commit()
        raise HTTPException(status_code=400, detail="Invitation expired")
    
    wo = db.query(WorkOrder).filter(WorkOrder.id == invitation.work_order_id).first()
    
    if request.accepted:
        invitation.status = "ACCEPTED"
        invitation.responded_at = datetime.utcnow()
        invitation.response_notes = request.notes
        
        if wo:
            wo.status = "SUPPLIER_ACCEPTED_PENDING_COORDINATOR"
        
        # Update rotation stats
        rotation = db.query(SupplierRotation).filter(
            SupplierRotation.supplier_id == invitation.supplier_id
        ).first()
        if rotation:
            rotation.successful_completions = (rotation.successful_completions or 0) + 1
    else:
        invitation.status = "DECLINED"
        invitation.responded_at = datetime.utcnow()
        invitation.decline_reason = request.decline_reason
        invitation.response_notes = request.notes
        
        # Update rotation rejection count
        rotation = db.query(SupplierRotation).filter(
            SupplierRotation.supplier_id == invitation.supplier_id
        ).first()
        if rotation:
            rotation.rejection_count = (rotation.rejection_count or 0) + 1
        
        # Auto-pick next supplier if declined
        if wo:
            wo.status = "PENDING"  # Reset to allow re-distribution
    
    db.commit()
    
    return {
        "success": True,
        "status": invitation.status,
        "work_order_status": wo.status if wo else None,
    }


@router.post("/coordinator-approve/{invitation_id}")
async def coordinator_approve(
    invitation_id: int,
    request: CoordinatorApproveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Coordinator final approval after supplier accepted.
    WO status: SUPPLIER_ACCEPTED_PENDING_COORDINATOR -> APPROVED_AND_SENT
    """
    invitation = db.query(SupplierInvitation).filter(
        SupplierInvitation.id == invitation_id
    ).first()
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    if invitation.status != "ACCEPTED":
        raise HTTPException(status_code=400, detail="Supplier has not accepted this invitation")
    
    wo = db.query(WorkOrder).filter(WorkOrder.id == invitation.work_order_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    if request.approved:
        wo.status = "APPROVED_AND_SENT"
        return {
            "success": True,
            "work_order_id": wo.id,
            "status": "APPROVED_AND_SENT",
            "message": "Work order approved and sent to supplier",
        }
    else:
        wo.status = "PENDING"
        invitation.status = "CANCELLED"
        db.commit()
        return {
            "success": True,
            "work_order_id": wo.id,
            "status": "PENDING",
            "message": "Coordinator rejected. WO returned to pending.",
        }


@router.get("/invitations")
async def list_invitations(
    work_order_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List supplier invitations with optional filters."""
    query = db.query(SupplierInvitation)
    
    if work_order_id:
        query = query.filter(SupplierInvitation.work_order_id == work_order_id)
    if status:
        query = query.filter(SupplierInvitation.status == status)
    
    invitations = query.order_by(SupplierInvitation.created_at.desc()).limit(100).all()
    
    # Enrich with supplier names
    supplier_ids = list(set(i.supplier_id for i in invitations))
    suppliers = {s.id: s.name for s in db.query(Supplier).filter(Supplier.id.in_(supplier_ids)).all()} if supplier_ids else {}
    
    return [
        {
            "id": inv.id,
            "work_order_id": inv.work_order_id,
            "supplier_id": inv.supplier_id,
            "supplier_name": suppliers.get(inv.supplier_id, f"Supplier #{inv.supplier_id}"),
            "status": inv.status,
            "token": inv.token,
            "sent_at": inv.sent_at.isoformat() if inv.sent_at else None,
            "responded_at": inv.responded_at.isoformat() if inv.responded_at else None,
            "decline_reason": inv.decline_reason,
            "rotation_position": inv.rotation_position,
        }
        for inv in invitations
    ]


@router.get("/invitation/{token}")
async def get_invitation_by_token(
    token: str,
    db: Session = Depends(get_db),
):
    """Get invitation details by token (for supplier portal)."""
    invitation = db.query(SupplierInvitation).filter(
        SupplierInvitation.token == token
    ).first()
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    # Mark as viewed
    if invitation.status == "PENDING":
        invitation.status = "VIEWED"
        invitation.viewed_at = datetime.utcnow()
        db.commit()
    
    # Get WO details
    wo = db.query(WorkOrder).filter(WorkOrder.id == invitation.work_order_id).first()
    supplier = db.query(Supplier).filter(Supplier.id == invitation.supplier_id).first()
    
    return {
        "invitation_id": invitation.id,
        "status": invitation.status,
        "supplier_name": supplier.name if supplier else None,
        "work_order": {
            "id": wo.id,
            "order_number": wo.order_number,
            "title": wo.title,
            "description": wo.description,
            "work_start_date": wo.work_start_date.isoformat() if wo.work_start_date else None,
            "work_end_date": wo.work_end_date.isoformat() if wo.work_end_date else None,
            "estimated_hours": float(wo.estimated_hours) if wo.estimated_hours else None,
        } if wo else None,
        "expires_at": invitation.token_expires_at.isoformat() if invitation.token_expires_at else None,
        "is_expired": invitation.token_expires_at < datetime.utcnow() if invitation.token_expires_at else False,
    }


@router.post("/expire-stale")
async def expire_stale_invitations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Auto-expire invitations past their token_expires_at.
    Resets WO status to PENDING so coordinator can re-distribute.
    Called periodically or manually.
    """
    expired = db.query(SupplierInvitation).filter(
        SupplierInvitation.status.in_(["PENDING", "VIEWED"]),
        SupplierInvitation.token_expires_at < datetime.utcnow(),
    ).all()
    
    count = 0
    for inv in expired:
        inv.status = "EXPIRED"
        wo = db.query(WorkOrder).filter(WorkOrder.id == inv.work_order_id).first()
        if wo and wo.status == "DISTRIBUTING":
            wo.status = "PENDING"
        count += 1
    
    db.commit()
    return {"expired_count": count, "message": f"{count} invitations expired"}
