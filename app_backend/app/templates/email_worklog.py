"""HTML email templates for Forewise — worklog + work order lifecycle.
Uses the Forewise logo PNG (base64-embedded) and branded design.
"""
import os as _os

def _load_logo_base64():
    """Load logo PNG as base64 data URI — cached after first call."""
    b64_path = _os.path.join(_os.path.dirname(__file__), "logo_base64.txt")
    try:
        with open(b64_path, "r") as f:
            return f.read().strip()
    except Exception:
        return ""

_LOGO_B64 = _load_logo_base64()

LOGO_SVG = f'<img src="data:image/png;base64,{_LOGO_B64}" alt="Forewise" width="120" height="auto" style="max-width:120px;height:auto;" />' if _LOGO_B64 else '''<svg width="70" height="70" viewBox="0 0 140 140" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M56 38 Q70 26 84 38" stroke="#4BAEE8" stroke-width="4" stroke-linecap="round" fill="none"/>
<path d="M44 52 Q70 35 96 52" stroke="#3BAE9A" stroke-width="4" stroke-linecap="round" fill="none"/>
<path d="M28 70 Q44 54 70 60 Q96 54 112 70 Q109 75 104 73 Q88 64 70 67 Q52 64 36 73 Q31 75 28 70Z" fill="#6B8C3A"/>
<line x1="70" y1="67" x2="70" y2="92" stroke="#8B5E3C" stroke-width="5" stroke-linecap="round"/>
<circle cx="70" cy="98" r="4" fill="#8B5E3C" opacity="0.55"/>
</svg>'''

BRAND_NAME = '''<div style="margin-top:8px;font-size:13px;font-weight:900;color:#1a6b3c;letter-spacing:0.25em;text-transform:uppercase;font-family:Arial,sans-serif;">FOREWISE</div>
<div style="font-size:10px;color:#6b8c6b;font-family:Arial,sans-serif;">מערכת לניהול פרויקטים ויערות</div>'''

FOOTER = '''<tr><td style="padding:24px 32px 28px;text-align:center;">
<div style="font-size:11px;color:#aab8b2;line-height:1.6;">
Forewise — מערכת ניהול יערות<br>
<a href="https://forewise.co" style="color:#1a6b3c;text-decoration:none;">forewise.co</a>
</div></td></tr>'''


def _header():
    return f'''<tr><td style="background:#ffffff;padding:32px 32px 0;text-align:center;">
{LOGO_SVG}{BRAND_NAME}</td></tr>'''


def _icon_circle(emoji):
    return f'''<table cellpadding="0" cellspacing="0" border="0" style="margin:0 auto 16px;">
<tr><td style="width:56px;height:56px;background:#e8f5ee;border-radius:28px;text-align:center;vertical-align:middle;">
<span style="font-size:24px;">{emoji}</span></td></tr></table>'''


def _detail_row(label, value, alt=False):
    bg = 'background:#f8fbf9;' if alt else ''
    return f'''<tr style="{bg}">
<td style="padding:11px 14px;font-size:12px;color:#6b7c72;width:42%;">{label}</td>
<td style="padding:11px 14px;font-size:13px;color:#111d15;">{value}</td></tr>'''


def _detail_row_bold(label, value, color="#111d15", alt=False):
    bg = 'background:#f8fbf9;' if alt else ''
    return f'''<tr style="{bg}">
<td style="padding:11px 14px;font-size:12px;color:#6b7c72;width:42%;">{label}</td>
<td style="padding:11px 14px;font-size:13px;font-weight:700;color:{color};">{value}</td></tr>'''


def _badge(text, bg="#fff8e8", border="#f0c060", color="#8a6000"):
    return f'''<tr><td style="padding:16px 32px 0;">
<table width="100%" cellpadding="0" cellspacing="0" border="0"
style="background:{bg};border:1px solid {border};border-radius:10px;text-align:center;">
<tr><td style="padding:14px;font-size:13px;color:{color};font-weight:600;">{text}</td></tr>
</table></td></tr>'''


