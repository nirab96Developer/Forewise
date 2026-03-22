// src/services/workLogService.ts
// Updated service to match new backend API - אישור דיווח שעות
import api from './api';

// === INTERFACES ===

export interface WorkLogSegment {
  id?: number;
  worklog_id?: number;
  segment_number: number;
  segment_type: 'work' | 'break';
  start_time: string;
  end_time: string;
  work_minutes: number;
  break_minutes: number;
  activity?: string;
  created_at?: string;
  duration_formatted?: string;
  work_hours_decimal?: number;
  break_hours_decimal?: number;
}

export interface WorkLog {
  id: number;
  report_number: number;
  report_number_formatted: string;

  // Relations
  work_order_id?: number;
  user_id?: number;
  project_id?: number;
  equipment_id?: number;
  supplier_id?: number;
  area_id?: number;

  // Details
  report_date: string;
  start_time?: string;
  end_time?: string;
  work_hours: string;
  break_hours: string;
  total_hours: string;

  // Work info
  work_type?: string;
  activity_description?: string;
  equipment_type?: string;

  // Standard/Non-standard
  is_standard: boolean;
  non_standard_reason?: string;

  // Status
  status: string;
  submitted_at?: string;
  submitted_by_id?: number;
  approved_by_user_id?: number;
  approved_at?: string;
  rejection_reason?: string;

  // Distribution
  sent_to_supplier?: boolean;
  sent_to_supplier_at?: string;
  sent_to_accountant?: boolean;
  sent_to_accountant_at?: string;
  sent_to_area_manager?: boolean;
  sent_to_area_manager_at?: string;

  // Control
  equipment_scanned?: boolean;
  scan_time?: string;

  // Notes
  notes?: string;

  // Pricing Snapshot
  hourly_rate_snapshot?: string;
  rate_source?: string;
  rate_source_name?: string;
  cost_before_vat?: string;
  vat_rate?: string;
  cost_with_vat?: string;

  // Timestamps
  created_at: string;
  updated_at: string;

  // Computed
  is_approved?: boolean;
  is_submitted?: boolean;
  is_rejected?: boolean;
  is_editable?: boolean;
  net_hours?: string;
  requires_reason?: boolean;

  // Relationship data
  work_order_number?: number;
  work_order_title?: string;
  user_name?: string;
  project_name?: string;
  equipment_name?: string;
  equipment_code?: string;
  supplier_name?: string;
  area_name?: string;
  approved_by_name?: string;
  submitted_by_name?: string;

  // Segments
  segments?: WorkLogSegment[];

  // Overnight
  is_overnight?: boolean;
  overnight_nights?: number;
  overnight_rate?: number;
  overnight_total?: number;
  paid_hours?: number;
  pdf_path?: string;
  pdf_generated_at?: string;
}

export interface WorkLogCreate {
  work_order_id?: number;
  project_id?: number;
  equipment_id?: number;
  equipment_type_id?: number;  // NEW: For pricing calculation
  supplier_id?: number;
  area_id?: number;
  report_date?: string;  // Made optional for legacy support
  report_number?: number;  // Made optional - server generates
  start_time?: string;
  end_time?: string;
  work_hours?: string;  // Made optional for legacy support
  break_hours?: string;
  total_hours?: string;
  work_type?: string;  // fieldwork | storage | general
  activity_description?: string;
  equipment_type?: string;
  is_standard: boolean;
  non_standard_reason?: string;
  notes?: string;
  equipment_scanned?: boolean;
  scan_time?: string;
  segments?: Omit<WorkLogSegment, 'id' | 'worklog_id' | 'created_at'>[];
  includes_guard?: boolean;
  is_overnight?: boolean;
  overnight_nights?: number;
  overnight_rate?: number;
  // Legacy fields for backwards compatibility
  work_date?: string;  // Alias for report_date
  description?: string;  // Alias for activity_description
}

export interface WorkLogUpdate {
  start_time?: string;
  end_time?: string;
  work_hours?: string;
  break_hours?: string;
  total_hours?: string;
  work_type?: string;
  activity_description?: string;
  equipment_type?: string;
  is_standard?: boolean;
  non_standard_reason?: string;
  notes?: string;
  segments?: Omit<WorkLogSegment, 'id' | 'worklog_id' | 'created_at'>[];
}

