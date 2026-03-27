import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Briefcase, Clock, FileText, DollarSign, FolderOpen,
  AlertTriangle, ChevronLeft, Info, ShieldAlert, Plus,
  CheckCircle, ClipboardList
} from "lucide-react";
import api from "../../services/api";
import UnifiedLoader from "../../components/common/UnifiedLoader";

interface AreaData {
  area_name: string;
  kpis: {
    open_work_orders: number; pending_worklogs: number;
    submitted_for_approval: number; draft_invoices: number; total_projects: number;
    stuck_work_orders: number;
  };
  budget: { total: number; committed: number; spent: number; remaining: number; utilization_pct: number };
  work_orders: {
    id: number; order_number: number; status: string; title: string;
    supplier_name: string | null; project_name: string; created_at: string | null;
  }[];
  pending_approvals: {
    id: number; report_date: string | null; work_hours: number;
    status: string; reporter: string; project_name: string;
  }[];
  alerts: { type: string; message: string; link: string }[];
}

const fmtCurrency = (n: number) =>
n >= 1e6 ? `${(n/1e6).toFixed(1)}M ` : n >= 1e3 ? `${(n/1e3).toFixed(0)}K ` : `${n.toLocaleString("he-IL", {maximumFractionDigits:0})}`;

const WO_STATUS: Record<string, { label: string; cls: string }> = {
  PENDING: { label: "ממתין", cls: "bg-yellow-100 text-yellow-800" },
  DISTRIBUTING: { label: "בהפצה", cls: "bg-blue-100 text-blue-800" },
  SUPPLIER_ACCEPTED_PENDING_COORDINATOR: { label: "ספק אישר", cls: "bg-blue-100 text-blue-800" },
  APPROVED_AND_SENT: { label: "אושר", cls: "bg-green-100 text-green-800" },
  COMPLETED: { label: "הושלם", cls: "bg-gray-100 text-gray-700" },
  REJECTED: { label: "נדחה", cls: "bg-red-100 text-red-700" },
  CANCELLED: { label: "בוטל", cls: "bg-red-100 text-red-700" },
  EXPIRED: { label: "פג תוקף", cls: "bg-gray-100 text-gray-600" },
  STOPPED: { label: "הופסק", cls: "bg-red-100 text-red-700" },
};

const AreaManagerDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<AreaData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/dashboard/area-overview")
      .then(r => setData(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <UnifiedLoader size="full" />;
  if (!data) return <div className="p-8 text-center text-gray-500">שגיאה בטעינת נתונים</div>;

  const k = data.kpis;
  const b = data.budget;

  return (
    <div className="min-h-full bg-gray-50" dir="rtl">
      <div className="p-3 sm:p-5 lg:p-6 space-y-4 sm:space-y-5 max-w-screen-2xl mx-auto">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FolderOpen className="w-6 h-6 text-green-600" />
            <div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-gray-900">אזור {data.area_name}</h1>
              <p className="text-xs text-gray-500">{k.total_projects} פרויקטים</p>
            </div>
          </div>
          <button onClick={() => navigate("/work-orders/new")}
            className="flex items-center gap-2 px-4 min-h-[44px] bg-blue-600 text-white text-sm font-bold rounded-xl hover:bg-blue-700 transition-colors">
            <Plus className="w-4 h-4" /> הזמנת עבודה
          </button>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          <KPI icon={<Briefcase className="w-5 h-5" />} label="הזמנות פתוחות" value={k.open_work_orders}
            accent={k.open_work_orders > 0 ? "border-r-blue-500 bg-blue-50" : "border-r-gray-200 bg-white"}
            fg={k.open_work_orders > 0 ? "text-blue-600" : "text-gray-400"} to="/order-coordination" />
          <KPI icon={<AlertTriangle className="w-5 h-5" />} label="תקועות >48שע" value={k.stuck_work_orders || 0}
            accent={(k.stuck_work_orders || 0) > 0 ? "border-r-red-600 bg-red-50" : "border-r-gray-200 bg-white"}
            fg={(k.stuck_work_orders || 0) > 0 ? "text-red-600" : "text-gray-400"}
            pulse={(k.stuck_work_orders || 0) > 0} to="/order-coordination" />
          <KPI icon={<Clock className="w-5 h-5" />} label="ממתינים לאישורי" value={k.submitted_for_approval}
            accent={k.submitted_for_approval > 0 ? "border-r-amber-500 bg-amber-50" : "border-r-gray-200 bg-white"}
            fg={k.submitted_for_approval > 0 ? "text-amber-600" : "text-gray-400"} to="/accountant-inbox" pulse={k.submitted_for_approval > 0} />
          <KPI icon={<FileText className="w-5 h-5" />} label="חשבוניות טיוטה" value={k.draft_invoices}
            accent={k.draft_invoices > 0 ? "border-r-orange-500 bg-orange-50" : "border-r-gray-200 bg-white"}
            fg={k.draft_invoices > 0 ? "text-orange-600" : "text-gray-400"} to="/invoices" />
          <KPI icon={<FolderOpen className="w-5 h-5" />} label="פרויקטים" value={k.total_projects}
            accent="border-r-green-400 bg-white" fg="text-green-600" to="/projects" />
        </div>

        {/* Alerts */}
        {data.alerts.length > 0 && (
          <div className="space-y-2">
            {data.alerts.map((a, i) => {
              const isErr = a.type === "error";
              const Icon = isErr ? ShieldAlert : a.type === "warning" ? AlertTriangle : Info;
              return (
                <div key={i} className={`rounded-xl border px-3 sm:px-4 py-3.5 flex flex-col sm:flex-row sm:items-center gap-2.5 ${
                  isErr ? "border-red-300 bg-red-50" : "border-amber-300 bg-amber-50"}`}>
                  <div className="flex items-center gap-3 flex-1">
                    <Icon className={`w-[22px] h-[22px] flex-shrink-0 ${isErr ? "text-red-600" : "text-amber-600"}`} />
                    <span className={`text-sm font-semibold ${isErr ? "text-red-800" : "text-amber-800"}`}>{a.message}</span>
                  </div>
                  <button onClick={() => navigate(a.link)}
                    className={`w-full sm:w-auto px-4 min-h-[44px] text-sm font-bold rounded-lg text-white ${
                      isErr ? "bg-red-600 hover:bg-red-700" : "bg-amber-600 hover:bg-amber-700"}`}>
                    {isErr ? "טפל עכשיו" : "צפה"}
                  </button>
                </div>
              );
            })}
          </div>
        )}

        {/* Budget + Quick Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Budget */}
          <div className="bg-white rounded-xl shadow-sm p-3 sm:p-4 lg:col-span-2">
            <h3 className="text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
              <DollarSign className="w-4 h-4" /> תקציב אזורי
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
              <div><p className="text-[11px] text-gray-500">סה״כ</p><p className="text-base sm:text-lg font-bold">{fmtCurrency(b.total)}</p></div>
              <div><p className="text-[11px] text-gray-500">מוקפא</p><p className="text-base sm:text-lg font-bold text-amber-600">{fmtCurrency(b.committed)}</p></div>
              <div><p className="text-[11px] text-gray-500">הוצא</p><p className="text-base sm:text-lg font-bold text-red-600">{fmtCurrency(b.spent)}</p></div>
              <div><p className="text-[11px] text-gray-500">זמין</p><p className="text-base sm:text-lg font-bold text-green-600">{fmtCurrency(b.remaining)}</p></div>
            </div>
            <div className="relative w-full bg-gray-100 rounded-full h-3 sm:h-4 overflow-hidden">
              <div className="h-full rounded-full transition-all duration-700"
                style={{ width: `${Math.min(b.utilization_pct, 100)}%`,
                  background: b.utilization_pct > 90 ? "#ef4444" : b.utilization_pct > 60 ? "#f59e0b" : "#22c55e" }} />
            </div>
            <p className="text-[10px] text-gray-400 mt-1">{b.utilization_pct}% ניצול</p>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-xl shadow-sm p-3 sm:p-4">
            <h3 className="text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
              <Plus className="w-4 h-4 text-green-600" /> פעולות
            </h3>
            <div className="space-y-2">
              {[
                { label: "הזמנת עבודה חדשה", path: "/work-orders/new", icon: <ClipboardList className="w-[18px] h-[18px]" />, cls: "bg-blue-600 text-white hover:bg-blue-700" },
                { label: "פרויקט חדש", path: "/projects/new", icon: <FolderOpen className="w-[18px] h-[18px]" />, cls: "bg-green-50 text-green-700 hover:bg-green-100" },
                { label: "אישור דיווחים", path: "/work-logs", icon: <CheckCircle className="w-[18px] h-[18px]" />, cls: "bg-amber-50 text-amber-700 hover:bg-amber-100" },
                { label: "חשבוניות", path: "/invoices", icon: <FileText className="w-[18px] h-[18px]" />, cls: "bg-gray-50 text-gray-700 hover:bg-gray-100" },
              ].map(a => (
                <button key={a.path} onClick={() => navigate(a.path)}
                  className={`w-full flex items-center gap-2.5 px-3 min-h-[44px] text-sm font-medium rounded-lg transition-colors ${a.cls}`}>
                  {a.icon} {a.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Work Orders + Pending Approvals */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

          {/* Work Orders */}
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 className="text-sm font-bold text-gray-700 flex items-center gap-2">
                <Briefcase className="w-4 h-4" /> הזמנות עבודה
              </h3>
              <button onClick={() => navigate("/work-orders")}
                className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center gap-0.5 min-h-[44px] px-2">
                הכל <ChevronLeft className="w-3 h-3" />
              </button>
            </div>
            <div className="divide-y divide-gray-100 max-h-[340px] overflow-y-auto">
              {data.work_orders.length === 0 ? (
                <div className="p-6 text-center text-sm text-gray-400">אין הזמנות</div>
              ) : data.work_orders.map(wo => {
                const st = WO_STATUS[wo.status] || { label: wo.status, cls: "bg-gray-100 text-gray-600" };
                return (
                  <div key={wo.id} onClick={() => navigate(`/work-orders/${wo.id}`)}
                    className="px-4 py-3 hover:bg-blue-50/40 cursor-pointer transition-colors">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-semibold text-gray-800">#{wo.order_number} {wo.title}</span>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${st.cls}`}>{st.label}</span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-gray-500">
                      <span>{wo.project_name}</span>
                      {wo.supplier_name && <span>· {wo.supplier_name}</span>}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Pending Approvals */}
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 className="text-sm font-bold text-gray-700 flex items-center gap-2">
                <Clock className="w-4 h-4" /> דיווחים ממתינים לאישור
              </h3>
              <button onClick={() => navigate("/work-logs")}
                className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center gap-0.5 min-h-[44px] px-2">
                הכל <ChevronLeft className="w-3 h-3" />
              </button>
            </div>
            <PendingApprovalsList approvals={data.pending_approvals} />
          </div>
        </div>

      </div>
    </div>
  );
};

const KPI: React.FC<{
  icon: React.ReactNode; label: string; value: number;
  accent: string; fg: string; to: string; pulse?: boolean;
}> = ({ icon, label, value, accent, fg, to, pulse }) => {
  const navigate = useNavigate();
  return (
    <div onClick={() => navigate(to)}
      className={`rounded-xl border border-gray-200 border-r-4 shadow-sm p-3 sm:p-4 min-h-[80px]
        cursor-pointer hover:shadow-lg active:scale-[0.98] transition-all ${accent}`}>
      <div className="flex items-center justify-between mb-1.5">
        <span className={fg}>{icon}</span>
        {pulse && <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />}
      </div>
      <p className="text-2xl sm:text-3xl font-extrabold text-gray-900">{value}</p>
      <p className="text-[11px] text-gray-500 mt-0.5">{label}</p>
    </div>
  );
};

const PendingApprovalsList: React.FC<{ approvals: AreaData["pending_approvals"] }> = ({ approvals }) => {
  const navigate = useNavigate();
  const [actioned, setActioned] = useState<Record<number, string>>({});
  const [busy, setBusy] = useState<number | null>(null);

  const handleAction = async (id: number, action: "approve" | "reject") => {
    setBusy(id);
    try {
      await api.post(`/worklogs/${id}/${action}`);
      setActioned(prev => ({ ...prev, [id]: action }));
    } catch {
      alert(action === "approve" ? "שגיאה באישור" : "שגיאה בדחייה");
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="divide-y divide-gray-100 max-h-[340px] overflow-y-auto">
      {approvals.length === 0 ? (
        <div className="p-6 text-center text-sm text-gray-400">אין דיווחים ממתינים</div>
      ) : approvals.map(wl => {
        const done = actioned[wl.id];
        return (
          <div key={wl.id} className={`px-4 py-3 transition-colors ${done ? "bg-gray-50 opacity-60" : "hover:bg-blue-50/40"}`}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-semibold text-gray-800 cursor-pointer hover:text-blue-600"
                onClick={() => navigate(`/work-logs/${wl.id}`)}>{wl.reporter}</span>
              <span className="text-xs font-bold text-amber-600">{wl.work_hours} שעות</span>
            </div>
            <div className="flex items-center gap-3 text-xs text-gray-500 mb-2">
              <span>{wl.project_name}</span>
              {wl.report_date && <span>· {wl.report_date}</span>}
            </div>
            {done ? (
              <span className={`text-xs font-bold ${done === "approve" ? "text-green-600" : "text-red-600"}`}>
{done === "approve" ? " אושר" : " נדחה"}
              </span>
            ) : (
              <div className="flex gap-2">
                <button disabled={busy === wl.id} onClick={(e) => { e.stopPropagation(); handleAction(wl.id, "approve"); }}
                  className="flex items-center gap-1 px-3 min-h-[36px] text-xs font-bold bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors">
                  <CheckCircle className="w-3.5 h-3.5" /> אשר
                </button>
                <button disabled={busy === wl.id} onClick={(e) => { e.stopPropagation(); handleAction(wl.id, "reject"); }}
                  className="flex items-center gap-1 px-3 min-h-[36px] text-xs font-bold bg-red-50 text-red-700 rounded-lg hover:bg-red-100 disabled:opacity-50 transition-colors">
                  נדחה
                </button>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default AreaManagerDashboard;
