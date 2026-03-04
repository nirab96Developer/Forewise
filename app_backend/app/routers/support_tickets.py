# app/routers/support_tickets.py
"""Support ticket endpoints."""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
import json
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.email import send_email
from app.core.config import settings
from app.models.user import User
from app.models.support_ticket import SupportTicket
from app.schemas.support_ticket import SupportTicketCreate, SupportTicketUpdate, SupportTicketResponse
from app.services.activity_logger import log_support_ticket_created, log_support_ticket_replied, log_support_ticket_status_changed

# Admin email for ticket notifications
ADMIN_EMAIL = "avitbulnir@gmail.com"


def _notify_admins_new_ticket(db, ticket_id: int, ticket_number: str,
                               title: str, description: str, user_name: str):
    """Send in-app notification to all ADMIN users about a new support ticket."""
    try:
        from app.services.notification_service import notification_service
        from app.schemas.notification import NotificationCreate
        admins = db.query(User).join(User.role).filter(
            User.is_active.is_(True)
        ).all()
        admins = [u for u in admins if getattr(getattr(u, 'role', None), 'code', '') == 'ADMIN']
        for admin in admins:
            notif = NotificationCreate(
                user_id=admin.id,
                title=f"📨 קריאת תמיכה חדשה מ-{user_name}",
                message=description[:120] + ('...' if len(description) > 120 else ''),
                notification_type="SUPPORT_TICKET",
                priority="high",
                link=f"/support",
            )
            notification_service.create_notification(db, notif)
    except Exception as e:
        print(f"[WARN] Admin support notification failed: {e}")


def _notify_user_ticket_update(db, ticket_id: int, ticket_number: str,
                                user_id: int, is_resolved: bool = False):
    """Notify ticket owner when admin replies or resolves."""
    try:
        from app.services.notification_service import notification_service
        from app.schemas.notification import NotificationCreate
        if is_resolved:
            title = f"✅ קריאתך {ticket_number} טופלה"
            message = "הצוות טיפל בקריאתך. תוכל לראות את הפרטים בדף התמיכה."
        else:
            title = f"💬 תגובה חדשה על קריאה {ticket_number}"
            message = "הצוות הגיב לקריאתך. לחץ לצפייה בתגובה."
        notif = NotificationCreate(
            user_id=user_id,
            title=title,
            message=message,
            notification_type="SUPPORT_TICKET",
            priority="normal",
            link=f"/support",
        )
        notification_service.create_notification(db, notif)
    except Exception as e:
        print(f"[WARN] User ticket update notification failed: {e}")


def _generate_ticket_number(db: Session) -> str:
    """Generate unique ticket number: TKT-YYYYMM-NNNN"""
    now = datetime.utcnow()
    count = (
        db.query(func.count(SupportTicket.id))
        .filter(
            func.extract("year", SupportTicket.created_at) == now.year,
            func.extract("month", SupportTicket.created_at) == now.month,
        )
        .scalar() or 0
    )
    return f"TKT-{now.year}{now.month:02d}-{count + 1:04d}"


def _send_new_ticket_email(ticket_id: int, title: str, description: str, user_name: str, category: str):
    """Send email notification to admin about new support ticket (runs in background)."""
    try:
        subject = f"🎫 טיקט חדש #{ticket_id}: {title}"
        body = f"""טיקט תמיכה חדש נפתח במערכת.

📋 פרטים:
• מספר: #{ticket_id}
• כותרת: {title}
• קטגוריה: {category}
• נפתח ע״י: {user_name}

📝 תיאור:
{description[:500]}

🔗 לצפייה במערכת:
http://167.99.228.10/support

---
מערכת ניהול יערות קק״ל
"""
        send_email(to=ADMIN_EMAIL, subject=subject, body=body)
    except Exception as e:
        print(f"[WARN] Failed to send ticket email: {e}")


# Schema for widget ticket creation
class StepResult(BaseModel):
    stepId: str
    helped: bool


class ClientContext(BaseModel):
    url: str
    browser: str
    resolution: str
    timestamp: str


class WidgetTicketCreate(BaseModel):
    """Schema for creating a ticket from the help widget."""
    userId: str
    userName: str
    userRole: str
    regionId: Optional[str] = None
    areaId: Optional[str] = None
    projectId: Optional[str] = None
    currentRoute: str
    category: str
    stepsWalked: List[StepResult]
    userMessage: str
    clientContext: ClientContext

router = APIRouter(prefix="/support-tickets", tags=["Support Tickets"])


