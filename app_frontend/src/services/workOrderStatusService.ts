// src/services/workOrderStatusService.ts
// שירות לניהול סטטוסים של הזמנות עבודה

export type WorkOrderStatus = 'pending' | 'approved' | 'in_progress' | 'completed' | 'cancelled';
export type WorkOrderPriority = 'low' | 'medium' | 'high';

export interface WorkOrderStatusInfo {
  status: WorkOrderStatus;
  label: string;
  color: string;
  icon?: string;
}

export interface WorkOrderPriorityInfo {
  priority: WorkOrderPriority;
  label: string;
  color: string;
  icon?: string;
}

class WorkOrderStatusService {
  getStatusInfo(status: WorkOrderStatus): WorkOrderStatusInfo {
    const statusMap: Record<WorkOrderStatus, WorkOrderStatusInfo> = {
      pending: {
        status: 'pending',
        label: 'ממתין לאישור',
        color: 'bg-yellow-100 text-yellow-800',
        icon: '⏳'
      },
      approved: {
        status: 'approved',
        label: 'אושר',
        color: 'bg-blue-100 text-blue-800',
        icon: '✅'
      },
      in_progress: {
        status: 'in_progress',
        label: 'בביצוע',
        color: 'bg-green-100 text-green-800',
        icon: '🔄'
      },
      completed: {
        status: 'completed',
        label: 'הושלם',
        color: 'bg-gray-100 text-gray-800',
        icon: '✔️'
      },
      cancelled: {
        status: 'cancelled',
        label: 'בוטל',
        color: 'bg-red-100 text-red-800',
        icon: '❌'
      }
    };

    return statusMap[status] || statusMap.pending;
  }

  getPriorityInfo(priority: WorkOrderPriority): WorkOrderPriorityInfo {
    const priorityMap: Record<WorkOrderPriority, WorkOrderPriorityInfo> = {
      low: {
        priority: 'low',
        label: 'נמוכה',
        color: 'bg-green-100 text-green-800',
        icon: '⬇️'
      },
      medium: {
        priority: 'medium',
        label: 'בינונית',
        color: 'bg-yellow-100 text-yellow-800',
        icon: '➡️'
      },
      high: {
        priority: 'high',
        label: 'גבוהה',
        color: 'bg-red-100 text-red-800',
        icon: '⬆️'
      }
    };

    return priorityMap[priority] || priorityMap.medium;
  }

  getAllStatuses(): WorkOrderStatusInfo[] {
    return [
      this.getStatusInfo('pending'),
      this.getStatusInfo('approved'),
      this.getStatusInfo('in_progress'),
      this.getStatusInfo('completed'),
      this.getStatusInfo('cancelled')
    ];
  }

  getAllPriorities(): WorkOrderPriorityInfo[] {
    return [
      this.getPriorityInfo('low'),
      this.getPriorityInfo('medium'),
      this.getPriorityInfo('high')
    ];
  }

  canTransition(from: WorkOrderStatus, to: WorkOrderStatus): boolean {
    const transitions: Record<WorkOrderStatus, WorkOrderStatus[]> = {
      pending: ['approved', 'cancelled'],
      approved: ['in_progress', 'cancelled'],
      in_progress: ['completed', 'cancelled'],
      completed: [],
      cancelled: []
    };

    return transitions[from]?.includes(to) || false;
  }
}

const workOrderStatusService = new WorkOrderStatusService();
export default workOrderStatusService;













