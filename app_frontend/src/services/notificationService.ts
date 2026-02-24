// src/services/notificationService.ts
import api from './api';

export interface Notification {
  id: number;
  user_id: number;
  type: string;
  title: string;
  message: string;
  data?: any;
  is_read: boolean;
  created_at: string;
  read_at?: string;
}

export interface NotificationCreate {
  user_id: number;
  type: string;
  title: string;
  message: string;
  data?: any;
}

export interface NotificationFilters {
  user_id?: number;
  type?: string;
  is_read?: boolean;
  page?: number;
  limit?: number;
}

export interface NotificationResponse {
  notifications: Notification[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
  unread_count: number;
}

class NotificationService {
  /**
   * קבלת רשימת התראות
   */
  async getNotifications(filters: NotificationFilters = {}): Promise<Notification[] | NotificationResponse> {
    try {
      const response = await api.get('/notifications/', { params: filters });
      // API returns array directly, not wrapped in response object
      return Array.isArray(response.data) ? response.data : response.data;
    } catch (error) {
      console.error('Error fetching notifications:', error);
      throw error;
    }
  }

  /**
   * קבלת התראות של המשתמש הנוכחי
   */
  async getMyNotifications(filters: Omit<NotificationFilters, 'user_id'> = {}): Promise<NotificationResponse> {
    try {
      const response = await api.get('/notifications/my', { params: filters });
      return response.data;
    } catch (error) {
      console.error('Error fetching my notifications:', error);
      throw error;
    }
  }

  /**
   * סימון התראה כנקראה
   */
  async markAsRead(id: number): Promise<Notification> {
    try {
      const response = await api.put(`/notifications/${id}/read`);
      return response.data;
    } catch (error) {
      console.error('Error marking notification as read:', error);
      throw error;
    }
  }

  /**
   * סימון כל ההתראות כנקראות
   */
  async markAllAsRead(): Promise<void> {
    try {
      await api.put('/notifications/read-all');
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
      throw error;
    }
  }

  /**
   * מחיקת התראה
   */
  async deleteNotification(id: number): Promise<void> {
    try {
      await api.delete(`/notifications/${id}`);
    } catch (error) {
      console.error('Error deleting notification:', error);
      throw error;
    }
  }

  /**
   * קבלת מספר התראות לא נקראות
   */
  async getUnreadCount(): Promise<number> {
    try {
      const response = await api.get('/notifications/unread-count');
      return response.data.count;
    } catch (error) {
      console.error('Error fetching unread count:', error);
      throw error;
    }
  }

  /**
   * יצירת התראה חדשה
   */
  async createNotification(notification: NotificationCreate): Promise<Notification> {
    try {
      const response = await api.post('/notifications', notification);
      return response.data;
    } catch (error) {
      console.error('Error creating notification:', error);
      throw error;
    }
  }

  /**
   * קבלת התראות לפי סוג
   */
  async getNotificationsByType(type: string): Promise<Notification[]> {
    try {
      const response = await api.get(`/notifications/type/${type}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching notifications by type:', error);
      throw error;
    }
  }

  /**
   * קבלת התראות אחרונות
   */
  async getRecentNotifications(limit: number = 10): Promise<Notification[]> {
    try {
      const response = await api.get('/notifications/recent', { params: { limit } });
      return response.data;
    } catch (error) {
      console.error('Error fetching recent notifications:', error);
      throw error;
    }
  }
}

const notificationService = new NotificationService();
export default notificationService;

