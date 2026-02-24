"""
PDF Preview endpoints - תצוגה מקדימה של דוחות PDF
"""
from fastapi import APIRouter, Response
from fastapi.responses import HTMLResponse
from app.services.pdf_report_service import pdf_report_service

router = APIRouter(prefix="/pdf-preview", tags=["PDF Preview"])


@router.get("/daily-work-report", response_class=HTMLResponse)
async def preview_daily_work_report():
    """Preview daily work report PDF template with sample data"""
    
    sample_data = {
        "report_date": "23/01/2026",
        "confirmation_number": "156137",
        "project_name": "שימור קרקע-אחזקתדר. 4599004870",
        "region": "דרום",
        "area": "שימור קרקע",
        "location": "מחלקת שימור קרקע אחזקת דרכים ותשתיות",
        "supplier_name": "א.ש.גולני - אלסייד שעבאן",
        "supplier_id": "56312515",
        "supplier_phone": "206011123",
        "supplier_email": "gmail.com@9188405",
        "equipment_number": "124281-3",
        "equipment_type": "מפלסת",
        "activity_type": "פריצת דרכים",
        "order_number": "930015684",
        "time_entries": [
            {
                "type": "work",
                "activity": "עבודה",
                "start_time": "06:30",
                "end_time": "10:30",
                "total_hours": "04:00",
                "billable_hours": "4:00",
                "notes": ""
            },
            {
                "type": "rest",
                "activity": "מנוחה",
                "start_time": "10:30",
                "end_time": "11:00",
                "total_hours": "00:30",
                "billable_hours": "0:00",
                "notes": ""
            },
            {
                "type": "work",
                "activity": "עבודה",
                "start_time": "11:00",
                "end_time": "16:00",
                "total_hours": "05:00",
                "billable_hours": "5:00",
                "notes": ""
            }
        ],
        "total_presence": "9:30",
        "total_billable": "9:00",
        "idle_hours": "0:00",
        "general_notes": "",
        "work_manager_name": "מיכאל דומברובסקי",
        "document_id": "WR-20260123-156137"
    }
    
    html_content = pdf_report_service.generate_daily_work_report(sample_data)
    return HTMLResponse(content=html_content)

