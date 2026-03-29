"""
PDF Document Generator — Production-grade A4 RTL documents
Generates: Invoice PDF, Work Order PDF
Uses weasyprint for pixel-perfect A4 rendering.
"""
import logging
import os
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

_GREEN = "#1a6b3c"
_GREEN_LIGHT = "#e8f5ee"
_GREEN_DARK = "#0d4a28"
_GRAY = "#6b7c72"
_GRAY_LIGHT = "#f8fbf9"
_BORDER = "#dde8e2"
_TEXT = "#111d15"

_REPORTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "reports",
)


def _load_logo() -> str:
    try:
        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "templates", "logo_base64.txt",
        )
        with open(logo_path, "r") as f:
            b64 = f.read().strip()
            if b64:
                return '<img src="data:image/png;base64,' + b64 + '" alt="Forewise" style="height:50px;width:auto;" />'
    except Exception:
        pass
    return '<div style="font-size:28px;font-weight:900;color:#1a6b3c;letter-spacing:0.3em;">FOREWISE</div>'


_LOGO_HTML = _load_logo()

_BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700;800&display=swap');
@page {
    size: A4;
    margin: 14mm 16mm 18mm 16mm;
    @bottom-center {
        content: counter(page) " / " counter(pages);
        font-family: 'Heebo', Arial, sans-serif;
        font-size: 8pt;
        color: #6b7c72;
    }
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: 'Heebo', 'Arial Hebrew', Arial, sans-serif;
    font-size: 10pt;
    line-height: 1.5;
    color: #111d15;
    direction: rtl;
    background: white;
}
.header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding-bottom: 14px;
    border-bottom: 3px solid #1a6b3c;
    margin-bottom: 18px;
}
.header-right { display: flex; align-items: center; gap: 16px; }
.doc-title { font-size: 22pt; font-weight: 800; color: #0d4a28; margin-bottom: 2px; }
.doc-subtitle { font-size: 9pt; color: #6b7c72; }
.doc-number-box {
    text-align: center;
    border: 2px solid #1a6b3c;
    padding: 8px 20px;
    border-radius: 10px;
}
.doc-number-label { font-size: 8pt; color: #6b7c72; margin-bottom: 2px; }
.doc-number { font-size: 18pt; font-weight: 800; color: #1a6b3c; direction: ltr; }
.meta-bar {
    background: #f8fbf9;
    border: 1px solid #dde8e2;
    border-radius: 8px;
    padding: 10px 20px;
    display: flex;
    justify-content: space-around;
    margin-bottom: 18px;
}
.meta-item { text-align: center; }
.meta-label { font-size: 7.5pt; color: #6b7c72; margin-bottom: 1px; }
.meta-value { font-size: 10pt; font-weight: 600; color: #111d15; }
.section { margin-bottom: 16px; }
.section-title {
    font-size: 11pt; font-weight: 700; color: #0d4a28;
    border-bottom: 1px solid #dde8e2;
    padding-bottom: 5px; margin-bottom: 10px;
}
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 14px; }
.info-box { border: 1px solid #dde8e2; border-radius: 8px; padding: 12px 14px; background: #f8fbf9; }
.info-box h4 {
    font-size: 9.5pt; color: #1a6b3c; font-weight: 700;
    margin-bottom: 8px; border-bottom: 1px solid #dde8e2; padding-bottom: 4px;
}
.info-row { display: flex; justify-content: space-between; padding: 3px 0; font-size: 9pt; }
.info-row .label { color: #6b7c72; }
.info-row .value { font-weight: 500; color: #111d15; }
table.data-table { width: 100%; border-collapse: collapse; margin-top: 6px; }
table.data-table thead th {
    background: #1a6b3c; color: white;
    padding: 8px 8px; font-size: 8.5pt; font-weight: 600;
    text-align: center; white-space: nowrap;
}
table.data-table thead { display: table-header-group; }
table.data-table tbody td {
    padding: 7px 8px; text-align: center;
    border-bottom: 1px solid #dde8e2; font-size: 9pt;
}
table.data-table tbody tr:nth-child(even) { background: #f8fbf9; }
table.data-table tfoot td {
    padding: 9px 8px; font-weight: 700; font-size: 10pt;
    border-top: 2px solid #1a6b3c;
}
.totals-box {
    margin-top: 16px; margin-right: auto; width: 280px;
    border: 2px solid #1a6b3c; border-radius: 10px; overflow: hidden;
}
.totals-row {
    display: flex; justify-content: space-between;
    padding: 8px 16px; font-size: 10pt; border-bottom: 1px solid #dde8e2;
}
.totals-row:last-child { border-bottom: none; }
.totals-row.grand {
    background: #1a6b3c; color: white;
    font-size: 13pt; font-weight: 800; padding: 10px 16px;
}
.status-badge {
    display: inline-block; padding: 3px 14px;
    border-radius: 20px; font-weight: 700; font-size: 9pt;
}
.footer-bar {
    margin-top: 24px; padding-top: 10px; border-top: 1px solid #dde8e2;
    display: flex; justify-content: space-between; font-size: 7.5pt; color: #6b7c72;
}
.equipment-highlight {
    border: 2px solid #1a6b3c; border-radius: 10px;
    padding: 12px; text-align: center; margin-bottom: 14px;
}
.equipment-highlight .eq-label { font-size: 8pt; color: #6b7c72; }
.equipment-highlight .eq-number {
    font-size: 22pt; font-weight: 800; color: #1a6b3c;
    letter-spacing: 2px; direction: ltr;
}
.equipment-highlight .eq-type { font-size: 9.5pt; color: #6b7c72; margin-top: 2px; }
"""


def _fmt_currency(v) -> str:
    if v is None:
        return "—"
    return f"{float(v):,.2f} ₪"


def _fmt_date(d) -> str:
    if not d:
        return "—"
    if isinstance(d, str):
        return d
    try:
        return d.strftime("%d/%m/%Y")
    except Exception:
        return str(d)


def _status_badge(status, status_map):
    sl = status_map.get(status or '', ('לא ידוע', '#374151', '#e5e7eb'))
    return '<span class="status-badge" style="background:' + sl[2] + ';color:' + sl[1] + ';">' + sl[0] + '</span>'


def _generate_pdf(html: str) -> bytes:
    from weasyprint import HTML
    from weasyprint.text.fonts import FontConfiguration
    fc = FontConfiguration()
    return HTML(string=html).write_pdf(font_config=fc)


# ==============================
#  INVOICE PDF
# ==============================

def generate_invoice_pdf(invoice_id: int, db: Session) -> bytes:
    from app.models.invoice import Invoice
    from app.models.invoice_item import InvoiceItem

    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise ValueError(f"Invoice {invoice_id} not found")

    sup = db.execute(text(
        "SELECT name, tax_id, phone, email FROM suppliers WHERE id=:sid"
    ), {"sid": inv.supplier_id}).first()

    proj_row = None
    if inv.project_id:
        proj_row = db.execute(text("""
            SELECT p.name, p.code, a.name, r.name
            FROM projects p LEFT JOIN areas a ON p.area_id=a.id
            LEFT JOIN regions r ON a.region_id=r.id WHERE p.id=:pid
        """), {"pid": inv.project_id}).first()

    items = (
        db.query(InvoiceItem)
        .filter(InvoiceItem.invoice_id == invoice_id, InvoiceItem.is_active == True)
        .order_by(InvoiceItem.line_number).all()
    )

    wl_rows = db.execute(text("""
        SELECT w.report_date, w.work_hours, w.hourly_rate_snapshot,
               w.cost_before_vat, COALESCE(w.equipment_type, e.equipment_type),
               e.license_plate
        FROM worklogs w LEFT JOIN equipment e ON w.equipment_id=e.id
        WHERE w.work_order_id IN (
            SELECT wo.id FROM work_orders wo
            WHERE wo.supplier_id=:sid AND wo.project_id=:pid
        )
        AND w.status='INVOICED' AND w.is_active=true
        AND EXTRACT(MONTH FROM w.report_date)=:m AND EXTRACT(YEAR FROM w.report_date)=:y
        ORDER BY w.report_date
    """), {"sid": inv.supplier_id, "pid": inv.project_id,
           "m": inv.issue_date.month, "y": inv.issue_date.year}).fetchall()

    detail_html = ""
    total_hours = 0.0
    if wl_rows:
        for i, wl in enumerate(wl_rows):
            h = float(wl[1] or 0)
            r = float(wl[2] or 0)
            lt = float(wl[3] or h * r)
            total_hours += h
            bg = ' style="background:#f8fbf9;"' if i % 2 == 0 else ""
            detail_html += '<tr' + bg + '>'
            detail_html += '<td>' + _fmt_date(wl[0]) + '</td>'
            detail_html += '<td>' + (wl[4] or '—') + '</td>'
            detail_html += '<td style="direction:ltr;">' + (wl[5] or '—') + '</td>'
            detail_html += '<td>' + f"{h:.1f}" + '</td>'
            detail_html += '<td>' + _fmt_currency(r) + '</td>'
            detail_html += '<td style="font-weight:600;">' + _fmt_currency(lt) + '</td>'
            detail_html += '</tr>'
    else:
        for item in items:
            total_hours += float(item.quantity)
            detail_html += '<tr>'
            detail_html += '<td>—</td>'
            detail_html += '<td colspan="2">' + item.description + '</td>'
            detail_html += '<td>' + f"{float(item.quantity):.1f}" + '</td>'
            detail_html += '<td>' + _fmt_currency(item.unit_price) + '</td>'
            detail_html += '<td style="font-weight:600;">' + _fmt_currency(item.total_price) + '</td>'
            detail_html += '</tr>'

    months = ['','ינואר','פברואר','מרץ','אפריל','מאי','יוני',
              'יולי','אוגוסט','ספטמבר','אוקטובר','נובמבר','דצמבר']
    period = months[inv.issue_date.month] + ' ' + str(inv.issue_date.year)

    inv_status_map = {
        'DRAFT': ('טיוטה', '#854d0e', '#fef9c3'),
        'PENDING': ('ממתין', '#854d0e', '#fef9c3'),
        'APPROVED': ('מאושר', '#0d4a28', '#e8f5ee'),
        'PAID': ('שולם', '#1e40af', '#dbeafe'),
        'CANCELLED': ('בוטל', '#991b1b', '#fee2e2'),
    }
    badge = _status_badge(inv.status, inv_status_map)

    html = '<!DOCTYPE html><html dir="rtl" lang="he"><head><meta charset="UTF-8">'
    html += '<title>חשבונית ' + inv.invoice_number + '</title>'
    html += '<style>' + _BASE_CSS + '</style></head><body>'

    # Header
    html += '<div class="header"><div class="header-right">' + _LOGO_HTML
    html += '<div><div class="doc-title">חשבונית</div>'
    html += '<div class="doc-subtitle">מערכת ניהול יערות — Forewise</div></div></div>'
    html += '<div class="doc-number-box"><div class="doc-number-label">מספר חשבונית</div>'
    html += '<div class="doc-number">' + inv.invoice_number + '</div></div></div>'

    # Meta bar
    html += '<div class="meta-bar">'
    html += '<div class="meta-item"><div class="meta-label">תאריך הנפקה</div><div class="meta-value">' + _fmt_date(inv.issue_date) + '</div></div>'
    html += '<div class="meta-item"><div class="meta-label">תקופה</div><div class="meta-value">' + period + '</div></div>'
    html += '<div class="meta-item"><div class="meta-label">תאריך לתשלום</div><div class="meta-value">' + _fmt_date(inv.due_date) + '</div></div>'
    html += '<div class="meta-item"><div class="meta-label">סטטוס</div><div class="meta-value">' + badge + '</div></div>'
    html += '</div>'

    # Supplier + Project
    html += '<div class="info-grid"><div class="info-box"><h4>פרטי ספק</h4>'
    html += '<div class="info-row"><span class="label">שם:</span><span class="value">' + (sup[0] if sup else '—') + '</span></div>'
    html += '<div class="info-row"><span class="label">ח.פ / עוסק:</span><span class="value">' + (sup[1] if sup and sup[1] else '—') + '</span></div>'
    html += '<div class="info-row"><span class="label">טלפון:</span><span class="value">' + (sup[2] if sup and sup[2] else '—') + '</span></div>'
    html += '<div class="info-row"><span class="label">אימייל:</span><span class="value">' + (sup[3] if sup and sup[3] else '—') + '</span></div>'
    html += '</div><div class="info-box"><h4>פרטי פרויקט</h4>'
    html += '<div class="info-row"><span class="label">פרויקט:</span><span class="value">' + (proj_row[0] if proj_row else '—') + '</span></div>'
    html += '<div class="info-row"><span class="label">קוד:</span><span class="value">' + (proj_row[1] if proj_row and proj_row[1] else '—') + '</span></div>'
    html += '<div class="info-row"><span class="label">אזור:</span><span class="value">' + (proj_row[2] if proj_row and proj_row[2] else '—') + '</span></div>'
    html += '<div class="info-row"><span class="label">מרחב:</span><span class="value">' + (proj_row[3] if proj_row and proj_row[3] else '—') + '</span></div>'
    html += '</div></div>'

    # Detail table
    html += '<div class="section"><div class="section-title">פירוט עבודה</div>'
    html += '<table class="data-table"><thead><tr>'
    html += '<th>תאריך</th><th>סוג כלי</th><th>מספר רישוי</th><th>שעות</th><th>תעריף</th><th>סה"כ</th>'
    html += '</tr></thead><tbody>' + detail_html + '</tbody>'
    html += '<tfoot><tr><td colspan="3" style="text-align:right;padding-right:16px;">סה"כ</td>'
    html += '<td>' + f"{total_hours:.1f}" + '</td><td></td>'
    html += '<td style="color:#1a6b3c;">' + _fmt_currency(inv.subtotal) + '</td></tr></tfoot></table></div>'

    # Totals
    html += '<div style="display:flex;justify-content:flex-start;"><div class="totals-box">'
    html += '<div class="totals-row"><span>סה"כ לפני מע"מ</span><span>' + _fmt_currency(inv.subtotal) + '</span></div>'
    html += '<div class="totals-row"><span>מע"מ (18%)</span><span>' + _fmt_currency(inv.tax_amount) + '</span></div>'
    html += '<div class="totals-row grand"><span>סה"כ לתשלום</span><span>' + _fmt_currency(inv.total_amount) + '</span></div>'
    html += '</div></div>'

    # Footer
    html += '<div class="footer-bar">'
    html += '<div>FW-INV-' + str(inv.id) + '</div>'
    html += '<div>Forewise — מערכת ניהול יערות</div>'
    html += '<div>' + datetime.utcnow().strftime('%d/%m/%Y %H:%M') + '</div>'
    html += '</div></body></html>'

    return _generate_pdf(html)


def save_invoice_pdf(invoice_id: int, db: Session) -> str:
    from app.models.invoice import Invoice
    pdf_bytes = generate_invoice_pdf(invoice_id, db)
    out_dir = os.path.join(_REPORTS_DIR, "invoices")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, str(invoice_id) + ".pdf")
    with open(path, "wb") as f:
        f.write(pdf_bytes)
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if inv:
        inv.pdf_path = path
        db.commit()
    return path


# ==============================
#  WORK ORDER PDF
# ==============================

def generate_work_order_pdf(work_order_id: int, db: Session) -> bytes:
    from app.models.work_order import WorkOrder

    wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not wo:
        raise ValueError(f"Work Order {work_order_id} not found")

    proj_name, area_name, region_name = '—', '—', '—'
    if wo.project_id:
        row = db.execute(text("""
            SELECT p.name, a.name, r.name FROM projects p
            LEFT JOIN areas a ON p.area_id=a.id
            LEFT JOIN regions r ON a.region_id=r.id WHERE p.id=:pid
        """), {"pid": wo.project_id}).first()
        if row:
            proj_name = row[0] or '—'
            area_name = row[1] or '—'
            region_name = row[2] or '—'

    supplier_name = '—'
    if wo.supplier_id:
        row = db.execute(text("SELECT name FROM suppliers WHERE id=:sid"), {"sid": wo.supplier_id}).first()
        if row:
            supplier_name = row[0] or '—'

    eq_type = wo.equipment_type or '—'
    eq_plate = wo.equipment_license_plate or '—'
    if wo.equipment_id:
        row = db.execute(text("SELECT name, license_plate, equipment_type FROM equipment WHERE id=:eid"),
                         {"eid": wo.equipment_id}).first()
        if row:
            eq_type = row[2] or row[0] or eq_type
            eq_plate = row[1] or eq_plate

    creator_name = '—'
    if wo.created_by_id:
        row = db.execute(text("SELECT full_name FROM users WHERE id=:uid"), {"uid": wo.created_by_id}).first()
        if row:
            creator_name = row[0] or '—'

    hours_used = 0.0
    wl_row = db.execute(text(
        "SELECT COALESCE(SUM(work_hours),0) FROM worklogs WHERE work_order_id=:woid AND is_active=true"
    ), {"woid": wo.id}).first()
    if wl_row:
        hours_used = float(wl_row[0])
    est = float(wo.estimated_hours or 0)
    remaining = max(est - hours_used, 0)
    pct = min(100, int(hours_used / est * 100)) if est > 0 else 0
    bar_color = '#1a6b3c' if pct < 80 else '#eab308' if pct < 100 else '#ef4444'

    wo_status_map = {
        'DRAFT': ('טיוטה', '#854d0e', '#fef9c3'),
        'PENDING': ('ממתין', '#854d0e', '#fef9c3'),
        'DISTRIBUTING': ('בהפצה', '#854d0e', '#fef9c3'),
        'SUPPLIER_ACCEPTED_PENDING_COORDINATOR': ('ממתין לאישור מתאם', '#854d0e', '#fef9c3'),
        'APPROVED': ('מאושר', '#0d4a28', '#e8f5ee'),
        'APPROVED_AND_SENT': ('אושר ונשלח', '#0d4a28', '#e8f5ee'),
        'IN_PROGRESS': ('בביצוע', '#1e40af', '#dbeafe'),
        'ACTIVE': ('פעיל', '#0d4a28', '#e8f5ee'),
        'COMPLETED': ('הושלם', '#374151', '#e5e7eb'),
        'REJECTED': ('נדחה', '#991b1b', '#fee2e2'),
        'CANCELLED': ('בוטל', '#991b1b', '#fee2e2'),
        'STOPPED': ('הופסק', '#991b1b', '#fee2e2'),
    }
    badge = _status_badge(wo.status, wo_status_map)

    html = '<!DOCTYPE html><html dir="rtl" lang="he"><head><meta charset="UTF-8">'
    html += '<title>דרישת עבודה #' + str(wo.order_number or wo.id) + '</title>'
    html += '<style>' + _BASE_CSS + '</style></head><body>'

    html += '<div class="header"><div class="header-right">' + _LOGO_HTML
    html += '<div><div class="doc-title">דרישת עבודה</div>'
    html += '<div class="doc-subtitle">מערכת ניהול יערות — Forewise</div></div></div>'
    html += '<div class="doc-number-box"><div class="doc-number-label">מספר דרישה</div>'
    html += '<div class="doc-number">' + str(wo.order_number or wo.id) + '</div></div></div>'

    html += '<div class="meta-bar">'
    html += '<div class="meta-item"><div class="meta-label">תאריך יצירה</div><div class="meta-value">' + _fmt_date(wo.created_at) + '</div></div>'
    html += '<div class="meta-item"><div class="meta-label">תאריך התחלה</div><div class="meta-value">' + _fmt_date(wo.work_start_date) + '</div></div>'
    html += '<div class="meta-item"><div class="meta-label">תאריך סיום</div><div class="meta-value">' + _fmt_date(wo.work_end_date) + '</div></div>'
    html += '<div class="meta-item"><div class="meta-label">סטטוס</div><div class="meta-value">' + badge + '</div></div>'
    html += '</div>'

    html += '<div class="info-grid"><div class="info-box"><h4>פרטי פרויקט</h4>'
    html += '<div class="info-row"><span class="label">פרויקט:</span><span class="value">' + proj_name + '</span></div>'
    html += '<div class="info-row"><span class="label">אזור:</span><span class="value">' + area_name + '</span></div>'
    html += '<div class="info-row"><span class="label">מרחב:</span><span class="value">' + region_name + '</span></div>'
    html += '<div class="info-row"><span class="label">יוצר:</span><span class="value">' + creator_name + '</span></div>'
    html += '</div><div class="info-box"><h4>פרטי ספק ועבודה</h4>'
    html += '<div class="info-row"><span class="label">ספק:</span><span class="value">' + supplier_name + '</span></div>'
    html += '<div class="info-row"><span class="label">עדיפות:</span><span class="value">' + (wo.priority or '—') + '</span></div>'
    html += '<div class="info-row"><span class="label">סוג עבודה:</span><span class="value">' + (wo.title or '—') + '</span></div>'
    html += '</div></div>'

    html += '<div class="equipment-highlight">'
    html += '<div class="eq-label">ציוד נדרש</div>'
    html += '<div class="eq-number">' + eq_plate + '</div>'
    html += '<div class="eq-type">' + eq_type + '</div></div>'

    html += '<div class="info-grid"><div class="info-box"><h4>תכנון זמן</h4>'
    html += '<div class="info-row"><span class="label">שעות מוערכות:</span><span class="value">' + f"{est:.0f}" + '</span></div>'
    html += '<div class="info-row"><span class="label">שנוצלו:</span><span class="value">' + f"{hours_used:.1f}" + '</span></div>'
    html += '<div class="info-row"><span class="label">נותרות:</span><span class="value">' + f"{remaining:.1f}" + '</span></div>'
    html += '<div style="margin-top:8px;background:#e5e7eb;border-radius:6px;height:10px;overflow:hidden;">'
    html += '<div style="width:' + str(pct) + '%;height:100%;background:' + bar_color + ';border-radius:6px;"></div></div>'
    html += '<div style="text-align:center;font-size:8pt;color:#6b7c72;margin-top:3px;">' + str(pct) + '% ניצול</div>'
    html += '</div><div class="info-box"><h4>תמחור</h4>'
    html += '<div class="info-row"><span class="label">תעריף שעתי:</span><span class="value">' + _fmt_currency(wo.hourly_rate) + '</span></div>'
    html += '<div class="info-row"><span class="label">סכום מוקפא:</span><span class="value">' + _fmt_currency(wo.frozen_amount) + '</span></div>'
    html += '<div class="info-row"><span class="label">יתרת הקפאה:</span><span class="value">' + _fmt_currency(wo.remaining_frozen) + '</span></div>'
    html += '</div></div>'

    if wo.description:
        html += '<div class="section"><div class="section-title">תיאור עבודה</div>'
        html += '<div style="background:#f8fbf9;border:1px solid #dde8e2;border-radius:8px;padding:12px 16px;font-size:9.5pt;line-height:1.7;">'
        html += wo.description + '</div></div>'

    html += '<div class="footer-bar">'
    html += '<div>FW-WO-' + str(wo.id) + '</div>'
    html += '<div>Forewise</div>'
    html += '<div>' + datetime.utcnow().strftime('%d/%m/%Y %H:%M') + '</div>'
    html += '</div></body></html>'

    return _generate_pdf(html)


def save_work_order_pdf(work_order_id: int, db: Session) -> str:
    pdf_bytes = generate_work_order_pdf(work_order_id, db)
    out_dir = os.path.join(_REPORTS_DIR, "work_orders")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, str(work_order_id) + ".pdf")
    with open(path, "wb") as f:
        f.write(pdf_bytes)
    return path
