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
  status: string;
  priority: string;
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
  status?: string;
  priority?: string;
  estimated_hours?: number;
  hourly_rate?: number;
}

export type WorkOrderStatus = string;
export type WorkOrderPriority = string;

export function getWorkOrderStatusText(status: string): string {
  const upper = (status || '').toUpperCase();
  const map: Record<string, string> = {
    PENDING: 'ממתין', DISTRIBUTING: 'בהפצה לספקים',
    SUPPLIER_ACCEPTED_PENDING_COORDINATOR: 'ספק אישר — ממתין למתאם',
    APPROVED_AND_SENT: 'אושר ונשלח', COMPLETED: 'הושלם',
    REJECTED: 'נדחה', CANCELLED: 'בוטל', EXPIRED: 'פג תוקף', STOPPED: 'הופסק',
  };
  return map[upper] || status;
}

export function getWorkOrderStatusColor(status: string): string {
  const upper = (status || '').toUpperCase();
  if (['APPROVED_AND_SENT', 'COMPLETED'].includes(upper)) return 'bg-green-100 text-green-800';
  if (['DISTRIBUTING', 'SUPPLIER_ACCEPTED_PENDING_COORDINATOR'].includes(upper)) return 'bg-blue-100 text-blue-800';
  if (['PENDING'].includes(upper)) return 'bg-yellow-100 text-yellow-800';
  if (['REJECTED', 'CANCELLED', 'EXPIRED', 'STOPPED'].includes(upper)) return 'bg-red-100 text-red-800';
  return 'bg-gray-100 text-gray-800';
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













