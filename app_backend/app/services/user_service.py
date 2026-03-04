"""
User Service - לוגיקה עסקית למשתמשים
"""
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, and_, or_, func

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserSearch
from app.services.base_service import BaseService
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException
from app.core.security import get_password_hash, verify_password


class UserService(BaseService[User]):
    """User service"""
    
    def __init__(self):
        super().__init__(User)
    
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """קבלת משתמש לפי email"""
        query = self._base_query(db).where(User.email == email)
        return db.execute(query).scalar_one_or_none()
    
    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """קבלת משתמש לפי username"""
        query = self._base_query(db).where(User.username == username)
        return db.execute(query).scalar_one_or_none()
    
    def list_with_filters(
        self,
        db: Session,
        filters: UserSearch
    ) -> Tuple[List[User], int]:
        """רשימת משתמשים עם פילטרים - optimized with eager loading"""
        # Use eager loading to prevent N+1 queries
        query = self._base_query(db).options(
            joinedload(User.role),
            joinedload(User.region),
            joinedload(User.area),
            joinedload(User.department)
        )
        
        # Apply filters
        if filters.email:
            query = query.where(User.email.ilike(f"%{filters.email}%"))
        
        if filters.full_name:
            query = query.where(User.full_name.ilike(f"%{filters.full_name}%"))
        
        if filters.role_id:
            query = query.where(User.role_id == filters.role_id)
        
        if filters.department_id:
            query = query.where(User.department_id == filters.department_id)
        
        if filters.region_id:
            query = query.where(User.region_id == filters.region_id)
        
        if filters.area_id:
            query = query.where(User.area_id == filters.area_id)
        
        if filters.is_active is not None:
            query = query.where(User.is_active == filters.is_active)
        
        if filters.status:
            query = query.where(User.status == filters.status)
        
        # Count (using a simple count query without eager loading)
        count_query = select(func.count(User.id))
        if self._has_deleted_at:
            count_query = count_query.where(User.deleted_at.is_(None))
        if filters.email:
            count_query = count_query.where(User.email.ilike(f"%{filters.email}%"))
        if filters.full_name:
            count_query = count_query.where(User.full_name.ilike(f"%{filters.full_name}%"))
        if filters.role_id:
            count_query = count_query.where(User.role_id == filters.role_id)
        if filters.department_id:
            count_query = count_query.where(User.department_id == filters.department_id)
        if filters.region_id:
            count_query = count_query.where(User.region_id == filters.region_id)
        if filters.area_id:
            count_query = count_query.where(User.area_id == filters.area_id)
        if filters.is_active is not None:
            count_query = count_query.where(User.is_active == filters.is_active)
        if filters.status:
            count_query = count_query.where(User.status == filters.status)
        
        total = db.execute(count_query).scalar() or 0
        
        # Sort
        if filters.sort_by and hasattr(User, filters.sort_by):
            order_col = getattr(User, filters.sort_by)
            query = query.order_by(order_col.desc() if filters.sort_desc else order_col.asc())
        
        # Paginate
        offset = (filters.page - 1) * filters.page_size
        query = query.offset(offset).limit(filters.page_size)
        
        users = db.execute(query).scalars().unique().all()
        
        return users, total
    
    def create_user(
        self,
        db: Session,
        user_data: UserCreate
    ) -> User:
        """יצירת משתמש חדש + שליחת welcome email עם סיסמה זמנית"""
        import logging
        log = logging.getLogger(__name__)

        # Validate email unique
        if self.get_by_email(db, user_data.email):
            raise DuplicateException("Email already exists")
        
        # Validate username unique
        if user_data.username and self.get_by_username(db, user_data.username):
            raise DuplicateException("Username already exists")

        plain_password = user_data.password  # save before hashing

        # Hash password
        password_hash = get_password_hash(plain_password)

        # Create — exclude fields that don't exist on the User model
        user_dict = user_data.model_dump(exclude={'password', 'project_ids'})
        user_dict['password_hash'] = password_hash

        user_dict['must_change_password'] = True  # enforce password change on first login
        user = self.create(db, user_dict)

        # ── Project assignments ───────────────────────────────────────────
        project_ids = getattr(user_data, 'project_ids', None) or []
        if project_ids:
            try:
                from sqlalchemy import text
                import datetime as _dt
                for pid in project_ids:
                    db.execute(text("""
                        INSERT INTO project_assignments
                            (project_id, user_id, role, status, is_active, created_at, updated_at)
                        VALUES (:pid, :uid, 'member', 'active', true, :now, :now)
                        ON CONFLICT DO NOTHING
                    """), {"pid": pid, "uid": user.id, "now": _dt.datetime.utcnow()})
                db.commit()
            except Exception as e:
                log.warning(f"Failed to create project assignments for user {user.id}: {e}")

        # ── Send welcome email with temp password ─────────────────────────
        try:
            from app.core.email import send_email
            from app.core.config import settings
            login_url = getattr(settings, "FRONTEND_URL", "http://167.99.228.10")
            full_name = getattr(user_data, "full_name", "") or user_data.email
            subject = "ברוך הבא למערכת קק\"ל — פרטי כניסה"
            body = (
                f"שלום {full_name},\n\n"
                f"נוצר עבורך חשבון חדש במערכת קק\"ל.\n\n"
                f"פרטי כניסה:\n"
                f"  אימייל:  {user_data.email}\n"
                f"  סיסמה:  {plain_password}\n\n"
                f"קישור לכניסה:\n{login_url}\n\n"
                f"מומלץ לשנות את הסיסמה לאחר הכניסה הראשונה.\n\n"
                "קק\"ל"
            )
            html_body = f"""
<div dir="rtl" style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;">
  <div style="background:#2d6a2d;color:#fff;padding:20px 24px;border-radius:8px 8px 0 0;">
    <h2 style="margin:0;">ברוך הבא למערכת קק&quot;ל 🌲</h2>
  </div>
  <div style="padding:24px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 8px 8px;">
    <p>שלום <strong>{full_name}</strong>,</p>
    <p>נוצר עבורך חשבון חדש במערכת ניהול ההזמנות של קק&quot;ל.</p>
    <table style="background:#f9fafb;border-radius:8px;padding:16px;width:100%;border-collapse:collapse;margin:16px 0;">
      <tr><td style="padding:6px 8px;color:#6b7280;">אימייל</td><td style="padding:6px 8px;font-weight:bold;">{user_data.email}</td></tr>
      <tr><td style="padding:6px 8px;color:#6b7280;">סיסמה זמנית</td><td style="padding:6px 8px;font-weight:bold;font-family:monospace;font-size:16px;">{plain_password}</td></tr>
    </table>
    <a href="{login_url}" style="display:inline-block;background:#2d6a2d;color:#fff;padding:12px 24px;border-radius:6px;text-decoration:none;font-size:15px;margin:8px 0;">
      כניסה למערכת →
    </a>
    <p style="color:#6b7280;font-size:13px;margin-top:20px;">מומלץ לשנות את הסיסמה לאחר הכניסה הראשונה.</p>
    <p style="color:#6b7280;font-size:13px;">קק&quot;ל</p>
  </div>
</div>"""
            send_email(to=user_data.email, subject=subject, body=body, html_body=html_body)
            log.info(f"Welcome email sent to {user_data.email}")
        except Exception as e:
            log.warning(f"Failed to send welcome email to {user_data.email}: {e}")

        # Audit log
        _audit_user(db, None, user.id, 'CREATE', {}, {'email': user.email, 'username': user.username})

        return user
    
    def update_user(
        self,
        db: Session,
        user_id: int,
        user_data: UserUpdate
    ) -> User:
        """עדכון משתמש"""
        user = self.get_by_id_or_404(db, user_id)
        
        # Validate email unique (if changed)
        if user_data.email and user_data.email != user.email:
            if self.get_by_email(db, user_data.email):
                raise DuplicateException("Email already exists")
        
        # Validate username unique (if changed)
        if user_data.username and user_data.username != user.username:
            if self.get_by_username(db, user_data.username):
                raise DuplicateException("Username already exists")
        
        # Update
        update_dict = user_data.model_dump(exclude_unset=True, exclude_none=True)
        return self.update(db, user_id, update_dict)
    
    def change_password(
        self,
        db: Session,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> None:
        """החלפת סיסמה"""
        user = self.get_by_id_or_404(db, user_id)
        
        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise ValidationException("Current password is incorrect")
        
        # Update
        new_hash = get_password_hash(new_password)
        user.password_hash = new_hash
        user.must_change_password = False
        
        db.commit()
    
    def lock_user(
        self,
        db: Session,
        user_id: int,
        locked_until: Optional[datetime] = None
    ) -> User:
        """נעילת משתמש"""
        user = self.get_by_id_or_404(db, user_id)
        
        user.is_locked = True
        user.locked_until = locked_until
        
        db.commit()
        db.refresh(user)
        
        return user
    
    def unlock_user(self, db: Session, user_id: int) -> User:
        """ביטול נעילה"""
        user = self.get_by_id_or_404(db, user_id)
        
        user.is_locked = False
        user.locked_until = None
        
        db.commit()
        db.refresh(user)
        
        return user
    
    def update_last_login(self, db: Session, user_id: int) -> None:
        """עדכון זמן כניסה אחרון"""
        user = self.get_by_id_or_404(db, user_id)
        user.last_login = datetime.utcnow()
        db.commit()


# Singleton instance
user_service = UserService()


def _audit_user(db, user_id, record_id, action, old_values=None, new_values=None):
    import logging, json
    try:
        from sqlalchemy import text
        db.execute(text("""
            INSERT INTO audit_logs (user_id, table_name, record_id, action, old_values, new_values)
            VALUES (:uid, 'users', :rid, :act, :ov::jsonb, :nv::jsonb)
        """), {
            "uid": user_id, "rid": record_id, "act": action,
            "ov": json.dumps(old_values or {}), "nv": json.dumps(new_values or {})
        })
        db.commit()
    except Exception as e:
        logging.getLogger(__name__).warning(f"User audit log failed: {e}")
