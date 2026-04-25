"""
Tests for permission + scope enforcement on /api/v1/supplier-rotations.

Phase 2 Wave 7.D — six endpoints, each gated by a different permission
from Wave 7.A's seed migration plus a per-row scope check that keeps
REGION_MANAGER / AREA_MANAGER away from rotations outside their own
region/area:

  GET    /supplier-rotations         supplier_rotations.list   + scope filter
  GET    /supplier-rotations/{id}    supplier_rotations.read   + scope check
  POST   /supplier-rotations         supplier_rotations.create
  PUT    /supplier-rotations/{id}    supplier_rotations.update + scope check
  PATCH  /supplier-rotations/{id}    supplier_rotations.update + scope check
                                      (delegates to PUT handler)
  DELETE /supplier-rotations/{id}    supplier_rotations.delete

Role expectations:
  ADMIN              -> everything, no scope
  ORDER_COORDINATOR  -> list/read/create/update, no scope
  REGION_MANAGER     -> list/read only, scoped to user.region_id
  AREA_MANAGER       -> list/read only, scoped to user.area_id
  WORK_MANAGER, ACCOUNTANT, SUPPLIER, anything else -> 403
"""
import asyncio
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.routers.supplier_rotations import (
    SupplierRotationCreate,
    SupplierRotationUpdate,
    _check_rotation_scope,
    create_supplier_rotation,
    delete_supplier_rotation,
    get_supplier_rotation,
    update_supplier_rotation,
)


# ---------------------------------------------------------------------------
# User factory
# ---------------------------------------------------------------------------

ROLE_PERMS = {
    "ADMIN": set(),  # ADMIN bypass
    "ORDER_COORDINATOR": {
        "supplier_rotations.list",
        "supplier_rotations.read",
        "supplier_rotations.create",
        "supplier_rotations.update",
    },
    "REGION_MANAGER": {
        "supplier_rotations.list",
        "supplier_rotations.read",
    },
    "AREA_MANAGER": {
        "supplier_rotations.list",
        "supplier_rotations.read",
    },
    "WORK_MANAGER": set(),
    "ACCOUNTANT": set(),
    "SUPPLIER": set(),
}


def _user(
    role_code: str,
    *,
    region_id: int | None = None,
    area_id: int | None = None,
    user_id: int = 1,
):
    user = MagicMock()
    user.id = user_id
    user.role_id = 1
    user.is_active = True
    user.region_id = region_id
    user.area_id = area_id
    user.role = MagicMock()
    user.role.code = role_code
    perms = ROLE_PERMS.get(role_code, set())
    user.role.permissions = [MagicMock(code=p) for p in perms]
    user._permissions = set(perms)
    return user


# ---------------------------------------------------------------------------
# Rotation + DB stub
# ---------------------------------------------------------------------------

def _rotation(rotation_id: int = 1, region_id: int | None = None,
              area_id: int | None = None, supplier_id: int = 100):
    rot = MagicMock()
    rot.id = rotation_id
    rot.supplier_id = supplier_id
    rot.region_id = region_id
    rot.area_id = area_id
    rot.equipment_type_id = 5
    rot.equipment_category_id = None
    rot.rotation_position = 1
    rot.total_assignments = 0
    rot.successful_completions = 0
    rot.rejection_count = 0
    rot.priority_score = 100
    rot.is_active = True
    rot.is_available = True
    rot.last_assignment_date = None
    rot.last_completion_date = None
    rot.unavailable_until = None
    rot.unavailable_reason = None
    return rot


class _DBStub:
    """Returns the seeded rotation for SupplierRotation queries; supplier
    queries return a stub; equipment_types / areas / regions raw SQL
    returns empty rows."""

    def __init__(self, rotation=None, supplier_exists=True):
        self._rotation = rotation
        self._supplier = MagicMock(id=100, name="Test Supplier") if supplier_exists else None

    def query(self, model):
        self._current = getattr(model, "__name__", str(model))
        return self

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def offset(self, *args):
        return self

    def limit(self, *args):
        return self

    def first(self):
        if self._current == "SupplierRotation":
            return self._rotation
        if self._current == "Supplier":
            return self._supplier
        return None

    def all(self):
        if self._current == "SupplierRotation":
            return [self._rotation] if self._rotation else []
        if self._current == "Supplier":
            return [self._supplier] if self._supplier else []
        return []

    def count(self):
        return 1 if self._rotation else 0

    def add(self, obj):
        pass

    def commit(self):
        pass

    def refresh(self, obj):
        pass

    def delete(self, obj):
        pass

    def rollback(self):
        pass

    def execute(self, *args, **kwargs):
        cursor = MagicMock()
        cursor.fetchall.return_value = []
        cursor.fetchone.return_value = (1,)  # equipment_type_id existence
        return cursor


