// src/services/locationService.ts
import api from './api';

export interface GeoFeature {
  type: string;
  properties?: Record<string, any>;
  geometry: {
    type: string;
    coordinates: number[][][] | number[];
  };
}

export interface LocationMetadata {
  geo?: GeoFeature;
  google?: {
    place_id?: string;
    formatted_address?: string;
  };
  source?: string;
  verified?: boolean;
  last_updated?: string;
}

export interface Location {
  id: number;
  code: string;
  name: string;
  description?: string;
  area_id: number;
  latitude?: number;
  longitude?: number;
  address?: string;
  metadata_json?: string;  // JSON string containing LocationMetadata
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

// Helper to parse metadata
export function parseLocationMetadata(metadataJson?: string): LocationMetadata | null {
  if (!metadataJson) return null;
  try {
    return JSON.parse(metadataJson);
  } catch {
    return null;
  }
}

export interface LocationCreate {
  code: string;
  name: string;
  description?: string;
  area_id: number;
  latitude?: number;
  longitude?: number;
  address?: string;
}

const locationService = {
  /**
   * קבלת כל המיקומים
   */
  async getAll(params?: {
    skip?: number;
    limit?: number;
    area_id?: number;
    search?: string;
  }): Promise<Location[]> {
    try {
      const response = await api.get('/locations', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching locations:', error);
      throw error;
    }
  },

  /**
   * קבלת מיקום לפי ID
   */
  async getById(id: number): Promise<Location> {
    try {
      const response = await api.get(`/locations/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching location ${id}:`, error);
      throw error;
    }
  },

  /**
   * יצירת מיקום חדש
   */
  async create(data: LocationCreate): Promise<Location> {
    try {
      const response = await api.post('/locations', data);
      return response.data;
    } catch (error) {
      console.error('Error creating location:', error);
      throw error;
    }
  },

  /**
   * עדכון מיקום
   */
  async update(id: number, data: Partial<LocationCreate>): Promise<Location> {
    try {
      const response = await api.put(`/locations/${id}`, data);
      return response.data;
    } catch (error) {
      console.error(`Error updating location ${id}:`, error);
      throw error;
    }
  },

  /**
   * מחיקת מיקום
   */
  async delete(id: number): Promise<void> {
    try {
      await api.delete(`/locations/${id}`);
    } catch (error) {
      console.error(`Error deleting location ${id}:`, error);
      throw error;
    }
  },

};

export default locationService;

