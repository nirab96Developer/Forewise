// src/strings/statuses.ts
//
// Single source of truth for every status label in the system.
// Backend stores statuses in UPPERCASE (work_orders, worklogs, invoices) or
// lowercase (equipment, project_assignments, support_tickets). Lookups are
// case-insensitive — see `getStatusLabel()` in `./index`.
//
// IMPORTANT: do NOT print raw enum values anywhere in the UI. Always go
// through getXxxStatusLabel(). The fallback is `'—'`, never the raw code.
import type { Tone } from './index';

// ─── Work Order ───────────────────────────────────────────────────────────
export const WORK_ORDER_STATUS_LABELS: Record<string, string> = {
  PENDING:                                'ממתין לשליחה',
  DISTRIBUTING:                           'בהפצה לספק',
  SUPPLIER_ACCEPTED_PENDING_COORDINATOR:  'ספק אישר — ממתין לאישור מתאם',
  APPROVED_AND_SENT:                      'אושר ונשלח',
  IN_PROGRESS:                            'בביצוע',
  ACTIVE:                                 'בביצוע', // legacy alias
  NEEDS_RE_COORDINATION:                  'דורש תיאום מחדש — סוג כלי שגוי',
  COMPLETED:                              'הושלם',
  REJECTED:                               'נדחה',
  CANCELLED:                              'בוטל',
  EXPIRED:                                'פג תוקף',
  STOPPED:                                'הופסק',
};

export const WORK_ORDER_STATUS_TONE: Record<string, Tone> = {
  PENDING:                                'warning',
  DISTRIBUTING:                           'info',
  SUPPLIER_ACCEPTED_PENDING_COORDINATOR:  'attention',
  APPROVED_AND_SENT:                      'success',
  IN_PROGRESS:                            'success',
  ACTIVE:                                 'success',
  NEEDS_RE_COORDINATION:                  'danger',
  COMPLETED:                              'neutral',
  REJECTED:                               'danger',
  CANCELLED:                              'danger',
  EXPIRED:                                'warning',
  STOPPED:                                'neutral',
};

// ─── Worklog ──────────────────────────────────────────────────────────────
export const WORKLOG_STATUS_LABELS: Record<string, string> = {
  DRAFT:     'טיוטה',
  PENDING:   'ממתין להגשה',
  SUBMITTED: 'הוגש לאישור',
  APPROVED:  'אושר',
  REJECTED:  'נדחה',
  INVOICED:  'הופק חשבון',
  CANCELLED: 'בוטל',
};

export const WORKLOG_STATUS_TONE: Record<string, Tone> = {
  DRAFT:     'neutral',
  PENDING:   'warning',
  SUBMITTED: 'info',
  APPROVED:  'success',
  REJECTED:  'danger',
  INVOICED:  'attention',
  CANCELLED: 'neutral',
};

// ─── Invoice ──────────────────────────────────────────────────────────────
export const INVOICE_STATUS_LABELS: Record<string, string> = {
  DRAFT:     'טיוטה',
  PENDING:   'ממתינה',
  APPROVED:  'מאושרת',
  SENT:      'נשלחה',
  PAID:      'שולמה',
  OVERDUE:   'באיחור',
  CANCELLED: 'בוטלה',
  VOID:      'מבוטלת',
  REJECTED:  'נדחתה',
};

export const INVOICE_STATUS_TONE: Record<string, Tone> = {
  DRAFT:     'neutral',
  PENDING:   'warning',
  APPROVED:  'info',
  SENT:      'attention',
  PAID:      'success',
  OVERDUE:   'danger',
  CANCELLED: 'neutral',
  VOID:      'neutral',
  REJECTED:  'danger',
};

