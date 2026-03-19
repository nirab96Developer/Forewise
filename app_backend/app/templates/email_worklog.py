"""HTML email templates for worklog lifecycle — 3 stages."""


def _base_template(content: str, footer_text: str = "") -> str:
    return f"""<!DOCTYPE html>
<html dir="rtl" lang="he">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f4f7f5;font-family:'Segoe UI',Tahoma,Arial,sans-serif">
<div style="max-width:560px;margin:20px auto;background:#fff;border-radius:16px;overflow:hidden;border:1px solid #e0e8e2">
  <div style="background:linear-gradient(135deg,#2e7d32,#43a047);padding:20px 28px;text-align:center">
    <div style="font-size:22px;font-weight:900;color:#fff;letter-spacing:1px">Forewise</div>
    <div style="font-size:11px;color:rgba(255,255,255,0.7);margin-top:2px">מערכת ניהול יערות</div>
  </div>
  <div style="padding:28px">
    {content}
  </div>
  <div style="padding:16px 28px;background:#f8faf8;border-top:1px solid #e8ede9;text-align:center;font-size:11px;color:#999">
    {footer_text or 'הודעה אוטומטית ממערכת Forewise — אין להשיב למייל זה'}
  </div>
</div>
</body>
</html>"""


def _badge(text: str, bg: str, color: str) -> str:
    return f'<span style="display:inline-block;padding:4px 14px;border-radius:20px;font-size:12px;font-weight:700;background:{bg};color:{color}">{text}</span>'


def _row(label: str, value: str) -> str:
    return f"""<tr>
      <td style="padding:6px 0;font-size:13px;color:#888;width:130px">{label}</td>
      <td style="padding:6px 0;font-size:13px;color:#333;font-weight:600">{value}</td>
    </tr>"""


def _cost_block(hours_cost: float, overnight_cost: float, total_before_vat: float, total_with_vat: float) -> str:
    return f"""
    <div style="background:#f0faf3;border:1px solid #c8e6c9;border-radius:12px;padding:16px;margin:16px 0">
      <div style="font-size:13px;font-weight:700;color:#2e7d32;margin-bottom:10px">פירוט עלות</div>
      <table style="width:100%;border-collapse:collapse">
        {_row('עלות שעות', f'₪{hours_cost:,.2f}')}
        {_row('לינת שטח', f'₪{overnight_cost:,.2f}') if overnight_cost > 0 else ''}
        <tr><td colspan="2" style="border-top:1px solid #c8e6c9;padding-top:8px"></td></tr>
        {_row('לפני מע"מ', f'₪{total_before_vat:,.2f}')}
        <tr>
          <td style="padding:6px 0;font-size:15px;color:#1b5e20;font-weight:900">כולל מע"מ</td>
          <td style="padding:6px 0;font-size:18px;color:#1b5e20;font-weight:900">₪{total_with_vat:,.2f}</td>
        </tr>
      </table>
    </div>"""


def stage1_pending(
    report_number: str,
    project_name: str,
    supplier_name: str,
    equipment_type: str,
    work_date: str,
    total_hours: float,
    report_type: str,
    worker_name: str,
    recipient_role: str,
) -> dict:
    """Stage 1: Worklog saved → PENDING — no cost yet."""
    
    badge = _badge("⏳ ממתין לאישור", "#FFF8E1", "#e65100")
    type_label = "תקן" if report_type == "standard" else "לא תקן"
    
    details = f"""<table style="width:100%;border-collapse:collapse">
      {_row('מספר דיווח', report_number)}
      {_row('פרויקט', project_name)}
      {_row('ספק', supplier_name)}
      {_row('סוג ציוד', equipment_type)}
      {_row('תאריך עבודה', work_date)}
      {_row('סוג דיווח', type_label)}
      {_row('שעות', str(total_hours))}
      {_row('מדווח', worker_name)}
    </table>"""

    if recipient_role == "accountant":
        subject = f"דיווח חדש ממתין לאישורך — {report_number}"
        body = f"""
          <h2 style="font-size:18px;color:#333;margin:0 0 8px">דיווח שעות חדש ממתין לאישורך</h2>
          <div style="margin:12px 0">{badge}</div>
          {details}
          <div style="text-align:center;margin-top:20px">
            <a href="https://forewise.co/accountant-inbox" style="display:inline-block;padding:12px 32px;background:#2e7d32;color:#fff;text-decoration:none;border-radius:12px;font-weight:700;font-size:14px">אשר דיווח</a>
          </div>"""
    elif recipient_role == "supplier":
        subject = f"אסמכתא — דיווח שעות התקבל {report_number}"
        body = f"""
          <h2 style="font-size:18px;color:#333;margin:0 0 8px">דיווח שעות התקבל</h2>
          <p style="font-size:13px;color:#666">הדיווח ממתין לאישור מנהלת חשבונות. תקבל עדכון לאחר האישור.</p>
          <div style="margin:12px 0">{badge}</div>
          {details}"""
    else:
        subject = f"דיווח שעות נשמר — {report_number}"
        body = f"""
          <h2 style="font-size:18px;color:#333;margin:0 0 8px">הדיווח נשמר בהצלחה</h2>
          <div style="margin:12px 0">{badge}</div>
          {details}"""

    return {"subject": subject, "html": _base_template(body)}


