
// src/pages/WorkLogs/AccountantInbox.tsx
// תיבת נכנסים מנהלת חשבונות — אישורי השקעה יומיים

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight, CheckCircle, XCircle, Clock, Loader2, Search,
  Calendar, Building2, FileText, ReceiptText,
  AlertCircle, RefreshCw, FileDown
} from 'lucide-react';
import api from '../../services/api';
import { useRoleAccess } from '../../hooks/useRoleAccess';

interface WorklogRow {
  id: number;
  report_date: string;
  work_order_id: number | null;
  project_id: number | null;
  supplier_id?: number | null;
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
  PENDING:     { label: 'ממתין',           color: 'bg-yellow-100 text-yellow-800 border-yellow-300', icon: <Clock className="w-3.5 h-3.5" /> },
  SUBMITTED:   { label: 'הוגש לאישור',    color: 'bg-yellow-100 text-yellow-800 border-yellow-300', icon: <Clock className="w-3.5 h-3.5" /> },
  APPROVED:    { label: 'מאושר',          color: 'bg-green-100 text-green-800 border-green-300',  icon: <CheckCircle className="w-3.5 h-3.5" /> },
  INVOICED:    { label: 'נוצרה חשבונית',  color: 'bg-blue-100 text-blue-800 border-blue-300',    icon: <ReceiptText className="w-3.5 h-3.5" /> },
  REJECTED:    { label: 'נדחה',           color: 'bg-red-100 text-red-800 border-red-300',        icon: <XCircle className="w-3.5 h-3.5" /> },
};
const normStatus = (s: string | null | undefined) => (s || '').toUpperCase();
const getStatus = (s: string | null) => STATUS_LABEL[normStatus(s)] || {
  label: s || 'לא ידוע',
  color: 'bg-gray-100 text-gray-700 border-gray-300',
  icon: <Clock className="w-3.5 h-3.5" />,
};

function openExportPdf(title: string, headers: string[], rows: string[][]) {
  const esc = (s: string) =>
    s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  const thead = `<tr>${headers.map(h => `<th>${esc(h)}</th>`).join('')}</tr>`;
  const tbody = rows.map(r => `<tr>${r.map(c => `<td>${esc(c)}</td>`).join('')}</tr>`).join('');
  const w = window.open('', '_blank');
  if (!w) return;
  w.document.write(`<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"/><title>${esc(title)}</title>
<style>body{font-family:system-ui,sans-serif;padding:16px} table{border-collapse:collapse;width:100%;font-size:12px} th,td{border:1px solid #ccc;padding:6px;text-align:right}</style></head><body>
<h1 style="font-size:18px">${esc(title)}</h1><table><thead>${thead}</thead><tbody>${tbody}</tbody></table>
<script>window.onload=function(){window.print()}</script>
</body></html>`);
  w.document.close();
}

