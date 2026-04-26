"""Per-resource ABAC scope strategies.

Each strategy answers two questions for a (user, resource) pair:

  check(user, resource) -> None | raises HTTPException(403)
      Verify a single resource is in the user's scope.

  filter(user, query)   -> Query
      Narrow a list query so the user only sees their own scope.

Wave 1 ships only `BudgetScopeStrategy`. Other resources (WorkOrder,
SupplierRotation, Notification, Worklog, Invoice, SupportTicket) are
declared as TODO in the registry below — adding them in later sub-waves
is a matter of writing one class and registering it; nothing else moves.
"""
from __future__ import annotations

from typing import Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User


def _is_global(user: User) -> bool:
    """ADMIN / SUPER_ADMIN / ORDER_COORDINATOR see across all scopes for
    most resources. Per-resource overrides go inside each strategy."""
    code = (user.role.code if user.role else "").upper()
    return code in ("ADMIN", "SUPER_ADMIN")


_FORBIDDEN = lambda detail: HTTPException(  # noqa: E731
    status_code=status.HTTP_403_FORBIDDEN, detail=detail
)


class BudgetScopeStrategy:
    """Mirrors `routers/budgets.py:_check_budget_scope` exactly.

    Behavior must stay identical so the 27 existing tests in
    test_budgets_scope_permissions.py keep passing without edits.

    Roles:
      ADMIN / SUPER_ADMIN  → all
      REGION_MANAGER       → budget.region_id == user.region_id
      AREA_MANAGER         → budget.area_id   == user.area_id
      ACCOUNTANT           → area_id OR region_id match
      WORK_MANAGER         → budget.project_id is in user's
                              active project_assignments (DB query)
      anything else (incl. SUPPLIER) → 403
    """

    DETAIL = "אין הרשאה לתקציב זה"

    def check(self, db: Session, user: User, budget) -> None:
        if _is_global(user):
            return

        code = (user.role.code if user.role else "").upper()

        if code == "REGION_MANAGER":
            if not user.region_id or budget.region_id != user.region_id:
                raise _FORBIDDEN(self.DETAIL)
            return

        if code == "AREA_MANAGER":
            if not user.area_id or budget.area_id != user.area_id:
                raise _FORBIDDEN(self.DETAIL)
            return

        if code == "ACCOUNTANT":
            if user.area_id and budget.area_id == user.area_id:
                return
            if user.region_id and budget.region_id == user.region_id:
                return
            raise _FORBIDDEN(self.DETAIL)

        if code == "WORK_MANAGER":
            if not budget.project_id:
                raise _FORBIDDEN(self.DETAIL)
            from app.models.project_assignment import ProjectAssignment
            assigned = (
                db.query(ProjectAssignment)
                .filter(
                    ProjectAssignment.user_id == user.id,
                    ProjectAssignment.project_id == budget.project_id,
                    ProjectAssignment.is_active == True,
                )
                .first()
            )
            if not assigned:
                raise _FORBIDDEN(self.DETAIL)
            return

        raise _FORBIDDEN(self.DETAIL)

    def filter(self, db: Session, user: User, query):
        """Narrow a Budget query to the user's scope.

        WORK_MANAGER's filter requires a JOIN against project_assignments;
        we stay defensive and return an empty query if the user has no
        usable scope at all.
        """
        from app.models import Budget

        if _is_global(user):
            return query

        code = (user.role.code if user.role else "").upper()

        if code == "REGION_MANAGER" and user.region_id:
            return query.filter(Budget.region_id == user.region_id)

        if code == "AREA_MANAGER" and user.area_id:
            return query.filter(Budget.area_id == user.area_id)

        if code == "ACCOUNTANT":
            from sqlalchemy import or_
            clauses = []
            if user.area_id:
                clauses.append(Budget.area_id == user.area_id)
            if user.region_id:
                clauses.append(Budget.region_id == user.region_id)
            if not clauses:
                return query.filter(False)
            return query.filter(or_(*clauses))

        if code == "WORK_MANAGER":
            from app.models.project_assignment import ProjectAssignment
            assigned_project_ids = (
                db.query(ProjectAssignment.project_id)
                .filter(
                    ProjectAssignment.user_id == user.id,
                    ProjectAssignment.is_active == True,
                )
                .subquery()
            )
            return query.filter(Budget.project_id.in_(assigned_project_ids))

        # Defensive: unknown role with no scope sees nothing.
        return query.filter(False)


