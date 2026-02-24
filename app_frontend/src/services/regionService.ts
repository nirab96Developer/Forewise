// src/services/regionService.ts
import api from './api';

export interface Region {
  id: number;
  name: string;
  code: string;
  manager_id?: number;
  description?: string;
  created_at?: string;
  updated_at?: string;
}

export interface RegionCreate {
  name: string;
  code?: string;
  manager_id?: number;
  description?: string;
}

const regionService = {
  /**
   * קבלת כל המרחבים
   */
  async getAll(params?: {
    skip?: number;
    limit?: number;
    search?: string;
  }): Promise<Region[]> {
    try {
      const response = await api.get('/regions', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching regions:', error);
      throw error;
    }
  },

  /**
   * קבלת מרחב לפי ID
   */
  async getById(id: number): Promise<Region> {
    try {
      const response = await api.get(`/regions/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching region ${id}:`, error);
      throw error;
    }
  },

  /**
   * יצירת מרחב חדש
   */
  async create(data: RegionCreate): Promise<Region> {
    try {
      const response = await api.post('/regions', data);
      return response.data;
    } catch (error) {
      console.error('Error creating region:', error);
      throw error;
    }
  },

  /**
   * עדכון מרחב
   */
  async update(id: number, data: Partial<RegionCreate>): Promise<Region> {
    try {
      const response = await api.put(`/regions/${id}`, data);
      return response.data;
    } catch (error) {
      console.error(`Error updating region ${id}:`, error);
      throw error;
    }
  },

  /**
   * מחיקת מרחב
   */
  async delete(id: number): Promise<void> {
    try {
      await api.delete(`/regions/${id}`);
    } catch (error) {
      console.error(`Error deleting region ${id}:`, error);
      throw error;
    }
  },

  /**
   * קבלת סטטיסטיקות מרחב
   */
  async getStatistics(id: number): Promise<any> {
    try {
      const response = await api.get(`/regions/${id}/statistics`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching region ${id} statistics:`, error);
      throw error;
    }
  },
};

export default regionService;

