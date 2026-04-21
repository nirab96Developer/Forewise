// src/strings/activity.ts
//
// Single source of truth for activity-log action labels.
//
// The backend emits actions in three styles, all of which we accept:
//   - dotted lowercase  : 'work_order.created'      (preferred, see activity_logger.py)
//   - flat lowercase    : 'user_login', 'password_changed'
//   - SCREAMING_SNAKE   : 'WORK_ORDER_DELETED', 'SUSPEND'
//
// Lookup is normalised in `getActivityLabel()` (./index.ts) — every variant
// resolves to the same Hebrew label.

export const ACTIVITY_LABELS: Record<string, string> = {
  // ─── User / Auth ──────────────────────────────────────────────────────
  'user.login':              'כניסה למערכת',
  'user.logout':             'יציאה מהמערכת',
  'user.otp_verified':       'אימות דו-שלבי הצליח',
  'user.password_changed':   'שינוי סיסמה',
  'user.account_locked':     'החשבון ננעל',
  'user.account_unlocked':   'החשבון שוחרר',
  'user.suspended':          'משתמש הושעה',
  'user.reactivated':        'משתמש הופעל מחדש',
  'user.role_changed':       'שינוי תפקיד',
  'user.created':            'משתמש נוצר',
  'user.deleted':            'משתמש נמחק',

  // ─── Work Order ───────────────────────────────────────────────────────
  'work_order.created':           'הזמנת עבודה נוצרה',
  'work_order.updated':           'הזמנת עבודה עודכנה',
  'work_order.approved':          'הזמנת עבודה אושרה',
  'work_order.rejected':          'הזמנת עבודה נדחתה',
  'work_order.cancelled':         'הזמנת עבודה בוטלה',
  'work_order.deleted':           'הזמנת עבודה נמחקה',
  'work_order.restored':          'הזמנת עבודה שוחזרה',
  'work_order.started':           'הזמנת עבודה החלה',
  'work_order.completed':         'הזמנת עבודה הושלמה',
  'work_order.sent_to_supplier':  'הזמנה נשלחה לספק',
  'work_order.supplier_changed':  'ספק שונה בהזמנה',
  'work_order.expired':           'הזמנה פגה (טיימר ספק)',
  'work_order.stopped':           'הזמנה הופסקה',

  // ─── Worklog ──────────────────────────────────────────────────────────
  'worklog.created':              'דיווח שעות נוצר',
  'worklog.submitted':            'דיווח נשלח לאישור',
  'worklog.approved':             'דיווח אושר',
  'worklog.rejected':             'דיווח נדחה',
  'worklog.cancelled':            'דיווח בוטל',
  'worklog.assigned_to_invoice':  'דיווח שויך לחשבונית',

  // ─── Equipment ────────────────────────────────────────────────────────
  'equipment.scanned':                 'ציוד נסרק',
  'equipment.released':                'ציוד שוחרר מהזמנה',
  'equipment.transfer_approved':       'אישור העברת כלי בין הזמנות',
  'equipment.type_change_pending':     'בקשה לשינוי סוג כלי — ממתין',
  'equipment.type_change_approved':    'שינוי סוג כלי אושר',
  'equipment.mismatch_detected':       'אי-התאמה בסריקת כלי',
  'equipment.created':                 'ציוד נוצר',
  'equipment.updated':                 'ציוד עודכן',

  // ─── Supplier ─────────────────────────────────────────────────────────
  'supplier.confirmed':            'ספק אישר הזמנה',
  'supplier.declined':             'ספק דחה הזמנה',
  'supplier.landing_page_sent':    'נשלח קישור לפורטל ספק',
  'supplier.timer_started':        'טיימר תגובת ספק החל',
  'supplier.timer_expired':        'תפוגת קישור ספק',
  'supplier.constraint_rejected':  'ספק דחה (אילוץ)',

  // ─── Invoice ──────────────────────────────────────────────────────────
  'invoice.created':            'חשבונית נוצרה',
  'invoice.approved':           'חשבונית אושרה',
  'invoice.sent_to_supplier':   'חשבונית נשלחה לספק',
  'invoice.paid':               'חשבונית שולמה',
  'invoice.cancelled':          'חשבונית בוטלה',

  // ─── Project assignments ──────────────────────────────────────────────
  'project_assignment.created':    'שיוך לפרויקט נוצר',
  'project_assignment.updated':    'שיוך לפרויקט עודכן',
  'project_assignment.removed':    'שיוך לפרויקט הוסר',
  'project_assignment.completed':  'שיוך לפרויקט הושלם',
  'project.bulk_assignment':       'שיוך מרוכז לפרויקט',
  'project.assignments_transferred': 'שיוכים הועברו',

  // ─── Budget ───────────────────────────────────────────────────────────
  'budget.frozen':           'תקציב הוקפא',
  'budget.released':         'תקציב שוחרר',
  'balance_release.created': 'בקשת שחרור יתרה',
  'balance_release.approved':'שחרור יתרה אושר',
  'balance_release.rejected':'שחרור יתרה נדחה',

  // ─── Support ticket ───────────────────────────────────────────────────
  'support_ticket.created':         'פנייה חדשה נפתחה',
  'support_ticket.replied':         'תגובה חדשה בפנייה',
  'support_ticket.status_changed':  'סטטוס פנייה השתנה',
  'support_ticket.resolved':        'פנייה נסגרה',
};

/**
 * Legacy / SCREAMING_SNAKE aliases that still occasionally show up in older
 * activity_log rows. Maps each variant to the canonical key in ACTIVITY_LABELS
 * above so we have a single Hebrew translation per concept.
 */
export const ACTIVITY_ALIASES: Record<string, string> = {
  // Old underscore-flat → dotted
  user_login:                   'user.login',
  user_logout:                  'user.logout',
  password_changed:             'user.password_changed',
  account_locked:               'user.account_locked',
  account_unlocked:             'user.account_unlocked',
  '2fa verification successful':'user.otp_verified',
  '2FA verification successful':'user.otp_verified',
  // SCREAMING_SNAKE → dotted
  WORK_ORDER_CREATED:   'work_order.created',
  WORK_ORDER_APPROVED:  'work_order.approved',
  WORK_ORDER_REJECTED:  'work_order.rejected',
  WORK_ORDER_DELETED:   'work_order.deleted',
  WORK_ORDER_RESTORED:  'work_order.restored',
  WORK_ORDER_CANCELLED: 'work_order.cancelled',
  STATUS_CHANGE_WORK_ORDER: 'work_order.updated',
  STATUS_CHANGE_WORKLOG:    'worklog.created',
  INVOICE_CREATED:      'invoice.created',
  BUDGET_FROZEN:        'budget.frozen',
  BUDGET_RELEASED:      'budget.released',
  SUSPEND:              'user.suspended',
  CHANGE_ROLE:          'user.role_changed',
  // Project assignments
  project_assignment_created:    'project_assignment.created',
  project_assignment_updated:    'project_assignment.updated',
  project_assignment_removed:    'project_assignment.removed',
  project_assignment_completed:  'project_assignment.completed',
  project_bulk_assignment:       'project.bulk_assignment',
  assignments_transferred:       'project.assignments_transferred',
  balance_release:               'balance_release.created',
};