def _cta_button(text, url="https://forewise.co"):
    return f'''<tr><td style="padding:20px 32px 0;text-align:center;">
<table cellpadding="0" cellspacing="0" border="0" style="margin:0 auto;">
<tr><td style="background:#1a6b3c;border-radius:10px;padding:13px 32px;">
<a href="{url}" style="color:white;font-size:14px;font-weight:700;text-decoration:none;">{text}</a>
</td></tr></table></td></tr>'''


def _cost_block(work_hours, hourly_rate, overnight_nights=0, overnight_rate=250, vat_rate=0.18):
    hours_cost = work_hours * hourly_rate
    overnight_cost = overnight_nights * overnight_rate
    total_before = hours_cost + overnight_cost
    total_with_vat = round(total_before * (1 + vat_rate), 2)

    overnight_row = ""
    if overnight_cost > 0:
        overnight_row = f'''<tr style="background:#f0f7f2;">
<td style="padding:10px 14px;font-size:12px;color:#6b7c72;"> לינת שטח</td>
<td style="padding:10px 4px;font-size:12px;color:#6b7c72;text-align:center;">{overnight_nights} לילה × {overnight_rate:,.0f}</td>
<td style="padding:10px 14px;font-size:13px;font-weight:700;color:#111d15;text-align:left;">{overnight_cost:,.0f}</td></tr>'''

    return f'''<tr><td style="padding:16px 32px 0;">
<table width="100%" cellpadding="0" cellspacing="0" border="0"
style="border-radius:10px;overflow:hidden;border:1px solid #b8dfc8;background:#f8fbf9;">
<tr><td colspan="3" style="padding:10px 14px 6px;font-size:11px;font-weight:700;color:#1a6b3c;letter-spacing:0.08em;text-transform:uppercase;border-bottom:1px solid #ddeee5;">
 &nbsp;חישוב עלות</td></tr>
<tr>
<td style="padding:10px 14px;font-size:12px;color:#6b7c72;width:44%;">שעות עבודה</td>
<td style="padding:10px 4px;font-size:12px;color:#6b7c72;text-align:center;">{work_hours} שע' × {hourly_rate:,.0f}</td>
<td style="padding:10px 14px;font-size:13px;font-weight:700;color:#111d15;text-align:left;">{hours_cost:,.0f}</td></tr>
{overnight_row}
<tr><td colspan="3" style="padding:0 14px;"><hr style="border:none;border-top:1px dashed #b8dfc8;"></td></tr>
<tr style="background:#e8f5ee;">
<td style="padding:12px 14px;font-size:13px;font-weight:700;color:#1a6b3c;">סה"כ לפני מע"מ</td><td></td>
<td style="padding:12px 14px;text-align:left;"><span style="font-size:20px;font-weight:800;color:#1a6b3c;">{total_before:,.0f}</span></td></tr>
<tr><td style="padding:8px 14px 10px;font-size:11px;color:#6b7c72;">כולל מע"מ ({int(vat_rate*100)}%)</td><td></td>
<td style="padding:8px 14px 10px;font-size:12px;font-weight:600;color:#6b7c72;text-align:left;">{total_with_vat:,.1f}</td></tr>
</table></td></tr>'''


def _wrap(inner_rows):
    return f'''<!DOCTYPE html><html dir="rtl" lang="he"><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#eef2f0;font-family:Heebo,Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#eef2f0;padding:32px 16px;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" border="0"
style="background:#ffffff;border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,0.08);max-width:600px;width:100%;overflow:hidden;">
{inner_rows}
</table></td></tr></table></body></html>'''


# 
# STAGE 1: Worklog created  PENDING
# 

