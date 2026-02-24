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

class ProjectService {
  /**
   * קבלת רשימת פרויקטים
   */
  async getProjects(filters: ProjectFilters = {}): Promise<ProjectResponse> {
    try {
      const response = await api.get('/projects', { params: filters });
      // המרה מ-PaginatedResponse ל-ProjectResponse
      return {
        projects: response.data.items || [],
        total: response.data.total || 0,
        page: response.data.page || 1,
        limit: response.data.page_size || 20,
        total_pages: response.data.pages || 1
      };
    } catch (error) {
      console.error('Error fetching projects:', error);
      throw error;
    }
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
   * קבלת סטטיסטיקות פרויקט
   */
  async getProjectStatistics(id: number): Promise<any> {
    try {
      const response = await api.get(`/projects/${id}/statistics`);
      return response.data;
    } catch (error) {
      console.error('Error fetching project statistics:', error);
      throw error;
    }
  }

  /**
   * עדכון סטטוס פרויקט
   */
  async updateProjectStatus(id: number, status: string): Promise<Project> {
    try {
      const response = await api.put(`/projects/${id}/status`, { status });
      return response.data;
    } catch (error) {
      console.error('Error updating project status:', error);
      throw error;
    }
  }
}

const projectService = new ProjectService();
export default projectService;

