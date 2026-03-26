// src/services/worklogStatusService.ts
// Canonical WL statuses — must match backend app/core/enums.py WorklogStatus

export type WorkLogStatus = 'PENDING' | 'SUBMITTED' | 'APPROVED' | 'REJECTED' | 'INVOICED';

export interface WorkLogStatusInfo {
  status: string;
  label: string;
  color: string;
  icon?: string;
}

const STATUS_MAP: Record<string, WorkLogStatusInfo> = {
  PENDING:   { status: 'PENDING',   label: 'ממתין',       color: 'bg-yellow-100 text-yellow-800', icon: '⏳' },
  SUBMITTED: { status: 'SUBMITTED', label: 'הוגש',        color: 'bg-blue-100 text-blue-800',    icon: '📤' },
  APPROVED:  { status: 'APPROVED',  label: 'אושר',        color: 'bg-green-100 text-green-800',  icon: '✅' },
  REJECTED:  { status: 'REJECTED',  label: 'נדחה',        color: 'bg-red-100 text-red-800',      icon: '❌' },
  INVOICED:  { status: 'INVOICED',  label: 'הופק חשבון', color: 'bg-purple-100 text-purple-800', icon: '💰' },
};

const DEFAULT_INFO: WorkLogStatusInfo = { status: '?', label: 'לא ידוע', color: 'bg-gray-100 text-gray-600' };

class WorkLogStatusService {
  getStatusInfo(status: string): WorkLogStatusInfo {
    const key = (status || '').toUpperCase();
    return STATUS_MAP[key] || { ...DEFAULT_INFO, status: key, label: key };
  }

  getAllStatuses(): WorkLogStatusInfo[] {
    return Object.values(STATUS_MAP);
  }

  canTransition(from: string, to: string): boolean {
    const transitions: Record<string, string[]> = {
      PENDING:   ['SUBMITTED'],
      SUBMITTED: ['APPROVED', 'REJECTED'],
      APPROVED:  ['INVOICED'],
      REJECTED:  ['SUBMITTED'],
      INVOICED:  [],
    };
    const key = (from || '').toUpperCase();
    return transitions[key]?.includes((to || '').toUpperCase()) || false;
  }
}

const worklogStatusService = new WorkLogStatusService();
export default worklogStatusService;
