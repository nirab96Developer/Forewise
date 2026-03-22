"""
PDF Service - General PDF generation functions
"""
import base64
from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


def generate_worklog_pdf(worklog_data: Dict[str, Any], segments: List[Dict[str, Any]] = None) -> bytes:
    """
    Generate PDF for a worklog report
    
    Args:
        worklog_data: Dictionary with worklog information
        segments: Optional list of time segments
        
    Returns:
        PDF as bytes
    """
    from weasyprint import HTML
    from weasyprint.text.fonts import FontConfiguration
    
    # Load Forewise logo
    logo_base64 = ""
    try:
        import os
        logo_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 
                                  'app_frontend', 'public', 'logo-kkl-transparent.png')
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                logo_base64 = f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
    except Exception as e:
        logger.warning(f"Could not load KKL logo: {e}")
    
    # Prepare time entries from segments or create default
    time_entries = []
    if segments:
        for seg in segments:
            time_entries.append({
                'type': 'work' if seg.get('is_work', True) else 'rest',
                'activity': 'עבודה' if seg.get('is_work', True) else 'מנוחה',
                'start_time': seg.get('start_time', ''),
                'end_time': seg.get('end_time', ''),
                'duration': seg.get('duration', ''),
                'billable': seg.get('billable_hours', ''),
                'notes': seg.get('notes', '')
            })
    else:
        # Create single entry from worklog data
        time_entries.append({
            'type': 'work',
            'activity': 'עבודה',
            'start_time': worklog_data.get('start_time', '06:30'),
            'end_time': worklog_data.get('end_time', '17:00'),
            'duration': f"{worklog_data.get('total_hours', 0)}:00",
            'billable': f"{worklog_data.get('billable_hours', worklog_data.get('total_hours', 0))}:00",
            'notes': ''
        })
    
    # Format hours for display
    def format_hours(value) -> str:
        if value is None:
            return "0:00"
        if isinstance(value, (int, float, Decimal)):
            hours = int(value)
            minutes = int((float(value) - hours) * 60)
            return f"{hours}:{minutes:02d}"
        return str(value)
    
    # Generate table rows
    table_rows = ""
    for entry in time_entries:
        table_rows += f'''
                    <tr>
                        <td class="status-{entry['type']}">{entry['activity']}</td>
                        <td>{entry['start_time']}</td>
                        <td>{entry['end_time']}</td>
                        <td>{entry['duration']}</td>
                        <td>{entry['billable']}</td>
                        <td>{entry.get('notes', '')}</td>
                    </tr>'''
    
    # Notes section
    notes_section = ""
    if worklog_data.get('notes'):
        notes_section = f'''
            <div class="notes-box">
                <span class="notes-title">הערות: </span>
                <span class="notes-content">{worklog_data.get('notes', '')}</span>
            </div>'''
    
    # Generate HTML
    html_content = f'''
<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
    <meta charset="UTF-8">
    <title>אישור דיווח עבודה יומי - Forewise</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700&display=swap');
        
        @page {{
            size: A4;
            margin: 12mm;
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Heebo', 'Arial Hebrew', Arial, sans-serif;
            font-size: 9pt;
            line-height: 1.4;
            color: #333;
            background: white;
        }}
        
        .document {{ border: 1px solid #DDD; }}
        
        .header {{
            padding: 20px 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #009557;
        }}
        
        .header-right {{ display: flex; align-items: center; gap: 20px; }}
        
        .logo-container {{ width: 70px; height: 70px; }}
        .logo-container img {{ width: 100%; height: 100%; object-fit: contain; }}
        
        .title-section h1 {{
            font-size: 18pt;
            font-weight: 700;
            color: #333;
            margin-bottom: 3px;
        }}
        
        .title-section .subtitle {{ font-size: 9pt; color: #666; }}
        
        .approval-box {{
            text-align: center;
            border: 2px solid #009557;
            padding: 10px 20px;
            border-radius: 8px;
        }}
        
        .approval-box .label {{ font-size: 8pt; color: #666; }}
        .approval-box .number {{ font-size: 20pt; font-weight: 700; color: #009557; }}
        
        .doc-info-bar {{
            background: #F9F9F9;
            padding: 10px 25px;
            display: flex;
            justify-content: space-around;
            border-bottom: 1px solid #EEE;
        }}
        
        .doc-info-item {{ text-align: center; }}
        .doc-info-item .label {{ font-size: 7pt; color: #888; }}
        .doc-info-item .value {{ font-size: 10pt; font-weight: 600; color: #333; }}
        
        .content {{ padding: 20px 25px; }}
        
        .section-title {{
            font-size: 10pt;
            font-weight: 600;
            color: #333;
            border-bottom: 1px solid #DDD;
            padding-bottom: 5px;
            margin-bottom: 10px;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 15px;
        }}
        
        .info-box {{
            border: 1px solid #E5E5E5;
            padding: 12px;
            background: #FAFAFA;
        }}
        
        .info-box h4 {{
            font-size: 9pt;
            color: #009557;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        
        .info-row {{
            display: flex;
            justify-content: space-between;
            padding: 3px 0;
            font-size: 9pt;
        }}
        
        .info-row .label {{ color: #666; }}
        .info-row .value {{ font-weight: 500; color: #333; }}
        
        .equipment-section {{
            border: 2px solid #009557;
            padding: 15px;
            text-align: center;
            margin-bottom: 15px;
        }}
        
        .equipment-section .equipment-label {{ font-size: 8pt; color: #666; }}
        .equipment-section .equipment-number {{
            font-size: 26pt;
            font-weight: 700;
            color: #009557;
            letter-spacing: 2px;
        }}
        .equipment-section .equipment-type {{ font-size: 10pt; color: #666; margin-top: 3px; }}
        
        .report-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 8px;
        }}
        
        .report-table th {{
            background: #009557;
            color: white;
            padding: 8px 6px;
            font-size: 8pt;
            font-weight: 600;
            text-align: center;
        }}
        
        .report-table td {{
            padding: 7px 6px;
            text-align: center;
            border: 1px solid #E5E5E5;
            font-size: 9pt;
        }}
        
        .report-table tr:nth-child(even) {{ background: #FAFAFA; }}
        
        .report-table .total-row {{
            background: #333 !important;
            color: white;
            font-weight: 600;
        }}
        
        .status-work {{ color: #009557; font-weight: 600; }}
        .status-rest {{ color: #888; }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin: 15px 0;
        }}
        
        .summary-box {{
            border: 1px solid #DDD;
            padding: 12px;
            text-align: center;
        }}
        
        .summary-box.primary {{
            background: #009557;
            color: white;
            border-color: #009557;
        }}
        
        .summary-box .summary-value {{ font-size: 20pt; font-weight: 700; }}
        .summary-box .summary-label {{ font-size: 8pt; margin-top: 3px; color: #666; }}
        .summary-box.primary .summary-label {{ color: rgba(255,255,255,0.9); }}
        .summary-box:not(.primary) .summary-value {{ color: #333; }}
        
        .signature-section {{
            margin-top: 20px;
            padding: 12px 15px;
            background: #F9F9F9;
            border: 1px solid #E5E5E5;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .signature-info {{ display: flex; align-items: center; gap: 25px; }}
        .signature-block {{ display: flex; align-items: center; gap: 8px; }}
        .signature-label {{ font-size: 9pt; color: #666; }}
        .signature-value {{ font-size: 11pt; font-weight: 600; color: #333; }}
        
        .approved-badge {{
            background: #009557;
            color: white;
            padding: 6px 16px;
            border-radius: 4px;
            font-size: 10pt;
            font-weight: 600;
        }}
        
        .footer {{
            background: #F5F5F5;
            padding: 10px 25px;
            border-top: 1px solid #DDD;
            display: flex;
            justify-content: space-between;
            font-size: 7pt;
            color: #888;
        }}
        
        .notes-box {{
            background: #FFFEF5;
            border: 1px solid #EED;
            padding: 10px;
            margin: 12px 0;
            font-size: 9pt;
        }}
        
        .notes-box .notes-title {{ font-weight: 600; color: #666; }}
        .notes-box .notes-content {{ color: #555; }}
    </style>
</head>
<body>
    <div class="document">
        <div class="header">
            <div class="header-right">
                <div class="logo-container">
                    {'<img src="' + logo_base64 + '" alt="Forewise Logo">' if logo_base64 else ''}
                </div>
                <div class="title-section">
                    <h1>אישור דיווח עבודה יומי</h1>
                    <div class="subtitle">מערכת ניהול יערות — Forewise</div>
                </div>
            </div>
            <div class="approval-box">
                <div class="label">מספר אישור</div>
                <div class="number">{worklog_data.get('report_number', worklog_data.get('id', ''))}</div>
            </div>
        </div>
        
        <div class="doc-info-bar">
            <div class="doc-info-item">
                <div class="label">תאריך דיווח</div>
                <div class="value">{worklog_data.get('work_date', worklog_data.get('report_date', ''))}</div>
            </div>
            <div class="doc-info-item">
                <div class="label">מספר הזמנה</div>
                <div class="value">{worklog_data.get('order_number', worklog_data.get('work_order_id', ''))}</div>
            </div>
            <div class="doc-info-item">
                <div class="label">סוג פעולה</div>
                <div class="value">{worklog_data.get('activity_type', worklog_data.get('work_type', 'עבודה'))}</div>
            </div>
            <div class="doc-info-item">
                <div class="label">סטטוס</div>
                <div class="value" style="color: #009557;">✓ מאושר</div>
            </div>
        </div>
        
        <div class="content">
            <div class="info-grid">
                <div class="info-box">
                    <h4>פרטי פרויקט</h4>
                    <div class="info-row">
                        <span class="label">שם הפרויקט:</span>
                        <span class="value">{worklog_data.get('project_name', '')}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">מרחב:</span>
                        <span class="value">{worklog_data.get('region_name', worklog_data.get('region', ''))}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">אזור:</span>
                        <span class="value">{worklog_data.get('area_name', worklog_data.get('area', ''))}</span>
                    </div>
                </div>
                
                <div class="info-box">
                    <h4>פרטי ספק</h4>
                    <div class="info-row">
                        <span class="label">שם הספק:</span>
                        <span class="value">{worklog_data.get('supplier_name', '')}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">מספר ספק:</span>
                        <span class="value">{worklog_data.get('supplier_id', '')}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">טלפון:</span>
                        <span class="value">{worklog_data.get('supplier_phone', '')}</span>
                    </div>
                </div>
            </div>
            
            <div class="equipment-section">
                <div class="equipment-label">מספר כלי מזהה</div>
                <div class="equipment-number">{worklog_data.get('equipment_code', worklog_data.get('equipment_number', ''))}</div>
                <div class="equipment-type">{worklog_data.get('equipment_type', '')} | רישוי: {worklog_data.get('equipment_license', worklog_data.get('license_plate', ''))}</div>
            </div>
            
            <div class="section-title">פירוט שעות עבודה</div>
            <table class="report-table">
                <thead>
                    <tr>
                        <th>סוג פעילות</th>
                        <th>שעת התחלה</th>
                        <th>שעת סיום</th>
                        <th>משך (שעות)</th>
                        <th>לתשלום</th>
                        <th>הערות</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                    <tr class="total-row">
                        <td colspan="3">סה"כ</td>
                        <td>{format_hours(worklog_data.get('total_hours', 0))}</td>
                        <td>{format_hours(worklog_data.get('billable_hours', worklog_data.get('total_hours', 0)))}</td>
                        <td></td>
                    </tr>
                </tbody>
            </table>
            
            <div class="summary-grid">
                <div class="summary-box primary">
                    <div class="summary-value">{format_hours(worklog_data.get('billable_hours', worklog_data.get('total_hours', 0)))}</div>
                    <div class="summary-label">שעות לתשלום</div>
                </div>
                <div class="summary-box">
                    <div class="summary-value">{format_hours(worklog_data.get('total_hours', 0))}</div>
                    <div class="summary-label">סה"כ נוכחות</div>
                </div>
                <div class="summary-box">
                    <div class="summary-value">{format_hours(worklog_data.get('idle_hours', 0))}</div>
                    <div class="summary-label">שעות בטלה</div>
                </div>
            </div>
            
            {notes_section}
            
            <div class="signature-section">
                <div class="signature-info">
                    <div class="signature-block">
                        <span class="signature-label">דווח על ידי:</span>
                        <span class="signature-value">{worklog_data.get('user_name', worklog_data.get('work_manager_name', ''))}</span>
                    </div>
                    <div class="signature-block">
                        <span class="signature-label">בתאריך:</span>
                        <span class="signature-value">{worklog_data.get('approved_at', datetime.now().strftime('%d/%m/%Y %H:%M'))}</span>
                    </div>
                </div>
                <div class="approved-badge">✓ אושר</div>
            </div>
        </div>
        
        <div class="footer">
            <div>מזהה: FW-WR-{datetime.now().strftime('%Y%m%d')}-{worklog_data.get('id', '')}</div>
            <div>מערכת ניהול יערות Forewise</div>
            <div>{datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
        </div>
    </div>
</body>
</html>
'''
    
    # Generate PDF
    font_config = FontConfiguration()
    pdf_bytes = HTML(string=html_content).write_pdf(font_config=font_config)
    
    return pdf_bytes


