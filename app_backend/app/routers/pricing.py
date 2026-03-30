"""
Pricing router - חישוב תעריפים ודוחות
API for computing work pricing and reports
"""

from datetime import date
from decimal import Decimal
from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, and_, text as _text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.services.rate_service import RateService, get_rate_service
from app.models.worklog import Worklog
from app.models.project import Project
from app.models.supplier import Supplier
from app.models.equipment import Equipment
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
    hours: Optional[float] = None
    hourly_rate: float
    daily_rate: Optional[float] = None
    total_cost: float
    total_cost_with_vat: float
    rate_source: str
    rate_source_id: Optional[int] = None
    rate_source_name: Optional[str] = None


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
    
    try:
        result = rate_service.compute_worklog_cost(
            work_type=request.work_type,
            hours=request.hours,
            equipment_id=request.equipment_id,
            equipment_type_id=request.equipment_type_id,
            supplier_id=request.supplier_id,
            project_id=request.project_id,
            for_date=request.for_date
        )
        
        result["hours"] = float(request.hours)
        return ComputeCostResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"שגיאה בחישוב עלות: {str(e)}"
        )


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
    
דוגמה: 5 ימים × 9 שעות × 120 = 5,400
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
        "vat_rate": 0.18,
        "vat_amount": result["total_cost_with_vat"] - result["total_cost"],
        "total_with_vat": result["total_cost_with_vat"],
        "rate_source": result["rate_source"],
        "rate_source_name": result["rate_source_name"]
    }


# =====================================================
# REPORTS - דוחות תמחור
# =====================================================

class WorklogDetail(BaseModel):
    """פרטי worklog בודד לתוך דוח פרויקט"""
    worklog_id: int
    report_date: Optional[str]
    work_hours: float
    cost_before_vat: Optional[float]
    cost_with_vat: Optional[float]
    hourly_rate_snapshot: Optional[float]
    supplier_name: Optional[str]
    equipment_license_plate: Optional[str]
    equipment_type: Optional[str]
    status: str
    is_verified: bool


class PricingReportItem(BaseModel):
    """שורה בדוח תמחור"""
    id: int
    name: str
    total_hours: float
    total_cost: float
    total_cost_with_vat: float
    worklog_count: int
    unverified_count: int = 0   # worklogs with cost_before_vat but no hourly_rate_snapshot
    worklogs_detail: List[WorklogDetail] = []


class PricingReportResponse(BaseModel):
    """דוח תמחור"""
    items: List[PricingReportItem]
    summary: dict
    total: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None


