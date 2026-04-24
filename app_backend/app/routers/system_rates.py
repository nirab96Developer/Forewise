"""
System Rates router - תעריפים גלובליים
"""

from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.system_rate import SystemRate
from app.schemas.system_rate import (
    SystemRateCreate,
    SystemRateUpdate
)

router = APIRouter(prefix="/system-rates", tags=["System Rates"])


@router.get("/", )
async def get_system_rates(
    active_only: bool = Query(True, description="רק פעילים"),
    valid_for_date: Optional[date] = Query(None, description="בתוקף לתאריך"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """
    קבלת רשימת תעריפים גלובליים
    """
    query = db.query(SystemRate)
    
    if active_only:
        query = query.filter(SystemRate.is_active == True)
    
    rates = query.all()
    
    # Filter by date validity if specified
    if valid_for_date:
        rates = [r for r in rates if r.is_valid_for_date(valid_for_date)]
    
    return rates


@router.get("/by-code/{code}", )
async def get_system_rate_by_code(
    code: str,
    valid_for_date: Optional[date] = Query(None, description="בתוקף לתאריך"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """
    קבלת תעריף גלובלי לפי קוד
    """
    rate = db.query(SystemRate).filter(
        SystemRate.code == code.upper(),
        SystemRate.is_active == True
    ).first()
    
    if not rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"תעריף עם קוד '{code}' לא נמצא"
        )
    
    if valid_for_date and not rate.is_valid_for_date(valid_for_date):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"תעריף '{code}' לא בתוקף לתאריך {valid_for_date}"
        )
    
    return rate


@router.get("/{rate_id}", )
async def get_system_rate(
    rate_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """
    קבלת תעריף גלובלי לפי ID
    """
    rate = db.query(SystemRate).filter(SystemRate.id == rate_id).first()
    if not rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="תעריף לא נמצא"
        )
    return rate


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_system_rate(
    data: SystemRateCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """
    יצירת תעריף גלובלי חדש (מנהל בלבד).

    Wave 7.B — locked behind `system.settings` (case-insensitive
    matches the existing `SYSTEM.SETTINGS` perm in the DB which is
    assigned to ADMIN only). Without this, any authenticated user could
    create/override system-wide hourly rates that affect every new
    worklog cost calculation.
    """
    require_permission(current_user, "system.settings")
    # Check if code already exists
    existing = db.query(SystemRate).filter(SystemRate.code == data.code.upper()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"תעריף עם קוד '{data.code}' כבר קיים"
        )
    
    rate_data = data.model_dump()
    rate_data['code'] = rate_data['code'].upper()
    
    rate = SystemRate(**rate_data)
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return rate


@router.patch("/{rate_id}", )
async def update_system_rate(
    rate_id: int,
    data: SystemRateUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """
    עדכון תעריף גלובלי (מנהל בלבד).

    Wave 7.B — locked behind `system.settings` (ADMIN only).
    """
    require_permission(current_user, "system.settings")
    rate = db.query(SystemRate).filter(SystemRate.id == rate_id).first()
    if not rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="תעריף לא נמצא"
        )
    
    update_data = data.model_dump(exclude_unset=True)
    if 'code' in update_data:
        update_data['code'] = update_data['code'].upper()
    
    for key, value in update_data.items():
        setattr(rate, key, value)
    
    db.commit()
    db.refresh(rate)
    return rate


@router.delete("/{rate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_system_rate(
    rate_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """
    מחיקת תעריף (soft delete).

    Wave 7.B — locked behind `system.settings` (ADMIN only).
    """
    require_permission(current_user, "system.settings")
    rate = db.query(SystemRate).filter(SystemRate.id == rate_id).first()
    if not rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="תעריף לא נמצא"
        )
    
    rate.is_active = False
    db.commit()