def stage1_pending(report_number, project_name, supplier_name, equipment_type,
                   license_plate, work_date, work_hours, report_type,
                   worker_name, hourly_rate=0, overnight_nights=0,
                   overnight_rate=250, recipient_role="accountant", **kw):
    type_badge = '<span style="background:#e8f5ee;color:#1a6b3c;font-size:11px;font-weight:700;padding:3px 10px;border-radius:20px;"> תקן</span>' if report_type == 'standard' else '<span style="background:#fff3e0;color:#e65100;font-size:11px;font-weight:700;padding:3px 10px;border-radius:20px;"> לא תקן</span>'

    details = f'''<tr><td style="padding:16px 32px 0;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-radius:10px;overflow:hidden;border:1px solid #e8ede9;">
{_detail_row_bold('מספר דיווח', report_number, '#1a6b3c', True)}
{_detail_row('פרויקט', project_name)}
{_detail_row('ספק', supplier_name, True)}
{_detail_row('סוג ציוד', f'{equipment_type} | {license_plate}' if license_plate else equipment_type)}
{_detail_row('תאריך עבודה', work_date, True)}
{_detail_row('שעות עבודה', f'<span style="font-size:20px;font-weight:800;color:#1a6b3c;">{work_hours}</span> <span style="font-size:12px;color:#6b7c72;">שעות</span>')}
{_detail_row('סוג דיווח', type_badge, True)}
{_detail_row('מנהל עבודה', worker_name)}
</table></td></tr>'''

    cost = _cost_block(work_hours, hourly_rate, overnight_nights, overnight_rate) if hourly_rate else ''

    if recipient_role == "accountant":
        title = "דיווח שעות חדש"
        subtitle = f'דיווח <strong style="color:#1a6b3c;">{report_number}</strong> ממתין לאישורך'
        badge = _badge(' &nbsp;הדיווח ממתין לאישורך במערכת Forewise')
        cta = _cta_button('עבור לאישור הדיווח ', 'https://forewise.co/accountant-inbox')
        subject = f"דיווח חדש ממתין לאישורך — {report_number}"
    elif recipient_role == "supplier":
        title = "אישור קבלת דיווח שעות"
        subtitle = f'שלום <strong>{supplier_name}</strong>,<br>דיווח שעות עבור הזמנה התקבל במערכת.'
        badge = _badge(' ממתין לאישור מנהלת חשבונות', '#fff8e8', '#f0c060', '#8a6000')
        cta = ''
        subject = f"אסמכתא — דיווח שעות התקבל {report_number}"
    else:
        title = "דיווח שעות נשמר"
        subtitle = f'דיווח <strong style="color:#1a6b3c;">{report_number}</strong> נשמר בהצלחה'
        badge = _badge(' ממתין לאישור מנהלת חשבונות')
        cta = ''
        subject = f"דיווח שעות נשמר — {report_number}"

    inner = f'''{_header()}
<tr><td style="padding:20px 32px 0;text-align:center;">
{_icon_circle('')}
<div style="font-size:22px;font-weight:800;color:#111d15;margin-bottom:6px;">{title}</div>
<div style="font-size:13px;color:#6b7c72;line-height:1.5;">{subtitle}</div>
</td></tr>
<tr><td style="padding:20px 32px 0;"><hr style="border:none;border-top:1px solid #e8ede9;"></td></tr>
{details}{cost}{badge}{cta}{FOOTER}'''

    return {"subject": subject, "html": _wrap(inner)}


# 
# STAGE 2: Worklog approved  APPROVED
# 

