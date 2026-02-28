// @ts-nocheck
// src/pages/WorkLogs/AccountantInbox.tsx
// תיבת נכנסים מנהלת חשבונות — אישורי השקעה יומיים

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight, CheckCircle, XCircle, Clock, Loader2, Search,
  Filter, Calendar, Truck, Building2, FileText, ReceiptText,
  AlertCircle, RefreshCw
} from 'lucide-react';
import api from '../../services/api';

interface WorklogRow {
  id: number;
  report_date: string;
  work_order_id: number | null;
  project_id: number | null;
  project_name?: string;
  project_code?: string;
  supplier_name?: string;
  equipment_type?: string;
  work_hours: string;
  total_hours: string;
  cost_before_vat: string | null;
  cost_with_vat: string | null;
  status: string | null;
  approved_at: string | null;
  approved_by_user_id: number | null;
  report_type: string;
  report_number: number;
}

const STATUS_LABEL: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  submitted:   { label: 'ממתין לאישור', color: 'bg-yellow-100 text-yellow-800 border-yellow-300', icon: <Clock className="w-3.5 h-3.5" /> },
  approved:    { label: 'מאושר',          color: 'bg-green-100 text-green-800 border-green-300',  icon: <CheckCircle className="w-3.5 h-3.5" /> },
  invoiced:    { label: 'נוצרה חשבונית',  color: 'bg-blue-100 text-blue-800 border-blue-300',    icon: <ReceiptText className="w-3.5 h-3.5" /> },
  rejected:    { label: 'נדחה',           color: 'bg-red-100 text-red-800 border-red-300',        icon: <XCircle className="w-3.5 h-3.5" /> },
  pending:     { label: 'ממתין לאישור', color: 'bg-yellow-100 text-yellow-800 border-yellow-300', icon: <Clock className="w-3.5 h-3.5" /> },
};
const getStatus = (s: string | null) => STATUS_LABEL[s || 'submitted'] || STATUS_LABEL.submitted;

