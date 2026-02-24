# app/routers/activity_types.py
# API endpoints לסוגי פעולות

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.activity_type import ActivityType

router = APIRouter(prefix="/activity-types", tags=["Activity Types"])


# Schemas
class ActivityTypeResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: bool = True
    sort_order: Optional[int] = 0
    
    class Config:
        from_attributes = True


class ActivityTypeCreate(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=50)
    is_active: bool = True
    sort_order: Optional[int] = 0


# Endpoints
@router.get("", response_model=List[ActivityTypeResponse])
def get_activity_types(
    active_only: bool = True,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """קבלת רשימת סוגי פעולות"""
    query = db.query(ActivityType)
    
    if active_only:
        query = query.filter(ActivityType.is_active == True)
    
    if category:
        query = query.filter(ActivityType.category == category)
    
    return query.order_by(ActivityType.sort_order, ActivityType.name).all()


@router.get("/{activity_type_id}", response_model=ActivityTypeResponse)
def get_activity_type(
    activity_type_id: int,
    db: Session = Depends(get_db)
):
    """קבלת סוג פעולה לפי ID"""
    activity_type = db.query(ActivityType).filter(ActivityType.id == activity_type_id).first()
    if not activity_type:
        raise HTTPException(status_code=404, detail="סוג פעולה לא נמצא")
    return activity_type


@router.post("", response_model=ActivityTypeResponse, status_code=status.HTTP_201_CREATED)
def create_activity_type(
    data: ActivityTypeCreate,
    db: Session = Depends(get_db)
):
    """יצירת סוג פעולה חדש"""
    # Check if code exists
    existing = db.query(ActivityType).filter(ActivityType.code == data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="קוד סוג פעולה כבר קיים")
    
    activity_type = ActivityType(**data.model_dump())
    db.add(activity_type)
    db.commit()
    db.refresh(activity_type)
    return activity_type


@router.put("/{activity_type_id}", response_model=ActivityTypeResponse)
def update_activity_type(
    activity_type_id: int,
    data: ActivityTypeCreate,
    db: Session = Depends(get_db)
):
    """עדכון סוג פעולה"""
    activity_type = db.query(ActivityType).filter(ActivityType.id == activity_type_id).first()
    if not activity_type:
        raise HTTPException(status_code=404, detail="סוג פעולה לא נמצא")
    
    for key, value in data.model_dump().items():
        setattr(activity_type, key, value)
    
    db.commit()
    db.refresh(activity_type)
    return activity_type


@router.delete("/{activity_type_id}")
def delete_activity_type(
    activity_type_id: int,
    db: Session = Depends(get_db)
):
    """מחיקת סוג פעולה (soft delete)"""
    activity_type = db.query(ActivityType).filter(ActivityType.id == activity_type_id).first()
    if not activity_type:
        raise HTTPException(status_code=404, detail="סוג פעולה לא נמצא")
    
    activity_type.is_active = False
    db.commit()
    return {"message": "סוג פעולה בוטל בהצלחה"}
