// src/services/activityLogService.ts
import api from './api';

export interface ActivityLog {
  id: number;
  user_id?: number;
  user_name?: string;
  user_email?: string;
  activity_type: string;
  action: string;
  entity_type?: string;
  entity_id?: number;
  details?: any;
  custom_metadata?: any;
  ip_address?: string;
  user_agent?: string;
  session_id?: string;
  created_at: string;
}

export interface ActivityLogFilters {
  user_id?: number;
  activity_type?: string;
  action?: string;
  entity_type?: string;
  entity_id?: number;
  start_date?: string;
  end_date?: string;
  search?: string;
  page?: number;
  per_page?: number;  // לפי החוזה - per_page במקום limit
  /** operational | financial | management | system — backend filters by category */
  category?: string;
}

export interface ActivityLogResponse {
  activities: ActivityLog[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

class ActivityLogService {
  /**
   * קבלת רשימת פעילויות
   */
  async getActivityLogs(filters: ActivityLogFilters = {}): Promise<ActivityLogResponse> {
    try {
      const { per_page, ...rest } = filters;
      const params: Record<string, unknown> = { ...rest };
      if (per_page != null) params.page_size = per_page;
      const response = await api.get('/activity-logs/', { params });
      // אם ה-API מחזיר List ישירות
      if (Array.isArray(response.data)) {
        return {
          activities: response.data,
          total: response.data.length,
          page: 1,
          limit: response.data.length,
          total_pages: 1
        };
      }
      // אם זה PaginatedResponse
      return {
        activities: response.data.items || [],
        total: response.data.total || 0,
        page: response.data.page || 1,
        limit: response.data.page_size || 20,
        total_pages: response.data.pages || 1
      };
    } catch (error) {
      console.error('Error fetching activity logs:', error);
      throw error;
    }
  }

  /**
   * קבלת פעילויות לפי entity (למשל פרויקט)
   */
  async getActivitiesByEntity(entityType: string, entityId: number): Promise<ActivityLog[]> {
    try {
      const response = await api.get('/activity-logs/', {
        params: {
          entity_type: entityType,
          entity_id: entityId
        }
      });
      return Array.isArray(response.data) ? response.data : (response.data.items || []);
    } catch (error) {
      console.error('Error fetching activities by entity:', error);
      throw error;
    }
  }

  /**
   * קבלת פעילויות לפי משתמש
   */
  async getUserActivities(userId: number, filters: Omit<ActivityLogFilters, 'user_id'> = {}): Promise<ActivityLog[]> {
    try {
      const response = await api.get(`/activity-logs/user/${userId}`, { params: filters });
      return Array.isArray(response.data) ? response.data : (response.data.items || []);
    } catch (error) {
      console.error('Error fetching user activities:', error);
      throw error;
    }
  }
}

const activityLogService = new ActivityLogService();
export default activityLogService;















