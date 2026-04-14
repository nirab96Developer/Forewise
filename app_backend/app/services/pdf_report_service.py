"""
PDF Report Generation Service - שירות יצירת דוחות PDF
"""
from datetime import datetime
from typing import Optional, Dict, Any
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
                # Standard / non-standard
                "is_standard": report_data.get("is_standard", True),
                "non_standard_reason": report_data.get("non_standard_reason", ""),
                # Overnight
                "is_overnight": report_data.get("is_overnight", False),
                "overnight_nights": report_data.get("overnight_nights", 1),
                "overnight_rate": report_data.get("overnight_rate", 250),
                "overnight_total": report_data.get("overnight_nights", 1) * report_data.get("overnight_rate", 250),
                # Logo
                "logo_base64": report_data.get("logo_base64", ""),
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



# Auto Worklog PDF 

import os as _os

REPORTS_DIR = _os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))),
    "reports", "worklogs"
)


def generate_and_save_worklog_pdf(worklog_id: int, db) -> str:
    """
    יוצר PDF לדיווח, שומר ב-reports/worklogs/{worklog_id}.pdf,
    מעדכן worklog.pdf_path + pdf_generated_at, ומחזיר את הנתיב.
    """
    from datetime import datetime as _dt
    from app.models.worklog import Worklog
    from app.models.worklog_segment import WorklogSegment

    wl = db.query(Worklog).filter(Worklog.id == worklog_id).first()
    if not wl:
        raise ValueError(f"Worklog {worklog_id} not found")

    segments = db.query(WorklogSegment).filter(
        WorklogSegment.worklog_id == worklog_id
    ).order_by(WorklogSegment.start_time).all()

# Build HTML 
    seg_rows = ""
    for s in segments:
        seg_rows += f"""
        <tr>
          <td>{s.start_time}</td><td>{s.end_time}</td>
          <td>{s.segment_type}</td>
          <td>{s.activity_type or ''}</td>
          <td>{float(s.duration_hours or 0):.2f}</td>
          <td>{s.payment_pct or 100}%</td>
<td>{float(s.amount or 0):,.2f}</td>
        </tr>"""

    overnight_row = ""
    if wl.is_overnight:
        overnight_row = f"""
        <tr class="overnight">
          <td colspan="6">שמירת לילה × {wl.overnight_nights} לילות</td>
<td>{float(wl.overnight_total or 0):,.2f}</td>
        </tr>"""

    project_name = getattr(wl.project, 'name', '') if wl.project else ''
    equipment_license = ""
    if wl.equipment:
        equipment_license = getattr(wl.equipment, 'license_plate', '') or ''
    supplier_name = getattr(wl.supplier, 'name', '') if hasattr(wl, 'supplier') and wl.supplier else ''
    work_order_num = ""
    if wl.work_order:
        work_order_num = str(getattr(wl.work_order, 'order_number', ''))

    # Load logo for PDF
    _logo_html = ""
    try:
        _logo_b64_path = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "templates", "logo_base64.txt")
        with open(_logo_b64_path, "r") as _lf:
            _lb64 = _lf.read().strip()
            if _lb64:
                _logo_html = f'<img src="data:image/png;base64,{_lb64}" alt="Forewise" width="80" style="max-width:80px;" />'
    except Exception:
        pass

    html = f"""<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
<meta charset="UTF-8"/>
<style>
  body {{ font-family: Arial, sans-serif; font-size: 12px; direction: rtl; }}
  h1 {{ color: #1a5c2e; font-size: 18px; }}
  .header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }}
  .meta {{ background: #f5f5f5; padding: 8px 12px; border-radius: 6px; margin-bottom: 12px; }}
  .meta td {{ padding: 3px 8px; }}
  .meta .label {{ font-weight: bold; color: #555; }}
  table.segs {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
  table.segs th {{ background: #1a5c2e; color: #fff; padding: 6px; }}
  table.segs td {{ padding: 5px 6px; border-bottom: 1px solid #e5e7eb; }}
  .overnight {{ background: #fef3c7; font-weight: bold; }}
  .totals {{ margin-top: 12px; text-align: left; }}
  .totals td {{ padding: 4px 10px; }}
  .totals .grand {{ font-size: 14px; font-weight: bold; color: #1a5c2e; }}
  .badge {{ display: inline-block; padding: 2px 10px; border-radius: 99px;
            background: #d1fae5; color: #065f46; font-weight: bold; font-size: 11px; }}
  .logo-block {{ text-align: center; margin-bottom: 8px; }}
  .logo-block img {{ max-width: 80px; }}
  .brand-text {{ font-size: 11px; font-weight: 900; color: #1a6b3c; letter-spacing: 0.2em; }}
  @page {{ margin: 20mm; }}
</style>
</head>
<body>
<div class="header">
  <div>
    <h1>דוח יומי — Forewise</h1>
    <span class="badge">{wl.status or 'PENDING'}</span>
  </div>
  <div style="text-align:left; color:#888; font-size:11px;">
    {_logo_html}
    <div class="brand-text">FOREWISE</div>
    <div style="margin-top:6px;">מספר דוח: {wl.report_number or wl.id}<br/>
    תאריך: {wl.report_date or wl.work_date or ''}</div>
  </div>
</div>

<table class="meta">
  <tr><td class="label">פרויקט:</td><td>{project_name}</td>
      <td class="label">הזמנה #:</td><td>{work_order_num}</td></tr>
  <tr><td class="label">כלי:</td><td>{getattr(wl.equipment,'name','') if wl.equipment else ''} {equipment_license}</td>
      <td class="label">ספק:</td><td>{supplier_name}</td></tr>
  <tr><td class="label">מנהל עבודה:</td><td>{getattr(wl.user,'full_name','') if wl.user else ''}</td>
<td class="label">תעריף שעתי:</td><td>{float(wl.hourly_rate_snapshot or 0):,.2f}</td></tr>
</table>

<table class="segs">
  <thead>
    <tr><th>שעת התחלה</th><th>שעת סיום</th><th>סוג</th><th>פעילות</th>
        <th>שעות</th><th>% תשלום</th><th>סכום</th></tr>
  </thead>
  <tbody>
    {seg_rows}
    {overnight_row}
  </tbody>
</table>

<table class="totals" align="left">
  <tr><td>שעות ברוטו:</td><td>{float(wl.net_hours or 0):.2f}</td></tr>
  <tr><td>שעות לתשלום:</td><td>{float(wl.paid_hours or 0):.2f}</td></tr>
<tr><td>שמירת לילה:</td><td>{float(wl.overnight_total or 0):,.2f}</td></tr>
<tr><td>סה"כ לפני מע"מ:</td><td>{float(wl.cost_before_vat or 0):,.2f}</td></tr>
<tr class="grand"><td>סה"כ כולל מע"מ:</td><td>{float(wl.cost_with_vat or 0):,.2f}</td></tr>
</table>
</body>
</html>"""

