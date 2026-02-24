// src/types/workOrder.ts
// הגדרות טיפוסים להזמנות עבודה

export interface WorkOrder {
  id: number;
  title: string;
  description?: string;
  project_id: number;
  project_name?: string;
  supplier_id?: number;
  supplier_name?: string;
  equipment_type: string;
  work_start_date: string;
  work_end_date: string;
  status: 'pending' | 'approved' | 'in_progress' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high';
  estimated_hours?: number;
  hourly_rate?: number;
  created_at: string;
  updated_at?: string;
  created_by?: number;
  approved_by?: number;
  approved_at?: string;
}

export interface WorkOrderCreate {
  title: string;
  description?: string;
  project_id: number;
  supplier_id?: number;
  equipment_type: string;
  work_start_date: string;
  work_end_date: string;
  priority: 'low' | 'medium' | 'high';
  estimated_hours?: number;
  hourly_rate?: number;
}

export interface WorkOrderUpdate {
  title?: string;
  description?: string;
  project_id?: number;
  supplier_id?: number;
  equipment_type?: string;
  work_start_date?: string;
  work_end_date?: string;
  status?: 'pending' | 'approved' | 'in_progress' | 'completed' | 'cancelled';
  priority?: 'low' | 'medium' | 'high';
  estimated_hours?: number;
  hourly_rate?: number;
}

export type WorkOrderStatus = 'pending' | 'approved' | 'in_progress' | 'completed' | 'cancelled';
export type WorkOrderPriority = 'low' | 'medium' | 'high';

export function getWorkOrderStatusText(status: WorkOrderStatus): string {
  switch (status) {
    case 'pending': return 'ממתין לאישור';
    case 'approved': return 'אושר';
    case 'in_progress': return 'בביצוע';
    case 'completed': return 'הושלם';
    case 'cancelled': return 'בוטל';
    default: return status;
  }
}

export function getWorkOrderStatusColor(status: WorkOrderStatus): string {
  switch (status) {
    case 'pending': return 'bg-yellow-100 text-yellow-800';
    case 'approved': return 'bg-blue-100 text-blue-800';
    case 'in_progress': return 'bg-green-100 text-green-800';
    case 'completed': return 'bg-gray-100 text-gray-800';
    case 'cancelled': return 'bg-red-100 text-red-800';
    default: return 'bg-gray-100 text-gray-800';
  }
}

export function getWorkOrderPriorityText(priority: WorkOrderPriority): string {
  switch (priority) {
    case 'low': return 'נמוכה';
    case 'medium': return 'בינונית';
    case 'high': return 'גבוהה';
    default: return priority;
  }
}

export function getWorkOrderPriorityColor(priority: WorkOrderPriority): string {
  switch (priority) {
    case 'low': return 'bg-green-100 text-green-800';
    case 'medium': return 'bg-yellow-100 text-yellow-800';
    case 'high': return 'bg-red-100 text-red-800';
    default: return 'bg-gray-100 text-gray-800';
  }
}













