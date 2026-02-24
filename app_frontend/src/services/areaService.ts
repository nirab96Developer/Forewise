// src/services/areaService.ts
import api from './api';

export interface Area {
  id: number;
  name: string;
  code?: string;
  region_id: number;
  manager_id?: number;
  description?: string;
  total_area_hectares?: number;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface AreaCreate {
  name: string;
  code?: string;
  region_id: number;
  manager_id?: number;
  description?: string;
  total_area_hectares?: number;
}

const areaService = {
  /**
   * קבלת כל האזורים
   */
  async getAll(params?: {
    skip?: number;
    limit?: number;
    region_id?: number;
    search?: string;
  }): Promise<Area[]> {
    try {
      const response = await api.get('/areas', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching areas:', error);
      throw error;
    }
  },

  /**
   * קבלת אזור לפי ID
   */
  async getById(id: number): Promise<Area> {
    try {
      const response = await api.get(`/areas/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching area ${id}:`, error);
      throw error;
    }
  },

  /**
   * יצירת אזור חדש
   */
  async create(data: AreaCreate): Promise<Area> {
    try {
      const response = await api.post('/areas', data);
      return response.data;
    } catch (error) {
      console.error('Error creating area:', error);
      throw error;
    }
  },

  /**
   * עדכון אזור
   */
  async update(id: number, data: Partial<AreaCreate>): Promise<Area> {
    try {
      const response = await api.put(`/areas/${id}`, data);
      return response.data;
    } catch (error) {
      console.error(`Error updating area ${id}:`, error);
      throw error;
    }
  },

  /**
   * מחיקת אזור
   */
  async delete(id: number): Promise<void> {
    try {
      await api.delete(`/areas/${id}`);
    } catch (error) {
      console.error(`Error deleting area ${id}:`, error);
      throw error;
    }
  },

  /**
   * קבלת סטטיסטיקות אזור
   */
  async getStatistics(id: number): Promise<any> {
    try {
      const response = await api.get(`/areas/${id}/statistics`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching area ${id} statistics:`, error);
      throw error;
    }
  },
};

export default areaService;

