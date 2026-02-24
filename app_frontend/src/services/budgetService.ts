// src/services/budgetService.ts
import api from './api';

export interface Budget {
  id: number;
  name: string;
  code?: string;
  description?: string;
  budget_type: string;
  status: string;
  parent_budget_id?: number;
  region_id?: number;
  area_id?: number;
  project_id?: number;
  total_amount: number;
  allocated_amount?: number;
  spent_amount?: number;
  committed_amount?: number;
  fiscal_year?: number;
  start_date?: string;
  end_date?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface BudgetCreate {
  name: string;
  code?: string;
  description?: string;
  budget_type: string;
  status: string;
  parent_budget_id?: number;
  region_id?: number;
  area_id?: number;
  project_id?: number;
  total_amount: number;
  fiscal_year?: number;
  start_date?: string;
  end_date?: string;
}

const budgetService = {
  /**
   * קבלת כל התקציבים
   */
  async getAll(params?: {
    skip?: number;
    limit?: number;
    budget_type?: string;
    fiscal_year?: number;
    region_id?: number;
    area_id?: number;
  }): Promise<Budget[]> {
    try {
      const response = await api.get('/budgets', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching budgets:', error);
      throw error;
    }
  },

  /**
   * קבלת תקציב לפי ID
   */
  async getById(id: number): Promise<Budget> {
    try {
      const response = await api.get(`/budgets/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching budget ${id}:`, error);
      throw error;
    }
  },

  /**
   * יצירת תקציב חדש
   */
  async create(data: BudgetCreate): Promise<Budget> {
    try {
      const response = await api.post('/budgets', data);
      return response.data;
    } catch (error) {
      console.error('Error creating budget:', error);
      throw error;
    }
  },

  /**
   * עדכון תקציב
   */
  async update(id: number, data: Partial<BudgetCreate>): Promise<Budget> {
    try {
      const response = await api.put(`/budgets/${id}`, data);
      return response.data;
    } catch (error) {
      console.error(`Error updating budget ${id}:`, error);
      throw error;
    }
  },

  /**
   * מחיקת תקציב
   */
  async delete(id: number): Promise<void> {
    try {
      await api.delete(`/budgets/${id}`);
    } catch (error) {
      console.error(`Error deleting budget ${id}:`, error);
      throw error;
    }
  },
};

export default budgetService;

