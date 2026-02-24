// Activity Type Service
import api from "./api";

export interface ActivityType {
  id: number;
  code: string;
  name: string;
  description?: string;
  is_active: boolean;
}

export const activityTypeService = {
  getAll: async (): Promise<ActivityType[]> => {
    try {
      const response = await api.get("/activity-types");
      return response.data?.items || response.data || [];
    } catch (error) {
      console.error("Error fetching activity types:", error);
      return [];
    }
  },

  getById: async (id: number): Promise<ActivityType | null> => {
    try {
      const response = await api.get(`/activity-types/${id}`);
      return response.data;
    } catch (error) {
      console.error("Error fetching activity type:", error);
      return null;
    }
  }
};

// Alias for backwards compatibility
export const getActivityTypes = activityTypeService.getAll;

export default activityTypeService;