@router.get("/")
async def get_support_tickets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    page: int = Query(1, ge=1),
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get support tickets with optional filters."""
    query = db.query(SupportTicket)
    
    # Apply filters
    if status_filter:
        query = query.filter(SupportTicket.status == status_filter)
    if priority:
        query = query.filter(SupportTicket.priority == priority)
    if category:
        query = query.filter(SupportTicket.category == category)
    
    # Filter by user if not admin
    if current_user.role.code != "ADMIN":
        query = query.filter(SupportTicket.user_id == current_user.id)
    
    # Order by most recent first
    offset = (page - 1) * limit if page > 1 else skip
    tickets = query.order_by(SupportTicket.created_at.desc()).offset(offset).limit(limit).all()
    
    return tickets


@router.get("/{ticket_id}")
async def get_support_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific support ticket by ID."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Support ticket not found"
        )
    
    # Check permission: admin or ticket owner
    if current_user.role.code != "ADMIN" and ticket.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this ticket"
        )
    
    return ticket


@router.post("/")
async def create_support_ticket(
    ticket: SupportTicketCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new support ticket."""
    ticket_number = _generate_ticket_number(db)
    
    new_ticket = SupportTicket(
        ticket_number=ticket_number,
        title=ticket.title,
        description=ticket.description,
        type=ticket.type if hasattr(ticket, 'type') else "other",
        priority=ticket.priority if hasattr(ticket, 'priority') else "normal",
        status="open",
        user_id=current_user.id,
        created_by_id=current_user.id,
        assigned_to_id=1,  # Always assign to admin (you)
        category=ticket.category if hasattr(ticket, 'category') else None,
        is_active=True,
    )
    
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    
    # Log to activity log (יומן פעילות)
    log_support_ticket_created(
        db=db,
        ticket_id=new_ticket.id,
        user_id=current_user.id,
        title=new_ticket.title,
        category=new_ticket.category or "general",
        source="manual",
    )
    
    # Send email notification to admin in background
    background_tasks.add_task(
        _send_new_ticket_email,
        new_ticket.id,
        new_ticket.title,
        new_ticket.description,
        current_user.full_name or current_user.username,
        new_ticket.category or "general",
    )

    # In-app notification to all ADMINs
    _notify_admins_new_ticket(db, new_ticket.id, new_ticket.ticket_number,
                              new_ticket.title, new_ticket.description,
                              current_user.full_name or current_user.username)

    return new_ticket


@router.post("/from-widget")
async def create_ticket_from_widget(
    data: WidgetTicketCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a support ticket from the smart help widget.
    Includes all context information for faster resolution.
    """
    # Build steps walked summary
    steps_summary = []
    for i, step in enumerate(data.stepsWalked):
        steps_summary.append({
            "step": i + 1,
            "stepId": step.stepId,
            "helped": step.helped
        })
    
    # Build metadata JSON
    metadata = {
        "source": "WIDGET",
        "route": data.currentRoute,
        "role": data.userRole,
        "region_id": data.regionId,
        "area_id": data.areaId,
        "project_id": data.projectId,
        "steps_walked": steps_summary,
        "client_context": {
            "url": data.clientContext.url,
            "browser": data.clientContext.browser[:200] if data.clientContext.browser else None,  # Truncate long user-agent
            "resolution": data.clientContext.resolution,
            "timestamp": data.clientContext.timestamp,
        },
        "created_at": datetime.utcnow().isoformat(),
    }
    
    # Map category to readable title
    category_titles = {
        "LOGIN": "בעיית התחברות",
        "WORKLOG": "בעיה בדיווח שעות",
        "WORK_ORDER": "בעיה בהזמנת עבודה",
        "PROJECT": "בעיה בפרויקט",
        "GENERAL": "בעיה כללית",
    }
    
    title = category_titles.get(data.category, "פנייה מהמערכת")
    
    # Generate ticket number
    ticket_number = _generate_ticket_number(db)
    
    # Create the ticket
    new_ticket = SupportTicket(
        ticket_number=ticket_number,
        title=f"{title} - {data.userName}",
        description=data.userMessage,
        type="technical_issue",
        category=data.category,
        priority="normal",
        status="open",
        user_id=current_user.id,
        created_by_id=current_user.id,
        assigned_to_id=1,  # Always assign to admin (you)
        is_active=True,
    )
    
    # Store metadata in custom_metadata_json
    try:
        new_ticket.custom_metadata_json = json.dumps(metadata, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Could not set metadata: {e}")
    
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    
    # Log to activity log (יומן פעילות)
    log_support_ticket_created(
        db=db,
        ticket_id=new_ticket.id,
        user_id=current_user.id,
        title=new_ticket.title,
        category=data.category,
        source="widget",
    )
    
    # Send email notification to admin in background (non-blocking)
    background_tasks.add_task(
        _send_new_ticket_email,
        new_ticket.id,
        new_ticket.title,
        data.userMessage,
        data.userName,
        data.category,
    )
    
    print(f"[SUPPORT] New ticket #{new_ticket.id} ({ticket_number}) created from widget")
    print(f"[SUPPORT] Category: {data.category}, User: {data.userName} ({data.userRole})")

    # In-app notification to all ADMINs
    _notify_admins_new_ticket(db, new_ticket.id, new_ticket.ticket_number,
                              new_ticket.title, data.userMessage,
                              data.userName)

    return {
        "ticket_id": new_ticket.id,
        "ticket_number": new_ticket.ticket_number,
        "status": new_ticket.status,
    }


@router.put("/{ticket_id}")
async def update_support_ticket(
    ticket_id: int,
    ticket: SupportTicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a support ticket."""
    db_ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not db_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Support ticket not found"
        )
    
    # Check permission
    if current_user.role.code != "ADMIN" and db_ticket.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this ticket"
        )
    
    # Track status change for logging
    old_status = db_ticket.status
    
    # Update fields
    for key, value in ticket.dict(exclude_unset=True).items():
        setattr(db_ticket, key, value)
    
    db.commit()
    db.refresh(db_ticket)
    
    # Log status change to activity log
    if hasattr(ticket, 'status') and ticket.status and ticket.status != old_status:
        log_support_ticket_status_changed(
            db=db,
            ticket_id=ticket_id,
            user_id=current_user.id,
            old_status=old_status,
            new_status=db_ticket.status,
        )
    
    return db_ticket


