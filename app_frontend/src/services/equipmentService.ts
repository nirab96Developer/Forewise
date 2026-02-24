// src/services/equipmentService.ts
import api from './api';

export interface Equipment {
  id: number;
  name: string;
  code: string;
  type: string;
  status: string;
  manufacturer?: string;
  model?: string;
  serial_number?: string;
  year?: number;
  fuel_type?: string;
  engine_power?: number;
  weight?: number;
  dimensions?: object;
  purchase_date?: string;
  purchase_price?: number;
  current_value?: number;
  location?: string;
  last_maintenance_date?: string;
  next_maintenance_date?: string;
  maintenance_interval?: number;
  supplier_id?: number;
  supplier_name?: string;
  created_at: string;
  updated_at?: string;
}

export interface EquipmentCreate {
  name: string;
  code: string;
  type: string;
  status?: string;
  manufacturer?: string;
  model?: string;
  serial_number?: string;
  year?: number;
  fuel_type?: string;
  engine_power?: number;
  weight?: number;
  dimensions?: object;
  purchase_date?: string;
  purchase_price?: number;
  current_value?: number;
  location?: string;
  last_maintenance_date?: string;
  next_maintenance_date?: string;
  maintenance_interval?: number;
  supplier_id?: number;
}

export interface EquipmentUpdate {
  name?: string;
  code?: string;
  type?: string;
  status?: string;
  manufacturer?: string;
  model?: string;
  serial_number?: string;
  year?: number;
  fuel_type?: string;
  engine_power?: number;
  weight?: number;
  dimensions?: object;
  purchase_date?: string;
  purchase_price?: number;
  current_value?: number;
  location?: string;
  last_maintenance_date?: string;
  next_maintenance_date?: string;
  maintenance_interval?: number;
  supplier_id?: number;
  is_active?: boolean;
}

export interface EquipmentFilters {
  type?: string;
  status?: string;
  manufacturer?: string;
  location?: string;
  supplier_id?: number;
  search?: string;
  q?: string; // Backend uses 'q' for search
  page?: number;
  page_size?: number;
}

export interface EquipmentResponse {
  items?: Equipment[]; // Backend returns 'items'
  equipment?: Equipment[]; // Legacy support
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface EquipmentCategory {
  id: number;
  name: string;
  code: string;
}

class EquipmentService {
  /**
   * קבלת קטגוריות ציוד (עם ID ו-name)
   */
  async getEquipmentCategories(): Promise<EquipmentCategory[]> {
    try {
      const response = await api.get('/equipment/types/list');
      // Handle both array and object with items
      const data = response.data;
      if (Array.isArray(data)) {
        return data;
      } else if (data?.items && Array.isArray(data.items)) {
        return data.items;
      }
      return [];
    } catch (error) {
      console.error('Error fetching equipment categories:', error);
      throw error;
    }
  }

  /**
   * קבלת סוגי ציוד (alias ל-getEquipmentCategories)
   */
  async getEquipmentTypes(): Promise<EquipmentCategory[]> {
    return this.getEquipmentCategories();
  }

  /**
   * קבלת רשימת ציוד
   */
  async getEquipment(filters: EquipmentFilters = {}): Promise<EquipmentResponse> {
    try {
      // Map 'search' to 'q' for backend compatibility
      const params: any = { ...filters };
      if (params.search) {
        params.q = params.search;
        delete params.search;
      }
      // Remove trailing slash - backend doesn't have it
      const response = await api.get('/equipment', { params });
      const data = response.data;
      // Normalize response to have 'equipment' for frontend compatibility
      return {
        items: data.items,
        equipment: data.items, // Map 'items' to 'equipment' for legacy support
        total: data.total || 0,
        page: data.page || 1,
        page_size: data.page_size || 50,
        total_pages: data.total_pages || 1
      };
    } catch (error) {
      console.error('Error fetching equipment:', error);
      throw error;
    }
  }

  /**
   * קבלת ציוד לפי ID
   */
  async getEquipmentById(id: number): Promise<Equipment> {
    try {
      const response = await api.get(`/equipment/${id}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching equipment:', error);
      throw error;
    }
  }

  /**
   * יצירת ציוד חדש
   */
  async createEquipment(equipment: EquipmentCreate): Promise<Equipment> {
    try {
      const response = await api.post('/equipment', equipment);
      return response.data;
    } catch (error) {
      console.error('Error creating equipment:', error);
      throw error;
    }
  }

  /**
   * עדכון ציוד
   */
  async updateEquipment(id: number, equipment: EquipmentUpdate): Promise<Equipment> {
    try {
      const response = await api.put(`/equipment/${id}`, equipment);
      return response.data;
    } catch (error) {
      console.error('Error updating equipment:', error);
      throw error;
    }
  }

  /**
   * מחיקת ציוד
   */
  async deleteEquipment(id: number): Promise<void> {
    try {
      await api.delete(`/equipment/${id}`);
    } catch (error) {
      console.error('Error deleting equipment:', error);
      throw error;
    }
  }

  /**
   * קבלת ציוד פעיל
   */
  async getActiveEquipment(): Promise<Equipment[]> {
    try {
      const response = await api.get('/equipment/active');
      return response.data;
    } catch (error) {
      console.error('Error fetching active equipment:', error);
      throw error;
    }
  }

  /**
   * קבלת ציוד שדורש תחזוקה
   */
  async getEquipmentNeedingMaintenance(): Promise<Equipment[]> {
    try {
      const response = await api.get('/equipment/maintenance-needed');
      return response.data;
    } catch (error) {
      console.error('Error fetching equipment needing maintenance:', error);
      throw error;
    }
  }

  /**
   * עדכון תחזוקה
   */
  async updateMaintenance(id: number, maintenanceData: any): Promise<Equipment> {
    try {
      const response = await api.put(`/equipment/${id}/maintenance`, maintenanceData);
      return response.data;
    } catch (error) {
      console.error('Error updating maintenance:', error);
      throw error;
    }
  }
}

const equipmentService = new EquipmentService();
export default equipmentService;

