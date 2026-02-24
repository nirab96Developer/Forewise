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
        """יצירת משתמש חדש"""
        # Validate email unique
        if self.get_by_email(db, user_data.email):
            raise DuplicateException("Email already exists")
        
        # Validate username unique
        if user_data.username and self.get_by_username(db, user_data.username):
            raise DuplicateException("Username already exists")
        
        # Hash password
        password_hash = get_password_hash(user_data.password)
        
        # Create
        user_dict = user_data.model_dump(exclude={'password'})
        user_dict['password_hash'] = password_hash
        
        return self.create(db, user_dict)
    
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
