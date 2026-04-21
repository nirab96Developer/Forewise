import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle, Send, CheckCircle, XCircle,
  Search, Filter, ChevronDown, ChevronUp,
  ShieldAlert, Info, RefreshCw, Clock, Inbox, ArrowLeftRight
} from "lucide-react";
import api from "../../services/api";
import UnifiedLoader from "../../components/common/UnifiedLoader";
import { getWorkOrderStatusLabel, getSupplierResponseLabel } from "../../strings";

interface WOItem {
  id: number; order_number: number; title: string; status: string;
  priority: string; project_name: string; project_id: number;
  supplier_name: string | null; supplier_id: number | null;
  creator_name: string; equipment_type: string;
  is_forced: boolean; constraint_notes: string | null;
  created_at: string | null; updated_at: string | null;
  equipment_plate: string | null; is_expired_soon: boolean;
  supplier_history: {
    supplier_name: string; status: string;
    sent_at: string | null; responded_at: string | null;
    notes: string | null; decline_reason: string | null;
  }[];
}

interface QueueData {
  kpis: Record<string, number>;
  alerts: { type: string; message: string }[];
  work_orders: WOItem[];
  filter_options: {
    projects: { id: number; name: string }[];
    statuses: { value: string; label: string }[];
  };
}

// Status visuals — labels via `src/strings/statuses.ts`. Local map only
// holds the action label (which is UI workflow, not text).
const STATUS_ACTION: Record<string, string | undefined> = {
  PENDING:                                "שלח לספק",
  DISTRIBUTING:                           "ספק הבא",
  SUPPLIER_ACCEPTED_PENDING_COORDINATOR:  "אשר סופית",
  EXPIRED:                                "שלח שוב",
};
const STATUS_CLS: Record<string, string> = {
  PENDING:                                "bg-yellow-100 text-yellow-800",
  DISTRIBUTING:                           "bg-blue-100 text-blue-800",
  SUPPLIER_ACCEPTED_PENDING_COORDINATOR:  "bg-emerald-100 text-emerald-800",
  APPROVED_AND_SENT:                      "bg-green-100 text-green-800",
  EXPIRED:                                "bg-red-100 text-red-700",
  STOPPED:                                "bg-gray-100 text-gray-600",
  REJECTED:                               "bg-red-100 text-red-700",
};
const statusCfg = (status: string) => {
  const upper = (status || '').toUpperCase();
  return {
    label: getWorkOrderStatusLabel(status),
    cls: STATUS_CLS[upper] || 'bg-gray-100 text-gray-600',
    actionLabel: STATUS_ACTION[upper],
  };
};

const timeAgo = (d: string | null) => {
  if (!d) return "";
  const mins = Math.floor((Date.now() - new Date(d).getTime()) / 60000);
  if (mins < 1) return "עכשיו";
  if (mins < 60) return `לפני ${mins} דק׳`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `לפני ${hrs} שע׳`;
  return `לפני ${Math.floor(hrs / 24)} ימים`;
};

const getGreeting = () => {
  const h = new Date().getHours();
  if (h < 12) return "בוקר טוב";
  if (h < 17) return "צהריים טובים";
  return "ערב טוב";
};

const OrderCoordinatorDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<QueueData | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [projectFilter, setProjectFilter] = useState("");
  const [searchText, setSearchText] = useState("");
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [actionBusy, setActionBusy] = useState<number | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (statusFilter) params.status_filter = statusFilter;
      if (projectFilter) params.project_id = projectFilter;
      if (searchText) params.search = searchText;
      const r = await api.get("/dashboard/coordinator-queue", { params });
      setData(r.data);
    } catch {}
    setLoading(false);
  }, [statusFilter, projectFilter, searchText]);

  useEffect(() => { loadData(); }, [loadData]);

  const doAction = async (woId: number, action: string) => {
    setActionBusy(woId);
    try {
      if (action === "send") await api.post(`/work-orders/${woId}/send-to-supplier`);
      else if (action === "approve") await api.post(`/work-orders/${woId}/approve`);
      else if (action === "reject") await api.post(`/work-orders/${woId}/reject`, { reason: "נדחה ע״י מתאם" });
      else if (action === "next") await api.post(`/work-orders/${woId}/move-to-next-supplier`);
      else if (action === "resend") await api.post(`/work-orders/${woId}/send-to-supplier`);
      await loadData();
    } catch (e: any) {
      alert(e?.response?.data?.detail || "שגיאה בביצוע פעולה");
    }
    setActionBusy(null);
  };

  if (loading && !data) return <UnifiedLoader size="full" />;
  if (!data) return <div className="p-8 text-center text-gray-500">שגיאה בטעינת נתונים</div>;

  const k = data.kpis || {} as Record<string, number>;
  const totalActive = (k.pending ?? 0) + (k.distributing ?? 0) + (k.supplier_accepted ?? 0) + (k.expired ?? 0);

  return (
    <div className="min-h-full bg-gray-50" dir="rtl">
      <div className="p-3 sm:p-5 space-y-4 max-w-screen-xl mx-auto">

        {/* Header */}
        <div className="bg-gradient-to-l from-green-700 to-green-800 rounded-2xl p-5 sm:p-6 text-white shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-200 text-sm mb-1">{getGreeting()}</p>
              <h1 className="text-xl sm:text-2xl font-extrabold flex items-center gap-2.5">
                <ArrowLeftRight className="w-6 h-6 text-green-300" />
                תיאום הזמנות
              </h1>
              <p className="text-green-200 text-sm mt-1">
                {totalActive > 0
                  ? `${totalActive} הזמנות דורשות טיפול`
                  : "אין הזמנות ממתינות — הכל מטופל"}
              </p>
            </div>
            <button onClick={loadData} disabled={loading}
              className="flex items-center gap-1.5 px-4 py-2.5 text-xs font-bold bg-white/15 hover:bg-white/25 text-white rounded-xl backdrop-blur-sm transition-colors disabled:opacity-50">
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} /> רענן
            </button>
          </div>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-3 sm:grid-cols-5 gap-2 sm:gap-3">
          <MiniKPI label="ממתין לשליחה" value={k.pending ?? 0} color={(k.pending ?? 0) > 0 ? "amber" : "gray"} icon={<Clock className="w-4 h-4" />} />
          <MiniKPI label="בהפצה" value={k.distributing ?? 0} color={(k.distributing ?? 0) > 0 ? "blue" : "gray"} icon={<Send className="w-4 h-4" />} />
          <MiniKPI label="ממתין לאישור" value={k.supplier_accepted ?? 0} color={(k.supplier_accepted ?? 0) > 0 ? "green" : "gray"} pulse={(k.supplier_accepted ?? 0) > 0} icon={<CheckCircle className="w-4 h-4" />} />
          <MiniKPI label="פג תוקף" value={k.expired ?? 0} color={(k.expired ?? 0) > 0 ? "red" : "gray"} icon={<AlertTriangle className="w-4 h-4" />} />
          <MiniKPI label="אילוץ ספק" value={k.forced_cases ?? 0} color={(k.forced_cases ?? 0) > 0 ? "orange" : "gray"} icon={<ShieldAlert className="w-4 h-4" />} />
        </div>

        {/* Alerts */}
        {(data.alerts?.length ?? 0) > 0 && (
          <div className="space-y-1.5">
            {(data.alerts || []).map((a, i) => {
              const Icon = a.type === "error" ? ShieldAlert : a.type === "warning" ? AlertTriangle : Info;
              const cls = a.type === "error" ? "border-red-300 bg-red-50 text-red-800" :
                          a.type === "warning" ? "border-amber-300 bg-amber-50 text-amber-800" :
                          "border-blue-200 bg-blue-50 text-blue-800";
              return (
                <div key={i} className={`rounded-lg border px-3 py-2 flex items-center gap-2.5 text-sm font-medium ${cls}`}>
                  <Icon className="w-4 h-4 flex-shrink-0" /> {a.message}
                </div>
              );
            })}
          </div>
        )}

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-3 flex flex-wrap gap-2 items-center">
          <div className="flex items-center gap-1.5 text-xs text-gray-500 font-medium"><Filter className="w-3.5 h-3.5" /> סינון:</div>
          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
            className="px-2.5 py-2 text-xs border border-gray-300 rounded-lg bg-white min-w-[130px] focus:ring-2 focus:ring-green-300 focus:border-green-400">
            <option value="">כל הסטטוסים</option>
            {(data.filter_options?.statuses || []).map(s => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
          <select value={projectFilter} onChange={e => setProjectFilter(e.target.value)}
            className="px-2.5 py-2 text-xs border border-gray-300 rounded-lg bg-white min-w-[130px] focus:ring-2 focus:ring-green-300 focus:border-green-400">
            <option value="">כל הפרויקטים</option>
            {(data.filter_options?.projects || []).map(p => (
              <option key={p.id} value={String(p.id)}>{p.name}</option>
            ))}
          </select>
          <div className="flex-1 min-w-[150px] relative">
            <Search className="w-3.5 h-3.5 absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
            <input type="text" value={searchText}
              onChange={e => setSearchText(e.target.value)}
              placeholder="חיפוש לפי מספר או כותרת..."
              className="w-full pr-8 pl-3 py-2 text-xs border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-300 focus:border-green-400" />
          </div>
        </div>

        {/* Queue */}
        <div className="space-y-2.5">
          {(data.work_orders?.length ?? 0) === 0 ? (
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-10 text-center">
              <div className="w-16 h-16 bg-green-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Inbox className="w-8 h-8 text-green-400" />
              </div>
              <p className="text-lg font-bold text-gray-700 mb-1">אין הזמנות בתור</p>
              <p className="text-sm text-gray-400">כל ההזמנות טופלו. המערכת תתעדכן אוטומטית כשיגיעו הזמנות חדשות.</p>
            </div>
          ) : (data.work_orders || []).map(wo => {
            const st = statusCfg(wo.status);
            const isExpanded = expandedId === wo.id;
            const isBusy = actionBusy === wo.id;

            return (
              <div key={wo.id} className={`bg-white rounded-xl shadow-sm border transition-all ${
                wo.is_expired_soon ? "border-red-300" : "border-gray-200"}`}>
                {/* Header row */}
                <div className="p-3.5 flex flex-col sm:flex-row sm:items-center gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-bold text-gray-900">#{wo.order_number}</span>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${st.cls}`}>{st.label}</span>
                      {wo.is_forced && <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-orange-100 text-orange-700">אילוץ</span>}
                      {wo.is_expired_soon && <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-red-100 text-red-700 animate-pulse">עומד לפוג</span>}
                    </div>
                    <p className="text-xs text-gray-700 font-medium truncate">{wo.title}</p>
                    <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-[11px] text-gray-500 mt-1">
                      <span>{wo.project_name}</span>
                      <span>מנהל: {wo.creator_name}</span>
                      {wo.equipment_type && <span>ציוד: {wo.equipment_type}</span>}
                      {wo.supplier_name && <span>ספק: {wo.supplier_name}</span>}
                      <span>{timeAgo(wo.updated_at)}</span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-1.5 flex-shrink-0 flex-wrap">
                    {wo.status === "PENDING" && (
                      <ActionBtn label="שלח לספק" icon={<Send className="w-3.5 h-3.5" />}
                        cls="bg-blue-600 text-white hover:bg-blue-700"
                        busy={isBusy} onClick={() => doAction(wo.id, "send")} />
                    )}
                    {wo.status === "DISTRIBUTING" && (
                      <ActionBtn label="ספק הבא" icon={<RefreshCw className="w-3.5 h-3.5" />}
                        cls="bg-amber-100 text-amber-800 hover:bg-amber-200"
                        busy={isBusy} onClick={() => doAction(wo.id, "next")} />
                    )}
                    {wo.status === "SUPPLIER_ACCEPTED_PENDING_COORDINATOR" && (<>
                      <ActionBtn label="אשר" icon={<CheckCircle className="w-3.5 h-3.5" />}
                        cls="bg-green-600 text-white hover:bg-green-700"
                        busy={isBusy} onClick={() => doAction(wo.id, "approve")} />
                      <ActionBtn label="דחה" icon={<XCircle className="w-3.5 h-3.5" />}
                        cls="bg-red-50 text-red-700 hover:bg-red-100"
                        busy={isBusy} onClick={() => doAction(wo.id, "reject")} />
                    </>)}
                    {wo.status === "EXPIRED" && (
                      <ActionBtn label="שלח שוב" icon={<Send className="w-3.5 h-3.5" />}
                        cls="bg-blue-600 text-white hover:bg-blue-700"
                        busy={isBusy} onClick={() => doAction(wo.id, "resend")} />
                    )}
                    <button onClick={() => navigate(`/work-orders/${wo.id}`)}
                      className="px-2.5 min-h-[36px] text-[11px] text-gray-500 hover:text-blue-600 transition-colors">
                      פרטים
                    </button>
                    {(wo.supplier_history?.length ?? 0) > 0 && (
                      <button onClick={() => setExpandedId(isExpanded ? null : wo.id)}
                        className="px-1.5 min-h-[36px] text-gray-400 hover:text-gray-600 transition-colors">
                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </button>
                    )}
                  </div>
                </div>

                {/* Expanded: supplier history */}
                {isExpanded && (wo.supplier_history?.length ?? 0) > 0 && (
                  <div className="border-t border-gray-100 bg-gray-50 px-4 py-3">
                    <p className="text-[10px] font-bold text-gray-500 mb-2 uppercase tracking-wide">היסטוריית ספקים</p>
                    <div className="space-y-1.5">
                      {wo.supplier_history.map((h, idx) => (
                        <div key={idx} className="flex items-center gap-2 text-xs">
                          <span className={`w-2 h-2 rounded-full flex-shrink-0 ${
                            h.status === "ACCEPTED" ? "bg-green-500" :
                            h.status === "REJECTED" ? "bg-red-500" : "bg-gray-400"}`} />
                          <span className="font-medium text-gray-800">{h.supplier_name || "ספק"}</span>
                          <span className={`text-[10px] font-bold ${
                            h.status === "ACCEPTED" ? "text-green-600" :
                            h.status === "REJECTED" ? "text-red-600" : "text-gray-500"}`}>
                            {getSupplierResponseLabel(h.status)}
                          </span>
                          {h.decline_reason && <span className="text-gray-400">— {h.decline_reason}</span>}
                          {h.responded_at && <span className="text-gray-400 mr-auto">{timeAgo(h.responded_at)}</span>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

      </div>
    </div>
  );
};

const MiniKPI: React.FC<{ label: string; value: number; color: string; pulse?: boolean; icon?: React.ReactNode }> = ({ label, value, color, pulse, icon }) => {
  const bg: Record<string, string> = {
    amber: "border-r-amber-500 bg-gradient-to-l from-amber-50 to-white", 
    blue: "border-r-blue-500 bg-gradient-to-l from-blue-50 to-white",
    green: "border-r-green-600 bg-gradient-to-l from-green-50 to-white", 
    red: "border-r-red-500 bg-gradient-to-l from-red-50 to-white",
    orange: "border-r-orange-500 bg-gradient-to-l from-orange-50 to-white", 
    gray: "border-r-gray-200 bg-white",
  };
  const fg: Record<string, string> = {
    amber: "text-amber-700", blue: "text-blue-700", green: "text-green-700",
    red: "text-red-700", orange: "text-orange-700", gray: "text-gray-300",
  };
  const iconCls: Record<string, string> = {
    amber: "text-amber-400", blue: "text-blue-400", green: "text-green-500",
    red: "text-red-400", orange: "text-orange-400", gray: "text-gray-300",
  };
  return (
    <div className={`rounded-xl border border-gray-200 border-r-4 shadow-sm p-3 sm:p-3.5 min-h-[72px] transition-shadow hover:shadow-md ${bg[color] || bg.gray}`}>
      <div className="flex items-center justify-between mb-1">
        <p className={`text-2xl sm:text-3xl font-extrabold ${fg[color] || "text-gray-900"}`}>{value}</p>
        <div className="flex items-center gap-1.5">
          {pulse && <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />}
          {icon && <span className={iconCls[color] || "text-gray-300"}>{icon}</span>}
        </div>
      </div>
      <p className="text-[10px] sm:text-[11px] font-medium text-gray-500">{label}</p>
    </div>
  );
};

const ActionBtn: React.FC<{
  label: string; icon: React.ReactNode; cls: string;
  busy: boolean; onClick: () => void;
}> = ({ label, icon, cls, busy, onClick }) => (
  <button disabled={busy} onClick={onClick}
    className={`flex items-center gap-1 px-2.5 min-h-[36px] text-[11px] font-bold rounded-lg transition-colors disabled:opacity-50 ${cls}`}>
    {icon} {label}
  </button>
);

export default OrderCoordinatorDashboard;
