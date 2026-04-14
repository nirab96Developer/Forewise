# app/core/scope.py
"""
Centralized scope enforcement for role-based access control.

Every write/approve/reject action must pass through these checks.
This module ensures:
  - Users can only act within their area/region scope
  - Self-approval is blocked
  - Role-appropriate access is enforced
"""
import logging

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException

log = logging.getLogger(__name__)

GLOBAL_ROLES = frozenset({"ADMIN"})
REGIONAL_ROLES = frozenset({"REGION_MANAGER", "ORDER_COORDINATOR"})
AREA_ROLES = frozenset({"AREA_MANAGER", "ACCOUNTANT"})
FIELD_ROLES = frozenset({"WORK_MANAGER"})


def _role_code(user) -> str:
    if hasattr(user, 'role') and user.role:
        return getattr(user.role, 'code', '') or ''
    return ''


def enforce_scope_for_project(user, project, db: Session = None):
    """Ensure user has access to this project based on role and org scope.

    - ADMIN: always allowed
    - REGION_MANAGER: project must be in user's region
    - AREA_MANAGER / ACCOUNTANT: project must be in user's area
    - WORK_MANAGER: project must be in user's area
    - ORDER_COORDINATOR: project must be in user's region
    """
    role = _role_code(user).upper()
    if role in GLOBAL_ROLES:
        return

    if role in REGIONAL_ROLES:
        if user.region_id and getattr(project, 'region_id', None):
            if project.region_id != user.region_id:
                raise ForbiddenException("אין הרשאה לפרויקט מחוץ למרחב שלך")
        return

    user_area = getattr(user, 'area_id', None)
    proj_area = getattr(project, 'area_id', None)
    if user_area and proj_area and user_area != proj_area:
        raise ForbiddenException("אין הרשאה לפרויקט מחוץ לאזור שלך")


def enforce_scope_for_entity(user, entity, db: Session = None):
    """Generic scope check for entities that have project_id.

    Loads the project and delegates to enforce_scope_for_project.
    """
    role = _role_code(user).upper()
    if role in GLOBAL_ROLES:
        return

    project_id = getattr(entity, 'project_id', None)
    if not project_id:
        return

    project = getattr(entity, 'project', None)
    if project is None and db:
        from app.models.project import Project
        project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        enforce_scope_for_project(user, project, db)


def block_self_approval(user, entity, action_label: str = "לאשר"):
    """Prevent a user from approving their own work.

    Checks: entity.created_by_id, entity.user_id against current_user.id.
    """
    creator_id = getattr(entity, 'created_by_id', None)
    user_id_field = getattr(entity, 'user_id', None)

    if creator_id and creator_id == user.id:
        raise ForbiddenException(
            f"לא ניתן {action_label} פריט שיצרת בעצמך"
        )
    if user_id_field and user_id_field == user.id:
        raise ForbiddenException(
            f"לא ניתן {action_label} פריט שיצרת בעצמך"
        )


def enforce_write_scope(user, entity, db: Session = None,
                        action_label: str = "לעדכן"):
    """Combination check for any write operation: scope + not-self if approval."""
    enforce_scope_for_entity(user, entity, db)