class WorkOrderScopeStrategy:
    """WorkOrder scope (Phase 3 Wave 1.2).

    The recon (PHASE3_WAVE12_FRONTEND_RECON.md) found two issues in the
    legacy code:
      1. list filtered by current_user.area_id for ANY role with an
         area_id — including admin.
      2. detail used a different scope rule (5-role allowlist), so the
         same WO would appear in the list but not the detail (or vice
         versa) for the same user — an information-leak path via direct
         URL access on `/work-orders/{id}`.

    This strategy unifies the two paths under one matrix verified
    against the live DB:
      ADMIN / SUPER_ADMIN  → all
      ORDER_COORDINATOR    → all (queue role, must see everything)
      ACCOUNTANT           → all, read-only by perm convention
      REGION_MANAGER       → wo.project.region_id == user.region_id
      AREA_MANAGER         → wo.project.area_id   == user.area_id
      WORK_MANAGER         → wo.project_id ∈ user's active project_assignments
      SUPPLIER             → 403 (suppliers go through /supplier-portal,
                              never call /work-orders directly)
      anything else        → 403
    """

    DETAIL = "אין הרשאה להזמנת עבודה זו"

    GLOBAL_ROLES = ("ADMIN", "SUPER_ADMIN", "ORDER_COORDINATOR", "ACCOUNTANT")

    def _project_for(self, db: Session, work_order):
        """Resolve the WO's project (for region/area scope). Returns None
        if the WO has no project — that's a data anomaly; non-global
        roles get 403 in that case."""
        from app.models import Project
        if not work_order.project_id:
            return None
        return db.query(Project).filter(Project.id == work_order.project_id).first()

    def check(self, db: Session, user: User, work_order) -> None:
        code = (user.role.code if user.role else "").upper()

        if code in self.GLOBAL_ROLES:
            return

        if code == "REGION_MANAGER":
            project = self._project_for(db, work_order)
            if not user.region_id or not project or project.region_id != user.region_id:
                raise _FORBIDDEN(self.DETAIL)
            return

        if code == "AREA_MANAGER":
            project = self._project_for(db, work_order)
            if not user.area_id or not project or project.area_id != user.area_id:
                raise _FORBIDDEN(self.DETAIL)
            return

        if code == "WORK_MANAGER":
            from app.models.project_assignment import ProjectAssignment
            if not work_order.project_id:
                raise _FORBIDDEN(self.DETAIL)
            assigned = (
                db.query(ProjectAssignment)
                .filter(
                    ProjectAssignment.user_id == user.id,
                    ProjectAssignment.project_id == work_order.project_id,
                    ProjectAssignment.is_active == True,
                )
                .first()
            )
            if not assigned:
                raise _FORBIDDEN(self.DETAIL)
            return

        # SUPPLIER + anything not listed → blocked. Suppliers belong on
        # the /supplier-portal/{token} path; if one shows up here, deny.
        raise _FORBIDDEN(self.DETAIL)

    def filter(self, db: Session, user: User, query):
        from app.models import WorkOrder, Project
        from app.models.project_assignment import ProjectAssignment

        code = (user.role.code if user.role else "").upper()

        if code in self.GLOBAL_ROLES:
            return query

        if code == "REGION_MANAGER" and user.region_id:
            return query.join(Project, Project.id == WorkOrder.project_id) \
                        .filter(Project.region_id == user.region_id)

        if code == "AREA_MANAGER" and user.area_id:
            return query.join(Project, Project.id == WorkOrder.project_id) \
                        .filter(Project.area_id == user.area_id)

        if code == "WORK_MANAGER":
            assigned_subq = (
                db.query(ProjectAssignment.project_id)
                .filter(
                    ProjectAssignment.user_id == user.id,
                    ProjectAssignment.is_active == True,
                )
                .subquery()
            )
            return query.filter(WorkOrder.project_id.in_(assigned_subq))

        # SUPPLIER and unknown roles see nothing.
        return query.filter(False)