// Monthly Invoice Button 
const MonthlyInvoiceButton: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [projects, setProjects] = useState<any[]>([]);
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [projectId, setProjectId] = useState('');
  const [supplierId, setSupplierId] = useState('');
  const now = new Date();
  const [month, setMonth] = useState(String(now.getMonth() + 1));
  const [year, setYear] = useState(String(now.getFullYear()));
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  const loadData = async () => {
    const [pRes, sRes] = await Promise.all([
      api.get('/projects', { params: { page_size: 200 } }).catch(() => ({ data: { items: [] } })),
      api.get('/suppliers', { params: { page_size: 200 } }).catch(() => ({ data: { items: [] } })),
    ]);
    setProjects(pRes.data?.items || pRes.data || []);
    setSuppliers(sRes.data?.items || sRes.data || []);
  };

  const handleOpen = () => { setOpen(true); loadData(); };

  const handleGenerate = async () => {
    if (!projectId || !supplierId) { setMsg('בחר פרויקט וספק'); return; }
    setSaving(true); setMsg('');
    try {
      const res = await api.post('/invoices/generate-monthly', {
        project_id: Number(projectId),
        supplier_id: Number(supplierId),
        month: Number(month),
        year: Number(year),
      });
setMsg(` ${res.data.message}`);
      setTimeout(() => { setOpen(false); setMsg(''); }, 2500);
    } catch (e: any) {
setMsg(` ${e?.response?.data?.detail || 'שגיאה'}`);
    }
    setSaving(false);
  };

  return (
    <>
      <button onClick={handleOpen}
        className="flex items-center gap-1.5 px-3 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-xl">
        <ReceiptText className="w-4 h-4" />
        הפק חשבונית חודשית
      </button>
      {open && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" dir="rtl">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
              <h2 className="font-bold text-gray-900">הפקת חשבונית חודשית</h2>
              <button onClick={() => setOpen(false)} className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-400">
                <XCircle className="w-4 h-4" />
              </button>
            </div>
            <div className="p-5 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">חודש</label>
                  <select value={month} onChange={e => setMonth(e.target.value)}
                    className="w-full border border-gray-300 rounded-xl px-2 pr-2 pl-8 py-2 text-sm">
                    {Array.from({length:12},(_,i)=>(
                      <option key={i+1} value={i+1}>{i+1}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">שנה</label>
                  <select value={year} onChange={e => setYear(e.target.value)}
                    className="w-full border border-gray-300 rounded-xl px-2 pr-2 pl-8 py-2 text-sm">
                    {[2024,2025,2026,2027].map(y=>(
                      <option key={y} value={y}>{y}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">פרויקט</label>
                <select value={projectId} onChange={e => setProjectId(e.target.value)}
                  className="w-full border border-gray-300 rounded-xl px-3 pr-3 pl-10 py-2 text-sm">
                  <option value="">בחר פרויקט...</option>
                  {projects.map((p:any) => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">ספק</label>
                <select value={supplierId} onChange={e => setSupplierId(e.target.value)}
                  className="w-full border border-gray-300 rounded-xl px-3 pr-3 pl-10 py-2 text-sm">
                  <option value="">בחר ספק...</option>
                  {suppliers.map((s:any) => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
{msg && <p className={`text-sm ${msg.includes('שגיאה') ? 'text-red-600' : 'text-green-600'}`}>{msg}</p>}
            </div>
            <div className="flex gap-2 px-5 py-4 border-t border-gray-100">
              <button onClick={handleGenerate} disabled={saving}
                className="flex-1 py-2.5 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-medium rounded-xl text-sm">
{saving ? 'מפיק...' : ' הפק חשבונית'}
              </button>
              <button onClick={() => setOpen(false)}
                className="px-4 border border-gray-200 rounded-xl text-gray-600 hover:bg-gray-50 text-sm">ביטול</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

const AccountantInbox: React.FC = () => {
  const navigate = useNavigate();
  const [worklogs, setWorklogs] = useState<WorklogRow[]>([]);
  const [loading, setLoading] = useState(true);
  const { canApproveWorklogs } = useRoleAccess();
  const [processing, setProcessing] = useState<number | null>(null);
  const [error, setError] = useState('');
  /** Default: מאושרים — מוכנים לחשבונית */
  const [filterStatus, setFilterStatus] = useState<string>('APPROVED');
  const [search, setSearch] = useState('');
  const [filterProjectId, setFilterProjectId] = useState<string>('');
  const [filterSupplierId, setFilterSupplierId] = useState<string>('');
  const [dateFrom, setDateFrom] = useState<string>('');
  const [dateTo, setDateTo] = useState<string>('');
  const [projectOptions, setProjectOptions] = useState<{ id: number; name: string }[]>([]);
  const [supplierOptions, setSupplierOptions] = useState<{ id: number; name: string }[]>([]);
  const [rejectModal, setRejectModal] = useState<{ id: number; open: boolean } | null>(null);
  const [rejectReason, setRejectReason] = useState('');

  const showToast = (msg: string, type = 'success') => {
    if ((window as any).showToast) (window as any).showToast(msg, type);
  };

  const loadWorklogs = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params: Record<string, string | number> = { page_size: 200 };
      if (filterStatus) params.status = filterStatus.toUpperCase();
      if (filterProjectId) params.project_id = Number(filterProjectId);
      if (filterSupplierId) params.supplier_id = Number(filterSupplierId);
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;

      const [res, pRes, sRes] = await Promise.all([
        api.get('/worklogs', { params }),
        Promise.resolve({ data: { items: [] } }),
        Promise.resolve({ data: { items: [] } }),
      ]);
      const items: WorklogRow[] = res.data?.items || res.data || [];

      const pItems = pRes.data?.items || pRes.data || [];
      const sItems = sRes.data?.items || sRes.data || [];
      const projectOptionsMap = new Map<number, string>();
      const supplierOptionsMap = new Map<number, string>();

      items.forEach((w) => {
        if (w.project_id && w.project_name) projectOptionsMap.set(w.project_id, w.project_name);
        if (w.supplier_id && w.supplier_name) supplierOptionsMap.set(w.supplier_id, w.supplier_name);
      });

      setProjectOptions(Array.from(projectOptionsMap.entries()).map(([id, name]) => ({ id, name })));
      setSupplierOptions(Array.from(supplierOptionsMap.entries()).map(([id, name]) => ({ id, name })));

      const projectMap: Record<number, { name: string; code: string }> = {};
      pItems.forEach((p: any) => { projectMap[p.id] = { name: p.name, code: p.code }; });
      const supplierNameById: Record<number, string> = {};
      sItems.forEach((s: any) => { supplierNameById[s.id] = s.name || `ספק ${s.id}`; });

      const woIds = [...new Set(items.filter(w => !w.supplier_id && w.work_order_id).map(w => w.work_order_id!))];
      const woSupplierMap: Record<number, number> = {};
      for (const wid of woIds) {
        try {
          const wo = await api.get(`/work-orders/${wid}`);
          if (wo.data?.supplier_id) woSupplierMap[wid] = wo.data.supplier_id;
        } catch { /* ignore */ }
      }

      setWorklogs(items.map((w) => {
        const supplier_id = w.supplier_id ?? (w.work_order_id ? woSupplierMap[w.work_order_id] : null) ?? null;
        return {
          ...w,
          supplier_id,
          project_name: projectMap[w.project_id!]?.name || `פרויקט ${w.project_id}`,
          project_code: projectMap[w.project_id!]?.code || '',
          supplier_name: w.supplier_name || (supplier_id ? supplierNameById[supplier_id] : '') || '',
        };
      }));
    } catch (e: any) {
      setError('שגיאה בטעינת הנתונים');
      showToast('שגיאה בטעינת הנתונים', 'error');
    } finally {
      setLoading(false);
    }
  }, [filterStatus, filterProjectId, filterSupplierId, dateFrom, dateTo]);

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
` חשבונית ${invoice_number} נוצרה בהצלחה — ${total_amount.toLocaleString('he-IL')}`,
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
      (w.report_date || '').includes(s) ||
      (w.supplier_name || '').toLowerCase().includes(s)
    );
  });

  const pendingCount = worklogs.filter(w => {
    const st = normStatus(w.status);
    return !st || st === 'SUBMITTED' || st === 'PENDING';
  }).length;

  return (
    <div className="min-h-screen bg-fw-bg" dir="rtl">
      {/* Reject modal */}
      {rejectModal?.open && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
            <h3 className="text-lg font-bold text-fw-text mb-3 flex items-center gap-2">
              <XCircle className="w-5 h-5 text-red-600" />
              סיבת דחייה
            </h3>
            <textarea
              value={rejectReason}
              onChange={e => setRejectReason(e.target.value)}
              placeholder="פרט את הסיבה לדחיית הדיווח..."
              rows={3}
              className="w-full p-3 border border-fw-border rounded-lg text-sm mb-4"
              autoFocus
            />
            <div className="flex gap-3">
              <button onClick={() => { setRejectModal(null); setRejectReason(''); }} className="flex-1 px-4 py-2 border border-fw-border rounded-lg text-sm text-gray-600 hover:bg-gray-50">ביטול</button>
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
          <button onClick={() => navigate('/settings')} className="text-fw-green text-sm flex items-center gap-1 mb-4">
            <ArrowRight className="w-4 h-4" />
            חזרה
          </button>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-fw-green rounded-xl flex items-center justify-center">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-fw-text">תיבת נכנסים — אישורי השקעה</h1>
                <p className="text-gray-500 text-sm">
                  {pendingCount > 0 ? (
                    <span className="text-yellow-700 font-medium">{pendingCount} ממתינים לאישורך</span>
) : 'כל הדיווחים טופלו '}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <MonthlyInvoiceButton />
              <button
                type="button"
                onClick={() => {
                  const csvRows = ['מספר דיווח,תאריך,פרויקט,ספק,שעות,עלות לפני מע״מ,עלות כולל מע״מ,סטטוס'];
                  filtered.forEach(w => csvRows.push(`${w.report_number},${w.report_date},${w.project_name || ''},${w.supplier_name || ''},${w.total_hours},${w.cost_before_vat || ''},${w.cost_with_vat || ''},${w.status || ''}`));
                  const blob = new Blob(['\ufeff' + csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a'); a.href = url; a.download = `worklogs-export-${new Date().toISOString().split('T')[0]}.csv`; a.click();
                  URL.revokeObjectURL(url);
                }}
                className="flex items-center gap-1 px-3 py-2 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 text-sm font-medium rounded-xl"
                title="ייצוא Excel (CSV)"
              >
                <FileText className="w-4 h-4" />
Excel
              </button>
              <button
                type="button"
                onClick={() => {
                  const headers = ['מספר', 'תאריך', 'פרויקט', 'ספק', 'שעות', 'לפני מע״מ', 'כולל מע״מ', 'סטטוס'];
                  const rows = filtered.map(w => [
                    String(w.report_number),
                    w.report_date ? new Date(w.report_date).toLocaleDateString('he-IL') : '',
                    w.project_name || '',
                    w.supplier_name || '',
                    String(w.total_hours ?? ''),
w.cost_before_vat ? `${parseFloat(String(w.cost_before_vat)).toLocaleString('he-IL')}` : '',
w.cost_with_vat ? `${parseFloat(String(w.cost_with_vat)).toLocaleString('he-IL')}` : '',
                    getStatus(w.status).label,
                  ]);
                  openExportPdf('תיבת נכנסים — דיווחי שעות', headers, rows);
                }}
                className="flex items-center gap-1 px-3 py-2 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 text-sm font-medium rounded-xl"
                title="ייצוא PDF"
              >
                <FileDown className="w-4 h-4" />
                PDF
              </button>
              <button onClick={loadWorklogs} className="p-2 hover:bg-gray-100 rounded-lg text-gray-500" title="רענן">
                <RefreshCw className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-sm border border-fw-border p-4 mb-6 space-y-3">
          <div className="flex flex-col lg:flex-row gap-3">
            <div className="relative flex-1 min-w-0">
              <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="חיפוש לפי פרויקט, ספק, תאריך, מספר..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="w-full pr-9 pl-4 py-2 border border-fw-border rounded-lg text-sm"
              />
            </div>
            <div className="flex flex-wrap gap-2">
              {[
                { value: 'SUBMITTED', label: 'ממתינים' },
                { value: 'APPROVED', label: 'מאושרים (לחשבונית)' },
                { value: 'REJECTED', label: 'נדחו' },
                { value: '', label: 'הכל' },
              ].map(f => (
                <button
                  key={f.value || 'all'}
                  type="button"
                  onClick={() => setFilterStatus(f.value)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    filterStatus === f.value
                      ? 'bg-fw-green text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>
          <div className="flex flex-col sm:flex-row flex-wrap gap-3 items-stretch sm:items-end">
            <div className="flex-1 min-w-[140px]">
              <label className="block text-xs font-medium text-gray-600 mb-1">פרויקט</label>
              <select
                value={filterProjectId}
                onChange={e => setFilterProjectId(e.target.value)}
                className="w-full border border-fw-border rounded-lg px-3 py-2 text-sm bg-white"
              >
                <option value="">כל הפרויקטים</option>
                {projectOptions.map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
            <div className="flex-1 min-w-[140px]">
              <label className="block text-xs font-medium text-gray-600 mb-1">ספק</label>
              <select
                value={filterSupplierId}
                onChange={e => setFilterSupplierId(e.target.value)}
                className="w-full border border-fw-border rounded-lg px-3 py-2 text-sm bg-white"
              >
                <option value="">כל הספקים</option>
                {supplierOptions.map(s => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">מתאריך</label>
              <input
                type="date"
                value={dateFrom}
                onChange={e => setDateFrom(e.target.value)}
                className="w-full border border-fw-border rounded-lg px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">עד תאריך</label>
              <input
                type="date"
                value={dateTo}
                onChange={e => setDateTo(e.target.value)}
                className="w-full border border-fw-border rounded-lg px-3 py-2 text-sm"
              />
            </div>
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
        <div className="bg-white rounded-xl shadow-sm border border-fw-border overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <div className="relative overflow-visible" style={{ padding: 4 }}>
          <div className="w-10 h-10 rounded-full border-[3px] border-emerald-200 border-t-emerald-500 animate-spin" style={{animationDuration:'0.9s'}} />
          <div className="absolute inset-0 flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 100" width="20" height="17">
                <defs>
                  <linearGradient id="ai1_t" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#1565c0"/><stop offset="100%" stopColor="#0097a7"/></linearGradient>
                  <linearGradient id="ai1_m" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#0097a7"/><stop offset="50%" stopColor="#2e7d32"/><stop offset="100%" stopColor="#66bb6a"/></linearGradient>
                  <linearGradient id="ai1_b" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#2e7d32"/><stop offset="40%" stopColor="#66bb6a"/><stop offset="100%" stopColor="#8B5e3c"/></linearGradient>
                </defs>
                <path d="M46 20 Q60 9 74 20" stroke="url(#ai1_t)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <path d="M30 47 Q42 34 60 43 Q78 34 90 47" stroke="url(#ai1_m)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <path d="M14 74 Q28 60 46 69 Q60 76 74 69 Q92 60 106 74" stroke="url(#ai1_b)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <line x1="60" y1="76" x2="60" y2="90" stroke="#8B5e3c" strokeWidth="3.5" strokeLinecap="round"/>
                <circle cx="60" cy="95" r="5" fill="#8B5e3c"/>
              </svg>
          </div>
        </div>
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-16 text-gray-500">
              <FileText className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p>אין דיווחים תואמים</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px]">
                <thead className="bg-gray-50 border-b border-fw-border">
                  <tr>
                    <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500">מספר</th>
                    <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500">תאריך</th>
                    <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500">פרויקט</th>
                    <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500">ספק</th>
                    <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500">סוג</th>
                    <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500">שעות</th>
                    <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500">לפני מע״מ</th>
                    <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500">כולל מע״מ</th>
                    <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500">סטטוס</th>
                    <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500">פעולות</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(w => {
                    const st = getStatus(w.status);
                    const ns = normStatus(w.status);
                    const isPending = !ns || ns === 'SUBMITTED' || ns === 'PENDING';
                    const isApproved = ns === 'APPROVED';
                    const isInvoiced = ns === 'INVOICED';
                    return (
                      <tr key={w.id} className="border-b border-fw-border hover:bg-gray-50 transition-colors">
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
                            <Building2 className="w-4 h-4 text-fw-green flex-shrink-0" />
                            <div>
                              <p className="text-sm font-medium text-fw-text">{w.project_name}</p>
                              {w.project_code && <p className="text-xs text-gray-400">{w.project_code}</p>}
                            </div>
                          </div>
                        </td>
                        {/* Supplier */}
                        <td className="px-4 py-3 text-sm text-fw-text max-w-[140px]">
                          <span className="line-clamp-2">{w.supplier_name || '—'}</span>
                        </td>
                        {/* Type */}
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${
                            w.report_type === 'standard'
                              ? 'bg-green-50 text-green-700'
                              : 'bg-orange-50 text-orange-700'
                          }`}>
{w.report_type === 'standard' ? ' תקן' : ' לא תקן'}
                          </span>
                        </td>
                        {/* Hours */}
                        <td className="px-4 py-3 text-center">
                          <span className="text-sm font-semibold text-fw-text">
                            {parseFloat(w.total_hours || '0').toFixed(1)}h
                          </span>
                        </td>
                        {/* Cost before VAT */}
                        <td className="px-4 py-3 text-center">
                          <span className="text-sm font-bold text-fw-text">
                            {w.cost_before_vat
? `${parseFloat(String(w.cost_before_vat)).toLocaleString('he-IL')}`
                              : '—'}
                          </span>
                        </td>
                        {/* Cost with VAT */}
                        <td className="px-4 py-3 text-center">
                          <span className="text-sm font-semibold text-gray-700">
                            {w.cost_with_vat
? `${parseFloat(String(w.cost_with_vat)).toLocaleString('he-IL')}`
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
                            {isPending && canApproveWorklogs && (
                              <>
                                <button
                                  onClick={() => handleApprove(w.id)}
                                  disabled={processing === w.id}
                                  className="flex items-center gap-1 px-3 py-1.5 bg-fw-green text-white rounded-lg text-xs font-medium hover:bg-fw-green-dark transition-colors disabled:opacity-50"
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
                            {isInvoiced && (
                              <span className="text-xs text-blue-600 font-medium">חויב</span>
                            )}
                            {!isPending && !isApproved && !isInvoiced && (
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
            <span className="font-medium text-fw-text">
סה"כ: {filtered
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