def generate_work_order_pdf(data: Dict[str, Any]) -> bytes:
    """
    Generate PDF for a work order.
    """
    from weasyprint import HTML
    from weasyprint.text.fonts import FontConfiguration

    logo_base64 = ""
    try:
        import os
        logo_path = os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                  'app_frontend', 'public', 'logo-kkl-transparent.png')
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                logo_base64 = f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
    except Exception as e:
        logger.warning(f"Could not load logo: {e}")

    status_map = {
        "PENDING": "ממתין", "DISTRIBUTING": "בתיאום", "SENT_TO_SUPPLIER": "נשלח לספק",
        "APPROVED": "אושר", "APPROVED_AND_SENT": "אושר ונשלח", "IN_PROGRESS": "בביצוע",
        "COMPLETED": "הושלם", "REJECTED": "נדחה", "CANCELLED": "בוטל", "CLOSED": "נסגר",
    }
    priority_map = {"low": "נמוכה", "medium": "בינונית", "high": "גבוהה", "critical": "קריטית"}
    status_he = status_map.get(data.get('status', ''), data.get('status', ''))
    priority_he = priority_map.get(data.get('priority', ''), data.get('priority', ''))

    html_content = f'''<!DOCTYPE html>
<html dir="rtl" lang="he">
<head><meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;600;700&display=swap');
  body {{ font-family: 'Heebo', sans-serif; padding: 40px; color: #333; direction: rtl; }}
  .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #2e7d32; padding-bottom: 15px; margin-bottom: 25px; }}
  .logo {{ height: 50px; }}
  h1 {{ color: #2e7d32; font-size: 22px; margin: 0; }}
  .subtitle {{ color: #666; font-size: 13px; }}
  table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
  th {{ background: #f5f5f5; text-align: right; padding: 10px 12px; font-size: 13px; border: 1px solid #ddd; }}
  td {{ padding: 10px 12px; font-size: 13px; border: 1px solid #ddd; }}
  .badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; }}
  .green {{ background: #e8f5e9; color: #2e7d32; }}
  .footer {{ margin-top: 40px; text-align: center; color: #999; font-size: 11px; border-top: 1px solid #eee; padding-top: 15px; }}
</style>
</head>
<body>
  <div class="header">
    <div>
      <h1>הזמנת עבודה #{data.get('order_number', data.get('id', ''))}</h1>
      <div class="subtitle">{data.get('title', '')}</div>
    </div>
    {"<img class='logo' src='" + logo_base64 + "' />" if logo_base64 else "<div>Forewise</div>"}
  </div>
  <table>
    <tr><th>פרויקט</th><td>{data.get('project_name', '')} ({data.get('project_code', '')})</td></tr>
    <tr><th>סטטוס</th><td><span class="badge green">{status_he}</span></td></tr>
    <tr><th>עדיפות</th><td>{priority_he}</td></tr>
    <tr><th>סוג ציוד</th><td>{data.get('equipment_type', '')}</td></tr>
    <tr><th>תאריך התחלה</th><td>{data.get('work_start_date', '')}</td></tr>
    <tr><th>תאריך סיום</th><td>{data.get('work_end_date', '')}</td></tr>
    <tr><th>שעות מוערכות</th><td>{data.get('estimated_hours', 0)}</td></tr>
    <tr><th>שעות בפועל</th><td>{data.get('actual_hours', 0)}</td></tr>
    <tr><th>תעריף שעתי</th><td>₪{data.get('hourly_rate', 0):,.2f}</td></tr>
    <tr><th>סכום כולל</th><td>₪{data.get('total_amount', 0):,.2f}</td></tr>
    <tr><th>סכום מוקפא</th><td>₪{data.get('frozen_amount', 0):,.2f}</td></tr>
  </table>
  {"<p><strong>תיאור:</strong> " + data.get('description', '') + "</p>" if data.get('description') else ""}
  <div class="footer">
    Forewise &copy; {datetime.now().year} | הופק בתאריך {datetime.now().strftime('%d/%m/%Y %H:%M')}
  </div>
</body>
</html>'''

    font_config = FontConfiguration()
    return HTML(string=html_content).write_pdf(font_config=font_config)