def stage2_approved(report_number, project_name, supplier_name, equipment_type,
                    work_date, total_hours, hourly_rate, overnight_nights=0,
                    overnight_rate=250, worker_name="", recipient_role="supplier", **kw):

    details = f'''<tr><td style="padding:16px 32px 0;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-radius:10px;overflow:hidden;border:1px solid #e8ede9;">
{_detail_row_bold('מספר דיווח', report_number, '#1a6b3c', True)}
{_detail_row('פרויקט', project_name)}
{_detail_row('תאריך עבודה', work_date, True)}
{_detail_row('שעות', f'<span style="font-size:20px;font-weight:800;color:#1a6b3c;">{total_hours}</span> שעות')}
{_detail_row('ספק', supplier_name, True)}
</table></td></tr>'''

    cost = _cost_block(total_hours, hourly_rate, overnight_nights, overnight_rate)
    badge = _badge(' &nbsp;אושר — ממתין להפקת חשבונית', '#e8f5ee', '#b8dfc8', '#1a6b3c')

    if recipient_role == "supplier":
        subject = f" אסמכתא מאושרת — {report_number}"
    else:
        subject = f"דיווח אושר — {report_number}"

    inner = f'''{_header()}
<tr><td style="padding:20px 32px 0;text-align:center;">
{_icon_circle('')}
<div style="font-size:22px;font-weight:800;color:#111d15;margin-bottom:6px;">דיווח שעות אושר</div>
<div style="font-size:13px;color:#6b7c72;">דיווח <strong style="color:#1a6b3c;">{report_number}</strong> אושר</div>
</td></tr>
<tr><td style="padding:20px 32px 0;"><hr style="border:none;border-top:1px solid #e8ede9;"></td></tr>
{details}{cost}{badge}{FOOTER}'''

    return {"subject": subject, "html": _wrap(inner)}


# 
# STAGE 3: Invoice created  INVOICED
# 

def stage3_invoiced(invoice_number, invoice_date, supplier_name, project_name,
                    worklogs_summary, total_amount, recipient_role="supplier", **kw):

    rows = ""
    for wl in worklogs_summary:
        rows += f'''<tr><td style="padding:6px 8px;font-size:12px;border-bottom:1px solid #eee;">{wl.get('report_number','')}</td>
<td style="padding:6px 8px;font-size:12px;border-bottom:1px solid #eee;">{wl.get('work_date','')}</td>
<td style="padding:6px 8px;font-size:12px;border-bottom:1px solid #eee;">{wl.get('hours',0)} שעות</td>
<td style="padding:6px 8px;font-size:12px;border-bottom:1px solid #eee;">{wl.get('amount',0):,.0f}</td></tr>'''

    table = f'''<tr><td style="padding:16px 32px 0;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-radius:10px;overflow:hidden;border:1px solid #e8ede9;">
{_detail_row_bold('מספר חשבונית', invoice_number, '#1a6b3c', True)}
{_detail_row('תאריך הפקה', invoice_date)}
{_detail_row('ספק', supplier_name, True)}
{_detail_row('פרויקט', project_name)}
</table></td></tr>
<tr><td style="padding:16px 32px 0;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="border:1px solid #e8ede9;border-radius:10px;overflow:hidden;">
<thead><tr style="background:#f5f5f5;">
<th style="padding:8px;font-size:12px;text-align:right;color:#666;">דיווח</th>
<th style="padding:8px;font-size:12px;text-align:right;color:#666;">תאריך</th>
<th style="padding:8px;font-size:12px;text-align:right;color:#666;">שעות</th>
<th style="padding:8px;font-size:12px;text-align:right;color:#666;">סכום</th></tr></thead>
<tbody>{rows}</tbody>
<tfoot><tr style="background:#e8f5ee;">
<td colspan="3" style="padding:10px 8px;font-size:14px;font-weight:900;color:#1b5e20;">סה"כ לתשלום</td>
<td style="padding:10px 8px;font-size:18px;font-weight:900;color:#1b5e20;">{total_amount:,.0f}</td></tr></tfoot>
</table></td></tr>'''

    badge = _badge(' &nbsp;חשבונית הופקה', '#e3f2fd', '#90caf9', '#1565c0')

    subject = f" חשבונית הופקה — {invoice_number}" if recipient_role == "supplier" else f"חשבונית {invoice_number} הופקה"

    inner = f'''{_header()}
<tr><td style="padding:20px 32px 0;text-align:center;">
{_icon_circle('')}
<div style="font-size:22px;font-weight:800;color:#111d15;margin-bottom:6px;">חשבונית הופקה</div>
<div style="font-size:13px;color:#6b7c72;">חשבונית <strong style="color:#1565c0;">{invoice_number}</strong></div>
</td></tr>
<tr><td style="padding:20px 32px 0;"><hr style="border:none;border-top:1px solid #e8ede9;"></td></tr>
{table}{badge}{FOOTER}'''

    return {"subject": subject, "html": _wrap(inner)}