class NotificationScopeStrategy:
    """Notifications are pure-ownership (Phase 3 Wave 3.1.4).

    Unlike WorkOrders or Budgets, notifications carry no region/area/
    project — they're delivered to a single user_id and that's the
    whole story. The strategy mirrors the legacy
    `_check_notification_ownership` helper exactly:

      ADMIN / SUPER_ADMIN  → bypass (used by support flows where a
                              coordinator helps a field worker mark
                              their own notifications)
      everyone else        → notification.user_id == user.id, else 403

    `check()` doesn't need a db handle but accepts one for the
    uniform Strategy contract. `filter()` narrows a list query to
    "my notifications" — used as a building block for any future
    `/notifications` listing that wants to consume the strategy.
    """

    DETAIL = "התראה לא שייכת למשתמש"

    def check(self, db: Session, user: User, notification) -> None:
        code = (user.role.code if user.role else "").upper()
        if code in ("ADMIN", "SUPER_ADMIN"):
            return
        if notification.user_id != user.id:
            raise _FORBIDDEN(self.DETAIL)

    def filter(self, db: Session, user: User, query):
        from app.models.notification import Notification
        code = (user.role.code if user.role else "").upper()
        if code in ("ADMIN", "SUPER_ADMIN"):
            # Admin's "/my" is still their own — but a future admin
            # cross-user listing endpoint can opt out by not calling
            # filter_query. Default to own-only here.
            return query.filter(Notification.user_id == user.id)
        return query.filter(Notification.user_id == user.id)


class ProjectScopeStrategy:
    """Project-level scope (Phase 3 Wave 1.3.e).

    Used by endpoints that act *on* a child of a project but where
    the entity doesn't exist yet — e.g. POST /work-orders, where we
    need to scope by `payload.project_id` before the WorkOrder row
    exists, so WorkOrderScopeStrategy's `wo.project` dereference
    doesn't apply.

    Mirrors WorkOrderScopeStrategy.GLOBAL_ROLES exactly to keep the
    matrix consistent: a user who can list a project's WOs in the
    UI can also create one in that project (subject to RBAC perm —
    e.g. ACCOUNTANT lacks `work_orders.create` so RBAC blocks even
    though they're in GLOBAL_ROLES here).

    Roles:
      ADMIN / SUPER_ADMIN / ORDER_COORDINATOR / ACCOUNTANT → all
      REGION_MANAGER → project.region_id == user.region_id
      AREA_MANAGER   → project.area_id   == user.area_id
      WORK_MANAGER   → project.id ∈ user's active project_assignments
      SUPPLIER / FIELD_WORKER / anything else → 403
    """

    DETAIL = "אין הרשאה לפרויקט זה"

    GLOBAL_ROLES = ("ADMIN", "SUPER_ADMIN", "ORDER_COORDINATOR", "ACCOUNTANT")

    def check(self, db: Session, user: User, project) -> None:
        code = (user.role.code if user.role else "").upper()

        if code in self.GLOBAL_ROLES:
            return

        if code == "REGION_MANAGER":
            if not user.region_id or project.region_id != user.region_id:
                raise _FORBIDDEN(self.DETAIL)
            return

        if code == "AREA_MANAGER":
            if not user.area_id or project.area_id != user.area_id:
                raise _FORBIDDEN(self.DETAIL)
            return

        if code == "WORK_MANAGER":
            from app.models.project_assignment import ProjectAssignment
            assigned = (
                db.query(ProjectAssignment)
                .filter(
                    ProjectAssignment.user_id == user.id,
                    ProjectAssignment.project_id == project.id,
                    ProjectAssignment.is_active == True,
                )
                .first()
            )
            if not assigned:
                raise _FORBIDDEN(self.DETAIL)
            return

        # SUPPLIER, FIELD_WORKER, anything else → blocked.
        raise _FORBIDDEN(self.DETAIL)

    def filter(self, db: Session, user: User, query):
        """Not used in Wave 1.3.e — left as a no-op so future "list
        projects I can act on" use cases can wire in without changing
        the strategy contract."""
        return query


# ---------------------------------------------------------------------------
# Strategy registry — Wave 1 ships only Budget. The rest are placeholders
# so a future wave adds the class then maps its name here, and the rest
# of the codebase doesn't need to change.
# ---------------------------------------------------------------------------

STRATEGIES: dict[str, Any] = {
    "Budget": BudgetScopeStrategy(),
    "WorkOrder": WorkOrderScopeStrategy(),                   # Wave 3.1.2
    "Project": ProjectScopeStrategy(),                       # Wave 3.1.3.e
    "Notification": NotificationScopeStrategy(),             # Wave 3.1.4
    # "SupplierRotation":  SupplierRotationScopeStrategy(),  # Wave 3.1.3
    # "Worklog":           WorklogScopeStrategy(),           # Wave 3.1.5
    # "Invoice":           InvoiceScopeStrategy(),           # Wave 3.1.6
    # "SupportTicket":     SupportTicketScopeStrategy(),     # Wave 3.1.7
}
