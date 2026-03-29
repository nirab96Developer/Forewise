// src/services/workOrderService.ts
import api from './api';

export interface WorkOrder {
  id: number;
  order_number?: number;
  title: string;
  description?: string;
  project_id: number;
  project_name?: string;
  supplier_id?: number;
  supplier_name?: string;
  equipment_type: string;
  work_start_date: string;
  work_end_date: string;
  status: string;
  priority: 'low' | 'medium' | 'high';
  estimated_hours?: number;
  hourly_rate?: number;
  total_amount?: number;
  frozen_amount?: number;
  created_at: string;
  updated_at?: string;
  created_by?: number;
  approved_by?: number;
  approved_at?: string;
  // Computed hours tracking
  used_hours?: number;
  remaining_hours?: number;
  days_total?: number;
  days_used?: number;
  days_remaining?: number;
}

export interface WorkOrderCreate {
  title: string;
  description?: string;
  project_id: number;
  supplier_id?: number;
  equipment_type: string;
  requested_equipment_model_id?: number;
  work_start_date: string;
  work_end_date: string;
  priority: 'low' | 'medium' | 'high';
  estimated_hours?: number;
  hourly_rate?: number;
  is_forced_selection?: boolean;
  constraint_reason_id?: number;
  constraint_notes?: string;
  requires_guard?: boolean;
  guard_days?: number;
  days?: number;
  has_overnight?: boolean;
  overnight_nights?: number;
  allocation_method?: string;
  total_amount?: number;
  frozen_amount?: number;
}

export interface WorkOrderUpdate {
  title?: string;
  description?: string;
  project_id?: number;
  supplier_id?: number;
  equipment_type?: string;
  work_start_date?: string;
  work_end_date?: string;
  status?: string;
  priority?: string;
  estimated_hours?: number;
  hourly_rate?: number;
}

export interface WorkOrderFilters {
  status?: string;
  priority?: string;
  project_id?: number;
  supplier_id?: number;
  equipment_type?: string;
  date_from?: string;
  date_to?: string;
}

