// src/services/supportTicketService.ts
import api from './api';

export interface Ticket {
  id: number;
  title: string;
  description: string;
  status: string;
  priority: string;
  type: string;
  created_at: string;
  updated_at: string;
  created_by: string;
  assigned_to?: string;
  comments?: TicketComment[];
}

export interface TicketComment {
  id: number;
  ticket_id: number;
  content: string;
  created_at: string;
  created_by: string;
  is_staff: boolean;
}

export interface TicketCreate {
  title: string;
  description: string;
  priority: string;
  type: string;
}

export interface TicketUpdate {
  title?: string;
  description?: string;
  status?: string;
  priority?: string;
  type?: string;
  assigned_to?: number;
}

export interface TicketFilters {
  status?: string;
  priority?: string;
  type?: string;
  search?: string;
  page?: number;
  per_page?: number;  // לפי החוזה - per_page במקום limit
}

export interface TicketResponse {
  tickets: Ticket[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

class SupportTicketService {
  /**
   * קבלת רשימת קריאות שירות
   */
  async getTickets(filters: TicketFilters = {}): Promise<TicketResponse> {
    try {
      const response = await api.get('/support-tickets', { params: filters });
      // אם ה-API מחזיר List ישירות
      if (Array.isArray(response.data)) {
        return {
          tickets: response.data,
          total: response.data.length,
          page: 1,
          limit: response.data.length,
          total_pages: 1
        };
      }
      // אם זה PaginatedResponse
      return {
        tickets: response.data.items || [],
        total: response.data.total || 0,
        page: response.data.page || 1,
        limit: response.data.page_size || 20,
        total_pages: response.data.pages || 1
      };
    } catch (error) {
      console.error('Error fetching tickets:', error);
      throw error;
    }
  }

  /**
   * קבלת קריאת שירות לפי ID
   */
  async getTicketById(id: number): Promise<Ticket> {
    try {
      const response = await api.get(`/support-tickets/${id}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching ticket:', error);
      throw error;
    }
  }

  /**
   * יצירת קריאת שירות חדשה
   */
  async createTicket(ticket: TicketCreate): Promise<Ticket> {
    try {
      const response = await api.post('/support-tickets', ticket);
      return response.data;
    } catch (error) {
      console.error('Error creating ticket:', error);
      throw error;
    }
  }

  /**
   * עדכון קריאת שירות
   */
  async updateTicket(id: number, ticket: TicketUpdate): Promise<Ticket> {
    try {
      const response = await api.put(`/support-tickets/${id}`, ticket);
      return response.data;
    } catch (error) {
      console.error('Error updating ticket:', error);
      throw error;
    }
  }

  /**
   * מחיקת קריאת שירות
   */
  async deleteTicket(id: number): Promise<void> {
    try {
      await api.delete(`/support-tickets/${id}`);
    } catch (error) {
      console.error('Error deleting ticket:', error);
      throw error;
    }
  }

  /**
   * הוספת תגובה לקריאת שירות
   */
  async addComment(ticketId: number, content: string): Promise<TicketComment> {
    try {
      const response = await api.post(`/support-tickets/${ticketId}/comments`, { content });
      return response.data;
    } catch (error) {
      console.error('Error adding comment:', error);
      throw error;
    }
  }

  /**
   * קבלת תגובות של קריאת שירות
   */
  async getComments(ticketId: number): Promise<TicketComment[]> {
    try {
      const response = await api.get(`/support-tickets/${ticketId}/comments`);
      return Array.isArray(response.data) ? response.data : (response.data.items || []);
    } catch (error) {
      console.error('Error fetching comments:', error);
      throw error;
    }
  }

  /**
   * קבלת קריאות שירות של המשתמש הנוכחי
   */
  async getMyTickets(filters: Omit<TicketFilters, 'created_by'> = {}): Promise<TicketResponse> {
    try {
      const response = await api.get('/support-tickets/my', { params: filters });
      if (Array.isArray(response.data)) {
        return {
          tickets: response.data,
          total: response.data.length,
          page: 1,
          limit: response.data.length,
          total_pages: 1
        };
      }
      return {
        tickets: response.data.items || [],
        total: response.data.total || 0,
        page: response.data.page || 1,
        limit: response.data.page_size || 20,
        total_pages: response.data.pages || 1
      };
    } catch (error) {
      console.error('Error fetching my tickets:', error);
      throw error;
    }
  }
}

const supportTicketService = new SupportTicketService();
export default supportTicketService;