def stage2_approved(
    report_number: str,
    project_name: str,
    supplier_name: str,
    equipment_type: str,
    work_date: str,
    total_hours: float,
    hourly_rate: float,
    overnight_nights: int,
    overnight_rate: float,
    worker_name: str,
    recipient_role: str,
) -> dict:
    """Stage 2: Accountant approved → APPROVED — with full cost."""
    
    badge = _badge("✅ אושר — ממתין להפקת חשבונית", "#E8F5E9", "#1b5e20")
    
    hours_cost = total_hours * hourly_rate
    overnight_cost = overnight_nights * overnight_rate if overnight_nights else 0
    total_before_vat = hours_cost + overnight_cost
    total_with_vat = round(total_before_vat * 1.17, 2)

    details = f"""<table style="width:100%;border-collapse:collapse">
      {_row('מספר דיווח', report_number)}
      {_row('פרויקט', project_name)}
      {_row('ספק', supplier_name)}
      {_row('סוג ציוד', equipment_type)}
      {_row('תאריך', work_date)}
      {_row('שעות', str(total_hours))}
      {_row('תעריף', f'₪{hourly_rate:,.0f}/שעה')}
    </table>"""

    cost = _cost_block(hours_cost, overnight_cost, total_before_vat, total_with_vat)

    if recipient_role == "supplier":
        subject = f"✅ אסמכתא מאושרת — {report_number}"
        body = f"""
          <h2 style="font-size:18px;color:#1b5e20;margin:0 0 8px">דיווח שעות אושר</h2>
          <p style="font-size:13px;color:#666">זוהי האסמכתא הרשמית שלך. הדיווח ממתין להפקת חשבונית.</p>
          <div style="margin:12px 0">{badge}</div>
          {details}
          {cost}"""
    else:
        subject = f"דיווח אושר — {report_number}"
        body = f"""
          <h2 style="font-size:18px;color:#1b5e20;margin:0 0 8px">דיווח שעות אושר</h2>
          <div style="margin:12px 0">{badge}</div>
          {details}
          {cost}"""

    return {"subject": subject, "html": _base_template(body)}


def stage3_invoiced(
    invoice_number: str,
    invoice_date: str,
    supplier_name: str,
    project_name: str,
    worklogs_summary: list,
    total_amount: float,
    recipient_role: str,
) -> dict:
    """Stage 3: Invoice created → INVOICED."""

    badge = _badge("📄 הוצא לחשבונית", "#E3F2FD", "#1565c0")

    rows = ""
    for wl in worklogs_summary:
        rows += f"""<tr>
          <td style="padding:6px 8px;font-size:12px;border-bottom:1px solid #eee">{wl.get('report_number','')}</td>
          <td style="padding:6px 8px;font-size:12px;border-bottom:1px solid #eee">{wl.get('work_date','')}</td>
          <td style="padding:6px 8px;font-size:12px;border-bottom:1px solid #eee">{wl.get('hours',0)} שעות</td>
          <td style="padding:6px 8px;font-size:12px;border-bottom:1px solid #eee">₪{wl.get('amount',0):,.2f}</td>
        </tr>"""

    table = f"""
    <table style="width:100%;border-collapse:collapse;margin:16px 0">
      <thead>
        <tr style="background:#f5f5f5">
          <th style="padding:8px;font-size:12px;text-align:right;color:#666">דיווח</th>
          <th style="padding:8px;font-size:12px;text-align:right;color:#666">תאריך</th>
          <th style="padding:8px;font-size:12px;text-align:right;color:#666">שעות</th>
          <th style="padding:8px;font-size:12px;text-align:right;color:#666">סכום</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
      <tfoot>
        <tr style="background:#e8f5e9">
          <td colspan="3" style="padding:10px 8px;font-size:14px;font-weight:900;color:#1b5e20">סה"כ לתשלום</td>
          <td style="padding:10px 8px;font-size:18px;font-weight:900;color:#1b5e20">₪{total_amount:,.2f}</td>
        </tr>
      </tfoot>
    </table>"""

    details = f"""<table style="width:100%;border-collapse:collapse">
      {_row('מספר חשבונית', invoice_number)}
      {_row('תאריך הפקה', invoice_date)}
      {_row('ספק', supplier_name)}
      {_row('פרויקט', project_name)}
    </table>"""

    if recipient_role == "supplier":
        subject = f"📄 חשבונית הופקה — {invoice_number}"
        body = f"""
          <h2 style="font-size:18px;color:#1565c0;margin:0 0 8px">חשבונית הופקה</h2>
          <div style="margin:12px 0">{badge}</div>
          {details}
          <h3 style="font-size:14px;color:#333;margin:20px 0 8px">פירוט דיווחים</h3>
          {table}"""
    else:
        subject = f"חשבונית {invoice_number} הופקה בהצלחה"
        body = f"""
          <h2 style="font-size:18px;color:#1565c0;margin:0 0 8px">חשבונית הופקה</h2>
          <div style="margin:12px 0">{badge}</div>
          {details}
          {table}"""

    return {"subject": subject, "html": _base_template(body)}
