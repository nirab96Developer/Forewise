"""
PDF Report Generation Service - שירות יצירת דוחות PDF
"""
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
import logging

logger = logging.getLogger(__name__)


class PDFReportService:
    """Service for generating PDF reports"""
    
    def __init__(self):
        # Set up Jinja2 template environment
        template_dir = Path(__file__).parent.parent / "templates" / "pdf"
        template_dir.mkdir(parents=True, exist_ok=True)
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
    
    def generate_daily_work_report(
        self,
        report_data: Dict[str, Any]
    ) -> str:
        """
        Generate daily work report HTML
        
        Args:
            report_data: Dictionary containing all report data
            
        Returns:
            HTML string ready for PDF conversion
        """
        try:
            template = self.env.get_template("daily_work_report.html")
            
            # Prepare data with defaults
            data = {
                "report_date": report_data.get("report_date", datetime.now().strftime("%d/%m/%Y")),
                "confirmation_number": report_data.get("confirmation_number", "000000"),
                "project_name": report_data.get("project_name", ""),
                "region": report_data.get("region", ""),
                "area": report_data.get("area", ""),
                "location": report_data.get("location", ""),
                "supplier_name": report_data.get("supplier_name", ""),
                "supplier_id": report_data.get("supplier_id", ""),
                "supplier_phone": report_data.get("supplier_phone", ""),
                "supplier_email": report_data.get("supplier_email", ""),
                "equipment_number": report_data.get("equipment_number", ""),
                "equipment_type": report_data.get("equipment_type", ""),
                "activity_type": report_data.get("activity_type", ""),
                "order_number": report_data.get("order_number", ""),
                "time_entries": report_data.get("time_entries", []),
                "total_presence": report_data.get("total_presence", "0:00"),
                "total_billable": report_data.get("total_billable", "0:00"),
                "idle_hours": report_data.get("idle_hours", "0:00"),
                "general_notes": report_data.get("general_notes", ""),
                "work_manager_name": report_data.get("work_manager_name", ""),
                "document_id": report_data.get("document_id", f"WR-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
            }
            
            html_content = template.render(**data)
            return html_content
            
        except Exception as e:
            logger.error(f"Error generating daily work report: {e}")
            raise
    
    def generate_work_report_pdf(
        self,
        report_data: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Generate PDF from work report data
        
        Note: Requires weasyprint or similar library for PDF generation
        For now, returns HTML that can be converted to PDF
        """
        html_content = self.generate_daily_work_report(report_data)
        
        try:
            # Try using weasyprint if available
            from weasyprint import HTML
            pdf_bytes = HTML(string=html_content).write_pdf()
            
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(pdf_bytes)
            
            return pdf_bytes
            
        except ImportError:
            logger.warning("weasyprint not installed, returning HTML instead")
            # Return HTML as fallback
            return html_content.encode('utf-8')
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            raise


# Singleton instance
pdf_report_service = PDFReportService()


def generate_confirmation_number(worklog_id: int, date: datetime) -> str:
    """Generate unique confirmation number for a worklog"""
    date_part = date.strftime("%y%m%d")
    return f"{date_part}-{worklog_id:06d}"