# Write PDF 
    _os.makedirs(REPORTS_DIR, exist_ok=True)
    pdf_path = _os.path.join(REPORTS_DIR, f"{worklog_id}.pdf")

    try:
        from weasyprint import HTML as _HTML
        _HTML(string=html).write_pdf(pdf_path)
    except Exception as e:
        logger.error(f"weasyprint PDF generation failed for worklog {worklog_id}: {e}")
        # שמור HTML כגיבוי
        pdf_path = pdf_path.replace(".pdf", ".html")
        with open(pdf_path, "w", encoding="utf-8") as f:
            f.write(html)

# Update worklog 
    wl.pdf_path = pdf_path
    wl.pdf_generated_at = _dt.now()
    db.commit()

# Send email 
    try:
        _send_worklog_pdf_email(wl, pdf_path, db)
    except Exception as e:
        logger.error(f"Failed to send worklog PDF email: {e}")

    return pdf_path


def _send_worklog_pdf_email(wl, pdf_path: str, db) -> None:
    """שולח את ה-PDF לספק + מנהלת חשבונות"""
    from app.core.email import send_email_with_pdf

    recipients = []
    if hasattr(wl, 'supplier') and wl.supplier and getattr(wl.supplier, 'email', None):
        recipients.append(wl.supplier.email)
    try:
        from app.models.user import User
        accountants = db.query(User).filter(User.is_active == True).all()
        for u in accountants:
            role_code = (u.role.code if hasattr(u, 'role') and u.role else "") or ""
            if role_code.upper() == "ACCOUNTANT" and u.email:
                recipients.append(u.email)
    except Exception:
        pass

    if not recipients:
        return

    try:
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
    except Exception as e:
        logger.warning(f"Could not read PDF file {pdf_path}: {e}")
        return

    project_name = getattr(wl.project, 'name', '') if wl.project else ''
    subject = f"דוח יומי #{wl.report_number or wl.id} — {project_name}"
    body = f"מצ'ב דוח יומי #{wl.report_number or wl.id} לתאריך {wl.report_date or wl.work_date}."

    for email in set(recipients):
        try:
            send_email_with_pdf(
                to=email,
                subject=subject,
                body=body,
                pdf_bytes=pdf_bytes,
                pdf_filename=f"worklog_{wl.id}.pdf",
            )
        except Exception as e:
            logger.warning(f"Could not send PDF to {email}: {e}")
