"""AuthorizationService — Phase 3 Wave 1.

One callable instead of `require_permission(...) + _check_X_scope(...)`
scattered through every router. Layered so each call only runs what it
needs:

  authorize(user, action, resource=None, context=None)
    1. RBAC   — require_permission(user, action) when `action` is set
    2. ABAC   — when `resource` is set AND its class is registered in
                STRATEGIES, run the per-resource scope check
    3. State  — when context.allowed_statuses is provided, verify the
                resource's status is allowed

  filter_query(user, query, resource_type, context=None)
    Applies the per-resource scope filter (region/area/project/etc.)
    to a list query. Replaces inline `if role == ...` blocks.

Wave 1 only registers Budget. Other resources fall through to "no
scope check" so existing routers stay untouched until their own wave.
"""
from __future__ import annotations

from typing import Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_permission
from app.core.authorization.scope_strategies import STRATEGIES
from app.models.user import User


class AuthorizationService:

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def authorize(
        self,
        user: User,
        action: Optional[str] = None,
        resource: Optional[Any] = None,
        resource_type: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> None:
        """Run RBAC + ABAC + state guards in order. Raise on first deny.

        - action ("budgets.read"): if set, runs require_permission.
        - resource: if set, the row to check.
        - resource_type: explicit override of the strategy lookup key.
          Defaults to type(resource).__name__. Tests pass mocked
          objects whose .__name__ is "MagicMock"; they should pass
          resource_type="Budget" explicitly.
        - context.allowed_statuses (list[str]): if set, verifies
          resource.status is in the list.
        """
        if action:
            require_permission(user, action)

        if resource is not None:
            key = resource_type or type(resource).__name__
            strategy = STRATEGIES.get(key)
            if strategy is not None:
                strategy.check(self.db, user, resource)

        if context and "allowed_statuses" in context:
            allowed = context["allowed_statuses"]
            current = getattr(resource, "status", None) if resource is not None else None
            if current not in allowed:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"פעולה לא מותרת בסטטוס '{current}'",
                )

    def filter_query(
        self,
        user: User,
        query,
        resource_type: str,
        context: Optional[dict] = None,
    ):
        """Narrow a list query by the user's scope for `resource_type`.
        If no strategy is registered for `resource_type`, returns the
        query unchanged (callers above the registered set continue to
        use their existing filters)."""
        strategy = STRATEGIES.get(resource_type)
        if strategy is None:
            return query
        return strategy.filter(self.db, user, query)


# ---------------------------------------------------------------------------
# FastAPI dependency helper.
# ---------------------------------------------------------------------------

def get_authorization_service(db: Session) -> AuthorizationService:
    """Build an AuthorizationService bound to the request's DB session.
    Callers usually do `Depends(get_authorization_service)` after
    `Depends(get_db)`."""
    return AuthorizationService(db)
