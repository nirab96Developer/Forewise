// src/services/dashboardService.ts
import api from './api';

export interface DashboardSummary {
  active_projects_count: number;
  total_projects_count?: number;
  avg_progress_pct: number;
  hours_month_total: number;
  open_alerts_count: number;
  can_report_hours: boolean;
  can_create_order: boolean;
  can_scan_equipment: boolean;
  can_open_ticket: boolean;
  // Stats fields
  total_users?: number;
  active_users?: number;
  total_regions?: number;
  total_areas?: number;
  pending_approvals_count?: number;
  pending_work_orders_count?: number;
  completed_work_orders_count?: number;
  equipment_in_use_count?: number;
  alerts_count?: number;
  pending_invoices_count?: number;
  suppliers_count?: number;
  active_suppliers_count?: number;
  today_worklogs_count?: number;
  total_suppliers_count?: number;
  total_equipment_count?: number;
  expired_contracts_count?: number;
}

export interface DashboardStats {
  total_projects: number;
  active_projects: number;
  completed_projects: number;
  pending_work_orders: number;
  total_equipment: number;
  available_equipment: number;
  total_suppliers: number;
  active_suppliers: number;
  monthly_hours: number;
  weekly_hours: number;
}

export interface DashboardProject {
  id: number;
  name: string;
  code: string;
  description?: string;
  status: string;
  priority: string;
  progress_percentage: number;
  days_remaining: number;
  is_overdue: boolean;
  budget_utilization: number;
  team_size: number;
  last_activity: string;
  planned_start_date?: string;
  planned_end_date?: string;
  allocated_budget?: number;
  spent_budget?: number;
  // Optional fields for display
  area_name?: string;
  region_name?: string;
  manager_name?: string;
}

export interface DashboardAlert {
  id: number;
  type: string;
  severity: string;
  title: string;
  description: string;
  project_id?: number;
  work_order_id?: number;
  equipment_id?: number;
  supplier_id?: number;
  created_at: string;
  expires_at?: string;
  action_required: boolean;
}

export interface DashboardActivity {
  id: number;
  type: string;
  title: string;
  description: string;
  user_name: string;
  project_name?: string;
  created_at: string;
  location?: string;
}

export interface MapData {
  projects: Array<{
    id: number;
    name: string;
    coordinates: {
      lat: number;
      lng: number;
    };
    status: string;
    progress_percentage: number;
  }>;
  equipment: Array<{
    id: number;
    name: string;
    coordinates: {
      lat: number;
      lng: number;
    };
    status: string;
    type: string;
  }>;
  locations: Array<{
    id: number;
    name: string;
    coordinates: {
      lat: number;
      lng: number;
    };
    type: string;
  }>;
}

class DashboardService {
  /**
   * קבלת סיכום כללי של הדאשבורד
   */
  async getSummary(): Promise<DashboardSummary> {
    try {
      const response = await api.get('/dashboard/summary');
      return response.data;
    } catch (error) {
      console.error('Error fetching dashboard summary:', error);
      throw error;
    }
  }

  /**
   * קבלת סטטיסטיקות מפורטות
   */
  async getStats(): Promise<DashboardStats> {
    try {
      const response = await api.get('/dashboard/stats');
      return response.data;
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      throw error;
    }
  }

  /**
   * קבלת פרויקטים עבור הדאשבורד
   */
  async getProjects(): Promise<DashboardProject[]> {
    try {
      const response = await api.get('/dashboard/projects');
      return response.data;
    } catch (error) {
      console.error('Error fetching dashboard projects:', error);
      throw error;
    }
  }

  /**
   * קבלת התראות עבור הדאשבורד
   */
  async getAlerts(): Promise<DashboardAlert[]> {
    try {
      const response = await api.get('/dashboard/alerts');
      return response.data;
    } catch (error) {
      console.error('Error fetching dashboard alerts:', error);
      throw error;
    }
  }

  /**
   * קבלת פעילות אחרונה
   */
  async getActivity(): Promise<DashboardActivity[]> {
    try {
      const response = await api.get('/dashboard/activity');
      return response.data;
    } catch (error) {
      console.error('Error fetching dashboard activity:', error);
      throw error;
    }
  }

  /**
   * קבלת נתוני שעות עבודה
   */
  async getHoursData(period: string = 'month'): Promise<any> {
    try {
      const response = await api.get('/dashboard/hours', { params: { period } });
      return response.data;
    } catch (error) {
      console.error('Error fetching hours data:', error);
      throw error;
    }
  }

  /**
   * קבלת ציוד פעיל
   */
  async getActiveEquipment(): Promise<any[]> {
    try {
      const response = await api.get('/dashboard/equipment/active');
      return response.data;
    } catch (error) {
      console.error('Error fetching active equipment:', error);
      throw error;
    }
  }

  /**
   * קבלת ספקים פעילים
   */
  async getActiveSuppliers(): Promise<any[]> {
    try {
      const response = await api.get('/dashboard/suppliers/active');
      return response.data;
    } catch (error) {
      console.error('Error fetching active suppliers:', error);
      throw error;
    }
  }

  /**
   * סגירת התראה
   */
  async dismissAlert(alertId: number): Promise<void> {
    try {
      await api.post(`/dashboard/alerts/${alertId}/dismiss`);
    } catch (error) {
      console.error('Error dismissing alert:', error);
      throw error;
    }
  }

  /**
   * פעולה על התראה
   */
  async handleAlertAction(alertId: number, action: string): Promise<void> {
    try {
      await api.post(`/dashboard/alerts/${alertId}/action`, null, {
        params: { action }
      });
    } catch (error) {
      console.error('Error handling alert action:', error);
      throw error;
    }
  }

  /**
   * קבלת נתונים עבור מפה
   */
  async getMapData(): Promise<MapData> {
    try {
      const response = await api.get('/dashboard/map');
      return response.data;
    } catch (error) {
      console.error('Error fetching map data:', error);
      throw error;
    }
  }
  /**
   * Get live counts for badges (settings pages, admin panels)
   */
  async getLiveCounts(): Promise<any> {
    try {
      const response = await api.get('/dashboard/live-counts');
      return response.data;
    } catch (error) {
      console.error('Error fetching live counts:', error);
      return {};
    }
  }

  /**
   * Get "what's waiting for me" - PendingTasksEngine
   * Same endpoint for ALL roles, content varies by role+scope
   */
  async getMyTasks(): Promise<any> {
    try {
      const response = await api.get('/dashboard/my-tasks');
      return response.data;
    } catch (error) {
      console.error('Error fetching my tasks:', error);
      return null;
    }
  }
}

const dashboardService = new DashboardService();
export default dashboardService;

