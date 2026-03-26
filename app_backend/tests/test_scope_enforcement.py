"""
Tests for scope enforcement (app/core/scope.py).
"""
import pytest
from unittest.mock import MagicMock
from app.core.scope import (
    block_self_approval,
    enforce_scope_for_project,
    enforce_scope_for_entity,
)
from app.core.exceptions import ForbiddenException


def _mock_user(role_code="WORK_MANAGER", user_id=10, area_id=1, region_id=1):
    user = MagicMock()
    user.id = user_id
    user.area_id = area_id
    user.region_id = region_id
    user.role = MagicMock()
    user.role.code = role_code
    return user


def _mock_project(area_id=1, region_id=1):
    proj = MagicMock()
    proj.area_id = area_id
    proj.region_id = region_id
    return proj


def _mock_entity(created_by_id=None, user_id=None, project_id=None, project=None):
    ent = MagicMock()
    ent.created_by_id = created_by_id
    ent.user_id = user_id
    ent.project_id = project_id
    ent.project = project
    return ent


class TestSelfApproval:

    def test_blocks_creator(self):
        user = _mock_user(user_id=5)
        entity = _mock_entity(created_by_id=5)
        with pytest.raises(ForbiddenException):
            block_self_approval(user, entity)

    def test_blocks_user_id(self):
        user = _mock_user(user_id=5)
        entity = _mock_entity(user_id=5)
        with pytest.raises(ForbiddenException):
            block_self_approval(user, entity)

    def test_allows_different_user(self):
        user = _mock_user(user_id=5)
        entity = _mock_entity(created_by_id=99, user_id=88)
        block_self_approval(user, entity)

    def test_allows_no_creator(self):
        user = _mock_user(user_id=5)
        entity = _mock_entity(created_by_id=None, user_id=None)
        block_self_approval(user, entity)


class TestProjectScope:

    def test_admin_always_allowed(self):
        user = _mock_user("ADMIN", area_id=1)
        proj = _mock_project(area_id=999)
        enforce_scope_for_project(user, proj)

    def test_region_manager_same_region(self):
        user = _mock_user("REGION_MANAGER", region_id=1)
        proj = _mock_project(region_id=1)
        enforce_scope_for_project(user, proj)

    def test_region_manager_different_region_blocked(self):
        user = _mock_user("REGION_MANAGER", region_id=1)
        proj = _mock_project(region_id=2)
        with pytest.raises(ForbiddenException):
            enforce_scope_for_project(user, proj)

    def test_area_manager_same_area(self):
        user = _mock_user("AREA_MANAGER", area_id=3)
        proj = _mock_project(area_id=3)
        enforce_scope_for_project(user, proj)

    def test_area_manager_different_area_blocked(self):
        user = _mock_user("AREA_MANAGER", area_id=3)
        proj = _mock_project(area_id=5)
        with pytest.raises(ForbiddenException):
            enforce_scope_for_project(user, proj)

    def test_work_manager_same_area(self):
        user = _mock_user("WORK_MANAGER", area_id=2)
        proj = _mock_project(area_id=2)
        enforce_scope_for_project(user, proj)

    def test_work_manager_different_area_blocked(self):
        user = _mock_user("WORK_MANAGER", area_id=2)
        proj = _mock_project(area_id=7)
        with pytest.raises(ForbiddenException):
            enforce_scope_for_project(user, proj)

    def test_accountant_same_area(self):
        user = _mock_user("ACCOUNTANT", area_id=4)
        proj = _mock_project(area_id=4)
        enforce_scope_for_project(user, proj)

    def test_accountant_different_area_blocked(self):
        user = _mock_user("ACCOUNTANT", area_id=4)
        proj = _mock_project(area_id=6)
        with pytest.raises(ForbiddenException):
            enforce_scope_for_project(user, proj)


class TestEntityScope:

    def test_entity_with_project(self):
        proj = _mock_project(area_id=3)
        entity = _mock_entity(project=proj, project_id=1)
        user = _mock_user("AREA_MANAGER", area_id=3)
        enforce_scope_for_entity(user, entity)

    def test_entity_wrong_area_blocked(self):
        proj = _mock_project(area_id=3)
        entity = _mock_entity(project=proj, project_id=1)
        user = _mock_user("AREA_MANAGER", area_id=99)
        with pytest.raises(ForbiddenException):
            enforce_scope_for_entity(user, entity)

    def test_entity_no_project_id_passes(self):
        entity = _mock_entity(project_id=None)
        user = _mock_user("AREA_MANAGER", area_id=99)
        enforce_scope_for_entity(user, entity)