@router.get("/reports/by-project", response_model=PricingReportResponse)
async def get_pricing_report_by_project(
    date_from: Optional[date] = Query(None, description="מתאריך"),
    date_to: Optional[date] = Query(None, description="עד תאריך"),
    supplier_id: Optional[int] = Query(None, description="ספק"),
    status: Optional[str] = Query(None, description="סטטוס (approved/submitted/all)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
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

    total_groups = query.count()
    results = query.offset((page - 1) * page_size).limit(page_size).all()

    # Build filters string for the detail sub-query
    filter_clauses = ["w.cost_before_vat IS NOT NULL"]
    filter_params: dict = {}
    if date_from:
        filter_clauses.append("w.report_date >= :date_from")
        filter_params["date_from"] = date_from
    if date_to:
        filter_clauses.append("w.report_date <= :date_to")
        filter_params["date_to"] = date_to
    if supplier_id:
        filter_clauses.append("w.supplier_id = :supplier_id")
        filter_params["supplier_id"] = supplier_id
    if status and status != "all":
        filter_clauses.append("w.status = :status")
        filter_params["status"] = status

    where_sql = " AND ".join(filter_clauses)

    # Fetch worklog details for all projects in one query
    detail_sql = _text(f"""
        SELECT
            w.id            AS worklog_id,
            w.project_id,
            w.report_date,
            w.work_hours,
            w.cost_before_vat,
            w.cost_with_vat,
            w.hourly_rate_snapshot,
            w.status,
            s.name          AS supplier_name,
            COALESCE(e.code, e.license_plate) AS equipment_license_plate,
            COALESCE(e.equipment_type, et.name) AS equipment_type
        FROM worklogs w
        LEFT JOIN suppliers s ON s.id = w.supplier_id
        LEFT JOIN equipment e ON e.id = w.equipment_id
        LEFT JOIN equipment_types et ON et.id = e.equipment_type_id
        WHERE {where_sql}
        ORDER BY w.report_date DESC
    """)
    try:
        detail_rows = db.execute(detail_sql, filter_params).fetchall()
    except Exception:
        detail_rows = []

    # Group details by project_id
    details_by_project: Dict[int, List[WorklogDetail]] = {}
    all_supplier_ids = set()
    for dr in detail_rows:
        pid = dr.project_id
        if pid not in details_by_project:
            details_by_project[pid] = []
        is_verified = dr.hourly_rate_snapshot is not None
        details_by_project[pid].append(WorklogDetail(
            worklog_id=dr.worklog_id,
            report_date=str(dr.report_date) if dr.report_date else None,
            work_hours=float(dr.work_hours or 0),
            cost_before_vat=float(dr.cost_before_vat) if dr.cost_before_vat is not None else None,
            cost_with_vat=float(dr.cost_with_vat) if dr.cost_with_vat is not None else None,
            hourly_rate_snapshot=float(dr.hourly_rate_snapshot) if dr.hourly_rate_snapshot is not None else None,
            supplier_name=dr.supplier_name,
            equipment_license_plate=dr.equipment_license_plate,
            equipment_type=dr.equipment_type,
            status=dr.status or "PENDING",
            is_verified=is_verified,
        ))
        if dr.supplier_name:
            all_supplier_ids.add(dr.supplier_name)

    items = []
    total_hours = 0
    total_cost = 0
    total_cost_with_vat = 0
    total_unverified = 0

    for row in results:
        hours = float(row.total_hours or 0)
        cost = float(row.total_cost or 0)
        cost_vat = float(row.total_cost_with_vat or 0)
        wl_details = details_by_project.get(row.id, [])
        unverified = sum(1 for d in wl_details if not d.is_verified)

        items.append(PricingReportItem(
            id=row.id,
            name=row.name or f"פרויקט {row.id}",
            total_hours=hours,
            total_cost=cost,
            total_cost_with_vat=cost_vat,
            worklog_count=row.worklog_count,
            unverified_count=unverified,
            worklogs_detail=wl_details,
        ))

        total_hours += hours
        total_cost += cost
        total_cost_with_vat += cost_vat
        total_unverified += unverified

    return PricingReportResponse(
        items=items,
        total=total_groups,
        page=page,
        page_size=page_size,
        summary={
            "total_projects": total_groups,
            "total_hours": total_hours,
            "total_cost": total_cost,
            "total_cost_with_vat": total_cost_with_vat,
            "average_hourly_rate": total_cost / total_hours if total_hours > 0 else 0,
            "total_unverified_worklogs": total_unverified,
            "total_suppliers": len(all_supplier_ids),
        }
    )


@router.get("/reports/by-supplier", response_model=PricingReportResponse)
async def get_pricing_report_by_supplier(
    date_from: Optional[date] = Query(None, description="מתאריך"),
    date_to: Optional[date] = Query(None, description="עד תאריך"),
    project_id: Optional[int] = Query(None, description="פרויקט"),
    status: Optional[str] = Query(None, description="סטטוס (approved/submitted/all)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
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
    
    total_groups = query.count()
    results = query.offset((page - 1) * page_size).limit(page_size).all()
    
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
        total=total_groups,
        page=page,
        page_size=page_size,
        summary={
            "total_suppliers": total_groups,
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
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
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
    from app.models.equipment import Equipment
    from app.models.equipment_category import EquipmentCategory
    from sqlalchemy import case as sa_case, text as sa_text

    et_id_expr = func.coalesce(
        Worklog.equipment_type_id,
        db.query(EquipmentType.id)
        .join(EquipmentCategory, EquipmentCategory.name == EquipmentType.name)
        .join(Equipment, Equipment.category_id == EquipmentCategory.id)
        .filter(Equipment.id == Worklog.equipment_id)
        .correlate(Worklog)
        .limit(1)
        .scalar_subquery()
    )

    query = db.query(
        EquipmentType.id,
        EquipmentType.name,
        func.sum(func.coalesce(Worklog.total_hours, Worklog.work_hours, 0)).label("total_hours"),
        func.sum(func.coalesce(Worklog.cost_before_vat, 0)).label("total_cost"),
        func.sum(func.coalesce(Worklog.cost_with_vat, 0)).label("total_cost_with_vat"),
        func.count(Worklog.id).label("worklog_count")
    ).join(
        Worklog, et_id_expr == EquipmentType.id
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

    total_groups = query.count()
    results = query.offset((page - 1) * page_size).limit(page_size).all()

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
        total=total_groups,
        page=page,
        page_size=page_size,
        summary={
            "total_equipment_types": total_groups,
            "total_hours": total_hours,
            "total_cost": total_cost,
            "total_cost_with_vat": total_cost_with_vat,
            "average_hourly_rate": total_cost / total_hours if total_hours > 0 else 0
        }
    )

