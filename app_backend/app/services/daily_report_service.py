# app/services/daily_report_service.py
"""Daily work report service."""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models.daily_work_report import DailyWorkReport
from app.models.project import Project
from app.models.work_order import WorkOrder
from app.models.worklog import Worklog
from app.schemas.daily_work_report import DailyReportCreate, DailyReportUpdate


class DailyReportService:
    """Service for daily work report operations."""

    def get_daily_report(
        self, db: Session, report_id: int
    ) -> Optional[DailyWorkReport]:
        """Get daily report by ID."""
        return (
            db.query(DailyWorkReport)
            .filter(
                and_(DailyWorkReport.id == report_id, DailyWorkReport.is_active == True)
            )
            .first()
        )

    def get_daily_report_by_date(
        self, db: Session, project_id: int, report_date: date
    ) -> Optional[DailyWorkReport]:
        """Get daily report for specific project and date."""
        return (
            db.query(DailyWorkReport)
            .filter(
                and_(
                    DailyWorkReport.project_id == project_id,
                    DailyWorkReport.report_date == report_date,
                    DailyWorkReport.is_active == True,
                )
            )
            .first()
        )

    def get_daily_reports(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        project_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        submitted_by: Optional[int] = None,
    ) -> List[DailyWorkReport]:
        """Get list of daily reports with filters."""
        query = db.query(DailyWorkReport).filter(DailyWorkReport.is_active == True)

        if project_id:
            query = query.filter(DailyWorkReport.project_id == project_id)
        if start_date:
            query = query.filter(DailyWorkReport.report_date >= start_date)
        if end_date:
            query = query.filter(DailyWorkReport.report_date <= end_date)
        if submitted_by:
            query = query.filter(DailyWorkReport.submitted_by == submitted_by)

        return (
            query.order_by(DailyWorkReport.report_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_daily_report(
        self, db: Session, report: DailyReportCreate, submitted_by_id: int
    ) -> DailyWorkReport:
        """Create new daily report."""
        # Check if report already exists for this date
        existing = self.get_daily_report_by_date(
            db, report.project_id, report.report_date
        )

        if existing:
            raise ValueError("Daily report already exists for this date")

        # Auto-calculate totals from worklogs if not provided
        if not report.total_hours:
            total_hours = self._calculate_daily_hours(
                db, report.project_id, report.report_date
            )
            report.total_hours = total_hours

        if not report.workers_count:
            workers_count = self._count_daily_workers(
                db, report.project_id, report.report_date
            )
            report.workers_count = workers_count

        # Create report
        db_report = DailyWorkReport(
            **report.dict(),
            submitted_by=submitted_by_id,
            created_at=datetime.utcnow(),
        )

        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        return db_report

    def update_daily_report(
        self, db: Session, report_id: int, report: DailyReportUpdate
    ) -> Optional[DailyWorkReport]:
        """Update daily report."""
        db_report = self.get_daily_report(db, report_id)
        if not db_report:
            return None

        update_data = report.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_report, field, value)

        db_report.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_report)
        return db_report

    def auto_generate_daily_report(
        self, db: Session, project_id: int, report_date: date, submitted_by_id: int
    ) -> DailyWorkReport:
        """Auto-generate daily report from worklogs."""
        # Check if already exists
        existing = self.get_daily_report_by_date(db, project_id, report_date)
        if existing:
            return existing

        # Get all worklogs for the day
        worklogs = (
            db.query(Worklog)
            .join(WorkOrder)
            .filter(
                and_(
                    WorkOrder.project_id == project_id,
                    Worklog.report_date == report_date,
                    Worklog.status.in_(["approved", "submitted"]),
                )
            )
            .all()
        )

        # Calculate totals
        total_hours = sum(w.total_hours for w in worklogs)
        workers = set(w.user_id for w in worklogs)
        workers_count = len(workers)

        # Get activities
        activities = []
        activity_types = {}
        for worklog in worklogs:
            if worklog.activity_type:
                if worklog.activity_type not in activity_types:
                    activity_types[worklog.activity_type] = 0
                activity_types[worklog.activity_type] += worklog.total_hours

        for activity_type, hours in activity_types.items():
            activities.append(f"{activity_type}: {hours} שעות")

        activities_summary = (
            "\n".join(activities) if activities else "אין פירוט פעילויות"
        )

        # Create report
        db_report = DailyWorkReport(
            project_id=project_id,
            report_date=report_date,
            workers_count=workers_count,
            total_work_hours=float(total_hours),
            activities_summary=activities_summary,
            safety_incidents=0,  # Default
            weather_conditions="תקין",  # Default
            status="draft",
            is_active=True,
            submitted_by=submitted_by_id,
            created_at=datetime.utcnow(),
        )

        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        return db_report

    def get_project_daily_summary(
        self, db: Session, project_id: int, start_date: date, end_date: date
    ) -> Dict[str, Any]:
        """Get project daily reports summary."""
        reports = self.get_daily_reports(
            db, project_id=project_id, start_date=start_date, end_date=end_date
        )

        if not reports:
            return {
                "project_id": project_id,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "reports_count": 0,
                "total_hours": 0,
                "total_workers": 0,
                "daily_data": [],
            }

        total_hours = sum(
            (r.total_work_hours or 0) for r in reports
        )
        unique_workers = set()
        safety_incidents = sum(r.safety_incidents for r in reports)

        daily_data = []
        for report in reports:
            daily_data.append(
                {
                    "date": report.report_date.isoformat(),
                    "hours": report.total_work_hours,
                    "workers": report.workers_count,
                    "safety_incidents": report.safety_incidents,
                    "weather": report.weather_conditions,
                }
            )

            # Track unique workers (approximate)
            for i in range(report.workers_count):
                unique_workers.add(f"{report.report_date}_{i}")

        return {
            "project_id": project_id,
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "reports_count": len(reports),
            "total_hours": total_hours,
            "average_daily_hours": total_hours / len(reports),
            "total_safety_incidents": safety_incidents,
            "daily_data": daily_data,
        }

    def get_missing_reports(
        self, db: Session, project_id: int, start_date: date, end_date: date
    ) -> List[date]:
        """Get dates missing daily reports for a project."""
        # Get project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return []

        # Get existing reports
        existing_reports = (
            db.query(DailyWorkReport.report_date)
            .filter(
                and_(
                    DailyWorkReport.project_id == project_id,
                    DailyWorkReport.report_date >= start_date,
                    DailyWorkReport.report_date <= end_date,
                    DailyWorkReport.is_active == True,
                )
            )
            .all()
        )

        existing_dates = {r.report_date for r in existing_reports}

        # Check each date
        missing_dates = []
        current = start_date
        while current <= end_date:
            # Skip weekends (Friday-Saturday in Israel)
            if current.weekday() not in [4, 5]:  # Not Friday or Saturday
                if current not in existing_dates:
                    # Check if there were worklogs for this date
                    has_worklogs = (
                        db.query(Worklog)
                        .join(WorkOrder)
                        .filter(
                            and_(
                                WorkOrder.project_id == project_id,
                                Worklog.report_date == current,
                            )
                        )
                        .first()
                    )

                    if has_worklogs:
                        missing_dates.append(current)

            current += timedelta(days=1)

        return missing_dates

    def _calculate_daily_hours(
        self, db: Session, project_id: int, report_date: date
    ) -> float:
        """Calculate total hours for a day from worklogs."""
        total = db.query(func.sum(Worklog.total_hours)).join(WorkOrder).filter(
            and_(
                WorkOrder.project_id == project_id,
                Worklog.report_date == report_date,
                Worklog.status.in_(["approved", "submitted"]),
            )
        ).scalar() or Decimal("0")

        return float(total)

    def _count_daily_workers(
        self, db: Session, project_id: int, report_date: date
    ) -> int:
        """Count unique workers for a day."""
        worker_ids = (
            db.query(Worklog.user_id)
            .join(WorkOrder)
            .filter(
                and_(
                    WorkOrder.project_id == project_id,
                    Worklog.report_date == report_date,
                )
            )
            .distinct()
            .all()
        )

        return len(worker_ids)

    def validate_report_completeness(
        self, db: Session, report_id: int
    ) -> Dict[str, Any]:
        """Validate if daily report is complete."""
        report = self.get_daily_report(db, report_id)
        if not report:
            return {"valid": False, "errors": ["Report not found"]}

        errors = []
        warnings = []

        # Check required fields
        if not report.activities_summary or len(report.activities_summary) < 10:
            errors.append("Activities summary is too short")

        if (report.total_work_hours or 0) <= 0:
            errors.append("Total hours must be greater than 0")

        if report.workers_count <= 0:
            errors.append("Workers count must be greater than 0")

        # Check consistency with worklogs
        actual_hours = self._calculate_daily_hours(
            db, report.project_id, report.report_date
        )

        if abs(actual_hours - (report.total_work_hours or 0)) > 0.5:
            warnings.append(
                f"Reported hours ({report.total_work_hours}) don't match worklogs ({actual_hours})"
            )

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}
