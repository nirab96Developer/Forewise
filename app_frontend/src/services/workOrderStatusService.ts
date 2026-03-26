// src/services/workOrderStatusService.ts
// Canonical WO statuses — must match backend app/core/enums.py WorkOrderStatus

export type WorkOrderStatus =
  | 'PENDING'
  | 'DISTRIBUTING'
  | 'SUPPLIER_ACCEPTED_PENDING_COORDINATOR'
  | 'APPROVED_AND_SENT'
  | 'COMPLETED'
  | 'REJECTED'
  | 'CANCELLED'
  | 'EXPIRED'
  | 'STOPPED';

export interface WorkOrderStatusInfo {
  status: string;
  label: string;
  color: string;
  icon?: string;
}

const STATUS_MAP: Record<string, WorkOrderStatusInfo> = {
PENDING: { status: 'PENDING', label: 'ממתין', color: 'bg-yellow-100 text-yellow-800', icon: '' },
DISTRIBUTING: { status: 'DISTRIBUTING', label: 'בהפצה לספקים', color: 'bg-yellow-100 text-yellow-800', icon: '' },
SUPPLIER_ACCEPTED_PENDING_COORDINATOR: { status: 'SUPPLIER_ACCEPTED_PENDING_COORDINATOR', label: 'ספק אישר — ממתין למתאם', color: 'bg-blue-100 text-blue-800', icon: '' },
APPROVED_AND_SENT:{ status: 'APPROVED_AND_SENT', label: 'אושר ונשלח', color: 'bg-green-100 text-green-800', icon: '' },
COMPLETED: { status: 'COMPLETED', label: 'הושלם', color: 'bg-gray-100 text-gray-800', icon: '' },
REJECTED: { status: 'REJECTED', label: 'נדחה', color: 'bg-red-100 text-red-800', icon: '' },
CANCELLED: { status: 'CANCELLED', label: 'בוטל', color: 'bg-red-100 text-red-800', icon: '' },
EXPIRED: { status: 'EXPIRED', label: 'פג תוקף', color: 'bg-gray-100 text-gray-600', icon: '' },
STOPPED: { status: 'STOPPED', label: 'הופסק', color: 'bg-red-100 text-red-800', icon: '' },
};

const DEFAULT_INFO: WorkOrderStatusInfo = { status: '?', label: 'לא ידוע', color: 'bg-gray-100 text-gray-600' };

class WorkOrderStatusService {
  getStatusInfo(status: string): WorkOrderStatusInfo {
    const key = (status || '').toUpperCase();
    return STATUS_MAP[key] || { ...DEFAULT_INFO, status: key, label: key };
  }

  getAllStatuses(): WorkOrderStatusInfo[] {
    return Object.values(STATUS_MAP);
  }

  getStatusColor(status: string): string {
    return this.getStatusInfo(status).color;
  }

  getStatusLabel(status: string): string {
    return this.getStatusInfo(status).label;
  }
}

const workOrderStatusService = new WorkOrderStatusService();
export default workOrderStatusService;
