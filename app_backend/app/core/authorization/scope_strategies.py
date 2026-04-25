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


# ---------------------------------------------------------------------------
# Strategy registry — Wave 1 ships only Budget. The rest are placeholders
# so a future wave adds the class then maps its name here, and the rest
# of the codebase doesn't need to change.
# ---------------------------------------------------------------------------

STRATEGIES: dict[str, Any] = {
    "Budget": BudgetScopeStrategy(),
    # "WorkOrder":         WorkOrderScopeStrategy(),         # Wave 3.1.2
    # "SupplierRotation":  SupplierRotationScopeStrategy(),  # Wave 3.1.3
    # "Notification":      NotificationScopeStrategy(),      # Wave 3.1.4
    # "Worklog":           WorklogScopeStrategy(),           # Wave 3.1.5
    # "Invoice":           InvoiceScopeStrategy(),           # Wave 3.1.6
    # "SupportTicket":     SupportTicketScopeStrategy(),     # Wave 3.1.7
}
