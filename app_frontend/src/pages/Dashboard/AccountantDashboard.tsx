import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  DollarSign, FileText, CheckCircle, AlertTriangle,
  Search, Filter, ShieldAlert, Info, RefreshCw, XCircle,
  Eye, X, Clock, Wrench
} from "lucide-react";
import api from "../../services/api";
import UnifiedLoader from "../../components/common/UnifiedLoader";

interface WLRow {
  id: number; report_number: number | null; report_date: string | null;
  status: string; work_hours: number; break_hours: number;
  hourly_rate: number; cost_before_vat: number; cost_with_vat: number;
  report_type: string | null; is_overnight: boolean; overnight_nights: number;
  project_name: string; supplier_name: string | null;
  reporter_name: string; equipment_type: string | null;
  approved_at: string | null; license_plate: string | null;
  flags: string[];
}

interface AcctData {
  kpis: {
    pending_reports: number; approved_today: number;
    pending_amount: number; monthly_approved: number; draft_invoices: number;
    anomalies: number;
  };
  alerts: { type: string; message: string }[];
  worklogs: WLRow[];
  filter_options: {
    projects: { id: number; name: string }[];
    suppliers: { id: number; name: string }[];
    statuses: { value: string; label: string }[];
  };
}

interface WLDetail {
  id: number; report_number: number; report_date: string; status: string;
  work_hours: number; break_hours: number; total_hours: number; net_hours: number;
  hourly_rate: number; rate_source: string; rate_source_name: string;
  cost_before_vat: number; vat_rate: number; cost_with_vat: number;
  is_overnight: boolean; overnight_nights: number; overnight_rate: number; overnight_total: number;
  report_type: string; equipment_type: string; equipment_scanned: boolean;
  project_name: string; supplier_name: string; reporter_name: string;
  approver_name: string | null; approved_at: string | null;
  license_plate: string; equipment_code: string;
  work_order_number: number | null;
  warnings: { type: string; message: string }[];
  audit_trail: { action: string; description: string; user_name: string; created_at: string }[];
  invoice: { invoice_number: string; status: string } | null;
}

const fmtILS = (n: number) => `${n.toLocaleString("he-IL", { maximumFractionDigits: 0 })}`;

const WL_STATUS: Record<string, { label: string; cls: string }> = {
  PENDING: { label: "טיוטה", cls: "bg-gray-100 text-gray-700" },
  SUBMITTED: { label: "ממתין לאישור", cls: "bg-yellow-100 text-yellow-800" },
  APPROVED: { label: "מאושר", cls: "bg-green-100 text-green-800" },
  REJECTED: { label: "נדחה", cls: "bg-red-100 text-red-700" },
  INVOICED: { label: "הופק חשבון", cls: "bg-purple-100 text-purple-800" },
};

const FLAG_LABELS: Record<string, { label: string; cls: string }> = {
  duplicate: { label: "כפול", cls: "bg-red-100 text-red-700" },
  high_hours: { label: "שעות חריגות", cls: "bg-amber-100 text-amber-700" },
  low_hours: { label: "שעות נמוכות", cls: "bg-gray-100 text-gray-600" },
  no_rate: { label: "ללא תעריף", cls: "bg-red-100 text-red-700" },
};

const AccountantDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<AcctData | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("SUBMITTED");
  const [projectFilter, setProjectFilter] = useState("");
  const [supplierFilter, setSupplierFilter] = useState("");
  const [searchText, setSearchText] = useState("");
  const [actionBusy, setActionBusy] = useState<number | null>(null);
  const [actioned, setActioned] = useState<Record<number, string>>({});
  const [detailId, setDetailId] = useState<number | null>(null);
  const [detail, setDetail] = useState<WLDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [invoiceSelection, setInvoiceSelection] = useState<Set<number>>(new Set());

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (statusFilter) params.status_filter = statusFilter;
      if (projectFilter) params.project_id = projectFilter;
      if (supplierFilter) params.supplier_id = supplierFilter;
      if (searchText) params.search = searchText;
      const r = await api.get("/dashboard/accountant-overview", { params });
      setData(r.data);
    } catch {}
    setLoading(false);
  }, [statusFilter, projectFilter, supplierFilter, searchText]);

  useEffect(() => { loadData(); }, [loadData]);

  const openDetail = async (wlId: number) => {
    setDetailId(wlId);
    setDetailLoading(true);
    try {
      const r = await api.get(`/dashboard/worklog-detail/${wlId}`);
      setDetail(r.data);
    } catch { setDetail(null); }
    setDetailLoading(false);
  };

  const doAction = async (wlId: number, action: "approve" | "reject") => {
    setActionBusy(wlId);
    try {
      await api.post(`/worklogs/${wlId}/${action}`);
      setActioned(prev => ({ ...prev, [wlId]: action }));
      if (detailId === wlId) setDetailId(null);
    } catch (e: any) { alert(e?.response?.data?.detail || "שגיאה"); }
    setActionBusy(null);
  };

  const toggleInvoiceSelect = (id: number) => {
    setInvoiceSelection(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const createInvoice = async () => {
    if (invoiceSelection.size === 0) return;
    try {
      await api.post("/invoices/from-worklogs", { worklog_ids: Array.from(invoiceSelection) });
      setInvoiceSelection(new Set());
      loadData();
      alert("חשבונית נוצרה בהצלחה");
    } catch (e: any) { alert(e?.response?.data?.detail || "שגיאה ביצירת חשבונית"); }
  };

  if (loading && !data) return <UnifiedLoader size="full" />;
  if (!data) return <div className="p-8 text-center text-gray-500">שגיאה בטעינת נתונים</div>;

  const k = data.kpis;
  const approvedWLs = data.worklogs.filter(wl => wl.status === "APPROVED" && !actioned[wl.id]);

  return (
    <div className="min-h-full bg-gray-50" dir="rtl">
      <div className="p-3 sm:p-5 space-y-4 max-w-screen-xl mx-auto">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <DollarSign className="w-6 h-6 text-green-600" />
            <h1 className="text-xl sm:text-2xl font-extrabold text-gray-900">בקרה כספית</h1>
          </div>
          <div className="flex gap-2">
            <button onClick={() => navigate("/invoices")}
              className="flex items-center gap-1.5 px-3 min-h-[40px] text-xs font-bold bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
              <FileText className="w-3.5 h-3.5" /> חשבוניות
            </button>
            <button onClick={loadData} disabled={loading}
              className="flex items-center gap-1.5 px-3 min-h-[40px] text-xs font-bold bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-colors">
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-2 sm:grid-cols-6 gap-2 sm:gap-3">
          <FKPI label="ממתינים" value={String(k.pending_reports)} color={k.pending_reports > 0 ? "amber" : "gray"} pulse={k.pending_reports > 0} />
          <FKPI label="אושרו היום" value={String(k.approved_today)} color="green" />
          <FKPI label="אושר החודש" value={fmtILS(k.monthly_approved)} color="blue" />
          <FKPI label="סה״כ ממתין" value={fmtILS(k.pending_amount)} color={k.pending_amount > 0 ? "red" : "gray"} />
          <FKPI label="חשבוניות טיוטה" value={String(k.draft_invoices)} color={k.draft_invoices > 0 ? "orange" : "gray"} />
          <FKPI label="חריגות" value={String(k.anomalies)} color={k.anomalies > 0 ? "red" : "green"} pulse={k.anomalies > 0} />
        </div>

        {/* Alerts */}
        {data.alerts.length > 0 && (
          <div className="space-y-1.5">
            {data.alerts.map((a, i) => {
              const Icon = a.type === "error" ? ShieldAlert : a.type === "warning" ? AlertTriangle : Info;
              const cls = a.type === "error" ? "border-red-300 bg-red-50 text-red-800" :
                          a.type === "warning" ? "border-amber-300 bg-amber-50 text-amber-800" :
                          "border-blue-200 bg-blue-50 text-blue-800";
              return <div key={i} className={`rounded-lg border px-3 py-2 flex items-center gap-2.5 text-sm font-medium ${cls}`}><Icon className="w-4 h-4 flex-shrink-0" /> {a.message}</div>;
            })}
          </div>
        )}

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-3 flex flex-wrap gap-2 items-center">
          <div className="flex items-center gap-1.5 text-xs text-gray-500"><Filter className="w-3.5 h-3.5" /> סינון:</div>
          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="px-2.5 py-2 text-xs border border-gray-300 rounded-lg bg-white">
            <option value="">כל הסטטוסים</option>
            {data.filter_options.statuses.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>
          <select value={projectFilter} onChange={e => setProjectFilter(e.target.value)} className="px-2.5 py-2 text-xs border border-gray-300 rounded-lg bg-white">
            <option value="">כל הפרויקטים</option>
            {data.filter_options.projects.map(p => <option key={p.id} value={String(p.id)}>{p.name}</option>)}
          </select>
          <select value={supplierFilter} onChange={e => setSupplierFilter(e.target.value)} className="px-2.5 py-2 text-xs border border-gray-300 rounded-lg bg-white">
            <option value="">כל הספקים</option>
            {data.filter_options.suppliers.map(s => <option key={s.id} value={String(s.id)}>{s.name}</option>)}
          </select>
          <div className="flex-1 min-w-[140px] relative">
            <Search className="w-3.5 h-3.5 absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
            <input type="text" value={searchText} onChange={e => setSearchText(e.target.value)} placeholder="חיפוש..." className="w-full pr-8 pl-3 py-2 text-xs border border-gray-300 rounded-lg" />
          </div>
        </div>

        {/* Invoice grouping bar */}
        {invoiceSelection.size > 0 && (
          <div className="bg-green-50 border border-green-200 rounded-xl p-3 flex items-center justify-between">
            <span className="text-sm font-bold text-green-800">{invoiceSelection.size} דיווחים נבחרו לחשבונית</span>
            <div className="flex gap-2">
              <button onClick={createInvoice} className="px-4 min-h-[40px] bg-green-600 text-white text-sm font-bold rounded-lg hover:bg-green-700 transition-colors">
                צור חשבונית
              </button>
              <button onClick={() => setInvoiceSelection(new Set())} className="px-3 min-h-[40px] text-sm text-gray-600 hover:text-gray-800">
                בטל
              </button>
            </div>
          </div>
        )}

        {/* Reports Table */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-gray-500 text-xs">
                  {statusFilter === "APPROVED" && <th className="px-2 py-3"><input type="checkbox" onChange={e => {
                    if (e.target.checked) setInvoiceSelection(new Set(approvedWLs.map(w => w.id)));
                    else setInvoiceSelection(new Set());
                  }} /></th>}
                  <th className="text-right px-3 py-3 font-semibold">מס׳</th>
                  <th className="text-right px-3 py-3 font-semibold">תאריך</th>
                  <th className="text-right px-3 py-3 font-semibold">פרויקט</th>
                  <th className="text-right px-3 py-3 font-semibold">ספק</th>
                  <th className="text-right px-3 py-3 font-semibold">מדווח</th>
                  <th className="text-center px-3 py-3 font-semibold">שעות</th>
                  <th className="text-right px-3 py-3 font-semibold">עלות</th>
                  <th className="text-center px-3 py-3 font-semibold">סטטוס</th>
                  <th className="text-center px-2 py-3 font-semibold">חריגות</th>
                  <th className="text-center px-3 py-3 font-semibold">פעולות</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.worklogs.length === 0 ? (
                  <tr><td colSpan={11} className="p-8 text-center text-gray-400">אין דיווחים</td></tr>
                ) : data.worklogs.map(wl => {
                  const st = WL_STATUS[wl.status] || { label: wl.status, cls: "bg-gray-100 text-gray-600" };
                  const done = actioned[wl.id];
                  const isBusy = actionBusy === wl.id;
                  const isSubmitted = wl.status === "SUBMITTED" && !done;
                  const isApproved = wl.status === "APPROVED" && !done;

                  return (
                    <tr key={wl.id} className={`transition-colors ${done ? "bg-gray-50 opacity-60" : wl.flags.length > 0 ? "bg-red-50/30 hover:bg-red-50/50" : "hover:bg-blue-50/30"}`}>
                      {statusFilter === "APPROVED" && (
                        <td className="px-2 py-2.5 text-center">
                          {isApproved && <input type="checkbox" checked={invoiceSelection.has(wl.id)} onChange={() => toggleInvoiceSelect(wl.id)} />}
                        </td>
                      )}
                      <td className="px-3 py-2.5 font-bold text-gray-900 text-xs">#{wl.report_number}</td>
                      <td className="px-3 py-2.5 text-xs text-gray-600">{wl.report_date}</td>
                      <td className="px-3 py-2.5 text-xs font-medium text-gray-800 max-w-[130px] truncate">{wl.project_name}</td>
                      <td className="px-3 py-2.5 text-xs text-gray-600 max-w-[110px] truncate">{wl.supplier_name || "—"}</td>
                      <td className="px-3 py-2.5 text-xs text-gray-600 max-w-[90px] truncate">{wl.reporter_name}</td>
                      <td className="px-3 py-2.5 text-center text-xs font-medium">
                        {wl.work_hours}
                        {wl.is_overnight && <span className="text-[9px] text-blue-600 mr-1">+לילה</span>}
                      </td>
                      <td className="px-3 py-2.5 text-xs font-bold text-gray-900">{fmtILS(wl.cost_with_vat)}</td>
                      <td className="px-3 py-2.5 text-center">
                        {done ? (
                          <span className={`text-[10px] font-bold ${done === "approve" ? "text-green-600" : "text-red-600"}`}>
{done === "approve" ? " אושר" : " נדחה"}
                          </span>
                        ) : <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${st.cls}`}>{st.label}</span>}
                      </td>
                      <td className="px-2 py-2.5 text-center">
                        {wl.flags.length > 0 && (
                          <div className="flex flex-wrap gap-0.5 justify-center">
                            {wl.flags.map(f => {
                              const fl = FLAG_LABELS[f] || { label: f, cls: "bg-gray-100 text-gray-600" };
                              return <span key={f} className={`px-1 py-0.5 rounded text-[8px] font-bold ${fl.cls}`}>{fl.label}</span>;
                            })}
                          </div>
                        )}
                      </td>
                      <td className="px-3 py-2.5 text-center">
                        <div className="flex gap-1 justify-center">
                          {isSubmitted && (<>
                            <button disabled={isBusy} onClick={() => doAction(wl.id, "approve")}
                              className="px-2 min-h-[28px] text-[10px] font-bold bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50">
                              אשר
                            </button>
                            <button disabled={isBusy} onClick={() => doAction(wl.id, "reject")}
                              className="px-2 min-h-[28px] text-[10px] font-bold bg-red-50 text-red-700 rounded hover:bg-red-100 disabled:opacity-50">
                              דחה
                            </button>
                          </>)}
                          <button onClick={() => openDetail(wl.id)} className="px-1.5 min-h-[28px] text-gray-400 hover:text-blue-600">
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Invoice CTA */}
        {approvedWLs.length > 0 && statusFilter !== "APPROVED" && (
          <div className="bg-green-50 border border-green-200 rounded-xl p-3 flex items-center justify-between">
            <p className="text-sm font-bold text-green-800">{approvedWLs.length} דיווחים מאושרים מוכנים לחשבונית</p>
            <button onClick={() => setStatusFilter("APPROVED")}
              className="px-4 min-h-[40px] bg-green-600 text-white text-sm font-bold rounded-lg hover:bg-green-700 flex items-center gap-2">
              <FileText className="w-4 h-4" /> בחר להפקת חשבונית
            </button>
          </div>
        )}

      </div>

      {/* Detail Modal */}
      {detailId && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={() => setDetailId(null)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            {detailLoading ? (
              <div className="p-12 text-center"><RefreshCw className="w-6 h-6 animate-spin text-gray-400 mx-auto" /></div>
            ) : detail ? (
              <div dir="rtl">
                {/* Modal header */}
                <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between sticky top-0 bg-white z-10">
                  <h2 className="text-base font-bold text-gray-900">דיווח #{detail.report_number}</h2>
                  <button onClick={() => setDetailId(null)} className="p-1 hover:bg-gray-100 rounded"><X className="w-5 h-5" /></button>
                </div>

                <div className="p-5 space-y-4">
                  {/* Warnings */}
                  {detail.warnings.length > 0 && (
                    <div className="space-y-1.5">
                      {detail.warnings.map((w, i) => (
                        <div key={i} className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 flex items-center gap-2 text-sm text-amber-800 font-medium">
                          <AlertTriangle className="w-4 h-4 flex-shrink-0" /> {w.message}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Info grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    <DField label="תאריך" value={detail.report_date} />
                    <DField label="פרויקט" value={detail.project_name} />
                    <DField label="ספק" value={detail.supplier_name} />
                    <DField label="מדווח" value={detail.reporter_name} />
                    <DField label="סוג דיווח" value={detail.report_type || "רגיל"} />
                    <DField label="הזמנה" value={detail.work_order_number ? `#${detail.work_order_number}` : "—"} />
                  </div>

                  {/* Hours */}
                  <div className="bg-gray-50 rounded-xl p-3">
                    <h3 className="text-xs font-bold text-gray-700 mb-2 flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> פירוט שעות</h3>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                      <DField label="שעות עבודה" value={`${detail.work_hours}`} />
                      <DField label="הפסקות" value={`${detail.break_hours}`} />
                      <DField label="שעות נטו" value={`${detail.net_hours || detail.work_hours}`} />
                      {detail.is_overnight && <DField label="לינת שטח" value={`${detail.overnight_nights} לילות (${fmtILS(detail.overnight_total)})`} />}
                    </div>
                  </div>

                  {/* Cost */}
                  <div className="bg-gray-50 rounded-xl p-3">
                    <h3 className="text-xs font-bold text-gray-700 mb-2 flex items-center gap-1"><DollarSign className="w-3.5 h-3.5" /> חישוב עלות</h3>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
<DField label="תעריף שעתי" value={`${detail.hourly_rate}`} />
                      <DField label="מקור תעריף" value={detail.rate_source_name || detail.rate_source || "—"} />
                      <DField label="לפני מע״מ" value={fmtILS(detail.cost_before_vat)} />
                      <DField label="כולל מע״מ" value={fmtILS(detail.cost_with_vat)} bold />
                    </div>
                  </div>

                  {/* Equipment */}
                  <div className="bg-gray-50 rounded-xl p-3">
                    <h3 className="text-xs font-bold text-gray-700 mb-2 flex items-center gap-1"><Wrench className="w-3.5 h-3.5" /> ציוד</h3>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
                      <DField label="סוג ציוד" value={detail.equipment_type || "—"} />
                      <DField label="מספר רישוי" value={detail.license_plate || "—"} />
<DField label="נסרק" value={detail.equipment_scanned ? "כן " : "לא"} />
                    </div>
                  </div>

                  {/* Invoice */}
                  {detail.invoice && (
                    <div className="bg-purple-50 border border-purple-200 rounded-xl p-3">
                      <p className="text-xs font-bold text-purple-800">חשבונית: {detail.invoice.invoice_number} ({detail.invoice.status})</p>
                    </div>
                  )}

                  {/* Audit trail */}
                  {detail.audit_trail.length > 0 && (
                    <div>
                      <h3 className="text-xs font-bold text-gray-700 mb-2">היסטוריית אישורים</h3>
                      <div className="space-y-1">
                        {detail.audit_trail.map((a, i) => (
                          <div key={i} className="flex items-center gap-2 text-xs text-gray-600 bg-gray-50 rounded px-2.5 py-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-blue-400 flex-shrink-0" />
                            <span className="font-medium text-gray-800">{a.description}</span>
                            {a.user_name && <span className="text-gray-400">— {a.user_name}</span>}
                            {a.created_at && <span className="text-gray-400 mr-auto text-[10px]">{new Date(a.created_at).toLocaleString("he-IL")}</span>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Approver info */}
                  {detail.approver_name && (
                    <div className="text-xs text-gray-500">
                      אושר על ידי <span className="font-bold text-gray-700">{detail.approver_name}</span>
                      {detail.approved_at && <> בתאריך {new Date(detail.approved_at).toLocaleString("he-IL")}</>}
                    </div>
                  )}

                  {/* Actions */}
                  {detail.status === "SUBMITTED" && (
                    <div className="flex gap-2 pt-2 border-t border-gray-100">
                      <button onClick={() => doAction(detail.id, "approve")}
                        className="flex-1 flex items-center justify-center gap-2 min-h-[44px] bg-green-600 text-white font-bold text-sm rounded-xl hover:bg-green-700">
                        <CheckCircle className="w-4 h-4" /> אשר דיווח
                      </button>
                      <button onClick={() => doAction(detail.id, "reject")}
                        className="flex-1 flex items-center justify-center gap-2 min-h-[44px] bg-red-50 text-red-700 font-bold text-sm rounded-xl hover:bg-red-100">
                        <XCircle className="w-4 h-4" /> דחה
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ) : <div className="p-8 text-center text-gray-400">שגיאה בטעינת פרטים</div>}
          </div>
        </div>
      )}
    </div>
  );
};

const FKPI: React.FC<{ label: string; value: string; color: string; pulse?: boolean }> = ({ label, value, color, pulse }) => {
  const bg: Record<string, string> = { amber: "border-r-amber-500 bg-amber-50", green: "border-r-green-500 bg-green-50", blue: "border-r-blue-500 bg-blue-50", red: "border-r-red-500 bg-red-50", orange: "border-r-orange-500 bg-orange-50", gray: "border-r-gray-200 bg-white" };
  const fg: Record<string, string> = { amber: "text-amber-700", green: "text-green-700", blue: "text-blue-700", red: "text-red-700", orange: "text-orange-700", gray: "text-gray-400" };
  return (
    <div className={`rounded-lg border border-gray-200 border-r-4 shadow-sm p-2.5 ${bg[color] || bg.gray}`}>
      <div className="flex items-center justify-between">
        <p className={`text-lg sm:text-xl font-extrabold ${fg[color] || "text-gray-900"}`}>{value}</p>
        {pulse && <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />}
      </div>
      <p className="text-[10px] text-gray-500 mt-0.5">{label}</p>
    </div>
  );
};

const DField: React.FC<{ label: string; value: string | null; bold?: boolean }> = ({ label, value, bold }) => (
  <div>
    <p className="text-[10px] text-gray-400">{label}</p>
    <p className={`text-xs ${bold ? "font-bold text-gray-900" : "text-gray-700"}`}>{value || "—"}</p>
  </div>
);

export default AccountantDashboard;
