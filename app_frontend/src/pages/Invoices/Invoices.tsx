
// src/pages/Invoices/Invoices.tsx
// דף חשבוניות - רשימת חשבוניות וניהול
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { 
  Loader2, 
  AlertCircle, 
  Receipt,
  Eye,
  Download,
  DollarSign
} from "lucide-react";
import invoiceService, { Invoice } from "../../services/invoiceService";

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

        const [invoicesData, summaryData] = await Promise.all([
          invoiceService.getInvoices().catch(() => []),
          invoiceService.getInvoiceSummary().catch(() => null)
        ]);

        // Map invoices to ensure work_order_id is always a number
        const mappedInvoices: Invoice[] = Array.isArray(invoicesData) 
          ? invoicesData.map(inv => ({
              ...inv,
              work_order_id: inv.work_order_id ?? 0
            }))
          : [];
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex items-center gap-2 bg-white p-4 rounded-lg shadow-sm">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span>טוען נתונים...</span>
        </div>
      </div>
    );
  }

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
    switch (status?.toLowerCase()) {
      case 'draft':
      case 'טיוטה':
        return 'bg-gray-100 text-gray-700';
      case 'approved':
      case 'מאושר':
        return 'bg-green-100 text-green-700';
      case 'sent':
      case 'נשלח':
        return 'bg-blue-100 text-blue-700';
      case 'paid':
      case 'שולם':
        return 'bg-purple-100 text-purple-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getStatusText = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'draft':
        return 'טיוטה';
      case 'approved':
        return 'מאושר';
      case 'sent':
        return 'נשלח';
      case 'paid':
        return 'שולם';
      default:
        return status || 'לא ידוע';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6" dir="rtl">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">חשבוניות</h1>
          <p className="text-sm text-gray-600 mt-1">ניהול וצפייה בחשבוניות</p>
        </div>

        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <div className="bg-white rounded-2xl p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-gray-500">סה"כ חשבוניות</div>
                  <div className="text-3xl font-semibold mt-2 text-gray-900">
                    {summary.total_invoices || invoices.length}
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
                    ₪{new Intl.NumberFormat('he-IL').format(summary.total_amount || 0)}
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
                    ₪{new Intl.NumberFormat('he-IL').format(summary.pending_amount || 0)}
                  </div>
                </div>
                <div className="w-12 h-12 bg-orange-50 rounded-xl flex items-center justify-center">
                  <AlertCircle className="w-6 h-6 text-orange-600" />
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
                        <span className="text-sm text-gray-600">{invoice.project_name || 'לא צוין'}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm text-gray-600">{invoice.supplier_name || 'לא צוין'}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm font-medium text-gray-900">
                          ₪{new Intl.NumberFormat('he-IL').format(invoice.amount || 0)}
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