const AccountantInbox: React.FC = () => {
  const navigate = useNavigate();
  const [worklogs, setWorklogs] = useState<WorklogRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState<number | null>(null);
  const [error, setError] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('submitted');
  const [search, setSearch] = useState('');
  const [rejectModal, setRejectModal] = useState<{ id: number; open: boolean } | null>(null);
  const [rejectReason, setRejectReason] = useState('');

  const showToast = (msg: string, type = 'success') => {
    if ((window as any).showToast) (window as any).showToast(msg, type);
  };

  const loadWorklogs = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params: Record<string, string> = { limit: '100' };
      if (filterStatus) params.status = filterStatus;
      const res = await api.get('/worklogs', { params });
      const items: WorklogRow[] = res.data?.items || res.data || [];

      // Enrich with project names if missing
      const projectIds = [...new Set(items.map(w => w.project_id).filter(Boolean))];
      const projectMap: Record<number, { name: string; code: string }> = {};
      if (projectIds.length > 0) {
        try {
          const pRes = await api.get('/projects', { params: { limit: 200 } });
          const pItems = pRes.data?.items || pRes.data || [];
          pItems.forEach((p: any) => { projectMap[p.id] = { name: p.name, code: p.code }; });
        } catch { /* ignore */ }
      }

      setWorklogs(items.map(w => ({
        ...w,
        project_name: projectMap[w.project_id!]?.name || `פרויקט ${w.project_id}`,
        project_code: projectMap[w.project_id!]?.code || '',
      })));
    } catch (e: any) {
      setError('שגיאה בטעינת הנתונים');
      showToast('שגיאה בטעינת הנתונים', 'error');
    } finally {
      setLoading(false);
    }
  }, [filterStatus]);

  useEffect(() => { loadWorklogs(); }, [loadWorklogs]);

  const handleApprove = async (id: number) => {
    setProcessing(id);
    try {
      await api.post(`/worklogs/${id}/approve`);
      showToast('אישור ההשקעה בוצע בהצלחה', 'success');
      loadWorklogs();
    } catch (e: any) {
      showToast(e?.response?.data?.detail || 'שגיאה באישור', 'error');
    } finally {
      setProcessing(null);
    }
  };

  const handleCreateInvoice = async (worklog: WorklogRow) => {
    if (!worklog.project_id) {
      showToast('לא ניתן ליצור חשבונית — פרויקט לא מוגדר בדיווח', 'error');
      return;
    }

    // We need supplier_id — get from work_order or project
    // Use a fallback supplier_id of 1 if not available on worklog
    // In production, fetch from work_order details
    let supplier_id = 0;
    if (worklog.work_order_id) {
      try {
        const wo = await api.get(`/work-orders/${worklog.work_order_id}`);
        supplier_id = wo.data?.supplier_id || 0;
      } catch { /* ignore */ }
    }

    if (!supplier_id) {
      showToast('לא נמצא ספק מקושר לדיווח זה. יש לוודא שההזמנה משויכת לספק.', 'error');
      return;
    }

    setProcessing(worklog.id);
    try {
      const res = await api.post('/invoices/from-worklogs', {
        worklog_ids: [worklog.id],
        supplier_id,
        project_id: worklog.project_id,
      });
      const { invoice_id, invoice_number, total_amount } = res.data;
      showToast(
        `✅ חשבונית ${invoice_number} נוצרה בהצלחה — ₪${total_amount.toLocaleString('he-IL')}`,
        'success'
      );
      // Refresh list immediately, then navigate to detail after 2s
      loadWorklogs();
      if (invoice_id) {
        setTimeout(() => {
          navigate(`/invoices/${invoice_id}`);
        }, 2000);
      }
    } catch (e: any) {
      const msg = e?.response?.data?.detail || 'שגיאה ביצירת החשבונית';
      showToast(typeof msg === 'string' ? msg : JSON.stringify(msg), 'error');
    } finally {
      setProcessing(null);
    }
  };

  const handleReject = async () => {
    if (!rejectModal) return;
    if (!rejectReason.trim()) { showToast('יש לציין סיבת דחייה', 'error'); return; }
    setProcessing(rejectModal.id);
    try {
      await api.post(`/worklogs/${rejectModal.id}/reject`, null, { params: { rejection_reason: rejectReason } });
      showToast('הדיווח נדחה', 'success');
      setRejectModal(null);
      setRejectReason('');
      loadWorklogs();
    } catch (e: any) {
      showToast(e?.response?.data?.detail || 'שגיאה בדחייה', 'error');
    } finally {
      setProcessing(null);
    }
  };

  const filtered = worklogs.filter(w => {
    if (!search) return true;
    const s = search.toLowerCase();
    return (
      w.project_name?.toLowerCase().includes(s) ||
      w.project_code?.toLowerCase().includes(s) ||
      String(w.report_number).includes(s) ||
      (w.report_date || '').includes(s)
    );
  });

  const pendingCount = worklogs.filter(w => !w.status || w.status === 'submitted' || w.status === 'pending').length;

  return (
    <div className="min-h-screen bg-kkl-bg" dir="rtl">
      {/* Reject modal */}
      {rejectModal?.open && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
            <h3 className="text-lg font-bold text-kkl-text mb-3 flex items-center gap-2">
              <XCircle className="w-5 h-5 text-red-600" />
              סיבת דחייה
            </h3>
            <textarea
              value={rejectReason}
              onChange={e => setRejectReason(e.target.value)}
              placeholder="פרט את הסיבה לדחיית הדיווח..."
              rows={3}
              className="w-full p-3 border border-kkl-border rounded-lg text-sm mb-4"
              autoFocus
            />
            <div className="flex gap-3">
              <button onClick={() => { setRejectModal(null); setRejectReason(''); }} className="flex-1 px-4 py-2 border border-kkl-border rounded-lg text-sm text-gray-600 hover:bg-gray-50">ביטול</button>
              <button
                onClick={handleReject}
                disabled={processing !== null}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {processing ? <Loader2 className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4" />}
                דחה דיווח
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-6">
          <button onClick={() => navigate('/settings')} className="text-kkl-green text-sm flex items-center gap-1 mb-4">
            <ArrowRight className="w-4 h-4" />
            חזרה
          </button>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-kkl-green rounded-xl flex items-center justify-center">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-kkl-text">תיבת נכנסים — אישורי השקעה</h1>
                <p className="text-gray-500 text-sm">
                  {pendingCount > 0 ? (
                    <span className="text-yellow-700 font-medium">{pendingCount} ממתינים לאישורך</span>
                  ) : 'כל הדיווחים טופלו ✅'}
                </p>
              </div>
            </div>
            <button onClick={loadWorklogs} className="p-2 hover:bg-gray-100 rounded-lg text-gray-500" title="רענן">
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-sm border border-kkl-border p-4 mb-6 flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="חיפוש לפי פרויקט, תאריך, מספר..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pr-9 pl-4 py-2 border border-kkl-border rounded-lg text-sm"
            />
          </div>
          <div className="flex gap-2">
            {[
              { value: 'submitted', label: 'ממתינים' },
              { value: 'approved', label: 'מאושרים' },
              { value: 'rejected', label: 'נדחו' },
              { value: '', label: 'הכל' },
            ].map(f => (
              <button
                key={f.value}
                onClick={() => setFilterStatus(f.value)}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  filterStatus === f.value
                    ? 'bg-kkl-green text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}

        {/* Table */}
        <div className="bg-white rounded-xl shadow-sm border border-kkl-border overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="w-8 h-8 text-kkl-green animate-spin" />
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-16 text-gray-500">
              <FileText className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p>אין דיווחים תואמים</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px]">
                <thead className="bg-gray-50 border-b border-kkl-border">
                  <tr>
                    <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500">מספר</th>
                    <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500">תאריך</th>
                    <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500">פרויקט</th>
                    <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500">סוג</th>
                    <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500">שעות</th>
                    <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500">סכום לפני מע"מ</th>
                    <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500">סטטוס</th>
                    <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500">פעולות</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(w => {
                    const st = getStatus(w.status);
                    const isPending = !w.status || w.status === 'submitted' || w.status === 'pending';
                    const isApproved = w.status === 'approved';
                    return (
                      <tr key={w.id} className="border-b border-kkl-border hover:bg-gray-50 transition-colors">
                        {/* Number */}
                        <td className="px-4 py-3">
                          <span className="text-sm font-mono text-gray-500">#{w.report_number}</span>
                        </td>
                        {/* Date */}
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1.5 text-sm">
                            <Calendar className="w-3.5 h-3.5 text-gray-400" />
                            {w.report_date ? new Date(w.report_date).toLocaleDateString('he-IL') : '—'}
                          </div>
                        </td>
                        {/* Project */}
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <Building2 className="w-4 h-4 text-kkl-green flex-shrink-0" />
                            <div>
                              <p className="text-sm font-medium text-kkl-text">{w.project_name}</p>
                              {w.project_code && <p className="text-xs text-gray-400">{w.project_code}</p>}
                            </div>
                          </div>
                        </td>
                        {/* Type */}
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${
                            w.report_type === 'standard'
                              ? 'bg-green-50 text-green-700'
                              : 'bg-orange-50 text-orange-700'
                          }`}>
                            {w.report_type === 'standard' ? '✓ תקן' : '⚡ לא תקן'}
                          </span>
                        </td>
                        {/* Hours */}
                        <td className="px-4 py-3 text-center">
                          <span className="text-sm font-semibold text-kkl-text">
                            {parseFloat(w.total_hours || '0').toFixed(1)}h
                          </span>
                        </td>
                        {/* Cost */}
                        <td className="px-4 py-3 text-center">
                          <span className="text-sm font-bold text-kkl-text">
                            {w.cost_before_vat
                              ? `₪${parseFloat(w.cost_before_vat).toLocaleString('he-IL')}`
                              : '—'}
                          </span>
                        </td>
                        {/* Status */}
                        <td className="px-4 py-3 text-center">
                          <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border ${st.color}`}>
                            {st.icon}
                            {st.label}
                          </span>
                        </td>
                        {/* Actions */}
                        <td className="px-4 py-3">
                          <div className="flex items-center justify-center gap-2">
                            {isPending && (
                              <>
                                <button
                                  onClick={() => handleApprove(w.id)}
                                  disabled={processing === w.id}
                                  className="flex items-center gap-1 px-3 py-1.5 bg-kkl-green text-white rounded-lg text-xs font-medium hover:bg-kkl-green-dark transition-colors disabled:opacity-50"
                                  title="אשר דיווח"
                                >
                                  {processing === w.id
                                    ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                    : <CheckCircle className="w-3.5 h-3.5" />}
                                  אשר
                                </button>
                                <button
                                  onClick={() => setRejectModal({ id: w.id, open: true })}
                                  disabled={processing === w.id}
                                  className="flex items-center gap-1 px-3 py-1.5 bg-red-50 text-red-600 border border-red-200 rounded-lg text-xs font-medium hover:bg-red-100 transition-colors disabled:opacity-50"
                                  title="דחה דיווח"
                                >
                                  <XCircle className="w-3.5 h-3.5" />
                                  דחה
                                </button>
                              </>
                            )}
                            {isApproved && (
                              <button
                                onClick={() => handleCreateInvoice(w)}
                                disabled={processing === w.id}
                                className="flex items-center gap-1 px-3 py-1.5 bg-blue-50 text-blue-700 border border-blue-200 rounded-lg text-xs font-medium hover:bg-blue-100 transition-colors disabled:opacity-50"
                                title="צור חשבונית מדיווח זה"
                              >
                                {processing === w.id
                                  ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                  : <ReceiptText className="w-3.5 h-3.5" />}
                                לחשבונית
                              </button>
                            )}
                            {!isPending && !isApproved && (
                              <span className="text-xs text-gray-400">—</span>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Summary Footer */}
        {filtered.length > 0 && !loading && (
          <div className="mt-4 flex items-center justify-between text-sm text-gray-500 px-1">
            <span>{filtered.length} דיווחים מוצגים</span>
            <span className="font-medium text-kkl-text">
              סה"כ: ₪{filtered
                .reduce((sum, w) => sum + parseFloat(w.cost_before_vat || '0'), 0)
                .toLocaleString('he-IL')}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default AccountantInbox;
