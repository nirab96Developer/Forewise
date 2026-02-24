# app/services/support_ticket_service.py
"""Support ticket management service."""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.support_ticket import SupportTicket
from app.models.support_ticket_comment import SupportTicketComment
from app.models.user import User
from app.schemas.support_ticket import (CommentCreate, TicketCreate,
                                        TicketUpdate)


class SupportTicketService:
    """Service for support ticket operations."""

    def get_ticket(self, db: Session, ticket_id: int) -> Optional[SupportTicket]:
        """Get support ticket by ID with relationships."""
        return (
            db.query(SupportTicket)
            .options(
                joinedload(SupportTicket.created_by),
                joinedload(SupportTicket.assigned_to),
                joinedload(SupportTicket.comments),
            )
            .filter(
                and_(SupportTicket.id == ticket_id, SupportTicket.is_active == True)
            )
            .first()
        )

    def get_ticket_by_number(
        self, db: Session, ticket_number: str
    ) -> Optional[SupportTicket]:
        """Get support ticket by ticket number."""
        return (
            db.query(SupportTicket)
            .filter(
                and_(
                    SupportTicket.ticket_number == ticket_number,
                    SupportTicket.is_active == True,
                )
            )
            .first()
        )

    def get_tickets(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        created_by_id: Optional[int] = None,
        assigned_to_id: Optional[int] = None,
    ) -> List[SupportTicket]:
        """Get list of support tickets with filters."""
        query = db.query(SupportTicket).filter(SupportTicket.is_active == True)

        if status:
            query = query.filter(SupportTicket.status == status)
        if priority:
            query = query.filter(SupportTicket.priority == priority)
        if category:
            query = query.filter(SupportTicket.category == category)
        if created_by_id:
            query = query.filter(SupportTicket.created_by_id == created_by_id)
        if assigned_to_id:
            query = query.filter(SupportTicket.assigned_to_id == assigned_to_id)

        return (
            query.order_by(
                SupportTicket.priority.asc(),  # Critical first
                SupportTicket.created_at.desc(),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_ticket(
        self, db: Session, ticket: TicketCreate, created_by_id: int
    ) -> SupportTicket:
        """Create new support ticket."""
        # Generate ticket number
        ticket_number = self._generate_ticket_number(db)

        # Set SLA based on priority
        sla_hours = {"critical": 2, "high": 4, "medium": 8, "low": 24}

        sla_deadline = datetime.utcnow() + timedelta(
            hours=sla_hours.get(ticket.priority, 24)
        )

        db_ticket = SupportTicket(
            ticket_number=ticket_number,
            title=ticket.title,
            description=ticket.description,
            category=ticket.category,
            priority=ticket.priority,
            status="open",
            created_by_id=created_by_id,
            sla_deadline=sla_deadline,
            created_at=datetime.utcnow(),
        )

        # Auto-assign based on category
        if ticket.category == "technical":
            # Find available tech support
            tech_support = (
                db.query(User)
                .join(Role)
                .filter(and_(Role.code == "tech_support", User.is_active == True))
                .first()
            )
            if tech_support:
                db_ticket.assigned_to_id = tech_support.id

        db.add(db_ticket)
        db.commit()
        db.refresh(db_ticket)

        # Send notification
        self._send_ticket_notification(db, db_ticket, "created")

        return db_ticket

    def update_ticket(
        self, db: Session, ticket_id: int, ticket: TicketUpdate, updated_by_id: int
    ) -> Optional[SupportTicket]:
        """Update support ticket."""
        db_ticket = self.get_ticket(db, ticket_id)
        if not db_ticket:
            return None

        # Track changes for notification
        old_status = db_ticket.status
        old_assigned = db_ticket.assigned_to_id

        update_data = ticket.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_ticket, field, value)

        db_ticket.updated_at = datetime.utcnow()

        # Add system comment for status change
        if ticket.status and ticket.status != old_status:
            self.add_comment(
                db,
                ticket_id=ticket_id,
                comment_text=f"Status changed from {old_status} to {ticket.status}",
                user_id=updated_by_id,
                is_system=True,
            )

            # Set resolution time if resolved
            if ticket.status in ["resolved", "closed"]:
                db_ticket.resolved_at = datetime.utcnow()
                db_ticket.resolved_by_id = updated_by_id

        # Send notification if assigned
        if ticket.assigned_to_id and ticket.assigned_to_id != old_assigned:
            self._send_ticket_notification(db, db_ticket, "assigned")

        db.commit()
        db.refresh(db_ticket)
        return db_ticket

    def add_comment(
        self,
        db: Session,
        ticket_id: int,
        comment_text: str,
        user_id: int,
        is_internal: bool = False,
        is_system: bool = False,
    ) -> Optional[SupportTicketComment]:
        """Add comment to ticket."""
        ticket = self.get_ticket(db, ticket_id)
        if not ticket:
            return None

        comment = SupportTicketComment(
            ticket_id=ticket_id,
            user_id=user_id,
            comment_text=comment_text,
            is_internal=is_internal,
            is_system=is_system,
            created_at=datetime.utcnow(),
        )

        db.add(comment)

        # Update ticket activity
        ticket.last_activity_at = datetime.utcnow()

        # Send notification to ticket creator if not internal
        if not is_internal and not is_system and user_id != ticket.created_by_id:
            self._send_ticket_notification(db, ticket, "comment_added")

        db.commit()
        db.refresh(comment)
        return comment

    def assign_ticket(
        self, db: Session, ticket_id: int, assignee_id: int, assigned_by_id: int
    ) -> Optional[SupportTicket]:
        """Assign ticket to user."""
        ticket = self.get_ticket(db, ticket_id)
        if not ticket:
            return None

        # Check if assignee exists
        assignee = db.query(User).filter(User.id == assignee_id).first()
        if not assignee:
            raise ValueError("Assignee not found")

        ticket.assigned_to_id = assignee_id
        ticket.status = "in_progress"
        ticket.updated_at = datetime.utcnow()

        # Add system comment
        self.add_comment(
            db,
            ticket_id=ticket_id,
            comment_text=f"Ticket assigned to {assignee.full_name}",
            user_id=assigned_by_id,
            is_system=True,
        )

        # Send notification
        self._send_ticket_notification(db, ticket, "assigned")

        db.commit()
        db.refresh(ticket)
        return ticket

    def resolve_ticket(
        self, db: Session, ticket_id: int, resolution: str, resolved_by_id: int
    ) -> Optional[SupportTicket]:
        """Resolve support ticket."""
        ticket = self.get_ticket(db, ticket_id)
        if not ticket:
            return None

        ticket.status = "resolved"
        ticket.resolution = resolution
        ticket.resolved_at = datetime.utcnow()
        ticket.resolved_by_id = resolved_by_id
        ticket.updated_at = datetime.utcnow()

        # Add resolution comment
        self.add_comment(
            db,
            ticket_id=ticket_id,
            comment_text=f"Ticket resolved: {resolution}",
            user_id=resolved_by_id,
            is_system=True,
        )

        # Send notification
        self._send_ticket_notification(db, ticket, "resolved")

        db.commit()
        db.refresh(ticket)
        return ticket

    def get_user_tickets(
        self,
        db: Session,
        user_id: int,
        role: str = "creator",  # "creator", "assignee", "both"
    ) -> List[SupportTicket]:
        """Get tickets for a user."""
        query = db.query(SupportTicket).filter(SupportTicket.is_active == True)

        if role == "creator":
            query = query.filter(SupportTicket.created_by_id == user_id)
        elif role == "assignee":
            query = query.filter(SupportTicket.assigned_to_id == user_id)
        elif role == "both":
            query = query.filter(
                or_(
                    SupportTicket.created_by_id == user_id,
                    SupportTicket.assigned_to_id == user_id,
                )
            )

        return query.order_by(SupportTicket.created_at.desc()).all()

    def get_ticket_statistics(self, db: Session, days_back: int = 30) -> Dict[str, Any]:
        """Get support ticket statistics."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        # Total tickets
        total_tickets = (
            db.query(func.count(SupportTicket.id))
            .filter(
                and_(
                    SupportTicket.created_at >= cutoff_date,
                    SupportTicket.is_active == True,
                )
            )
            .scalar()
            or 0
        )

        # By status
        status_counts = (
            db.query(SupportTicket.status, func.count(SupportTicket.id))
            .filter(
                and_(
                    SupportTicket.created_at >= cutoff_date,
                    SupportTicket.is_active == True,
                )
            )
            .group_by(SupportTicket.status)
            .all()
        )

        # By priority
        priority_counts = (
            db.query(SupportTicket.priority, func.count(SupportTicket.id))
            .filter(
                and_(
                    SupportTicket.created_at >= cutoff_date,
                    SupportTicket.is_active == True,
                )
            )
            .group_by(SupportTicket.priority)
            .all()
        )

        # Average resolution time
        resolved_tickets = (
            db.query(SupportTicket)
            .filter(
                and_(
                    SupportTicket.created_at >= cutoff_date,
                    SupportTicket.status == "resolved",
                    SupportTicket.resolved_at != None,
                )
            )
            .all()
        )

        avg_resolution_hours = 0
        if resolved_tickets:
            total_hours = sum(
                (t.resolved_at - t.created_at).total_seconds() / 3600
                for t in resolved_tickets
            )
            avg_resolution_hours = total_hours / len(resolved_tickets)

        # SLA compliance
        sla_breached = (
            db.query(func.count(SupportTicket.id))
            .filter(
                and_(
                    SupportTicket.created_at >= cutoff_date,
                    SupportTicket.resolved_at > SupportTicket.sla_deadline,
                )
            )
            .scalar()
            or 0
        )

        sla_compliance = 100
        if resolved_tickets:
            sla_compliance = (
                (len(resolved_tickets) - sla_breached) / len(resolved_tickets)
            ) * 100

        return {
            "period_days": days_back,
            "total_tickets": total_tickets,
            "by_status": dict(status_counts),
            "by_priority": dict(priority_counts),
            "resolved_count": len(resolved_tickets),
            "avg_resolution_hours": round(avg_resolution_hours, 2),
            "sla_compliance_percent": round(sla_compliance, 2),
            "sla_breached_count": sla_breached,
        }

    def _generate_ticket_number(self, db: Session) -> str:
        """Generate unique ticket number."""
        year = datetime.now().year
        month = datetime.now().month

        count = (
            db.query(func.count(SupportTicket.id))
            .filter(
                func.extract("year", SupportTicket.created_at) == year,
                func.extract("month", SupportTicket.created_at) == month,
            )
            .scalar()
            or 0
        )

        return f"TKT-{year}{month:02d}-{count + 1:04d}"

    def _send_ticket_notification(
        self, db: Session, ticket: SupportTicket, event_type: str
    ):
        """Send notification for ticket events."""
        from app.services.notification_service import NotificationService

        notification_service = NotificationService()

        if event_type == "created":
            # Notify assigned person
            if ticket.assigned_to_id:
                notification_service.create_notification(
                    db=db,
                    user_id=ticket.assigned_to_id,
                    title="New Support Ticket",
                    message=f"Ticket {ticket.ticket_number}: {ticket.title}",
                    notification_type="info",
                    priority=ticket.priority,
                    channels=["in_app", "email"],
                    metadata={"ticket_id": ticket.id},
                )

        elif event_type == "assigned":
            # Notify new assignee
            if ticket.assigned_to_id:
                notification_service.create_notification(
                    db=db,
                    user_id=ticket.assigned_to_id,
                    title="Ticket Assigned to You",
                    message=f"Ticket {ticket.ticket_number}: {ticket.title}",
                    notification_type="info",
                    priority=ticket.priority,
                    channels=["in_app", "email"],
                    metadata={"ticket_id": ticket.id},
                )

        elif event_type == "resolved":
            # Notify ticket creator
            notification_service.create_notification(
                db=db,
                user_id=ticket.created_by_id,
                title="Ticket Resolved",
                message=f"Your ticket {ticket.ticket_number} has been resolved",
                notification_type="success",
                channels=["in_app", "email"],
                metadata={"ticket_id": ticket.id},
            )
