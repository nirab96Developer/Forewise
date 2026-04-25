"""Centralized authorization (Phase 3 Wave 1).

Single entry point that combines RBAC (require_permission), ABAC scope
(region/area/project/ownership) and state guards (status rules) into
one consistent surface area.

Phase 3 Wave 1 scope: budgets domain only. Other domains continue to
use their existing _check_*_scope helpers until later sub-waves.
"""
from app.core.authorization.service import AuthorizationService

__all__ = ["AuthorizationService"]
