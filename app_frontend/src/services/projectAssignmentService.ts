// src/services/projectAssignmentService.ts
import api from './api';

export interface ProjectAssignment {
  id: number;
  project_id: number;
  user_id: number;
  role: string;
  status: string;
  start_date: string;
  end_date?: string;
  allocation_percentage: number;
  estimated_hours?: number;
  actual_hours?: number;
  can_approve_reports: boolean;
  can_manage_team: boolean;
  can_edit_budget: boolean;
  responsibilities?: string;
  notes?: string;
  approved_by_id?: number;
  approved_at?: string;
  // Joined fields
  user_name?: string;
  user_email?: string;
  project_name?: string;
  project_code?: string;
}

export interface TeamMember {
  user_id: number;
  user_name: string;
  user_email?: string;
  role: string;
  status: string;
  start_date: string;
  end_date?: string;
  allocation_percentage: number;
  can_approve_reports: boolean;
  can_manage_team: boolean;
  can_edit_budget: boolean;
}

export interface AssignmentCreate {
  project_id: number;
  user_id: number;
  role: string;
  start_date: string;
  end_date?: string;
  allocation_percentage?: number;
  can_approve_reports?: boolean;
  can_manage_team?: boolean;
  can_edit_budget?: boolean;
  responsibilities?: string;
  notes?: string;
}

export interface UserProject {
  project_id: number;
  project_name: string;
  project_code: string;
  role: string;
  status: string;
  start_date: string;
  end_date?: string;
}

class ProjectAssignmentService {
  /**
   * Get current user's project assignments
   */
  async getMyAssignments(activeOnly: boolean = true): Promise<UserProject[]> {
    try {
      const response = await api.get('/project-assignments/my-assignments', {
        params: { active_only: activeOnly }
      });
      return response.data.projects || [];
    } catch (error) {
      console.error('Error fetching my assignments:', error);
      throw error;
    }
  }

  /**
   * Get project team members
   */
  async getProjectTeam(projectId: number, includeInactive: boolean = false): Promise<TeamMember[]> {
    try {
      const response = await api.get(`/project-assignments/project/${projectId}/team`, {
        params: { include_inactive: includeInactive }
      });
      return response.data.team_members || [];
    } catch (error) {
      console.error('Error fetching project team:', error);
      throw error;
    }
  }

  /**
   * Get user's projects
   */
  async getUserProjects(userId: number, activeOnly: boolean = true): Promise<UserProject[]> {
    try {
      const response = await api.get(`/project-assignments/user/${userId}/projects`, {
        params: { active_only: activeOnly }
      });
      return response.data.projects || [];
    } catch (error) {
      console.error('Error fetching user projects:', error);
      throw error;
    }
  }

  /**
   * Add user to project
   */
  async addTeamMember(assignment: AssignmentCreate): Promise<ProjectAssignment> {
    try {
      const response = await api.post('/project-assignments', assignment);
      return response.data;
    } catch (error) {
      console.error('Error adding team member:', error);
      throw error;
    }
  }

  /**
   * Remove user from project
   */
  async removeTeamMember(assignmentId: number, reason: string): Promise<void> {
    try {
      await api.delete(`/project-assignments/${assignmentId}`, {
        params: { reason }
      });
    } catch (error) {
      console.error('Error removing team member:', error);
      throw error;
    }
  }

  /**
   * Bulk assign users to project
   */
  async bulkAssign(
    projectId: number,
    userIds: number[],
    role: string,
    startDate?: string,
    endDate?: string
  ): Promise<any> {
    try {
      const response = await api.post(`/project-assignments/project/${projectId}/bulk-assign`, {
        user_ids: userIds,
        role: role,
        start_date: startDate,
        end_date: endDate
      });
      return response.data;
    } catch (error) {
      console.error('Error bulk assigning users:', error);
      throw error;
    }
  }

  /**
   * Get available assignment roles
   */
  async getAssignmentRoles(): Promise<{ value: string; label: string }[]> {
    try {
      const response = await api.get('/project-assignments/roles/list');
      return response.data;
    } catch (error) {
      console.error('Error fetching roles:', error);
      // Return default roles if API fails
      return [
        { value: 'manager', label: 'מנהל פרויקט' },
        { value: 'supervisor', label: 'מפקח' },
        { value: 'worker', label: 'עובד' },
        { value: 'specialist', label: 'מומחה' },
        { value: 'consultant', label: 'יועץ' },
        { value: 'observer', label: 'משקיף' },
      ];
    }
  }

  /**
   * Check user availability
   */
  async checkAvailability(
    userId: number,
    startDate: string,
    endDate: string,
    hoursRequired: number
  ): Promise<any> {
    try {
      const response = await api.get('/project-assignments/availability/check', {
        params: {
          user_id: userId,
          start_date: startDate,
          end_date: endDate,
          hours_required: hoursRequired
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error checking availability:', error);
      throw error;
    }
  }
}

const projectAssignmentService = new ProjectAssignmentService();
export default projectAssignmentService;

