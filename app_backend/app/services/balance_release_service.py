# app/services/balance_release_service.py
"""Budget balance release management service."""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload

from app.models.balance_release import BalanceRelease
from app.models.budget import Budget
from app.schemas.balance_release import ReleaseCreate


class BalanceReleaseService:
    """Service for balance release operations."""

    def get_release(self, db: Session, release_id: int) -> Optional[BalanceRelease]:
        """Get balance release by ID."""
        return (
            db.query(BalanceRelease)
            .options(
                joinedload(BalanceRelease.budget),
                joinedload(BalanceRelease.requested_by),
                joinedload(BalanceRelease.approved_by),
            )
            .filter(
                and_(BalanceRelease.id == release_id, BalanceRelease.is_active == True)
            )
            .first()
        )

    def get_releases(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        budget_id: Optional[int] = None,
        release_type: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[BalanceRelease]:
        """Get list of balance releases with filters."""
        query = db.query(BalanceRelease).filter(BalanceRelease.is_active == True)

        if budget_id:
            query = query.filter(BalanceRelease.budget_id == budget_id)
        if release_type:
            query = query.filter(BalanceRelease.release_type == release_type)
        if status:
            query = query.filter(BalanceRelease.status == status)
        if start_date:
            query = query.filter(BalanceRelease.scheduled_date >= start_date)
        if end_date:
            query = query.filter(BalanceRelease.scheduled_date <= end_date)

        return (
            query.order_by(BalanceRelease.scheduled_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_release(
        self, db: Session, release: ReleaseCreate, requested_by_id: int
    ) -> BalanceRelease:
        """Create balance release request."""
        # Get budget
        budget = db.query(Budget).filter(Budget.id == release.budget_id).first()
        if not budget:
            raise ValueError("Budget not found")

        # Check available balance
        available = (
            budget.total_amount - budget.allocated_amount - budget.committed_amount
        )
        if release.amount > available:
            raise ValueError(f"Insufficient budget. Available: {available}")

        # Create release
        db_release = BalanceRelease(
            budget_id=release.budget_id,
            release_type=release.release_type,
            amount=release.amount,
            reason=release.reason,
            scheduled_date=release.scheduled_date or date.today(),
            requested_by_id=requested_by_id,
            status="pending",
            created_at=datetime.utcnow(),
        )

        # Handle different release types
        if release.release_type == "immediate":
            db_release.scheduled_date = date.today()
            db_release.requires_approval = True

        elif release.release_type == "scheduled":
            if not release.scheduled_date:
                raise ValueError("Scheduled date required for scheduled release")
            db_release.scheduled_date = release.scheduled_date
            db_release.requires_approval = True

        elif release.release_type == "conditional":
            if not release.condition:
                raise ValueError("Condition required for conditional release")
            db_release.condition = release.condition
            db_release.requires_approval = True

        elif release.release_type == "recurring":
            if not release.recurrence_pattern:
                raise ValueError("Recurrence pattern required for recurring release")
            db_release.recurrence_pattern = release.recurrence_pattern
            db_release.next_release_date = self._calculate_next_release_date(
                release.scheduled_date or date.today(), release.recurrence_pattern
            )

        db.add(db_release)
        db.commit()
        db.refresh(db_release)
        return db_release

    def approve_release(
        self,
        db: Session,
        release_id: int,
        approved_by_id: int,
        approval_notes: Optional[str] = None,
    ) -> Optional[BalanceRelease]:
        """Approve balance release."""
        db_release = self.get_release(db, release_id)
        if not db_release:
            return None

        if db_release.status != "pending":
            raise ValueError("Release not in pending status")

        db_release.status = "approved"
        db_release.approved_by_id = approved_by_id
        db_release.approved_at = datetime.utcnow()
        db_release.approval_notes = approval_notes
        db_release.updated_at = datetime.utcnow()

        # Execute if immediate or scheduled for today
        if db_release.release_type == "immediate" or (
            db_release.release_type == "scheduled"
            and db_release.scheduled_date <= date.today()
        ):
            self._execute_release(db, db_release)

        db.commit()
        db.refresh(db_release)
        return db_release

    def reject_release(
        self, db: Session, release_id: int, rejected_by_id: int, rejection_reason: str
    ) -> Optional[BalanceRelease]:
        """Reject balance release."""
        db_release = self.get_release(db, release_id)
        if not db_release:
            return None

        if db_release.status != "pending":
            raise ValueError("Release not in pending status")

        db_release.status = "rejected"
        db_release.rejected_by_id = rejected_by_id
        db_release.rejected_at = datetime.utcnow()
        db_release.rejection_reason = rejection_reason
        db_release.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(db_release)
        return db_release

    def execute_scheduled_releases(self, db: Session) -> int:
        """Execute all scheduled releases due today."""
        releases = (
            db.query(BalanceRelease)
            .filter(
                and_(
                    BalanceRelease.status == "approved",
                    BalanceRelease.scheduled_date <= date.today(),
                    BalanceRelease.executed_at == None,
                    BalanceRelease.is_active == True,
                )
            )
            .all()
        )

        count = 0
        for release in releases:
            try:
                self._execute_release(db, release)
                count += 1
            except Exception as e:
                # Log error but continue with other releases
                import logging; logging.getLogger(__name__).error(f"Failed to execute release {release.id}: {e}")

        db.commit()
        return count

    def check_conditional_releases(self, db: Session) -> int:
        """Check and execute conditional releases."""
        releases = (
            db.query(BalanceRelease)
            .filter(
                and_(
                    BalanceRelease.status == "approved",
                    BalanceRelease.release_type == "conditional",
                    BalanceRelease.executed_at == None,
                    BalanceRelease.is_active == True,
                )
            )
            .all()
        )

        count = 0
        for release in releases:
            if self._check_condition(db, release):
                self._execute_release(db, release)
                count += 1

        db.commit()
        return count

    def process_recurring_releases(self, db: Session) -> int:
        """Process recurring releases."""
        releases = (
            db.query(BalanceRelease)
            .filter(
                and_(
                    BalanceRelease.release_type == "recurring",
                    BalanceRelease.status == "approved",
                    BalanceRelease.next_release_date <= date.today(),
                    BalanceRelease.is_active == True,
                )
            )
            .all()
        )

        count = 0
        for release in releases:
            # Execute current release
            self._execute_release(db, release)

            # Calculate next release date
            release.next_release_date = self._calculate_next_release_date(
                release.next_release_date, release.recurrence_pattern
            )

            # Check if more occurrences
            if release.recurrence_count:
                release.recurrence_count -= 1
                if release.recurrence_count == 0:
                    release.status = "completed"

            count += 1

        db.commit()
        return count

    def get_release_forecast(
        self, db: Session, budget_id: int, days_ahead: int = 30
    ) -> List[Dict[str, Any]]:
        """Get forecast of upcoming releases."""
        end_date = date.today() + timedelta(days=days_ahead)

        releases = (
            db.query(BalanceRelease)
            .filter(
                and_(
                    BalanceRelease.budget_id == budget_id,
                    BalanceRelease.status.in_(["pending", "approved"]),
                    BalanceRelease.scheduled_date <= end_date,
                    BalanceRelease.executed_at == None,
                    BalanceRelease.is_active == True,
                )
            )
            .order_by(BalanceRelease.scheduled_date)
            .all()
        )

        forecast = []
        cumulative = Decimal("0")

        for release in releases:
            cumulative += release.amount
            forecast.append(
                {
                    "release_id": release.id,
                    "date": release.scheduled_date.isoformat(),
                    "amount": float(release.amount),
                    "cumulative": float(cumulative),
                    "type": release.release_type,
                    "status": release.status,
                    "reason": release.reason,
                }
            )

        return forecast

    def get_release_summary(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        budget_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get release summary statistics."""
        query = db.query(BalanceRelease).filter(
            and_(
                BalanceRelease.executed_at >= start_date,
                BalanceRelease.executed_at <= end_date,
                BalanceRelease.is_active == True,
            )
        )

        if budget_id:
            query = query.filter(BalanceRelease.budget_id == budget_id)

        releases = query.all()

        # Calculate totals
        total_amount = sum(r.amount for r in releases)

        # Group by type
        by_type = {}
        for release in releases:
            if release.release_type not in by_type:
                by_type[release.release_type] = {"count": 0, "amount": Decimal("0")}
            by_type[release.release_type]["count"] += 1
            by_type[release.release_type]["amount"] += release.amount

        # Average approval time
        approval_times = []
        for release in releases:
            if release.approved_at and release.created_at:
                time_diff = (
                    release.approved_at - release.created_at
                ).total_seconds() / 3600
                approval_times.append(time_diff)

        avg_approval_time = (
            sum(approval_times) / len(approval_times) if approval_times else 0
        )

        return {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "total_releases": len(releases),
            "total_amount": float(total_amount),
            "by_type": {
                k: {"count": v["count"], "amount": float(v["amount"])}
                for k, v in by_type.items()
            },
            "avg_approval_hours": round(avg_approval_time, 2),
        }

    def _execute_release(self, db: Session, release: BalanceRelease):
        """Execute balance release."""
        budget = release.budget
        if not budget:
            raise ValueError("Budget not found for release")

        # Update budget
        budget.allocated_amount += release.amount
        budget.available_amount = (
            budget.total_amount
            - budget.allocated_amount
            - budget.committed_amount
            - budget.spent_amount
        )

        # Mark release as executed
        release.status = "executed"
        release.executed_at = datetime.utcnow()
        release.actual_amount = release.amount

        # Log transaction
        from app.services.activity_log_service import ActivityLogService

        log_service = ActivityLogService()
        log_service.log_audit(
            db=db,
            table_name="budgets",
            record_id=budget.id,
            action="balance_release",
            new_values={
                "release_id": release.id,
                "amount": float(release.amount),
                "new_allocated": float(budget.allocated_amount),
                "new_available": float(budget.available_amount),
            },
            user_id=release.requested_by_id,
        )

    def _check_condition(self, db: Session, release: BalanceRelease) -> bool:
        """Check if conditional release condition is met."""
        if not release.condition:
            return False

        condition = release.condition

        # Example conditions (implement based on business rules)
        if condition.get("type") == "budget_utilization":
            budget = release.budget
            if budget:
                utilization = (
                    (budget.spent_amount / budget.total_amount * 100)
                    if budget.total_amount
                    else 0
                )
                threshold = condition.get("threshold", 0)
                return utilization >= threshold

        elif condition.get("type") == "date_reached":
            target_date = condition.get("date")
            if target_date:
                return date.today() >= date.fromisoformat(target_date)

        elif condition.get("type") == "project_milestone":
            # Check if project milestone is completed
            from app.models.milestone import Milestone

            milestone_id = condition.get("milestone_id")
            if milestone_id:
                milestone = (
                    db.query(Milestone).filter(Milestone.id == milestone_id).first()
                )
                return milestone and milestone.status == "completed"

        return False

    def _calculate_next_release_date(
        self, current_date: date, pattern: Dict[str, Any]
    ) -> date:
        """Calculate next release date based on recurrence pattern."""
        frequency = pattern.get("frequency", "monthly")
        interval = pattern.get("interval", 1)

        if frequency == "daily":
            return current_date + timedelta(days=interval)
        elif frequency == "weekly":
            return current_date + timedelta(weeks=interval)
        elif frequency == "monthly":
            # Handle month boundaries
            from dateutil.relativedelta import relativedelta

            return current_date + relativedelta(months=interval)
        elif frequency == "quarterly":
            from dateutil.relativedelta import relativedelta

            return current_date + relativedelta(months=3 * interval)
        elif frequency == "yearly":
            from dateutil.relativedelta import relativedelta

            return current_date + relativedelta(years=interval)

        return current_date + timedelta(days=30)  # Default