export interface WorkLogFilters {
  user_id?: number;
  project_id?: number;
  work_order_id?: number;
  equipment_id?: number;
  supplier_id?: number;
  area_id?: number;
  date_from?: string;  // Backend uses date_from, not report_date_from
  date_to?: string;    // Backend uses date_to, not report_date_to
  status?: string;
  is_standard?: boolean;
  q?: string;          // Backend uses q for search
  page?: number;       // Backend uses page, not skip
  page_size?: number;  // Backend uses page_size, not limit
  limit?: number;      // Alias for page_size
}

export interface WorkLogResponse {
  work_logs?: WorkLog[];  // Some endpoints use work_logs
  items?: WorkLog[];       // Some endpoints use items
  total: number;
  page: number;
  page_size?: number;
  total_pages: number;
}

export interface WorkLogStats {
  total_worklogs: number;
  draft_count: number;
  pending_count: number;
  submitted_count: number;
  approved_count: number;
  rejected_count: number;
  invoiced_count: number;
  total_hours: number;
  average_hours: number;
  standard_count: number;
  non_standard_count: number;
}

// === SERVICE ===

class WorkLogService {
  /**
   * קבלת רשימת דיווחי שעות
   */
  async getWorkLogs(filters: WorkLogFilters = {}): Promise<WorkLogResponse> {
    try {
      const response = await api.get('/worklogs', { params: filters });
      // Backend returns { items: [...], total, page, page_size, total_pages }
      const data = response.data;
      return {
        work_logs: data.items || data.work_logs || (Array.isArray(data) ? data : []),
        items: data.items,
        total: data.total || 0,
        page: data.page || 1,
        page_size: data.page_size || filters.page_size || 50,
        total_pages: data.total_pages || 1
      };
    } catch (error) {
      console.error('Error fetching work logs:', error);
      throw error;
    }
  }

