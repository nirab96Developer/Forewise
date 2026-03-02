"""
Project Service
"""

from typing import Optional, List, Tuple
import time
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func, or_

from app.models.project import Project
from app.models.user import User
from app.models.region import Region
from app.models.area import Area
from app.models.location import Location
from app.models.budget import Budget
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectSearch, ProjectStatistics
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException


class ProjectService:
    """Project Service - CORE"""
    
    def get_by_id(self, db: Session, id: int) -> Optional[Project]:
        """Get by ID with location eagerly loaded"""
        return db.query(Project).options(
            joinedload(Project.location)
        ).filter(
            Project.id == id,
            Project.deleted_at.is_(None)
        ).first()
    
    def get_by_id_or_404(self, db: Session, id: int) -> Project:
        """Get by ID or raise"""
        item = self.get_by_id(db, id)
        if not item:
            raise NotFoundException(f"Project {id} not found")
        return item
    
    def create(self, db: Session, data: ProjectCreate, current_user_id: int) -> Project:
        """Create"""
        item_dict = data.model_dump(exclude_unset=True)
        if not item_dict.get("code"):
            item_dict["code"] = f"PRJ-{int(time.time() * 1000)}"

        # ── Required-field validation (Fix 7) ──────────────────────────────
        missing = []
        if not item_dict.get("region_id"):
            missing.append("מרחב (region_id)")
        if not item_dict.get("area_id"):
            missing.append("אזור (area_id)")
        if not item_dict.get("manager_id"):
            missing.append("מנהל עבודה (manager_id)")
        if missing:
            raise ValidationException(
                f"שדות חובה חסרים: {', '.join(missing)}. "
                "פרויקט חייב לכלול מרחב, אזור ומנהל עבודה."
            )
        # ───────────────────────────────────────────────────────────────────

        # Validate UNIQUE: code (if provided)
        if item_dict.get("code"):
            existing = db.query(Project).filter(
                func.lower(Project.code) == func.lower(item_dict["code"]),
                Project.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Project code '{item_dict['code']}' already exists")
        
        # Validate FK: manager_id
        manager = db.query(User).filter(User.id == data.manager_id).first()
        if not manager:
            raise ValidationException(f"מנהל עבודה עם ID {data.manager_id} לא נמצא")
        
        # Validate FK: region_id
        region = db.query(Region).filter(
            Region.id == data.region_id,
            Region.deleted_at.is_(None)
        ).first()
        if not region:
            raise ValidationException(f"Region {data.region_id} not found")
        
        # Validate FK: area_id
        area = db.query(Area).filter(
            Area.id == data.area_id,
            Area.deleted_at.is_(None)
        ).first()
        if not area:
            raise ValidationException(f"Area {data.area_id} not found")
        
        # Validate FK: location_id
        location = db.query(Location).filter(
            Location.id == data.location_id,
            Location.deleted_at.is_(None)
        ).first()
        if not location:
            raise ValidationException(f"Location {data.location_id} not found")
        
        # Validate FK: budget_id (optional)
        if data.budget_id:
            budget = db.query(Budget).filter(
                Budget.id == data.budget_id,
                Budget.deleted_at.is_(None)
            ).first()
            if not budget:
                raise ValidationException(f"Budget {data.budget_id} not found")
        
        # Create
        item = Project(**item_dict)
        
        db.add(item)
        db.commit()
        db.refresh(item)

        # Auto-create budget for new project
        try:
            from app.models.budget import Budget
            import datetime as _dt
            budget = Budget(
                project_id=item.id,
                total_amount=0,
                spent_amount=0,
                committed_amount=0,
                status='ACTIVE',
            )
            db.add(budget)
            db.commit()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to auto-create budget for project {item.id}: {e}")

        return item
    
    def update(self, db: Session, item_id: int, data: ProjectUpdate, current_user_id: int) -> Project:
        """Update"""
        item = self.get_by_id_or_404(db, item_id)
        
        # Version check
        if data.version is not None and item.version != data.version:
            raise DuplicateException("Item was modified by another user")
        
        update_dict = data.model_dump(exclude_unset=True, exclude={'version'})

        # ── Required-field validation on update (Fix 7) ──────────────────
        # If the user is explicitly nullifying required fields, block it
        for field, label in [("region_id", "מרחב"), ("area_id", "אזור"), ("manager_id", "מנהל עבודה")]:
            if field in update_dict and not update_dict[field]:
                raise ValidationException(f"לא ניתן להסיר {label} מפרויקט. שדה זה הוא חובה.")
        # ──────────────────────────────────────────────────────────────────

        # Validate UNIQUE: code (if changed)
        if 'code' in update_dict and update_dict['code'] and update_dict['code'] != item.code:
            existing = db.query(Project).filter(
                func.lower(Project.code) == func.lower(update_dict['code']),
                Project.id != item_id,
                Project.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Project code '{update_dict['code']}' already exists")
        
        # Validate FKs if changed
        if 'manager_id' in update_dict:
            manager = db.query(User).filter(User.id == update_dict['manager_id']).first()
            if not manager:
                raise ValidationException(f"Manager {update_dict['manager_id']} not found")
        
        if 'region_id' in update_dict:
            region = db.query(Region).filter(
                Region.id == update_dict['region_id'],
                Region.deleted_at.is_(None)
            ).first()
            if not region:
                raise ValidationException(f"Region {update_dict['region_id']} not found")
        
        if 'area_id' in update_dict:
            area = db.query(Area).filter(
                Area.id == update_dict['area_id'],
                Area.deleted_at.is_(None)
            ).first()
            if not area:
                raise ValidationException(f"Area {update_dict['area_id']} not found")
        
        if 'location_id' in update_dict:
            location = db.query(Location).filter(
                Location.id == update_dict['location_id'],
                Location.deleted_at.is_(None)
            ).first()
            if not location:
                raise ValidationException(f"Location {update_dict['location_id']} not found")
        
        if 'budget_id' in update_dict and update_dict['budget_id']:
            budget = db.query(Budget).filter(
                Budget.id == update_dict['budget_id'],
                Budget.deleted_at.is_(None)
            ).first()
            if not budget:
                raise ValidationException(f"Budget {update_dict['budget_id']} not found")
        
        # Capture old status for audit
        old_status = item.status

        # Update
        for field, value in update_dict.items():
            setattr(item, field, value)
        
        if item.version is not None:
            item.version += 1
        
        db.commit()
        db.refresh(item)

        # Audit log if status changed
        if 'status' in update_dict and update_dict['status'] != old_status:
            _audit_project(db, current_user_id, item.id, 'STATUS_CHANGE',
                           {'status': old_status}, {'status': item.status})

        return item
    
    def list(self, db: Session, search: ProjectSearch) -> Tuple[List[Project], int]:
        """List - optimized with eager loading"""
        # Use eager loading to prevent N+1 queries
        query = select(Project).options(
            joinedload(Project.location),
            joinedload(Project.region),
            joinedload(Project.area),
            joinedload(Project.manager)
        )
        
        # Build filter conditions for count query
        filter_conditions = []
        
        if not search.include_deleted:
            filter_conditions.append(Project.deleted_at.is_(None))
        
        if search.q:
            term = f"%{search.q}%"
            filter_conditions.append(or_(
                Project.name.ilike(term),
                Project.code.ilike(term),
                Project.description.ilike(term)
            ))
        
        if search.manager_id is not None:
            filter_conditions.append(Project.manager_id == search.manager_id)
        
        if search.region_id is not None:
            filter_conditions.append(Project.region_id == search.region_id)
        
        if search.area_id is not None:
            filter_conditions.append(Project.area_id == search.area_id)
        
        if search.location_id is not None:
            filter_conditions.append(Project.location_id == search.location_id)
        
        if search.is_active is not None:
            filter_conditions.append(Project.is_active == search.is_active)
        
        # Apply filters to main query
        for condition in filter_conditions:
            query = query.where(condition)
        
        # Count query (simple, no eager loading)
        count_query = select(func.count(Project.id))
        for condition in filter_conditions:
            count_query = count_query.where(condition)
        total = db.execute(count_query).scalar() or 0
        
        sort_col = getattr(Project, search.sort_by, Project.name)
        query = query.order_by(sort_col.desc() if search.sort_desc else sort_col.asc())
        
        offset = (search.page - 1) * search.page_size
        items = db.execute(query.offset(offset).limit(search.page_size)).scalars().unique().all()
        
        return items, total
    
    def get_by_code(self, db: Session, code: str) -> Optional[Project]:
        """Get by code with location eagerly loaded"""
        return db.execute(
            select(Project).options(
                joinedload(Project.location)
            ).where(
                func.lower(Project.code) == func.lower(code),
                Project.deleted_at.is_(None)
            )
        ).unique().scalar_one_or_none()
    
    def soft_delete(self, db: Session, item_id: int, current_user_id: int) -> Project:
        """Soft delete"""
        item = self.get_by_id_or_404(db, item_id)
        from datetime import datetime
        item.deleted_at = datetime.utcnow()
        item.is_active = False
        db.commit()
        db.refresh(item)
        return item
    
    def restore(self, db: Session, item_id: int, current_user_id: int) -> Project:
        """Restore"""
        item = db.query(Project).filter(
            Project.id == item_id
        ).first()
        if not item:
            raise NotFoundException(f"Project {item_id} not found")
        item.deleted_at = None
        item.is_active = True
        db.commit()
        db.refresh(item)
        return item
    
    def get_statistics(self, db: Session) -> ProjectStatistics:
        """Get statistics"""
        items = db.execute(
            select(Project).where(Project.deleted_at.is_(None))
        ).scalars().all()
        
        return ProjectStatistics(
            total=len(items),
            active_count=sum(1 for i in items if i.is_active)
        )


def _audit_project(db, user_id, record_id, action, old_values=None, new_values=None):
    import logging, json
    try:
        from sqlalchemy import text
        db.execute(text("""
            INSERT INTO audit_logs (user_id, table_name, record_id, action, old_values, new_values)
            VALUES (:uid, 'projects', :rid, :act, :ov::jsonb, :nv::jsonb)
        """), {
            "uid": user_id, "rid": record_id, "act": action,
            "ov": json.dumps(old_values or {}), "nv": json.dumps(new_values or {})
        })
        db.commit()
    except Exception as e:
        logging.getLogger(__name__).warning(f"Project audit log failed: {e}")
