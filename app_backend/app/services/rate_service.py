"""Rate service for pricing calculations"""
from sqlalchemy.orm import Session
from typing import Optional, List


class RateService:
    """Service for calculating rates and pricing"""
    
    def get_equipment_rate(
        self,
        db: Session,
        equipment_type_id: int,
        supplier_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> float:
        """Get the applicable rate for equipment type"""
        # Default rate
        return 100.0
    
    def get_hourly_rate(
        self,
        db: Session,
        work_type: str,
        supplier_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> float:
        """Get hourly rate for work type"""
        # Default rate
        return 50.0
    
    def calculate_worklog_cost(
        self,
        db: Session,
        hours: float,
        work_type: str,
        equipment_type_id: Optional[int] = None,
        supplier_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> dict:
        """Calculate cost for a worklog entry"""
        hourly_rate = self.get_hourly_rate(db, work_type, supplier_id, project_id)
        equipment_rate = 0.0
        
        if equipment_type_id:
            equipment_rate = self.get_equipment_rate(db, equipment_type_id, supplier_id, project_id)
        
        labor_cost = hours * hourly_rate
        equipment_cost = hours * equipment_rate
        total_cost = labor_cost + equipment_cost
        
        return {
            "hours": hours,
            "hourly_rate": hourly_rate,
            "equipment_rate": equipment_rate,
            "labor_cost": labor_cost,
            "equipment_cost": equipment_cost,
            "total_cost": total_cost,
            "currency": "ILS"
        }


# Service instance factory
def get_rate_service() -> RateService:
    """Get rate service instance"""
    return RateService()
