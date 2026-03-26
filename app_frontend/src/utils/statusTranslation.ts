// src/utils/statusTranslation.ts
// Canonical status translations — case-insensitive lookup

export const WORKLOG_STATUS: Record<string, string> = {
  PENDING:   'ממתין',
  SUBMITTED: 'הוגש',
  APPROVED:  'אושר',
  REJECTED:  'נדחה',
  INVOICED:  'הופק חשבון',
  CANCELLED: 'בוטל',
};

export const PROJECT_STATUS: Record<string, string> = {
  PLANNING:  'תכנון',
  ACTIVE:    'פעיל',
  ON_HOLD:   'מושהה',
  COMPLETED: 'הושלם',
  CANCELLED: 'בוטל',
};

export const WORK_ORDER_STATUS: Record<string, string> = {
  PENDING:          'ממתין',
  DISTRIBUTING:     'בהפצה לספקים',
  SUPPLIER_ACCEPTED_PENDING_COORDINATOR: 'ספק אישר — ממתין למתאם',
  APPROVED_AND_SENT:'אושר ונשלח',
  COMPLETED:        'הושלם',
  REJECTED:         'נדחה',
  CANCELLED:        'בוטל',
  EXPIRED:          'פג תוקף',
  STOPPED:          'הופסק',
};

export const INVOICE_STATUS: Record<string, string> = {
  DRAFT:     'טיוטה',
  APPROVED:  'מאושר',
  SENT:      'נשלח',
  PAID:      'שולם',
  CANCELLED: 'בוטל',
};

export const PRIORITY: Record<string, string> = {
  LOW:    'נמוכה',
  MEDIUM: 'בינונית',
  HIGH:   'גבוהה',
  URGENT: 'דחוף',
};

function _lookup(map: Record<string, string>, status: string): string {
  if (!status) return status;
  return map[status.toUpperCase()] || map[status] || status;
}

export const translateWorklogStatus = (status: string): string => _lookup(WORKLOG_STATUS, status);
export const translateProjectStatus = (status: string): string => _lookup(PROJECT_STATUS, status);
export const translateWorkOrderStatus = (status: string): string => _lookup(WORK_ORDER_STATUS, status);
export const translateInvoiceStatus = (status: string): string => _lookup(INVOICE_STATUS, status);

export const translateStatus = (status: string, type: 'worklog' | 'project' | 'work_order' | 'invoice' = 'worklog'): string => {
  switch (type) {
    case 'worklog':    return translateWorklogStatus(status);
    case 'project':    return translateProjectStatus(status);
    case 'work_order': return translateWorkOrderStatus(status);
    case 'invoice':    return translateInvoiceStatus(status);
    default:           return status;
  }
};

export const getStatusColor = (status: string): string => {
  const upper = (status || '').toUpperCase();
  if (['APPROVED', 'APPROVED_AND_SENT', 'COMPLETED', 'ACTIVE', 'PAID'].includes(upper))
    return 'bg-green-100 text-green-800 border-green-200';
  if (['SUBMITTED', 'DISTRIBUTING', 'SENT', 'SUPPLIER_ACCEPTED_PENDING_COORDINATOR'].includes(upper))
    return 'bg-blue-100 text-blue-800 border-blue-200';
  if (['PENDING', 'DRAFT', 'ON_HOLD'].includes(upper))
    return 'bg-yellow-100 text-yellow-800 border-yellow-200';
  if (['REJECTED', 'CANCELLED', 'EXPIRED', 'STOPPED'].includes(upper))
    return 'bg-red-100 text-red-800 border-red-200';
  return 'bg-gray-100 text-gray-600 border-gray-200';
};

export const StatusBadge = ({ status, type = 'worklog' }: { status: string; type?: 'worklog' | 'project' | 'work_order' | 'invoice' }) => {
  const translatedStatus = translateStatus(status, type);
  const colorClass = getStatusColor(status);
  return `<span class="px-2.5 py-1 text-xs font-medium rounded-full border ${colorClass}">${translatedStatus}</span>`;
};

export default {
  translateWorklogStatus,
  translateProjectStatus,
  translateWorkOrderStatus,
  translateInvoiceStatus,
  translateStatus,
  getStatusColor,
  StatusBadge,
};
