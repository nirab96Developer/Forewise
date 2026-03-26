// src/services/supplierService.ts
import api from './api';

export interface Supplier {
  id: number;
  name: string;
  code?: string;
  tax_id?: string;
  contact_name?: string;
  email?: string;
  phone?: string;
  address?: string;
  supplier_type?: string;
  region_id?: number;
  area_id?: number;
  is_active?: boolean;
  rating?: number;
  priority_score?: number;
  average_response_time?: number;
  last_selected?: string;
  created_at?: string;
  updated_at?: string;
}

export interface SupplierCreate {
  name: string;
  code: string;
  tax_id?: string;
  contact_name?: string;
  email?: string;
  phone?: string;
  address?: string;
  supplier_type?: string;
  region_id?: number;
  area_id?: number;
  rating?: number;
  priority_score?: number;
  is_active?: boolean;
}

export interface SupplierUpdate {
  name?: string;
  code?: string;
  tax_id?: string;
  contact_name?: string;
  email?: string;
  phone?: string;
  address?: string;
  supplier_type?: string;
  region_id?: number;
  area_id?: number;
  rating?: number;
  priority_score?: number;
  average_response_time?: number;
  is_active?: boolean;
  version?: number;
}

export interface SupplierFilters {
  supplier_type?: string;
  region_id?: number;
  area_id?: number;
  is_active?: boolean;
  q?: string;
  page?: number;
  page_size?: number;
}

