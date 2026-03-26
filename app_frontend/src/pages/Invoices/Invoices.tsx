
// src/pages/Invoices/Invoices.tsx
// דף חשבוניות - רשימת חשבוניות וניהול
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { 
  AlertCircle, 
  Receipt,
  Eye,
  Download,
  DollarSign
} from "lucide-react";
import invoiceService, { Invoice } from "../../services/invoiceService";
import UnifiedLoader from "../../components/common/UnifiedLoader";
import api from "../../services/api";

const Invoices: React.FC = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [summary, setSummary] = useState<any>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const [invoicesRaw, summaryData] = await Promise.all([
          invoiceService.getInvoices({}).catch(() => []),
          invoiceService.getInvoiceSummary().catch(() => null)
        ]);

        // Handle both array and { items: [...] } response shapes
        const invoicesData: Invoice[] = Array.isArray(invoicesRaw)
          ? invoicesRaw
          : Array.isArray((invoicesRaw as any)?.items)
          ? (invoicesRaw as any).items
          : [];

        // Map invoices to ensure work_order_id is always a number
        const mappedInvoices: Invoice[] = invoicesData.map(inv => ({
          ...inv,
          work_order_id: inv.work_order_id ?? 0
        }));
        setInvoices(mappedInvoices);
        setSummary(summaryData);
        setIsLoading(false);
      } catch (err) {
        console.error('Error loading invoices:', err);
        setError('שגיאה בטעינת חשבוניות');
        setIsLoading(false);
      }
    };

    loadData();
  }, []);

  if (isLoading) return <UnifiedLoader size="full" />;

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h2 className="text-red-600 font-medium mb-2">שגיאה</h2>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    const upper = (status || '').toUpperCase();
    if (upper === 'DRAFT') return 'bg-gray-100 text-gray-700';
    if (upper === 'APPROVED') return 'bg-green-100 text-green-700';
    if (upper === 'SENT') return 'bg-blue-100 text-blue-700';
    if (upper === 'PAID') return 'bg-purple-100 text-purple-700';
    if (upper === 'CANCELLED') return 'bg-red-100 text-red-700';
    return 'bg-gray-100 text-gray-700';
  };

  const getStatusText = (status: string) => {
    const map: Record<string, string> = {
      DRAFT: 'טיוטה', APPROVED: 'מאושר', SENT: 'נשלח',
      PAID: 'שולם', CANCELLED: 'בוטל',
    };
    return map[(status || '').toUpperCase()] || status || 'לא ידוע';
  };

  const handleExportExcel = async () => {
    try {
      const response = await api.get(`/reports/export/excel?type=invoices`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `invoices_${new Date().toISOString().slice(0, 10)}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      (window as any).showToast?.("שגיאה בייצוא Excel", "error");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6" dir="rtl">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">חשבוניות</h1>
            <p className="text-sm text-gray-600 mt-1">ניהול וצפייה בחשבוניות</p>
          </div>
          <button
            onClick={handleExportExcel}
            className="inline-flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 px-4 py-2 text-sm font-medium text-green-700 hover:bg-green-100 transition-colors"
          >
            <Download className="w-4 h-4" />
ייצוא Excel
          </button>
        </div>

        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
            <div className="bg-white rounded-2xl p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-gray-500">סה"כ חשבוניות</div>
                  <div className="text-3xl font-semibold mt-2 text-gray-900">
                    {summary.total ?? summary.total_invoices ?? invoices.length}
                  </div>
                </div>
                <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center">
                  <Receipt className="w-6 h-6 text-blue-600" />
                </div>
              </div>
            </div>
            <div className="bg-white rounded-2xl p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-gray-500">סה"כ סכום</div>
                  <div className="text-3xl font-semibold mt-2 text-gray-900">
{new Intl.NumberFormat('he-IL').format(summary.total_amount || 0)}
                  </div>
                </div>
                <div className="w-12 h-12 bg-green-50 rounded-xl flex items-center justify-center">
                  <DollarSign className="w-6 h-6 text-green-600" />
                </div>
              </div>
            </div>
            <div className="bg-white rounded-2xl p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-gray-500">ממתין לתשלום</div>
                  <div className="text-3xl font-semibold mt-2 text-gray-900">
{new Intl.NumberFormat('he-IL').format(summary.balance_due ?? summary.pending_amount ?? 0)}
                  </div>
                  {(summary.overdue_count ?? 0) > 0 && (
                    <div className="mt-1 inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-700">
                      {summary.overdue_count} באיחור
                    </div>
                  )}
                </div>
                <div className="w-12 h-12 bg-orange-50 rounded-xl flex items-center justify-center">
                  <AlertCircle className="w-6 h-6 text-orange-600" />
                </div>
              </div>
            </div>
            <div className="bg-white rounded-2xl p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-gray-500">שולם</div>
                  <div className="text-3xl font-semibold mt-2 text-green-700">
{new Intl.NumberFormat('he-IL').format(summary.paid_amount || 0)}
                  </div>
                </div>
                <div className="w-12 h-12 bg-green-50 rounded-xl flex items-center justify-center">
                  <DollarSign className="w-6 h-6 text-green-600" />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Invoices Table */}
        <div className="bg-white rounded-2xl shadow-sm">
          <div className="px-6 py-4 border-b">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">רשימת חשבוניות</h3>
            </div>
          </div>
          
          {invoices.length === 0 ? (
            <div className="p-16 text-center">
              <div className="w-24 h-24 bg-gradient-to-br from-gray-100 to-gray-200 rounded-full flex items-center justify-center mx-auto mb-6">
                <Receipt className="w-12 h-12 text-gray-400" />
              </div>
              <h3 className="text-xl font-semibold text-gray-800 mb-2">אין חשבוניות עדיין</h3>
              <p className="text-gray-500 mb-6 max-w-sm mx-auto">
                חשבוניות יופיעו כאן לאחר אישור הזמנות עבודה על ידי ספקים
              </p>
              <div className="flex items-center justify-center gap-3">
                <button 
                  onClick={() => navigate('/work-orders')}
                  className="px-5 py-2.5 bg-gradient-to-r from-kkl-green to-green-600 text-white rounded-lg font-medium hover:shadow-lg transition-all"
                >
                  צפה בהזמנות עבודה
                </button>
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b bg-gray-50">
                    <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">מספר חשבונית</th>
                    <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">פרויקט</th>
                    <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">ספק</th>
                    <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">סכום</th>
                    <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">סטטוס</th>
                    <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">תאריך</th>
                    <th className="text-center px-6 py-3 text-xs font-medium text-gray-500 uppercase">פעולות</th>
                  </tr>
                </thead>
                <tbody>
                  {invoices.map((invoice) => (
                    <tr key={invoice.id} className="border-b hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4">
                        <span className="text-sm font-medium text-gray-900">{invoice.invoice_number || `#${invoice.id}`}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`text-sm ${invoice.project_name ? 'text-gray-900' : 'text-gray-300'}`}>{invoice.project_name || '—'}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`text-sm ${invoice.supplier_name ? 'text-gray-900' : 'text-gray-300'}`}>{invoice.supplier_name || '—'}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm font-medium text-gray-900">
{new Intl.NumberFormat('he-IL').format(invoice.amount || 0)}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${getStatusColor(invoice.status)}`}>
                          {getStatusText(invoice.status)}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm text-gray-600">
                          {invoice.created_at ? new Date(invoice.created_at).toLocaleDateString('he-IL') : 'לא צוין'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center justify-center gap-2">
                          <button 
                            onClick={() => navigate(`/invoices/${invoice.id}`)}
                            className="p-2 hover:bg-gray-100 rounded-lg"
                            title="צפייה"
                          >
                            <Eye className="w-4 h-4 text-gray-600" />
                          </button>
                          <button 
                            className="p-2 hover:bg-gray-100 rounded-lg"
                            title="הורדה"
                          >
                            <Download className="w-4 h-4 text-gray-600" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Invoices;