# ===========================================================================
# _check_rotation_scope unit tests
# ===========================================================================

class TestCheckRotationScope:

    def test_admin_global_access(self):
        _check_rotation_scope(_user("ADMIN"), _rotation(region_id=99, area_id=99))

    def test_coordinator_global_access(self):
        _check_rotation_scope(_user("ORDER_COORDINATOR"),
                              _rotation(region_id=99, area_id=99))

    def test_region_manager_in_scope(self):
        u = _user("REGION_MANAGER", region_id=5)
        _check_rotation_scope(u, _rotation(region_id=5))

    def test_region_manager_out_of_scope_403(self):
        u = _user("REGION_MANAGER", region_id=5)
        with pytest.raises(HTTPException) as exc:
            _check_rotation_scope(u, _rotation(region_id=99))
        assert exc.value.status_code == 403

    def test_region_manager_null_rotation_region_403(self):
        """NULL region rotations are global config — hide from non-globals."""
        u = _user("REGION_MANAGER", region_id=5)
        with pytest.raises(HTTPException) as exc:
            _check_rotation_scope(u, _rotation(region_id=None))
        assert exc.value.status_code == 403

    def test_area_manager_in_scope(self):
        u = _user("AREA_MANAGER", area_id=10)
        _check_rotation_scope(u, _rotation(area_id=10))

    def test_area_manager_out_of_scope_403(self):
        u = _user("AREA_MANAGER", area_id=10)
        with pytest.raises(HTTPException) as exc:
            _check_rotation_scope(u, _rotation(area_id=99))
        assert exc.value.status_code == 403

    def test_unknown_role_403(self):
        with pytest.raises(HTTPException) as exc:
            _check_rotation_scope(_user("WORK_MANAGER"), _rotation())
        assert exc.value.status_code == 403


# ===========================================================================
# GET /{id}  — read
# ===========================================================================

class TestGetSingleRotation:

    def test_admin_passes(self):
        result = asyncio.run(get_supplier_rotation(
            rotation_id=1,
            db=_DBStub(rotation=_rotation(region_id=5)),
            current_user=_user("ADMIN"),
        ))
        assert result["id"] == 1

    def test_coordinator_passes(self):
        result = asyncio.run(get_supplier_rotation(
            rotation_id=1,
            db=_DBStub(rotation=_rotation(region_id=5)),
            current_user=_user("ORDER_COORDINATOR"),
        ))
        assert result["id"] == 1

    def test_region_manager_in_scope_passes(self):
        u = _user("REGION_MANAGER", region_id=5)
        result = asyncio.run(get_supplier_rotation(
            rotation_id=1,
            db=_DBStub(rotation=_rotation(region_id=5)),
            current_user=u,
        ))
        assert result["id"] == 1

    def test_region_manager_cross_region_403(self):
        u = _user("REGION_MANAGER", region_id=5)
        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_supplier_rotation(
                rotation_id=1,
                db=_DBStub(rotation=_rotation(region_id=99)),
                current_user=u,
            ))
        assert exc.value.status_code == 403

    def test_supplier_blocked_by_permission_403(self):
        u = _user("SUPPLIER")
        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_supplier_rotation(
                rotation_id=1,
                db=_DBStub(rotation=_rotation()),
                current_user=u,
            ))
        assert exc.value.status_code == 403

    def test_work_manager_blocked_by_permission_403(self):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_supplier_rotation(
                rotation_id=1,
                db=_DBStub(rotation=_rotation()),
                current_user=_user("WORK_MANAGER"),
            ))
        assert exc.value.status_code == 403


# ===========================================================================
# POST  — create
# ===========================================================================

def _create_payload():
    """Cleanup #2 — equipment_category_id removed from the schema.
    Passing it would now raise a Pydantic ValidationError, which
    is a separate test below."""
    return SupplierRotationCreate(
        supplier_id=100,
        equipment_type_id=5,
        region_id=5,
        area_id=10,
    )