  /**
   * קבלת דיווח שעות לפי ID
   */
  async getWorkLog(id: number): Promise<WorkLog> {
    try {
      const response = await api.get(`/worklogs/${id}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching work log:', error);
      throw error;
    }
  }

  /**
   * קבלת דיווחי המשתמש הנוכחי
   */
  async getMyWorkLogs(filters: WorkLogFilters = {}): Promise<WorkLogResponse> {
    try {
      const response = await api.get('/worklogs/my-worklogs', { params: filters });
      // Backend returns { items: [...], total, page, page_size, total_pages }
      const data = response.data;
      return {
        work_logs: data.items || data.work_logs || (Array.isArray(data) ? data : []),
        items: data.items,
        total: data.total || 0,
        page: data.page || 1,
        page_size: data.page_size || filters.page_size || 50,
        total_pages: data.total_pages || 1
      };
    } catch (error) {
      console.error('Error fetching my work logs:', error);
      throw error;
    }
  }

  /**
   * קבלת דיווחים ממתינים לאישור
   */
  async getPendingApproval(filters: WorkLogFilters = {}): Promise<WorkLog[]> {
    try {
      const response = await api.get('/worklogs/pending-approval', { params: filters });
      return Array.isArray(response.data) ? response.data : response.data.items || [];
    } catch (error) {
      console.error('Error fetching pending work logs:', error);
      throw error;
    }
  }

  /**
   * קבלת סטטיסטיקות
   */
  async getStatistics(filters: {
    user_id?: number;
    project_id?: number;
    date_from?: string;
    date_to?: string;
  } = {}): Promise<WorkLogStats> {
    try {
      const response = await api.get('/worklogs/statistics', { params: filters });
      return response.data;
    } catch (error) {
      console.error('Error fetching statistics:', error);
      throw error;
    }
  }

  /**
   * יצירת דיווח שעות חדש
   */
  async createWorkLog(workLog: WorkLogCreate): Promise<WorkLog> {
    try {
      // Handle legacy fields
      const data: any = { ...workLog };
      if (data.work_date && !data.report_date) {
        data.report_date = data.work_date;
      }
      if (data.description && !data.activity_description) {
        data.activity_description = data.description;
      }
      // Remove legacy fields before sending
      delete data.work_date;
      delete data.description;

      const response = await api.post('/worklogs', data);
      return response.data;
    } catch (error) {
      console.error('Error creating work log:', error);
      throw error;
    }
  }

  /**
   * יצירת דיווח תקן - פירוק אוטומטי
   */
  async createStandardWorkLog(data: {
    project_id?: number;
    work_order_id?: number;
    equipment_id?: number;
    supplier_id?: number;
    area_id?: number;
    report_date: string;
    work_hours?: string;
    equipment_type?: string;
    start_time?: string;
  }): Promise<WorkLog> {
    const workLog: WorkLogCreate = {
      ...data,
      report_number: 0, // Server generates
      work_hours: data.work_hours || '9.0',
      break_hours: '1.5',
      total_hours: '10.5',
      is_standard: true,
      start_time: data.start_time || '06:30:00',
    };
    return this.createWorkLog(workLog);
  }

  /**
   * יצירת דיווח לא-תקן עם מקטעים
   */
  async createNonStandardWorkLog(data: {
    project_id?: number;
    work_order_id?: number;
    equipment_id?: number;
    supplier_id?: number;
    area_id?: number;
    report_date: string;
    work_hours: string;
    break_hours?: string;
    equipment_type?: string;
    non_standard_reason: string;
    segments: Omit<WorkLogSegment, 'id' | 'worklog_id' | 'created_at'>[];
  }): Promise<WorkLog> {
    const totalWorkMinutes = data.segments
      .filter(s => s.segment_type === 'work')
      .reduce((sum, s) => sum + s.work_minutes, 0);
    const totalBreakMinutes = data.segments
      .filter(s => s.segment_type === 'break')
      .reduce((sum, s) => sum + s.break_minutes, 0);

    const workLog: WorkLogCreate = {
      ...data,
      report_number: 0, // Server generates
      work_hours: (totalWorkMinutes / 60).toFixed(2),
      break_hours: (totalBreakMinutes / 60).toFixed(2),
      total_hours: ((totalWorkMinutes + totalBreakMinutes) / 60).toFixed(2),
      is_standard: false,
    };
    return this.createWorkLog(workLog);
  }

  /**
   * עדכון דיווח שעות
   */
  async updateWorkLog(id: number, workLog: WorkLogUpdate): Promise<WorkLog> {
    try {
      const response = await api.put(`/worklogs/${id}`, workLog);
      return response.data;
    } catch (error) {
      console.error('Error updating work log:', error);
      throw error;
    }
  }

  /**
   * מחיקת דיווח שעות
   */
  async deleteWorkLog(id: number): Promise<void> {
    try {
      await api.delete(`/worklogs/${id}`);
    } catch (error) {
      console.error('Error deleting work log:', error);
      throw error;
    }
  }

  /**
   * הגשה לאישור
   */
  async submitWorkLog(id: number, notes?: string): Promise<WorkLog> {
    try {
      const response = await api.post(`/worklogs/${id}/submit`, { notes });
      return response.data;
    } catch (error) {
      console.error('Error submitting work log:', error);
      throw error;
    }
  }

  /**
   * אישור דיווח
   */
  async approveWorkLog(id: number, notes?: string): Promise<WorkLog> {
    try {
      const response = await api.post(`/worklogs/${id}/approve`, { notes });
      return response.data;
    } catch (error) {
      console.error('Error approving work log:', error);
      throw error;
    }
  }

  /**
   * דחיית דיווח
   */
  async rejectWorkLog(id: number, rejection_reason: string): Promise<WorkLog> {
    try {
      const response = await api.post(`/worklogs/${id}/reject`, { rejection_reason });
      return response.data;
    } catch (error) {
      console.error('Error rejecting work log:', error);
      throw error;
    }
  }

  /**
   * הורדת PDF
   */
  async downloadPDF(id: number): Promise<Blob> {
    try {
      const response = await api.get(`/worklogs/${id}/pdf`, {
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      console.error('Error downloading PDF:', error);
      throw error;
    }
  }
}

const workLogService = new WorkLogService();
export default workLogService;
