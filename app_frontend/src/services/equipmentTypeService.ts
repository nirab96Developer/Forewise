// src/services/equipmentTypeService.ts
import api from './api';

export interface EquipmentType {
  id: number;
  name: string;
  description?: string;
  default_hourly_rate: number;
  category?: string;
  is_active?: boolean;
}

export interface ComputeCostRequest {
  work_type: string;
  hours: number;
  equipment_type_id?: number;
  supplier_id?: number;
  project_id?: number;
}

export interface ComputeCostResponse {
  hours: number;
  hourly_rate: number;
  total_cost: number;
  total_cost_with_vat: number;
  rate_source: string;
  rate_source_name?: string;
}

class EquipmentTypeService {
  async getEquipmentTypes(): Promise<EquipmentType[]> {
    try {
      const response = await api.get('/equipment-types');
      return response.data?.items || response.data || [];
    } catch (error) {
      console.error('Error fetching equipment types:', error);
      return [];
    }
  }

  async computeCost(request: ComputeCostRequest): Promise<ComputeCostResponse> {
    const response = await api.post('/equipment-types/compute-cost', request);
    return response.data;
  }
}

const equipmentTypeService = new EquipmentTypeService();
export default equipmentTypeService;