export interface SupplierResponse {
  suppliers: Supplier[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface EquipmentModel {
  id: number;
  name: string;
  category_id?: number | null;
}

export type SupplierEquipmentStatus = 'available' | 'busy' | 'inactive';

export interface SupplierEquipmentItem {
  id: number;
  supplier_id: number;
  equipment_model_id?: number | null;
  equipment_category_id?: number | null;
  license_plate?: string | null;
  status?: SupplierEquipmentStatus | string | null;
  quantity_available?: number | null;
  hourly_rate?: number | null;
  is_active?: boolean | null;
}

export interface SupplierEquipmentCreate {
  equipment_model_id: number;
  license_plate: string;
  status?: SupplierEquipmentStatus;
  quantity_available?: number;
  hourly_rate?: number;
}

export interface SupplierEquipmentUpdate {
  status?: SupplierEquipmentStatus;
  quantity_available?: number;
  hourly_rate?: number;
}

class SupplierService {
  /**
   * קבלת רשימת ספקים
   */
  async getSuppliers(filters: SupplierFilters = {}): Promise<SupplierResponse> {
    try {
      const response = await api.get('/suppliers', { params: filters });
      if (response.data?.items) {
        return {
          suppliers: response.data.items,
          total: response.data.total ?? 0,
          page: response.data.page ?? 1,
          page_size: response.data.page_size ?? 50,
          total_pages: response.data.total_pages ?? 1,
        };
      }
      return {
        suppliers: response.data,
        total: response.data.length,
        page: filters.page || 1,
        page_size: filters.page_size || 50,
        total_pages: 1
      };
    } catch (error) {
      console.error('Error fetching suppliers:', error);
      throw error;
    }
  }

  /**
   * קבלת ספק לפי ID
   */
  async getSupplier(id: number): Promise<Supplier> {
    try {
      const response = await api.get(`/suppliers/${id}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching supplier:', error);
      throw error;
    }
  }

  /**
   * יצירת ספק חדש
   */
  async createSupplier(supplier: SupplierCreate): Promise<Supplier> {
    try {
      const response = await api.post('/suppliers', supplier);
      return response.data;
    } catch (error) {
      console.error('Error creating supplier:', error);
      throw error;
    }
  }

  /**
   * עדכון ספק
   */
  async updateSupplier(id: number, supplier: SupplierUpdate): Promise<Supplier> {
    try {
      const response = await api.put(`/suppliers/${id}`, supplier);
      return response.data;
    } catch (error) {
      console.error('Error updating supplier:', error);
      throw error;
    }
  }

  /**
   * מחיקת ספק
   */
  async deleteSupplier(id: number): Promise<void> {
    try {
      await api.delete(`/suppliers/${id}`);
    } catch (error) {
      console.error('Error deleting supplier:', error);
      throw error;
    }
  }

  /**
   * קבלת ספקים פעילים
   */
  async getActiveSuppliers(equipmentCategoryId?: number): Promise<Supplier[]> {
    try {
      const url = equipmentCategoryId
        ? `/suppliers/active?equipment_category_id=${equipmentCategoryId}`
        : '/suppliers/active';
      const response = await api.get(url);
      return response.data?.items || response.data || [];
    } catch (error) {
      console.error('Error fetching active suppliers:', error);
      throw error;
    }
  }

  async getActiveEquipmentModels(): Promise<EquipmentModel[]> {
    try {
      const response = await api.get('/suppliers/equipment-models/active');
      return response.data || [];
    } catch (error) {
      console.error('Error fetching equipment models:', error);
      throw error;
    }
  }

  async getSupplierEquipment(supplierId: number): Promise<SupplierEquipmentItem[]> {
    try {
      const response = await api.get(`/suppliers/${supplierId}/equipment`);
      return response.data || [];
    } catch (error) {
      console.error('Error fetching supplier equipment:', error);
      throw error;
    }
  }

  async addSupplierEquipment(supplierId: number, payload: SupplierEquipmentCreate): Promise<SupplierEquipmentItem> {
    try {
      const response = await api.post(`/suppliers/${supplierId}/equipment`, payload);
      return response.data;
    } catch (error) {
      console.error('Error adding supplier equipment:', error);
      throw error;
    }
  }

  async updateSupplierEquipment(
    supplierId: number,
    supplierEquipmentId: number,
    payload: SupplierEquipmentUpdate
  ): Promise<SupplierEquipmentItem> {
    try {
      const response = await api.patch(`/suppliers/${supplierId}/equipment/${supplierEquipmentId}`, payload);
      return response.data;
    } catch (error) {
      console.error('Error updating supplier equipment:', error);
      throw error;
    }
  }

  /**
   * קבלת ספקים פעילים לפי קטגוריית ציוד (ID)
   */
  async getActiveSuppliersByCategory(categoryId: number): Promise<Supplier[]> {
    try {
      const url = `/suppliers/active?equipment_category_id=${encodeURIComponent(categoryId)}&page=1&page_size=50`;
      const response = await api.get(url);
      // Handle both array and object with items
      const data = response.data;
      if (Array.isArray(data)) {
        return data;
      } else if (data?.items && Array.isArray(data.items)) {
        return data.items;
      }
      return [];
    } catch (error) {
      console.error(`Error fetching suppliers by category ${categoryId}:`, error);
      throw new Error(`Suppliers fetch failed: ${error}`);
    }
  }

  /**
   * קבלת ספקים לפי סוג ציוד
   */
  async getSuppliersByEquipmentType(equipmentType: string): Promise<Supplier[]> {
    try {
      const response = await api.get(`/suppliers/equipment/${equipmentType}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching suppliers by equipment type:', error);
      throw error;
    }
  }

  /**
   * קבלת הספק הבא בתור (Rotation)
   */
  async getNextSupplier(equipmentType: string): Promise<Supplier> {
    try {
      const response = await api.get(`/suppliers/next/${equipmentType}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching next supplier:', error);
      throw error;
    }
  }

  /**
   * עדכון סדר הסבב
   */
  async updateRotationOrder(supplierId: number, newOrder: number): Promise<Supplier> {
    try {
      const response = await api.put(`/suppliers/${supplierId}/rotation`, { order: newOrder });
      return response.data;
    } catch (error) {
      console.error('Error updating rotation order:', error);
      throw error;
    }
  }

  /**
   * קבלת סטטיסטיקות ספק
   */
  async getSupplierStats(id: number): Promise<{
    total_work_orders: number;
    completed_work_orders: number;
    response_rate: number;
    average_response_time: number;
    total_hours: number;
    last_work_order?: string;
  }> {
    try {
      const response = await api.get(`/suppliers/${id}/stats`);
      return response.data;
    } catch (error) {
      console.error('Error fetching supplier stats:', error);
      throw error;
    }
  }

  /**
   * חיפוש ספקים
   */
  async searchSuppliers(query: string): Promise<Supplier[]> {
    try {
      const response = await api.get('/suppliers/search', { params: { q: query } });
      return response.data;
    } catch (error) {
      console.error('Error searching suppliers:', error);
      throw error;
    }
  }
}

const supplierService = new SupplierService();
export default supplierService;

