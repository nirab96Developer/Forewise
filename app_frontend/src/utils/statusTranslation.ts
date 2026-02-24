// src/utils/statusTranslation.ts
// תרגום סטטוסים לעברית - תצוגה בלבד

// סטטוסי דיווח שעות
export const WORKLOG_STATUS: Record<string, string> = {
  'draft': 'טיוטה',
  'DRAFT': 'טיוטה',
  'submitted': 'נשלח',
  'SUBMITTED': 'נשלח',
  'pending': 'ממתין לאישור',
  'PENDING': 'ממתין לאישור',
  'approved': 'אושר',
  'APPROVED': 'אושר',
  'rejected': 'נדחה',
  'REJECTED': 'נדחה',
  'cancelled': 'בוטל',
  'CANCELLED': 'בוטל',
};

// סטטוסי פרויקט
export const PROJECT_STATUS: Record<string, string> = {
  'planning': 'תכנון',
  'PLANNING': 'תכנון',
  'active': 'פעיל',
  'ACTIVE': 'פעיל',
  'on_hold': 'מושהה',
  'ON_HOLD': 'מושהה',
  'completed': 'הושלם',
  'COMPLETED': 'הושלם',
  'cancelled': 'בוטל',
  'CANCELLED': 'בוטל',
};

// סטטוסי הזמנת עבודה
export const WORK_ORDER_STATUS: Record<string, string> = {
  'draft': 'טיוטה',
  'DRAFT': 'טיוטה',
  'pending': 'ממתין',
  'PENDING': 'ממתין',
  'sent': 'נשלח לספק',
  'SENT': 'נשלח לספק',
  'confirmed': 'אושר',
  'CONFIRMED': 'אושר',
  'rejected': 'נדחה',
  'REJECTED': 'נדחה',
  'in_progress': 'בביצוע',
  'IN_PROGRESS': 'בביצוע',
  'completed': 'הושלם',
  'COMPLETED': 'הושלם',
  'cancelled': 'בוטל',
  'CANCELLED': 'בוטל',
  'expired': 'פג תוקף',
  'EXPIRED': 'פג תוקף',
};

// סטטוסי חשבונית
export const INVOICE_STATUS: Record<string, string> = {
  'draft': 'טיוטה',
  'DRAFT': 'טיוטה',
  'pending': 'ממתין לאישור',
  'PENDING': 'ממתין לאישור',
  'approved': 'אושר',
  'APPROVED': 'אושר',
  'paid': 'שולם',
  'PAID': 'שולם',
  'cancelled': 'בוטל',
  'CANCELLED': 'בוטל',
};

// עדיפות
export const PRIORITY: Record<string, string> = {
  'low': 'נמוכה',
  'LOW': 'נמוכה',
  'medium': 'בינונית',
  'MEDIUM': 'בינונית',
  'high': 'גבוהה',
  'HIGH': 'גבוהה',
  'urgent': 'דחוף',
  'URGENT': 'דחוף',
};

// פונקציות עזר
export const translateWorklogStatus = (status: string): string => {
  return WORKLOG_STATUS[status] || status;
};

export const translateProjectStatus = (status: string): string => {
  return PROJECT_STATUS[status] || status;
};

export const translateWorkOrderStatus = (status: string): string => {
  return WORK_ORDER_STATUS[status] || status;
};

export const translateInvoiceStatus = (status: string): string => {
  return INVOICE_STATUS[status] || status;
};

export const translatePriority = (priority: string): string => {
  return PRIORITY[priority] || priority;
};

// פונקציה כללית לתרגום סטטוס
export const translateStatus = (status: string, type: 'worklog' | 'project' | 'work_order' | 'invoice' = 'worklog'): string => {
  switch (type) {
    case 'worklog':
      return translateWorklogStatus(status);
    case 'project':
      return translateProjectStatus(status);
    case 'work_order':
      return translateWorkOrderStatus(status);
    case 'invoice':
      return translateInvoiceStatus(status);
    default:
      return status;
  }
};

// צבעי סטטוס
export const getStatusColor = (status: string): string => {
  const lowerStatus = status?.toLowerCase() || '';
  
  // ירוק - מאושר/הושלם/פעיל
  if (['approved', 'completed', 'active', 'paid', 'confirmed'].includes(lowerStatus)) {
    return 'bg-green-100 text-green-700 border-green-200';
  }
  
  // כחול - בתהליך
  if (['submitted', 'sent', 'in_progress', 'planning'].includes(lowerStatus)) {
    return 'bg-blue-100 text-blue-700 border-blue-200';
  }
  
  // צהוב/כתום - ממתין
  if (['pending', 'draft', 'on_hold'].includes(lowerStatus)) {
    return 'bg-yellow-100 text-yellow-700 border-yellow-200';
  }
  
  // אדום - נדחה/בוטל/פג תוקף
  if (['rejected', 'cancelled', 'expired'].includes(lowerStatus)) {
    return 'bg-red-100 text-red-700 border-red-200';
  }
  
  // ברירת מחדל - אפור
  return 'bg-gray-100 text-gray-700 border-gray-200';
};

// קומפוננטת Badge לסטטוס
export const StatusBadge = ({ status, type = 'worklog' }: { status: string; type?: 'worklog' | 'project' | 'work_order' | 'invoice' }) => {
  const translatedStatus = translateStatus(status, type);
  const colorClass = getStatusColor(status);
  
  return `<span class="px-2.5 py-1 text-xs font-medium rounded-full border ${colorClass}">${translatedStatus}</span>`;
};

export default {
  WORKLOG_STATUS,
  PROJECT_STATUS,
  WORK_ORDER_STATUS,
  INVOICE_STATUS,
  PRIORITY,
  translateWorklogStatus,
  translateProjectStatus,
  translateWorkOrderStatus,
  translateInvoiceStatus,
  translatePriority,
  translateStatus,
  getStatusColor,
};
