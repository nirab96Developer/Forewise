// src/services/roleService.ts
import api from './api';

export interface Role {
  id: number;
  code: string;
  name: string;
  description?: string;
  is_active: boolean;
  display_order: number;
  created_at?: string;
  updated_at?: string;
}

export interface RoleCreate {
  code: string;
  name: string;
  description?: string;
  is_active?: boolean;
  display_order?: number;
}

const roleService = {
  /**
   * קבלת כל התפקידים
   */
  async getAll(params?: {
    skip?: number;
    limit?: number;
    search?: string;
  }): Promise<Role[]> {
    try {
      const response = await api.get('/roles', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching roles:', error);
      throw error;
    }
  },

  /**
   * קבלת תפקיד לפי ID
   */
  async getById(id: number): Promise<Role> {
    try {
      const response = await api.get(`/roles/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching role ${id}:`, error);
      throw error;
    }
  },

  /**
   * יצירת תפקיד חדש
   */
  async create(data: RoleCreate): Promise<Role> {
    try {
      const response = await api.post('/roles', data);
      return response.data;
    } catch (error) {
      console.error('Error creating role:', error);
      throw error;
    }
  },

  /**
   * עדכון תפקיד
   */
  async update(id: number, data: Partial<RoleCreate>): Promise<Role> {
    try {
      const response = await api.put(`/roles/${id}`, data);
      return response.data;
    } catch (error) {
      console.error(`Error updating role ${id}:`, error);
      throw error;
    }
  },

  /**
   * מחיקת תפקיד
   */
  async delete(id: number): Promise<void> {
    try {
      await api.delete(`/roles/${id}`);
    } catch (error) {
      console.error(`Error deleting role ${id}:`, error);
      throw error;
    }
  },
};

export default roleService;

