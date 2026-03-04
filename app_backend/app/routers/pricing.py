"""
Pricing router - חישוב תעריפים ודוחות
API for computing work pricing and reports
"""

from datetime import date
from decimal import Decimal
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.services.rate_service import RateService, get_rate_service
from app.models.worklog import Worklog
from app.models.project import Project
from app.models.supplier import Supplier
from app.models.equipment_type import EquipmentType


router = APIRouter(prefix="/pricing", tags=["Pricing"])


class ComputeCostRequest(BaseModel):
    """בקשה לחישוב עלות"""
    work_type: str = Field(..., description="סוג עבודה (fieldwork/storage/general)")
    hours: Decimal = Field(..., ge=0, description="מספר שעות")
    equipment_id: Optional[int] = Field(None, description="מזהה כלי")
    equipment_type_id: Optional[int] = Field(None, description="מזהה סוג כלי")
    supplier_id: Optional[int] = Field(None, description="מזהה ספק")
    project_id: Optional[int] = Field(None, description="מזהה פרויקט")
    for_date: Optional[date] = Field(None, description="תאריך לחישוב")


class ComputeCostResponse(BaseModel):
    """תשובת חישוב עלות"""
    hours: float
    hourly_rate: float
    daily_rate: Optional[float]
    total_cost: float
    total_cost_with_vat: float
    rate_source: str
    rate_source_id: Optional[int]
    rate_source_name: Optional[str]


