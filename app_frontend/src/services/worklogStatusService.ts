// src/services/worklogStatusService.ts
// שירות לניהול סטטוסים של דיווחי עבודה

export type WorkLogStatus = 'draft' | 'submitted' | 'approved' | 'rejected' | 'invoiced';

export interface WorkLogStatusInfo {
  status: WorkLogStatus;
  label: string;
  color: string;
  icon?: string;
}

class WorkLogStatusService {
  getStatusInfo(status: WorkLogStatus): WorkLogStatusInfo {
    const statusMap: Record<WorkLogStatus, WorkLogStatusInfo> = {
      draft: {
        status: 'draft',
        label: 'טיוטה',
        color: 'bg-blue-100 text-blue-800',
        icon: '📝'
      },
      submitted: {
        status: 'submitted',
        label: 'הוגש',
        color: 'bg-yellow-100 text-yellow-800',
        icon: '📤'
      },
      approved: {
        status: 'approved',
        label: 'אושר',
        color: 'bg-green-100 text-green-800',
        icon: '✅'
      },
      rejected: {
        status: 'rejected',
        label: 'נדחה',
        color: 'bg-red-100 text-red-800',
        icon: '❌'
      },
      invoiced: {
        status: 'invoiced',
        label: 'חויב',
        color: 'bg-purple-100 text-purple-800',
        icon: '💰'
      }
    };

    return statusMap[status] || statusMap.draft;
  }

  getAllStatuses(): WorkLogStatusInfo[] {
    return [
      this.getStatusInfo('draft'),
      this.getStatusInfo('submitted'),
      this.getStatusInfo('approved'),
      this.getStatusInfo('rejected'),
      this.getStatusInfo('invoiced')
    ];
  }

  canTransition(from: WorkLogStatus, to: WorkLogStatus): boolean {
    const transitions: Record<WorkLogStatus, WorkLogStatus[]> = {
      draft: ['submitted'],
      submitted: ['approved', 'rejected'],
      approved: ['invoiced'],
      rejected: ['draft', 'submitted'],
      invoiced: []
    };

    return transitions[from]?.includes(to) || false;
  }
}

const worklogStatusService = new WorkLogStatusService();
export default worklogStatusService;