# 
# EMAIL 4: Work order approved  all stakeholders
# 

def work_order_approved(order_number, project_name, project_code, supplier_name,
                        equipment_type, license_plate, work_start, work_end,
                        estimated_hours, area_name, region_name, worker_name,
                        lat=None, lng=None, recipient_label="", **kw):

    details = f'''<tr><td style="padding:16px 32px 0;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-radius:10px;overflow:hidden;border:1px solid #e8ede9;">
{_detail_row_bold('פרויקט', f'{project_name} ({project_code})', alt=True)}
{_detail_row('ספק', supplier_name)}
{_detail_row('ציוד ומספר רישוי', f'{equipment_type} | <strong>{license_plate}</strong>' if license_plate else equipment_type, True)}
{_detail_row('תאריכים', f'{work_start} – {work_end}')}
{_detail_row_bold('שעות מוערכות', f'{estimated_hours} שעות', alt=True)}
{_detail_row('אזור / מרחב', f'{area_name} / {region_name}')}
{_detail_row('מנהל עבודה', worker_name, True)}
</table></td></tr>'''

    badge = _badge(' &nbsp;ההזמנה אושרה ונשלחה לספק לביצוע', '#e8f5ee', '#b8dfc8', '#1a6b3c')

    nav = ""
    if lat and lng:
        nav = f'''<tr><td style="padding:16px 32px 0;text-align:center;">
<div style="font-size:12px;color:#6b7c72;margin-bottom:8px;"> ניווט לאתר העבודה</div>
<a href="https://waze.com/ul?ll={lat},{lng}&navigate=yes" style="display:inline-block;background:#33ccff;color:#0a2540;padding:11px 22px;border-radius:10px;text-decoration:none;font-weight:700;font-size:13px;margin-left:8px;"> Waze</a>
<a href="https://www.google.com/maps/dir/?api=1&destination={lat},{lng}" style="display:inline-block;background:#fff;border:1.5px solid #dde8e2;color:#1a2e21;padding:11px 22px;border-radius:10px;text-decoration:none;font-weight:700;font-size:13px;"> Google Maps</a>
</td></tr>'''

    cta = _cta_button('צפה בפרטי ההזמנה ')
    subject = f"הזמנת עבודה #{order_number} אושרה — {project_name}"

    role_tag = f'<span style="font-size:11px;background:#f4f8f5;padding:2px 8px;border-radius:20px;color:#6b7c72;">{recipient_label}</span>' if recipient_label else ''

    inner = f'''{_header()}
<tr><td style="padding:20px 32px 0;text-align:center;">
{_icon_circle('')}
<div style="font-size:22px;font-weight:800;color:#111d15;margin-bottom:6px;">הזמנת עבודה אושרה!</div>
<div style="font-size:13px;color:#6b7c72;line-height:1.6;">הזמנה <strong style="color:#1a6b3c;">#{order_number}</strong> אושרה ונשלחה לספק<br>{role_tag}</div>
</td></tr>
<tr><td style="padding:20px 32px 0;"><hr style="border:none;border-top:1px solid #e8ede9;"></td></tr>
{details}{badge}{nav}{cta}{FOOTER}'''

    return {"subject": subject, "html": _wrap(inner)}
