// src/services/reportService.ts
import api from './api';

export interface Report {
  id: number;
  name: string;
  description?: string;
  report_type: string;
  parameters?: Record<string, any>;
  created_at: string;
  updated_at?: string;
  created_by?: number;
}

export interface ReportCreate {
  name: string;
  description?: string;
  report_type: string;
  parameters?: Record<string, any>;
}

export interface ReportUpdate {
  name?: string;
  description?: string;
  report_type?: string;
  parameters?: Record<string, any>;
}

export interface ReportRun {
  id: number;
  report_id: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  parameters?: Record<string, any>;
  result?: any;
  error?: string;
  created_at: string;
  completed_at?: string;
  created_by?: number;
}

class ReportService {
  async getReports(): Promise<Report[]> {
    try {
      const response = await api.get('/reports');
      return response.data;
    } catch (error) {
      console.error('Error fetching reports:', error);
      throw error;
    }
  }

  async getReport(id: number): Promise<Report> {
    try {
      const response = await api.get(`/reports/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching report ${id}:`, error);
      throw error;
    }
  }

  async createReport(report: ReportCreate): Promise<Report> {
    try {
      const response = await api.post('/reports', report);
      return response.data;
    } catch (error) {
      console.error('Error creating report:', error);
      throw error;
    }
  }

  async updateReport(id: number, report: ReportUpdate): Promise<Report> {
    try {
      const response = await api.put(`/reports/${id}`, report);
      return response.data;
    } catch (error) {
      console.error(`Error updating report ${id}:`, error);
      throw error;
    }
  }

  async deleteReport(id: number): Promise<void> {
    try {
      await api.delete(`/reports/${id}`);
    } catch (error) {
      console.error(`Error deleting report ${id}:`, error);
      throw error;
    }
  }

  async runReport(id: number, parameters?: Record<string, any>): Promise<ReportRun> {
    try {
      const response = await api.post(`/reports/${id}/run`, { parameters });
      return response.data;
    } catch (error) {
      console.error(`Error running report ${id}:`, error);
      throw error;
    }
  }

  async getReportRuns(reportId?: number): Promise<ReportRun[]> {
    try {
      const params = reportId ? { report_id: reportId } : {};
      const response = await api.get('/reports/runs', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching report runs:', error);
      throw error;
    }
  }

  async getReportRun(id: number): Promise<ReportRun> {
    try {
      const response = await api.get(`/reports/runs/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching report run ${id}:`, error);
      throw error;
    }
  }
}

const reportService = new ReportService();
export default reportService;