@router.post("/compute-cost", response_model=ComputeCostResponse)
async def compute_cost(
    request: ComputeCostRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """
    חישוב עלות דיווח
    
    מחשב את התעריף והעלות הכוללת לפי:
    - סוג עבודה
    - סוג כלי
    - דריסות מחיר (אם קיימות)
    
    מחזיר את מקור התעריף (equipment_type/pricing_override/system_rate)
    """
    rate_service = get_rate_service(db)
    
    result = rate_service.compute_worklog_cost(
        work_type=request.work_type,
        hours=request.hours,
        equipment_id=request.equipment_id,
        equipment_type_id=request.equipment_type_id,
        supplier_id=request.supplier_id,
        project_id=request.project_id,
        for_date=request.for_date
    )
    
    return ComputeCostResponse(**result)


@router.get("/rate-for-equipment-type/{type_id}")
async def get_rate_for_equipment_type(
    type_id: int,
    work_type: str = Query("fieldwork", description="סוג עבודה"),
    supplier_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    for_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """
    קבלת תעריף לסוג כלי
    
    מחפש דריסות מחיר לפני שמחזיר את ברירת המחדל
    """
    rate_service = get_rate_service(db)
    
    resolved = rate_service.resolve_rate(
        work_type=work_type,
        equipment_type_id=type_id,
        supplier_id=supplier_id,
        project_id=project_id,
        for_date=for_date
    )
    
    return resolved.to_dict()


@router.get("/simulate-days")
async def simulate_days_cost(
    equipment_type_id: int = Query(..., description="סוג כלי"),
    days: int = Query(..., ge=1, description="מספר ימים"),
    hours_per_day: int = Query(9, ge=1, le=24, description="שעות ליום"),
    supplier_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """
    סימולציה: חישוב עלות לפי ימים
    
    דוגמה: 5 ימים × 9 שעות × ₪120 = ₪5,400
    """
    rate_service = get_rate_service(db)
    
    total_hours = Decimal(days * hours_per_day)
    
    result = rate_service.compute_worklog_cost(
        work_type="fieldwork",
        hours=total_hours,
        equipment_type_id=equipment_type_id,
        supplier_id=supplier_id,
        project_id=project_id
    )
    
    return {
        "days": days,
        "hours_per_day": hours_per_day,
        "total_hours": float(total_hours),
        "hourly_rate": result["hourly_rate"],
        "subtotal": result["total_cost"],
        "vat_rate": 0.17,
        "vat_amount": result["total_cost_with_vat"] - result["total_cost"],
        "total_with_vat": result["total_cost_with_vat"],
        "rate_source": result["rate_source"],
        "rate_source_name": result["rate_source_name"]
    }


# =====================================================
# REPORTS - דוחות תמחור
# =====================================================

class PricingReportItem(BaseModel):
    """שורה בדוח תמחור"""
    id: int
    name: str
    total_hours: float
    total_cost: float
    total_cost_with_vat: float
    worklog_count: int
    unverified_count: int = 0   # worklogs with cost_before_vat but no hourly_rate_snapshot


class PricingReportResponse(BaseModel):
    """דוח תמחור"""
    items: List[PricingReportItem]
    summary: dict


@router.get("/reports/by-project", response_model=PricingReportResponse)
async def get_pricing_report_by_project(
    date_from: Optional[date] = Query(None, description="מתאריך"),
    date_to: Optional[date] = Query(None, description="עד תאריך"),
    supplier_id: Optional[int] = Query(None, description="ספק"),
    status: Optional[str] = Query(None, description="סטטוס (approved/submitted/all)"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """
    דוח תמחור לפי פרויקט
    
    מסכם את כל הדיווחים לפי פרויקט:
    - סה״כ שעות
    - סה״כ עלות לפני מע״מ
    - סה״כ עלות כולל מע״מ
    - מספר דיווחים
    """
    query = db.query(
        Project.id,
        Project.name,
        func.sum(Worklog.total_hours).label("total_hours"),
        func.sum(Worklog.cost_before_vat).label("total_cost"),
        func.sum(Worklog.cost_with_vat).label("total_cost_with_vat"),
        func.count(Worklog.id).label("worklog_count"),
        # Count worklogs that have cost_before_vat but no hourly_rate_snapshot
        func.count(
            func.nullif(
                Worklog.cost_before_vat.isnot(None) & Worklog.hourly_rate_snapshot.is_(None),
                False
            )
        ).label("unverified_count"),
    ).join(
        Worklog, Worklog.project_id == Project.id
    ).filter(
        Worklog.cost_before_vat.isnot(None)  # Only worklogs with pricing
    )

    # Apply filters
    if date_from:
        query = query.filter(Worklog.report_date >= date_from)
    if date_to:
        query = query.filter(Worklog.report_date <= date_to)
    if supplier_id:
        query = query.filter(Worklog.supplier_id == supplier_id)
    if status and status != "all":
        query = query.filter(Worklog.status == status)

    query = query.group_by(Project.id, Project.name).order_by(func.sum(Worklog.cost_before_vat).desc())

    results = query.all()

    # Fallback: fetch unverified counts via a separate simple query if needed
    # (SQLAlchemy bool expression in nullif can be tricky — safer raw approach)
    from sqlalchemy import text as _text
    unverified_map: Dict[int, int] = {}
    try:
        urows = db.execute(_text("""
            SELECT w.project_id, COUNT(*) as cnt
            FROM worklogs w
            WHERE w.cost_before_vat IS NOT NULL
              AND w.hourly_rate_snapshot IS NULL
            GROUP BY w.project_id
        """)).fetchall()
        unverified_map = {r.project_id: r.cnt for r in urows}
    except Exception:
        pass

    items = []
    total_hours = 0
    total_cost = 0
    total_cost_with_vat = 0
    total_unverified = 0

    for row in results:
        hours = float(row.total_hours or 0)
        cost = float(row.total_cost or 0)
        cost_vat = float(row.total_cost_with_vat or 0)
        unverified = unverified_map.get(row.id, 0)

        items.append(PricingReportItem(
            id=row.id,
            name=row.name or f"פרויקט {row.id}",
            total_hours=hours,
            total_cost=cost,
            total_cost_with_vat=cost_vat,
            worklog_count=row.worklog_count,
            unverified_count=unverified,
        ))

        total_hours += hours
        total_cost += cost
        total_cost_with_vat += cost_vat
        total_unverified += unverified

    return PricingReportResponse(
        items=items,
        summary={
            "total_projects": len(items),
            "total_hours": total_hours,
            "total_cost": total_cost,
            "total_cost_with_vat": total_cost_with_vat,
            "average_hourly_rate": total_cost / total_hours if total_hours > 0 else 0,
            "total_unverified_worklogs": total_unverified,
        }
    )


@router.get("/reports/by-supplier", response_model=PricingReportResponse)
async def get_pricing_report_by_supplier(
    date_from: Optional[date] = Query(None, description="מתאריך"),
    date_to: Optional[date] = Query(None, description="עד תאריך"),
    project_id: Optional[int] = Query(None, description="פרויקט"),
    status: Optional[str] = Query(None, description="סטטוס (approved/submitted/all)"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """
    דוח תמחור לפי ספק
    
    מסכם את כל הדיווחים לפי ספק:
    - סה״כ שעות
    - סה״כ עלות לפני מע״מ
    - סה״כ עלות כולל מע״מ
    - מספר דיווחים
    """
    query = db.query(
        Supplier.id,
        Supplier.name,
        func.sum(Worklog.total_hours).label("total_hours"),
        func.sum(Worklog.cost_before_vat).label("total_cost"),
        func.sum(Worklog.cost_with_vat).label("total_cost_with_vat"),
        func.count(Worklog.id).label("worklog_count")
    ).join(
        Worklog, Worklog.supplier_id == Supplier.id
    ).filter(
        Worklog.cost_before_vat.isnot(None)  # Only worklogs with pricing
    )
    
    # Apply filters
    if date_from:
        query = query.filter(Worklog.report_date >= date_from)
    if date_to:
        query = query.filter(Worklog.report_date <= date_to)
    if project_id:
        query = query.filter(Worklog.project_id == project_id)
    if status and status != "all":
        query = query.filter(Worklog.status == status)
    
    query = query.group_by(Supplier.id, Supplier.name).order_by(func.sum(Worklog.cost_before_vat).desc())
    
    results = query.all()
    
    items = []
    total_hours = 0
    total_cost = 0
    total_cost_with_vat = 0
    
    for row in results:
        hours = float(row.total_hours or 0)
        cost = float(row.total_cost or 0)
        cost_vat = float(row.total_cost_with_vat or 0)
        
        items.append(PricingReportItem(
            id=row.id,
            name=row.name or f"ספק {row.id}",
            total_hours=hours,
            total_cost=cost,
            total_cost_with_vat=cost_vat,
            worklog_count=row.worklog_count
        ))
        
        total_hours += hours
        total_cost += cost
        total_cost_with_vat += cost_vat
    
    return PricingReportResponse(
        items=items,
        summary={
            "total_suppliers": len(items),
            "total_hours": total_hours,
            "total_cost": total_cost,
            "total_cost_with_vat": total_cost_with_vat,
            "average_hourly_rate": total_cost / total_hours if total_hours > 0 else 0
        }
    )


@router.get("/reports/by-equipment-type", response_model=PricingReportResponse)
async def get_pricing_report_by_equipment_type(
    date_from: Optional[date] = Query(None, description="מתאריך"),
    date_to: Optional[date] = Query(None, description="עד תאריך"),
    project_id: Optional[int] = Query(None, description="פרויקט"),
    supplier_id: Optional[int] = Query(None, description="ספק"),
    status: Optional[str] = Query(None, description="סטטוס"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """
    דוח תמחור לפי סוג כלי
    
    מסכם את כל הדיווחים לפי סוג כלי:
    - סה״כ שעות
    - סה״כ עלות
    - מספר דיווחים
    """
    query = db.query(
        EquipmentType.id,
        EquipmentType.name,
        func.sum(Worklog.total_hours).label("total_hours"),
        func.sum(Worklog.cost_before_vat).label("total_cost"),
        func.sum(Worklog.cost_with_vat).label("total_cost_with_vat"),
        func.count(Worklog.id).label("worklog_count")
    ).join(
        Worklog, Worklog.equipment_type_id == EquipmentType.id
    ).filter(
        Worklog.cost_before_vat.isnot(None)
    )
    
    # Apply filters
    if date_from:
        query = query.filter(Worklog.report_date >= date_from)
    if date_to:
        query = query.filter(Worklog.report_date <= date_to)
    if project_id:
        query = query.filter(Worklog.project_id == project_id)
    if supplier_id:
        query = query.filter(Worklog.supplier_id == supplier_id)
    if status and status != "all":
        query = query.filter(Worklog.status == status)
    
    query = query.group_by(EquipmentType.id, EquipmentType.name).order_by(func.sum(Worklog.cost_before_vat).desc())
    
    results = query.all()
    
    items = []
    total_hours = 0
    total_cost = 0
    total_cost_with_vat = 0
    
    for row in results:
        hours = float(row.total_hours or 0)
        cost = float(row.total_cost or 0)
        cost_vat = float(row.total_cost_with_vat or 0)
        
        items.append(PricingReportItem(
            id=row.id,
            name=row.name or f"סוג כלי {row.id}",
            total_hours=hours,
            total_cost=cost,
            total_cost_with_vat=cost_vat,
            worklog_count=row.worklog_count
        ))
        
        total_hours += hours
        total_cost += cost
        total_cost_with_vat += cost_vat
    
    return PricingReportResponse(
        items=items,
        summary={
            "total_equipment_types": len(items),
            "total_hours": total_hours,
            "total_cost": total_cost,
            "total_cost_with_vat": total_cost_with_vat,
            "average_hourly_rate": total_cost / total_hours if total_hours > 0 else 0
        }
    )