# ============================================
# COMMENTS (Chat Messages)
# ============================================

class CommentInput(BaseModel):
    content: str


@router.get("/{ticket_id}/comments")
async def get_ticket_comments(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all comments/messages for a ticket."""
    from app.models.support_ticket_comment import SupportTicketComment
    
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Permission check
    if current_user.role.code != "ADMIN" and ticket.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    comments = (
        db.query(SupportTicketComment)
        .filter(SupportTicketComment.ticket_id == ticket_id)
        .order_by(SupportTicketComment.created_at.asc())
        .all()
    )
    
    # Enrich with user names
    result = []
    for c in comments:
        user = db.query(User).filter(User.id == c.user_id).first()
        result.append({
            "id": c.id,
            "ticket_id": c.ticket_id,
            "user_id": c.user_id,
            "user_name": user.full_name if user else "Unknown",
            "is_staff": user.role.code == "ADMIN" if user and user.role else False,
            "content": c.comment_text,
            "is_internal": c.is_internal or False,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    
    return result


@router.post("/{ticket_id}/comments")
async def add_ticket_comment(
    ticket_id: int,
    comment: CommentInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a comment/message to a ticket. Auto-updates status."""
    from app.models.support_ticket_comment import SupportTicketComment
    
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Permission check
    if current_user.role.code != "ADMIN" and ticket.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    is_staff = current_user.role.code == "ADMIN"
    
    # Create comment
    new_comment = SupportTicketComment(
        ticket_id=ticket_id,
        user_id=current_user.id,
        comment_text=comment.content,
        is_internal=False,
    )
    db.add(new_comment)
    
    # Auto-update ticket status
    old_status = ticket.status
    if is_staff and ticket.status == "open":
        ticket.status = "in_progress"
    
    ticket.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(new_comment)
    
    # Log to activity
    log_support_ticket_replied(
        db=db,
        ticket_id=ticket_id,
        user_id=current_user.id,
        is_staff=is_staff,
    )
    
    if ticket.status != old_status:
        log_support_ticket_status_changed(
            db=db,
            ticket_id=ticket_id,
            user_id=current_user.id,
            old_status=old_status,
            new_status=ticket.status,
        )

    # Notify ticket owner when admin replies
    if is_staff and ticket.user_id != current_user.id:
        _notify_user_ticket_update(db, ticket_id, ticket.ticket_number,
                                   ticket.user_id, is_resolved=False)

    return {
        "id": new_comment.id,
        "ticket_id": ticket_id,
        "user_id": current_user.id,
        "user_name": current_user.full_name,
        "is_staff": is_staff,
        "content": new_comment.comment_text,
        "created_at": new_comment.created_at.isoformat() if new_comment.created_at else None,
    }


class TicketStatusPatch(BaseModel):
    status: str  # "open" | "in_progress" | "resolved"


@router.patch("/{ticket_id}/status")
async def patch_ticket_status(
    ticket_id: int,
    body: TicketStatusPatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Admin-only: change ticket status and notify owner."""
    if current_user.role.code != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")

    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    old_status = ticket.status
    ticket.status = body.status
    ticket.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(ticket)

    log_support_ticket_status_changed(
        db=db, ticket_id=ticket_id, user_id=current_user.id,
        old_status=old_status, new_status=body.status,
    )

    # Notify owner
    if ticket.user_id != current_user.id:
        _notify_user_ticket_update(
            db, ticket_id, ticket.ticket_number,
            ticket.user_id, is_resolved=(body.status == "resolved")
        )

    return {"ticket_id": ticket_id, "status": ticket.status}
