// src/services/invoiceService.ts
import api from './api';

export interface Invoice {
  id: number;
  invoice_number: string;
  project_id?: number;
  project_name?: string;
  supplier_id: number;
  supplier_name?: string;
  work_order_id?: number;
  invoice_date: string;
  due_date?: string;
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  amount: number; // Alias for total_amount
  status: string;
  notes?: string;
  created_by_id?: number;
  approved_by_id?: number;
  approved_at?: string;
  sent_to_supplier_at?: string;
  paid_at?: string;
  approval_notes?: string;
  created_at: string;
  updated_at?: string;
  items?: InvoiceItem[];
}

export interface InvoiceItem {
  id: number;
  invoice_id: number;
  description: string;
  quantity: number;
  unit_price: number;
  total_amount: number;
}

export interface InvoiceSummary {
  total_invoices: number;
  total_amount: number;
  pending_amount: number;
  approved_amount: number;
  paid_amount: number;
}

export interface InvoiceCreate {
  project_id?: number;
  supplier_id: number;
  work_order_id?: number;
  invoice_date?: string;
  due_date?: string;
  subtotal: number;
  tax_amount?: number;
  total_amount: number;
  notes?: string;
  items?: InvoiceItemCreate[];
}

export interface InvoiceItemCreate {
  description: string;
  quantity: number;
  unit_price: number;
}

export interface InvoiceUpdate {
  invoice_date?: string;
  due_date?: string;
  subtotal?: number;
  tax_amount?: number;
  total_amount?: number;
  status?: string;
  notes?: string;
}

class InvoiceService {
  /**
   * קבלת רשימת חשבוניות
   */
  async getInvoices(params?: {
    skip?: number;
    limit?: number;
    project_id?: number;
    supplier_id?: number;
    status?: string;
  }): Promise<Invoice[]> {
    try {
      const response = await api.get('/invoices', { params });
      return response.data || [];
    } catch (error) {
      console.error('Error fetching invoices:', error);
      throw error;
    }
  }

  /**
   * קבלת חשבונית לפי ID
   */
  async getInvoice(invoiceId: number): Promise<Invoice> {
    try {
      const response = await api.get(`/invoices/${invoiceId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching invoice:', error);
      throw error;
    }
  }

  /**
   * קבלת סיכום חשבוניות
   */
  async getInvoiceSummary(projectId?: number): Promise<InvoiceSummary> {
    try {
      const response = await api.get('/invoices/summary/stats', {
        params: projectId ? { project_id: projectId } : {}
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching invoice summary:', error);
      throw error;
    }
  }

  /**
   * יצירת חשבונית מ-work order
   */
  async createInvoiceFromWorkOrder(workOrderId: number): Promise<Invoice> {
    try {
      const response = await api.post(`/invoices/from-work-order/${workOrderId}`);
      return response.data;
    } catch (error) {
      console.error('Error creating invoice from work order:', error);
      throw error;
    }
  }

  /**
   * עדכון חשבונית
   */
  async updateInvoice(invoiceId: number, invoiceUpdate: InvoiceUpdate): Promise<Invoice> {
    try {
      const response = await api.put(`/invoices/${invoiceId}`, invoiceUpdate);
      return response.data;
    } catch (error) {
      console.error('Error updating invoice:', error);
      throw error;
    }
  }

  /**
   * אישור חשבונית
   */
  async approveInvoice(
    invoiceId: number,
    notes?: string,
    sendToSupplier: boolean = false
  ): Promise<Invoice> {
    try {
      const response = await api.post(`/invoices/${invoiceId}/approve`, {
        notes,
        send_to_supplier: sendToSupplier
      });
      return response.data;
    } catch (error) {
      console.error('Error approving invoice:', error);
      throw error;
    }
  }

  /**
   * שליחת חשבונית לספק
   */
  async sendInvoiceToSupplier(invoiceId: number): Promise<void> {
    try {
      await api.post(`/invoices/${invoiceId}/send`);
    } catch (error) {
      console.error('Error sending invoice to supplier:', error);
      throw error;
    }
  }

  /**
   * מחיקת חשבונית
   */
  async deleteInvoice(invoiceId: number): Promise<void> {
    try {
      await api.delete(`/invoices/${invoiceId}`);
    } catch (error) {
      console.error('Error deleting invoice:', error);
      throw error;
    }
  }
}

const invoiceService = new InvoiceService();
export default invoiceService;