export interface WorkOrderResponse {
  items: WorkOrder[];
  data?: WorkOrder[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface CalendarEvent {
  id: number;
  title: string;
  date: string;
  type: 'work_order';
  data: WorkOrder;
}

class WorkOrderService {
  private baseUrl = '/work-orders';

  async getWorkOrders(
    page: number = 1,
    pageSize: number = 20,
    filters?: WorkOrderFilters
  ): Promise<WorkOrderResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: pageSize.toString(),
    });

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }

    // DB indexes optimized - query now takes ~0.15s instead of ~45s
    const response = await api.get(`${this.baseUrl}?${params}`);
    return response.data;
  }

  async getWorkOrderById(id: number): Promise<WorkOrder> {
    const response = await api.get(`${this.baseUrl}/${id}`);
    return response.data;
  }

  async createWorkOrder(workOrder: WorkOrderCreate): Promise<WorkOrder> {
    const response = await api.post(this.baseUrl, workOrder);
    return response.data;
  }

  async updateWorkOrder(id: number, workOrder: WorkOrderUpdate): Promise<WorkOrder> {
    const response = await api.patch(`${this.baseUrl}/${id}`, workOrder);
    return response.data;
  }

  async deleteWorkOrder(id: number): Promise<void> {
    await api.delete(`${this.baseUrl}/${id}`);
  }

  async approveWorkOrder(id: number): Promise<WorkOrder> {
    const response = await api.patch(`${this.baseUrl}/${id}/approve`);
    return response.data;
  }

  async rejectWorkOrder(id: number, reason?: string): Promise<WorkOrder> {
    const response = await api.patch(`${this.baseUrl}/${id}/reject`, { reason });
    return response.data;
  }

  async startWorkOrder(id: number): Promise<WorkOrder> {
    const response = await api.patch(`${this.baseUrl}/${id}/start`);
    return response.data;
  }

  async completeWorkOrder(id: number): Promise<WorkOrder> {
    const response = await api.patch(`${this.baseUrl}/${id}/complete`);
    return response.data;
  }

  async getWorkOrdersForCalendar(
    startDate: string,
    endDate: string
  ): Promise<CalendarEvent[]> {
    try {
      const response = await api.get(`${this.baseUrl}`, { params: { page_size: 100 } });
      const items = response.data?.items || response.data || [];
      return items
        .filter((wo: any) => {
          const d = (wo.created_at || wo.work_start_date || '').split('T')[0];
          return d >= startDate && d <= endDate;
        })
        .map((wo: any) => ({
          id: wo.id,
          title: wo.title || wo.equipment_type || `הזמנה #${wo.order_number || wo.id}`,
          date: (wo.created_at || wo.work_start_date || '').split('T')[0],
          type: 'work_order' as const,
          data: wo,
        }));
    } catch { return []; }
  }

  async getPendingWorkOrders(): Promise<WorkOrder[]> {
    const response = await api.get(`${this.baseUrl}/pending`);
    return response.data;
  }

  async getWorkOrdersByProject(projectId: number): Promise<WorkOrder[]> {
    const response = await api.get(`${this.baseUrl}/project/${projectId}`);
    return response.data;
  }

  async getWorkOrdersBySupplier(supplierId: number): Promise<WorkOrder[]> {
    const response = await api.get(`${this.baseUrl}/supplier/${supplierId}`);
    return response.data;
  }

  async getWorkOrderStats(): Promise<{
    total: number;
    pending: number;
    approved: number;
    in_progress: number;
    completed: number;
    cancelled: number;
  }> {
    const response = await api.get(`${this.baseUrl}/stats`);
    return response.data;
  }

  // Helper methods
  getStatusColor(status: string): string {
    const upper = (status || '').toUpperCase();
    if (['APPROVED_AND_SENT'].includes(upper)) return 'bg-green-100 text-green-800 border-green-200';
    if (['DISTRIBUTING', 'SUPPLIER_ACCEPTED_PENDING_COORDINATOR'].includes(upper)) return 'bg-blue-100 text-blue-800 border-blue-200';
    if (['PENDING'].includes(upper)) return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    if (['COMPLETED'].includes(upper)) return 'bg-gray-100 text-gray-800 border-gray-200';
    if (['REJECTED', 'CANCELLED', 'EXPIRED', 'STOPPED'].includes(upper)) return 'bg-red-100 text-red-800 border-red-200';
    return 'bg-gray-100 text-gray-800 border-gray-200';
  }

  getPriorityColor(priority: string): string {
    const upper = (priority || '').toUpperCase();
    if (upper === 'HIGH') return 'bg-red-100 text-red-800';
    if (upper === 'MEDIUM') return 'bg-yellow-100 text-yellow-800';
    if (upper === 'LOW') return 'bg-green-100 text-green-800';
    return 'bg-gray-100 text-gray-800';
  }

  getStatusText(status: string): string {
    const map: Record<string, string> = {
      PENDING: 'ממתין', DISTRIBUTING: 'בהפצה לספקים',
      SUPPLIER_ACCEPTED_PENDING_COORDINATOR: 'ספק אישר — ממתין לאישור מתאם',
      APPROVED_AND_SENT: 'אושר ונשלח', COMPLETED: 'הושלם',
      REJECTED: 'נדחה', CANCELLED: 'בוטל', EXPIRED: 'פג תוקף', STOPPED: 'הופסק',
    };
    return map[(status || '').toUpperCase()] || status || 'לא ידוע';
  }

  getPriorityText(priority: WorkOrder['priority']): string {
    switch (priority) {
      case 'high':
        return 'גבוהה';
      case 'medium':
        return 'בינונית';
      case 'low':
        return 'נמוכה';
      default:
        return 'לא ידועה';
    }
  }
}

export default new WorkOrderService();