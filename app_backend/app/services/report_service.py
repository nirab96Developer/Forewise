"""
Report Service
"""

from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_

from app.models.report import Report
from app.schemas.report import ReportCreate, ReportUpdate, ReportSearch, ReportStatistics
from app.services.base_service import BaseService
from app.core.exceptions import DuplicateException


class ReportService(BaseService[Report]):
    """Report Service - CORE"""
    
    def __init__(self):
        super().__init__(Report)
    
    def create(self, db: Session, data: ReportCreate, current_user_id: int) -> Report:
        """Create report"""
        # Validate UNIQUE: code
        existing = db.query(Report).filter(
            Report.code == data.code,
            Report.deleted_at.is_(None)
        ).first()
        if existing:
            raise DuplicateException(f"Report code '{data.code}' already exists")
        
        # Create
        report_dict = data.model_dump(exclude_unset=True)
        report_dict['created_by_id'] = current_user_id
        
        report = Report(**report_dict)
        db.add(report)
        db.commit()
        db.refresh(report)
        return report
    
    def update(self, db: Session, report_id: int, data: ReportUpdate, current_user_id: int) -> Report:
        """Update report"""
        report = self.get_by_id_or_404(db, report_id)
        
        # Version check
        if data.version is not None and report.version != data.version:
            raise DuplicateException("Report was modified by another user")
        
        update_dict = data.model_dump(exclude_unset=True, exclude={'version'})
        
        # Validate UNIQUE: code (if changed)
        if 'code' in update_dict and update_dict['code'] != report.code:
            existing = db.query(Report).filter(
                Report.code == update_dict['code'],
                Report.id != report_id,
                Report.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Report code '{update_dict['code']}' already exists")
        
        # Update
        for field, value in update_dict.items():
            setattr(report, field, value)
        
        if report.version is not None:
            report.version += 1
        
        db.commit()
        db.refresh(report)
        return report
    
    def list(self, db: Session, search: ReportSearch) -> Tuple[List[Report], int]:
        """List reports"""
        query = self._base_query(db, include_deleted=search.include_deleted)
        
        if search.q:
            term = f"%{search.q}%"
            query = query.where(or_(
                Report.name.ilike(term),
                Report.code.ilike(term),
                Report.description.ilike(term)
            ))
        
        if search.type:
            query = query.where(Report.type == search.type.value)
        if search.status:
            query = query.where(Report.status == search.status.value)
        if search.owner_id:
            query = query.where(Report.owner_id == search.owner_id)
        if search.is_scheduled is not None:
            query = query.where(Report.is_scheduled == search.is_scheduled)
        if search.is_active is not None:
            query = query.where(Report.is_active == search.is_active)
        
        total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0
        
        sort_col = getattr(Report, search.sort_by, Report.name)
        query = query.order_by(sort_col.desc() if search.sort_desc else sort_col.asc())
        
        offset = (search.page - 1) * search.page_size
        reports = db.execute(query.offset(offset).limit(search.page_size)).scalars().all()
        
        return reports, total
    
    def get_by_code(self, db: Session, code: str) -> Optional[Report]:
        """Get by code"""
        return db.execute(
            select(Report).where(Report.code == code, Report.deleted_at.is_(None))
        ).scalar_one_or_none()
    
    def get_statistics(self, db: Session) -> ReportStatistics:
        """Get statistics"""
        query = select(Report).where(Report.deleted_at.is_(None))
        reports = db.execute(query).scalars().all()
        
        by_type = {}
        for r in reports:
            by_type[r.type] = by_type.get(r.type, 0) + 1
        
        by_status = {}
        for r in reports:
            by_status[r.status] = by_status.get(r.status, 0) + 1
        
        return ReportStatistics(
            total=len(reports),
            by_type=by_type,
            by_status=by_status,
            scheduled_count=sum(1 for r in reports if r.is_scheduled)
        )
