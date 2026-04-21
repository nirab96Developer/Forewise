// src/services/projectService.ts
import api from './api';

// Location object embedded in project
export interface ProjectLocation {
  id: number;
  code: string;
  name: string;
  latitude?: number;
  longitude?: number;
  address?: string;
  metadata_json?: string;
}

export interface Project {
  id: number;
  name: string;
  code: string;
  description?: string;
  status: string;
  priority: string;
  progress_percentage: number;
  planned_start_date?: string;
  planned_end_date?: string;
  actual_start_date?: string;
  actual_end_date?: string;
  allocated_budget?: number;
  spent_budget?: number;
  manager_id?: number;
  manager_name?: string;
  region_id?: number;
  region_name?: string;
  area_id?: number;
  area_name?: string;
  location_id?: number;
  location_name?: string;
  location?: ProjectLocation;  // Full location object with geo data
  created_at: string;
  updated_at?: string;
}

export interface ProjectCreate {
  name: string;
  code: string;
  description?: string;
  status?: string;
  priority?: string;
  planned_start_date?: string;
  planned_end_date?: string;
  allocated_budget?: number;
  manager_id?: number;
  region_id?: number;
  area_id?: number;
  location_id?: number;
  project_type?: string;
  objectives?: object;
  deliverables?: object;
  requires_equipment?: boolean;
  requires_suppliers?: boolean;
}

export interface ProjectUpdate {
  name?: string;
  code?: string;
  description?: string;
  status?: string;
  priority?: string;
  planned_start_date?: string;
  planned_end_date?: string;
  actual_start_date?: string;
  actual_end_date?: string;
  allocated_budget?: number;
  progress_percentage?: number;
  manager_id?: number;
  region_id?: number;
  area_id?: number;
  location_id?: number;
  project_type?: string;
  objectives?: object;
  deliverables?: object;
  requires_equipment?: boolean;
  requires_suppliers?: boolean;
  is_active?: boolean;
}

export interface ProjectFilters {
  status?: string;
  region_id?: number;
  area_id?: number;
  location_id?: number;
  manager_id?: number;
  start_date?: string;
  end_date?: string;
  search?: string;
  page?: number;
  per_page?: number;  // לפי החוזה - per_page במקום limit
  my_projects?: boolean;  // Filter to only user's assigned projects
}

export interface ProjectResponse {
  projects: Project[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

// In-flight deduplication: if the same request is already in-flight, reuse its promise
const _inflight: Map<string, Promise<ProjectResponse>> = new Map();

class ProjectService {
  /**
   * קבלת רשימת פרויקטים — עם deduplication של קריאות כפולות
   */
  async getProjects(filters: ProjectFilters = {}, signal?: AbortSignal): Promise<ProjectResponse> {
    const key = JSON.stringify(filters);

    // If identical request is already in-flight, share its promise
    if (_inflight.has(key)) {
      return _inflight.get(key)!;
    }

    const promise = api.get('/projects', { params: filters, signal })
      .then(response => ({
        projects: response.data.items || [],
        total: response.data.total || 0,
        page: response.data.page || 1,
        limit: response.data.page_size || 20,
        // BE returns the field as `total_pages` (was wrongly read as `pages`,
        // which always fell back to 1 and broke pagination on >50 projects).
        total_pages: response.data.total_pages || response.data.pages || 1,
      }))
      .finally(() => {
        _inflight.delete(key);
      });

    _inflight.set(key, promise);
    return promise;
  }

  /** נקה cache בין פעולות (יצירה/עריכה/מחיקה) */
  invalidateCache() {
    _inflight.clear();
  }

  /**
   * קבלת פרויקט לפי code
   */
  async getProjectByCode(code: string): Promise<Project> {
    try {
      const response = await api.get(`/projects/code/${code}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching project by code:', error);
      throw error;
    }
  }

  /**
   * קבלת פרויקט לפי ID
   */
  async getProject(id: number): Promise<Project> {
    try {
      const response = await api.get(`/projects/${id}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching project:', error);
      throw error;
    }
  }

  /**
   * יצירת פרויקט חדש
   */
  async createProject(project: ProjectCreate): Promise<Project> {
    try {
      const response = await api.post('/projects', project);
      return response.data;
    } catch (error) {
      console.error('Error creating project:', error);
      throw error;
    }
  }

  /**
   * עדכון פרויקט
   */
  async updateProject(id: number, project: ProjectUpdate): Promise<Project> {
    try {
      const response = await api.put(`/projects/${id}`, project);
      return response.data;
    } catch (error) {
      console.error('Error updating project:', error);
      throw error;
    }
  }

  /**
   * מחיקת פרויקט
   */
  async deleteProject(id: number): Promise<void> {
    try {
      await api.delete(`/projects/${id}`);
    } catch (error) {
      console.error('Error deleting project:', error);
      throw error;
    }
  }

  /**
   * קבלת סטטיסטיקות פרויקטים גלובליות.
   * (אין endpoint per-id ב-BE; השדה היחיד הוא `/projects/statistics`.)
   */
  async getProjectStatistics(): Promise<any> {
    try {
      const response = await api.get('/projects/statistics');
      return response.data;
    } catch (error) {
      console.error('Error fetching project statistics:', error);
      throw error;
    }
  }

  /**
   * עדכון סטטוס פרויקט — דרך updateProject הסטנדרטי.
   * (לא היה endpoint `/projects/:id/status` ב-BE; משתמשים ב-PUT `/projects/:id`.)
   */
  async updateProjectStatus(id: number, status: string): Promise<Project> {
    return this.updateProject(id, { status });
  }
}

const projectService = new ProjectService();
export default projectService;

