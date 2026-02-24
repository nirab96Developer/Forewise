// src/services/departmentService.ts
import api from './api';

export interface Department {
  id: number;
  code: string;
  name: string;
  description?: string;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface DepartmentCreate {
  code: string;
  name: string;
  description?: string;
  is_active?: boolean;
}

const departmentService = {
  /**
   * קבלת כל המחלקות
   */
  async getAll(params?: {
    skip?: number;
    limit?: number;
    search?: string;
  }): Promise<Department[]> {
    try {
      const response = await api.get('/departments', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching departments:', error);
      throw error;
    }
  },

  /**
   * קבלת מחלקה לפי ID
   */
  async getById(id: number): Promise<Department> {
    try {
      const response = await api.get(`/departments/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching department ${id}:`, error);
      throw error;
    }
  },

  /**
   * יצירת מחלקה חדשה
   */
  async create(data: DepartmentCreate): Promise<Department> {
    try {
      const response = await api.post('/departments', data);
      return response.data;
    } catch (error) {
      console.error('Error creating department:', error);
      throw error;
    }
  },

  /**
   * עדכון מחלקה
   */
  async update(id: number, data: Partial<DepartmentCreate>): Promise<Department> {
    try {
      const response = await api.put(`/departments/${id}`, data);
      return response.data;
    } catch (error) {
      console.error(`Error updating department ${id}:`, error);
      throw error;
    }
  },

  /**
   * מחיקת מחלקה
   */
  async delete(id: number): Promise<void> {
    try {
      await api.delete(`/departments/${id}`);
    } catch (error) {
      console.error(`Error deleting department ${id}:`, error);
      throw error;
    }
  },
};

export default departmentService;