class TestCreateRotation:

    def test_admin_passes(self):
        """Cleanup #2 — equipment_category_id no longer passed to the
        model. Admin now succeeds end-to-end instead of getting a
        TypeError after the perm gate."""
        result = asyncio.run(create_supplier_rotation(
            data=_create_payload(),
            db=_DBStub(),
            current_user=_user("ADMIN"),
        ))
        assert result is not None

    def test_coordinator_passes(self):
        result = asyncio.run(create_supplier_rotation(
            data=_create_payload(),
            db=_DBStub(),
            current_user=_user("ORDER_COORDINATOR"),
        ))
        assert result is not None

    def test_payload_with_equipment_category_id_silently_dropped(self):
        """Cleanup #2 — back-compat boundary. Pydantic v2 default is to
        ignore extra fields, so an old caller that still sends
        equipment_category_id is accepted but the field is dropped
        BEFORE the handler ever sees it. No more TypeError when the
        handler builds the SupplierRotation row."""
        s = SupplierRotationCreate(
            supplier_id=100,
            equipment_type_id=5,
            equipment_category_id=99,  # ignored by Pydantic
            region_id=5,
            area_id=10,
        )
        dump = s.model_dump()
        assert "equipment_category_id" not in dump, (
            "equipment_category_id must not survive into the model dump"
        )

    def test_region_manager_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(create_supplier_rotation(
                data=_create_payload(),
                db=_DBStub(),
                current_user=_user("REGION_MANAGER", region_id=5),
            ))
        assert exc.value.status_code == 403

    def test_area_manager_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(create_supplier_rotation(
                data=_create_payload(),
                db=_DBStub(),
                current_user=_user("AREA_MANAGER", area_id=10),
            ))
        assert exc.value.status_code == 403

    def test_supplier_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(create_supplier_rotation(
                data=_create_payload(),
                db=_DBStub(),
                current_user=_user("SUPPLIER"),
            ))
        assert exc.value.status_code == 403


# ===========================================================================
# PUT — update
# ===========================================================================

class TestUpdateRotation:

    def test_admin_passes(self):
        result = asyncio.run(update_supplier_rotation(
            rotation_id=1,
            data=SupplierRotationUpdate(priority_score=50),
            db=_DBStub(rotation=_rotation()),
            current_user=_user("ADMIN"),
        ))
        assert "message" in result

    def test_coordinator_passes(self):
        result = asyncio.run(update_supplier_rotation(
            rotation_id=1,
            data=SupplierRotationUpdate(priority_score=50),
            db=_DBStub(rotation=_rotation()),
            current_user=_user("ORDER_COORDINATOR"),
        ))
        assert "message" in result

    def test_region_manager_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(update_supplier_rotation(
                rotation_id=1,
                data=SupplierRotationUpdate(priority_score=50),
                db=_DBStub(rotation=_rotation(region_id=5)),
                current_user=_user("REGION_MANAGER", region_id=5),
            ))
        assert exc.value.status_code == 403

    def test_supplier_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(update_supplier_rotation(
                rotation_id=1,
                data=SupplierRotationUpdate(priority_score=50),
                db=_DBStub(rotation=_rotation()),
                current_user=_user("SUPPLIER"),
            ))
        assert exc.value.status_code == 403


# ===========================================================================
# DELETE
# ===========================================================================

class TestDeleteRotation:

    def test_admin_passes(self):
        result = asyncio.run(delete_supplier_rotation(
            rotation_id=1,
            db=_DBStub(rotation=_rotation()),
            current_user=_user("ADMIN"),
        ))
        assert "message" in result

    def test_coordinator_blocked_403(self):
        """ORDER_COORDINATOR has list/read/create/update but NOT delete."""
        with pytest.raises(HTTPException) as exc:
            asyncio.run(delete_supplier_rotation(
                rotation_id=1,
                db=_DBStub(rotation=_rotation()),
                current_user=_user("ORDER_COORDINATOR"),
            ))
        assert exc.value.status_code == 403

    def test_region_manager_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(delete_supplier_rotation(
                rotation_id=1,
                db=_DBStub(rotation=_rotation(region_id=5)),
                current_user=_user("REGION_MANAGER", region_id=5),
            ))
        assert exc.value.status_code == 403

    def test_supplier_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(delete_supplier_rotation(
                rotation_id=1,
                db=_DBStub(rotation=_rotation()),
                current_user=_user("SUPPLIER"),
            ))
        assert exc.value.status_code == 403