// ─── Project ──────────────────────────────────────────────────────────────
// Backend currently stores `active` / `inactive` (lowercase) plus the formal
// uppercase enum below. Lookup is case-insensitive (see strings/index.ts) so
// 'inactive' resolves to 'INACTIVE' here. Without the INACTIVE entry the UI
// silently falls back to '—' for ~70% of projects.
export const PROJECT_STATUS_LABELS: Record<string, string> = {
  DRAFT:      'טיוטה',
  PLANNING:   'בתכנון',
  ACTIVE:     'פעיל',
  INACTIVE:   'לא פעיל',
  ON_HOLD:    'מושהה',
  SUSPENDED:  'מושהה',
  COMPLETED:  'הושלם',
  CANCELLED:  'בוטל',
  ARCHIVED:   'בארכיון',
};

// ─── Equipment ────────────────────────────────────────────────────────────
// (backend uses lowercase here)
export const EQUIPMENT_STATUS_LABELS: Record<string, string> = {
  AVAILABLE:      'זמין',
  ACTIVE:         'פעיל',
  IN_USE:         'בשימוש',
  BUSY:           'בשימוש',
  RESERVED:       'משוריין',
  MAINTENANCE:    'בתחזוקה',
  OUT_OF_SERVICE: 'לא תקין',
  RETIRED:        'הוצא משימוש',
  INACTIVE:       'לא פעיל',
};

// ─── Equipment Request / Approval ────────────────────────────────────────
export const EQUIPMENT_REQUEST_STATUS_LABELS: Record<string, string> = {
  PENDING:  'ממתין לאישור',
  APPROVED: 'אושר',
  REJECTED: 'נדחה',
  CANCELLED:'בוטל',
};

// ─── Budget ───────────────────────────────────────────────────────────────
// CHECK constraint on `budgets.status` (Phase 2.1) accepts:
//   DRAFT, ACTIVE, FROZEN, CLOSED, EXHAUSTED, ARCHIVED
// All six must be mapped here so a budget created in DRAFT never shows '—'.
export const BUDGET_STATUS_LABELS: Record<string, string> = {
  DRAFT:     'טיוטה',
  ACTIVE:    'פעיל',
  FROZEN:    'מוקפא',
  CLOSED:    'סגור',
  EXHAUSTED: 'מוצה',
  ARCHIVED:  'בארכיון',
};

// ─── Budget Transfer ─────────────────────────────────────────────────────
export const BUDGET_TRANSFER_STATUS_LABELS: Record<string, string> = {
  PENDING:    'ממתין לאישור',
  APPROVED:   'אושר',
  REJECTED:   'נדחה',
  COMPLETED:  'בוצע',
  CANCELLED:  'בוטל',
  IN_PROGRESS:'מתבצע',
};

// ─── Support Ticket ──────────────────────────────────────────────────────
export const SUPPORT_TICKET_STATUS_LABELS: Record<string, string> = {
  OPEN:        'פתוחה',
  IN_PROGRESS: 'בטיפול',
  PENDING:     'ממתינה',
  RESOLVED:    'טופלה',
  CLOSED:      'סגורה',
  ESCALATED:   'הוסלמה',
};

// ─── Supplier Invitation / Response ──────────────────────────────────────
export const SUPPLIER_RESPONSE_LABELS: Record<string, string> = {
  PENDING:              'ממתין לתגובה',
  WAITING:              'ממתין לתגובה',
  SENT:                 'נשלח',
  VIEWED:               'נצפה',
  ACCEPTED:             'אישר',
  CONFIRMED:            'אישר',
  DECLINED:             'דחה',
  REJECTED:             'דחה',
  CONSTRAINT_REJECTED:  'דחה (אילוץ)',
  EXPIRED:              'פג תוקף',
  TIMEOUT:              'פג תוקף',
  CANCELLED:            'בוטל',
};

// ─── Priority (work order, worklog) ──────────────────────────────────────
export const PRIORITY_LABELS: Record<string, string> = {
  URGENT: 'דחופה',
  HIGH:   'גבוהה',
  MEDIUM: 'בינונית',
  LOW:    'נמוכה',
};
