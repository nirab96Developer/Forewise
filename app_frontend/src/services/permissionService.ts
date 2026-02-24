// src/services/permissionService.ts
import api from './api';

export interface Permission {
  id: number;
  code: string;
  name: string;
  description?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface PermissionCreate {
  code: string;
  name: string;
  description?: string;
  is_active?: boolean;
}

const permissionService = {
  /**
   * קבלת כל ההרשאות
   */
  async getAll(params?: {
    skip?: number;
    limit?: number;
    search?: string;
  }): Promise<Permission[]> {
    try {
      const response = await api.get('/permissions', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching permissions:', error);
      throw error;
    }
  },

  /**
   * קבלת הרשאה לפי ID
   */
  async getById(id: number): Promise<Permission> {
    try {
      const response = await api.get(`/permissions/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching permission ${id}:`, error);
      throw error;
    }
  },

  /**
   * יצירת הרשאה חדשה
   */
  async create(data: PermissionCreate): Promise<Permission> {
    try {
      const response = await api.post('/permissions', data);
      return response.data;
    } catch (error) {
      console.error('Error creating permission:', error);
      throw error;
    }
  },

  /**
   * עדכון הרשאה
   */
  async update(id: number, data: Partial<PermissionCreate>): Promise<Permission> {
    try {
      const response = await api.put(`/permissions/${id}`, data);
      return response.data;
    } catch (error) {
      console.error(`Error updating permission ${id}:`, error);
      throw error;
    }
  },

  /**
   * מחיקת הרשאה
   */
  async delete(id: number): Promise<void> {
    try {
      await api.delete(`/permissions/${id}`);
    } catch (error) {
      console.error(`Error deleting permission ${id}:`, error);
      throw error;
    }
  },
};

export default permissionService;

