
// src/pages/Invoices/InvoiceDetail.tsx
// דף פרטי חשבונית — /invoices/{id}

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowRight, FileText, Loader2, AlertCircle,
  Printer, Mail, ReceiptText, Building2, Calendar,
  DollarSign, Truck, CreditCard
} from 'lucide-react';
import api from '../../services/api';
import UnifiedLoader from '../../components/common/UnifiedLoader';

interface InvoiceItem {
  id: number;
  worklog_id: number | null;
  description: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  report_date: string | null;
  total_hours: number | null;
  hourly_rate: number | null;
}

interface InvoiceFull {
  id: number;
  invoice_number: string;
  supplier_id: number;
  supplier_name: string | null;
  project_id: number | null;
  project_name: string | null;
  project_code: string | null;
  issue_date: string | null;
  due_date: string | null;
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  paid_amount: number;
  balance_due: number;
  status: string;
  notes: string | null;
  created_at: string | null;
}

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  PENDING:  { label: 'ממתין לתשלום', color: 'bg-yellow-100 text-yellow-800 border-yellow-300' },
  APPROVED: { label: 'מאושר',         color: 'bg-green-100  text-green-800  border-green-300'  },
  PAID:     { label: 'שולם',          color: 'bg-blue-100   text-blue-800   border-blue-300'   },
  DRAFT:    { label: 'טיוטה',         color: 'bg-gray-100   text-gray-700   border-gray-300'   },
  CANCELLED:{ label: 'בוטל',          color: 'bg-red-100    text-red-700    border-red-300'    },
};

const fmtDate = (d: string | null) => d ? new Date(d).toLocaleDateString('he-IL') : '—';
const fmtILS  = (n: number) => `₪${n.toLocaleString('he-IL', { minimumFractionDigits: 2 })}`;

const InvoiceDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [invoice, setInvoice] = useState<InvoiceFull | null>(null);
  const [items, setItems] = useState<InvoiceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState('');

  const showToast = (msg: string, type = 'success') => {
    if ((window as any).showToast) (window as any).showToast(msg, type);
  };

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get(`/invoices/${id}/items`);
      setInvoice(res.data.invoice);
      setItems(res.data.items || []);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'שגיאה בטעינת החשבונית');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [id]);

  const handleMarkPaid = async () => {
    if (!window.confirm('לסמן חשבונית זו כשולמה?')) return;
    setActionLoading(true);
    try {
      await api.post(`/invoices/${id}/mark-paid`);
      showToast('החשבונית סומנה כשולמה ✅', 'success');
      load();
    } catch (e: any) {
      showToast(e?.response?.data?.detail || 'שגיאה', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSendEmail = async () => {
    setActionLoading(true);
    try {
      await api.post(`/invoices/${id}/send`);
      showToast('החשבונית נשלחה לספק במייל ✉️', 'success');
    } catch (e: any) {
      showToast(e?.response?.data?.detail || 'שגיאה בשליחת המייל', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  if (loading) return <UnifiedLoader size="full" />;

  if (error || !invoice) return (
    <div className="min-h-screen bg-kkl-bg flex items-center justify-center" dir="rtl">
      <div className="text-center">
        <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-3" />
        <p className="text-red-700">{error || 'חשבונית לא נמצאה'}</p>
        <button onClick={() => navigate('/invoices')} className="mt-4 text-kkl-green text-sm underline">
          חזרה לרשימת חשבוניות
        </button>
      </div>
    </div>
  );

  const st = STATUS_MAP[invoice.status] || STATUS_MAP.PENDING;
  const isPaid = invoice.status === 'PAID';

  return (
    <div className="min-h-screen bg-kkl-bg print:bg-white" dir="rtl">
      <div className="max-w-4xl mx-auto px-4 py-6 print:py-2 print:px-0">

        {/* Header — hidden on print */}
        <div className="mb-6 print:hidden">
          <button onClick={() => navigate('/invoices')} className="text-kkl-green text-sm flex items-center gap-1 mb-4">
            <ArrowRight className="w-4 h-4" />
            חזרה לחשבוניות
          </button>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-kkl-green rounded-xl flex items-center justify-center">
                <ReceiptText className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-kkl-text">חשבונית {invoice.invoice_number}</h1>
                <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border ${st.color}`}>
                  {st.label}
                </span>
              </div>
            </div>
            {/* Action Buttons */}
            <div className="flex gap-2">
              <button
                onClick={handlePrint}
                className="flex items-center gap-1.5 px-3 py-2 border border-kkl-border rounded-lg text-sm text-gray-600 hover:bg-gray-50 transition-colors"
              >
                <Printer className="w-4 h-4" />
                הדפס
              </button>
              <button
                onClick={handleSendEmail}
                disabled={actionLoading}
                className="flex items-center gap-1.5 px-3 py-2 border border-kkl-border rounded-lg text-sm text-gray-600 hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                <Mail className="w-4 h-4" />
                שלח לספק
              </button>
              {!isPaid && (
                <button
                  onClick={handleMarkPaid}
                  disabled={actionLoading}
                  className="flex items-center gap-1.5 px-4 py-2 bg-kkl-green text-white rounded-lg text-sm hover:bg-kkl-green-dark transition-colors disabled:opacity-50"
                >
                  {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CreditCard className="w-4 h-4" />}
                  סמן כשולם
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Invoice Header Card */}
        <div className="bg-white rounded-xl shadow-sm border border-kkl-border p-6 mb-4 print:shadow-none print:border print:rounded-none">
          {/* Print header */}
          <div className="hidden print:block text-center mb-6">
            <h1 className="text-2xl font-bold">חשבונית מספר: {invoice.invoice_number}</h1>
            <p className="text-gray-500">קרן קיימת לישראל — מערכת ניהול יערות</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Supplier */}
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 bg-kkl-green-light rounded-lg flex items-center justify-center flex-shrink-0">
                <Truck className="w-4 h-4 text-kkl-green" />
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-0.5">ספק</p>
                <p className="text-sm font-semibold text-kkl-text">{invoice.supplier_name || `ספק #${invoice.supplier_id}`}</p>
              </div>
            </div>

            {/* Project */}
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
                <Building2 className="w-4 h-4 text-blue-600" />
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-0.5">פרויקט</p>
                <p className="text-sm font-semibold text-kkl-text">
                  {invoice.project_name || '—'}
                  {invoice.project_code && <span className="text-gray-400 text-xs block">{invoice.project_code}</span>}
                </p>
              </div>
            </div>

            {/* Issue Date */}
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 bg-orange-50 rounded-lg flex items-center justify-center flex-shrink-0">
                <Calendar className="w-4 h-4 text-orange-600" />
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-0.5">תאריך הנפקה</p>
                <p className="text-sm font-semibold text-kkl-text">{fmtDate(invoice.issue_date)}</p>
                <p className="text-xs text-gray-500">לתשלום עד: {fmtDate(invoice.due_date)}</p>
              </div>
            </div>

            {/* Status / Balance */}
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 bg-kkl-green-light rounded-lg flex items-center justify-center flex-shrink-0">
                <DollarSign className="w-4 h-4 text-kkl-green" />
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-0.5">יתרה לתשלום</p>
                <p className={`text-sm font-bold ${isPaid ? 'text-green-600' : 'text-kkl-text'}`}>
                  {fmtILS(invoice.balance_due)}
                </p>
                {isPaid && <p className="text-xs text-green-600 font-medium">✅ שולם</p>}
              </div>
            </div>
          </div>

          {invoice.notes && (
            <div className="mt-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
              <p className="text-xs text-gray-500 mb-0.5">הערות</p>
              <p className="text-sm text-gray-700">{invoice.notes}</p>
            </div>
          )}
        </div>

        {/* Invoice Items Table */}
        <div className="bg-white rounded-xl shadow-sm border border-kkl-border overflow-hidden mb-4 print:shadow-none print:border print:rounded-none">
          <div className="px-4 py-3 border-b border-kkl-border bg-gray-50 flex items-center gap-2">
            <FileText className="w-4 h-4 text-kkl-green" />
            <h2 className="text-sm font-semibold text-kkl-text">פריטי חשבונית</h2>
            <span className="text-xs text-gray-400 mr-auto">{items.length} פריטים</span>
          </div>

          {items.length === 0 ? (
            <div className="text-center py-12 text-gray-400 text-sm">אין פריטים בחשבונית זו</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-kkl-border">
                  <tr>
                    <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500">תיאור</th>
                    <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500">תאריך</th>
                    <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500">שעות</th>
                    <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500">תעריף</th>
                    <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500">כמות</th>
                    <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 bg-kkl-green-light">סה"כ</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item, idx) => (
                    <tr key={item.id} className={`border-b border-kkl-border ${idx % 2 === 0 ? '' : 'bg-gray-50/50'}`}>
                      <td className="px-4 py-3 text-sm text-kkl-text max-w-xs">
                        <p className="font-medium leading-snug">{item.description || '—'}</p>
                        {item.worklog_id && (
                          <p className="text-xs text-gray-400 mt-0.5">דיווח #{item.worklog_id}</p>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center text-sm text-gray-600">
                        {item.report_date ? fmtDate(item.report_date) : '—'}
                      </td>
                      <td className="px-4 py-3 text-center text-sm">
                        {item.total_hours != null ? (
                          <span className="font-medium">{item.total_hours.toFixed(1)}h</span>
                        ) : '—'}
                      </td>
                      <td className="px-4 py-3 text-center text-sm">
                        {item.hourly_rate != null ? `₪${item.hourly_rate}` : '—'}
                      </td>
                      <td className="px-4 py-3 text-center text-sm text-gray-600">{item.quantity}</td>
                      <td className="px-4 py-3 text-center bg-kkl-green-light/30">
                        <span className="text-sm font-bold text-kkl-text">{fmtILS(item.total_price)}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Totals Summary */}
        <div className="bg-white rounded-xl shadow-sm border border-kkl-border p-5 print:shadow-none print:border print:rounded-none">
          <div className="max-w-sm mr-auto space-y-2">
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-600">סכום לפני מע"מ</span>
              <span className="font-medium text-kkl-text">{fmtILS(invoice.subtotal)}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-600">מע"מ (17%)</span>
              <span className="font-medium text-kkl-text">{fmtILS(invoice.tax_amount)}</span>
            </div>
            <div className="h-px bg-kkl-border my-2" />
            <div className="flex justify-between items-center">
              <span className="text-base font-bold text-kkl-text">סה"כ לתשלום</span>
              <span className="text-xl font-bold text-kkl-green">{fmtILS(invoice.total_amount)}</span>
            </div>
            {invoice.paid_amount > 0 && (
              <>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-green-700">שולם</span>
                  <span className="text-green-700 font-medium">- {fmtILS(invoice.paid_amount)}</span>
                </div>
                <div className="flex justify-between items-center text-sm font-bold">
                  <span className={isPaid ? 'text-green-700' : 'text-red-600'}>יתרה</span>
                  <span className={isPaid ? 'text-green-700' : 'text-red-600'}>{fmtILS(invoice.balance_due)}</span>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Print Footer */}
        <div className="hidden print:block text-center mt-8 text-xs text-gray-400">
          <p>מסמך זה הופק אוטומטית ממערכת Forewise — קרן קיימת לישראל</p>
          <p>{invoice.invoice_number} | {fmtDate(invoice.issue_date)}</p>
        </div>
      </div>
    </div>
  );
};

export default InvoiceDetail;
