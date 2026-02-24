"""
ReportRun Service
"""

from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.report_run import ReportRun
from app.models.report import Report
from app.schemas.report_run import ReportRunCreate, ReportRunUpdate, ReportRunSearch, ReportRunStatistics
from app.core.exceptions import NotFoundException, ValidationException


class ReportRunService:
    """ReportRun Service - TRANSACTIONS"""
    
    def _generate_run_number(self, db: Session) -> int:
        """Generate unique run number"""
        max_num = db.query(func.max(ReportRun.run_number)).scalar() or 0
        return max_num + 1
    
    def create(self, db: Session, data: ReportRunCreate, current_user_id: int) -> ReportRun:
        """Create report run"""
        # Validate FK: report_id
        report = db.query(Report).filter_by(id=data.report_id).first()
        if not report:
            raise ValidationException(f"Report {data.report_id} not found")
        if not report.is_active:
            raise ValidationException(f"Report {data.report_id} is not active")
        
        # Generate run_number
        run_number = self._generate_run_number(db)
        
        # Create
        run_dict = data.model_dump(exclude_unset=True)
        run_dict['run_by'] = current_user_id
        run_dict['run_number'] = run_number
        run_dict['retry_count'] = 0
        run_dict['queued_at'] = datetime.utcnow()
        
        # Ensure status has default
        if 'status' not in run_dict or not run_dict['status']:
            run_dict['status'] = 'PENDING'
        
        run = ReportRun(**run_dict)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run
    
    def get_by_id(self, db: Session, run_id: int) -> Optional[ReportRun]:
        """Get run"""
        return db.query(ReportRun).filter_by(id=run_id).first()
    
    def update(self, db: Session, run_id: int, data: ReportRunUpdate, current_user_id: int) -> ReportRun:
        """Update run"""
        run = self.get_by_id(db, run_id)
        if not run:
            raise NotFoundException(f"ReportRun {run_id} not found")
        
        update_dict = data.model_dump(exclude_unset=True)
        
        for field, value in update_dict.items():
            setattr(run, field, value)
        
        db.commit()
        db.refresh(run)
        return run
    
    def list(self, db: Session, search: ReportRunSearch) -> Tuple[List[ReportRun], int]:
        """List report runs"""
        query = db.query(ReportRun)
        
        if search.report_id:
            query = query.filter(ReportRun.report_id == search.report_id)
        if search.status:
            query = query.filter(ReportRun.status == search.status.value)
        if search.run_by:
            query = query.filter(ReportRun.run_by == search.run_by)
        if search.date_from:
            query = query.filter(ReportRun.created_at >= search.date_from)
        if search.date_to:
            query = query.filter(ReportRun.created_at <= search.date_to)
        
        total = query.count()
        
        sort_col = getattr(ReportRun, search.sort_by, ReportRun.created_at)
        query = query.order_by(sort_col.desc() if search.sort_desc else sort_col.asc())
        
        offset = (search.page - 1) * search.page_size
        runs = query.offset(offset).limit(search.page_size).all()
        
        return runs, total
    
    def get_statistics(self, db: Session, report_id: Optional[int] = None) -> ReportRunStatistics:
        """Get statistics"""
        query = db.query(ReportRun)
        
        if report_id:
            query = query.filter(ReportRun.report_id == report_id)
        
        runs = query.all()
        
        by_status = {}
        for run in runs:
            by_status[run.status] = by_status.get(run.status, 0) + 1
        
        success_count = sum(1 for r in runs if r.status == 'SUCCESS')
        failed_count = sum(1 for r in runs if r.status == 'FAILED')
        
        exec_times = [r.execution_time_ms for r in runs if r.execution_time_ms]
        avg_exec = sum(exec_times) // len(exec_times) if exec_times else None
        
        return ReportRunStatistics(
            total=len(runs),
            by_status=by_status,
            success_count=success_count,
            failed_count=failed_count,
            avg_execution_time_ms=avg_exec
        )
