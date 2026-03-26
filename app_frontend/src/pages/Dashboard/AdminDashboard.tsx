import React, { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle, TrendingUp, FileText, Clock, Users, Truck,
  DollarSign, Activity, ChevronLeft, Plus,
  BarChart3, Settings, FolderOpen, Briefcase, UserPlus,
  ClipboardList, Info, ShieldAlert
} from "lucide-react";
import api from "../../services/api";
import UnifiedLoader from "../../components/common/UnifiedLoader";

interface AdminData {
  kpis: {
    open_work_orders: number; stuck_orders: number; pending_worklogs: number;
    pending_invoices: number; budget_overrun: number; expired_wo_week: number;
    total_users: number; total_suppliers: number; total_projects: number;
  };
  financial: { total: number; committed: number; spent: number; remaining: number; utilization_pct: number };
  alerts: { type: string; message: string; link: string }[];
  wo_chart: { date: string; count: number }[];
  wl_chart: { date: string; count: number }[];
  recent_events: {
    id: number; action: string; description: string;
    entity_type: string; entity_id: number; user_id: number;
    created_at: string; metadata: string | null; user_name: string | null;
  }[];
}

const fmtCurrency = (n: number) =>
n >= 1_000_000 ? `${(n / 1_000_000).toFixed(1)}M ` :
n >= 1_000 ? `${(n / 1_000).toFixed(0)}K ` :
`${n.toLocaleString("he-IL", { maximumFractionDigits: 0 })}`;

const timeAgo = (d: string) => {
  if (!d) return "";
  const diff = Date.now() - new Date(d).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "עכשיו";
  if (mins < 60) return `לפני ${mins} דק׳`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `לפני ${hrs} שע׳`;
  return `לפני ${Math.floor(hrs / 24)} ימים`;
};

const ACTION_CFG: Record<string, { label: string; dot: string }> = {
  STATUS_CHANGE_WORK_ORDER: { label: "שינוי סטטוס הזמנה", dot: "bg-blue-400" },
  STATUS_CHANGE_WORKLOG: { label: "שינוי סטטוס דיווח", dot: "bg-emerald-400" },
  STATUS_CHANGE_INVOICE: { label: "שינוי סטטוס חשבונית", dot: "bg-orange-400" },
  WORK_ORDER_CREATED: { label: "הזמנה חדשה", dot: "bg-green-500" },
  WORK_ORDER_APPROVED: { label: "הזמנה אושרה", dot: "bg-green-600" },
  WORK_ORDER_DELETED: { label: "הזמנה נמחקה", dot: "bg-red-400" },
  INVOICE_CREATED: { label: "חשבונית נוצרה", dot: "bg-orange-500" },
  BUDGET_FROZEN: { label: "תקציב הוקפא", dot: "bg-amber-500" },
  BUDGET_RELEASED: { label: "תקציב שוחרר", dot: "bg-emerald-400" },
  PROJECT_CREATED: { label: "פרויקט נוצר", dot: "bg-blue-500" },
  WORK_ORDER_EQUIPMENT_REMOVED: { label: "ציוד הוסר", dot: "bg-red-400" },
};

const AdminDashboard: React.FC = () => {
  const [data, setData] = useState<AdminData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/dashboard/admin-overview")
      .then(r => setData(r.data))
      .catch(() => { })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <UnifiedLoader size="full" />;
  if (!data) return <div className="p-8 text-center text-gray-500">שגיאה בטעינת נתונים</div>;

  const k = data.kpis;
  const f = data.financial;

  return (
    <div className="min-h-full bg-gray-50" dir="rtl">
      <div className="p-3 sm:p-5 lg:p-6 space-y-4 sm:space-y-5 max-w-screen-2xl mx-auto">

{/* PRIMARY KPIs */}
        <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          <KPI icon={<Briefcase className="w-5 h-5" />} label="הזמנות פתוחות" value={k.open_work_orders}
            accent="border-r-4 border-r-blue-500 bg-white" fg="text-blue-600" to="/work-orders" />
          <KPI icon={<AlertTriangle className="w-5 h-5" />} label="תקועות מעל 48 שעות" value={k.stuck_orders}
            accent={k.stuck_orders > 0 ? "border-r-4 border-r-red-600 bg-red-50" : "border-r-4 border-r-gray-200 bg-white"}
            fg={k.stuck_orders > 0 ? "text-red-600" : "text-gray-400"}
            pulse={k.stuck_orders > 0} to="/work-orders" />
          <KPI icon={<Clock className="w-5 h-5" />} label="דיווחים ממתינים" value={k.pending_worklogs}
            accent={k.pending_worklogs > 0 ? "border-r-4 border-r-amber-500 bg-amber-50" : "border-r-4 border-r-gray-200 bg-white"}
            fg={k.pending_worklogs > 0 ? "text-amber-600" : "text-gray-400"} to="/work-logs" />
          <KPI icon={<FileText className="w-5 h-5" />} label="חשבוניות טיוטה" value={k.pending_invoices}
            accent={k.pending_invoices > 0 ? "border-r-4 border-r-orange-500 bg-orange-50" : "border-r-4 border-r-gray-200 bg-white"}
            fg={k.pending_invoices > 0 ? "text-orange-600" : "text-gray-400"} to="/invoices" />
          <KPI icon={<DollarSign className="w-5 h-5" />} label="חריגות תקציב" value={k.budget_overrun}
            accent={k.budget_overrun > 0 ? "border-r-4 border-r-red-600 bg-red-50" : "border-r-4 border-r-green-400 bg-white"}
            fg={k.budget_overrun > 0 ? "text-red-600" : "text-green-600"}
            pulse={k.budget_overrun > 0} to="/settings/budgets" />
        </div>

{/* SECONDARY STATS */}
        <div className="grid grid-cols-3 gap-3">
          <MiniStat icon={<Users className="w-4 h-4 text-blue-500" />} label="משתמשים" value={k.total_users} to="/settings/admin/users" />
          <MiniStat icon={<Truck className="w-4 h-4 text-green-500" />} label="ספקים" value={k.total_suppliers} to="/settings/suppliers" />
          <MiniStat icon={<FolderOpen className="w-4 h-4 text-purple-500" />} label="פרויקטים" value={k.total_projects} to="/projects" />
        </div>

{/* ALERTS */}
        {data.alerts.length > 0 && (
          <div className="space-y-2">
            {data.alerts.map((a, i) => (
              <AlertRow key={i} alert={a} />
            ))}
          </div>
        )}

{/* QUICK ACTIONS + FINANCIAL */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 sm:gap-4">
          <QuickActions />
          <FinancialCard f={f} />
        </div>

{/* CHART + ACTIVITY FEED */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-3 sm:gap-4">
          <ActivityChart woChart={data.wo_chart} wlChart={data.wl_chart} />
          <EventFeed events={data.recent_events} />
        </div>

      </div>
    </div>
  );
};

/* */
/* KPI Card                                                        */
/* */

const KPI: React.FC<{
  icon: React.ReactNode; label: string; value: number;
  accent: string; fg: string; to: string; pulse?: boolean;
}> = ({ icon, label, value, accent, fg, to, pulse }) => {
  const navigate = useNavigate();
  return (
    <div onClick={() => navigate(to)}
      className={`rounded-xl border border-gray-200 shadow-sm p-3 sm:p-4 min-h-[80px] sm:min-h-[96px]
        cursor-pointer hover:shadow-lg active:scale-[0.98] transition-all ${accent}`}>
      <div className="flex items-center justify-between mb-1 sm:mb-2">
        <span className={fg}>{icon}</span>
        {pulse && <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />}
      </div>
      <p className="text-2xl sm:text-3xl font-extrabold text-gray-900">{value}</p>
      <p className="text-[11px] sm:text-xs text-gray-500 mt-0.5 leading-snug">{label}</p>
    </div>
  );
};

/* */
/* Mini Stat (secondary row)                                       */
/* */

const MiniStat: React.FC<{ icon: React.ReactNode; label: string; value: number; to: string }> = ({ icon, label, value, to }) => {
  const navigate = useNavigate();
  return (
    <div onClick={() => navigate(to)}
      className="bg-white rounded-lg border border-gray-200 shadow-sm px-3 py-2.5 sm:py-3
        flex items-center gap-2.5 cursor-pointer hover:shadow-md active:scale-[0.98] transition-all min-h-[44px]">
      {icon}
      <span className="text-lg sm:text-xl font-bold text-gray-900">{value}</span>
      <span className="text-xs text-gray-500">{label}</span>
    </div>
  );
};

/* */
/* Alert Row                                                       */
/* */

const AlertRow: React.FC<{ alert: { type: string; message: string; link: string } }> = ({ alert: a }) => {
  const navigate = useNavigate();
  const isErr = a.type === "error";
  const isWarn = a.type === "warning";

  const Icon = isErr ? ShieldAlert : isWarn ? AlertTriangle : Info;
  const border = isErr ? "border-red-300 bg-red-50" : isWarn ? "border-amber-300 bg-amber-50" : "border-blue-200 bg-blue-50";
  const iconCls = isErr ? "text-red-600" : isWarn ? "text-amber-600" : "text-blue-500";
  const textCls = isErr ? "text-red-800" : isWarn ? "text-amber-800" : "text-blue-800";
  const btnCls = isErr ? "bg-red-600 hover:bg-red-700" : isWarn ? "bg-amber-600 hover:bg-amber-700" : "bg-blue-600 hover:bg-blue-700";

  return (
    <div className={`rounded-xl border px-3 sm:px-4 py-3.5 flex flex-col sm:flex-row sm:items-center gap-2.5 sm:gap-3 ${border}`}>
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <Icon className={`w-[22px] h-[22px] flex-shrink-0 ${iconCls}`} />
        <span className={`text-sm font-semibold ${textCls}`}>{a.message}</span>
      </div>
      <button onClick={() => navigate(a.link)}
        className={`w-full sm:w-auto px-4 min-h-[44px] text-sm font-bold rounded-lg text-white transition-colors ${btnCls}`}>
        {isErr ? "טפל עכשיו" : "צפה"}
      </button>
    </div>
  );
};

/* */
/* Quick Actions                                                   */
/* */

const QuickActions: React.FC = React.memo(() => {
  const navigate = useNavigate();

  const primaryActions = [
    { label: "הזמנת עבודה חדשה", path: "/work-orders/new", icon: <ClipboardList className="w-5 h-5" />, cls: "bg-blue-600 text-white hover:bg-blue-700" },
  ];
  const secondaryActions = [
    { label: "משתמש חדש", path: "/settings/admin/users/new", icon: <UserPlus className="w-[18px] h-[18px]" />, cls: "bg-blue-50 text-blue-700 hover:bg-blue-100" },
    { label: "ספק חדש", path: "/settings/suppliers?action=new", icon: <Truck className="w-[18px] h-[18px]" />, cls: "bg-green-50 text-green-700 hover:bg-green-100" },
    { label: "פרויקט חדש", path: "/projects/new", icon: <FolderOpen className="w-[18px] h-[18px]" />, cls: "bg-purple-50 text-purple-700 hover:bg-purple-100" },
  ];
  const manageActions = [
    { label: "תקציבות", path: "/settings/budgets", icon: <DollarSign className="w-4 h-4" /> },
    { label: "סבב ספקים", path: "/settings/fair-rotation", icon: <TrendingUp className="w-4 h-4" /> },
    { label: "הגדרות", path: "/settings", icon: <Settings className="w-4 h-4" /> },
    { label: "יומן פעילות", path: "/activity-log", icon: <Activity className="w-4 h-4" /> },
  ];

  return (
    <div className="bg-white rounded-xl shadow-sm p-3 sm:p-4 space-y-3">
      <h3 className="text-sm font-bold text-gray-700 flex items-center gap-2">
        <Plus className="w-4 h-4 text-green-600" /> פעולות מהירות
      </h3>

      {primaryActions.map(a => (
        <button key={a.path} onClick={() => navigate(a.path)}
          className={`w-full flex items-center justify-center gap-2 min-h-[48px] text-sm font-bold rounded-xl transition-colors ${a.cls}`}>
          {a.icon} {a.label}
        </button>
      ))}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
        {secondaryActions.map(a => (
          <button key={a.path} onClick={() => navigate(a.path)}
            className={`flex items-center gap-2.5 px-3 min-h-[44px] text-sm font-medium rounded-lg transition-colors ${a.cls}`}>
            {a.icon} {a.label}
          </button>
        ))}
      </div>

      <div className="border-t border-gray-100 pt-2.5">
        <p className="text-[10px] font-semibold text-gray-400 mb-2 uppercase tracking-wide">ניהול</p>
        <div className="grid grid-cols-2 gap-2">
          {manageActions.map(a => (
            <button key={a.path} onClick={() => navigate(a.path)}
              className="flex items-center gap-2 px-2.5 min-h-[38px] text-xs rounded-md bg-gray-50 hover:bg-gray-100 text-gray-600 transition-colors">
              {a.icon} {a.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
});

/* */
/* Financial Card                                                  */
/* */

const FinancialCard: React.FC<{ f: AdminData["financial"] }> = React.memo(({ f }) => {
  const pct = Math.min(f.utilization_pct, 100);
  const barBg = pct > 90 ? "linear-gradient(to left, #dc2626, #f59e0b)"
    : pct > 60 ? "linear-gradient(to left, #f59e0b, #22c55e)"
      : "#22c55e";

  return (
    <div className="bg-white rounded-xl shadow-sm p-3 sm:p-4 lg:col-span-2">
      <h3 className="text-sm font-bold text-gray-700 mb-3 sm:mb-4 flex items-center gap-2">
        <DollarSign className="w-4 h-4" /> סיכום תקציבי
      </h3>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mb-4">
        <div><p className="text-[11px] text-gray-500">סה״כ תקציב</p><p className="text-base sm:text-lg font-bold text-gray-900">{fmtCurrency(f.total)}</p></div>
        <div><p className="text-[11px] text-gray-500">מוקפא</p><p className="text-base sm:text-lg font-bold text-amber-600">{fmtCurrency(f.committed)}</p></div>
        <div><p className="text-[11px] text-gray-500">הוצא</p><p className="text-base sm:text-lg font-bold text-red-600">{fmtCurrency(f.spent)}</p></div>
        <div><p className="text-[11px] text-gray-500">זמין</p><p className="text-base sm:text-lg font-bold text-green-600">{fmtCurrency(f.remaining)}</p></div>
      </div>
      <div className="relative w-full bg-gray-100 rounded-full h-3 sm:h-4 overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, background: barBg }} />
        {pct > 8 && (
          <span className="absolute inset-0 flex items-center justify-center text-[9px] sm:text-[10px] font-bold text-white drop-shadow-sm">
            {f.utilization_pct}%
          </span>
        )}
      </div>
      <p className="text-[10px] text-gray-400 mt-1 text-left">{f.utilization_pct}% ניצול תקציבי</p>
    </div>
  );
});

/* */
/* Activity Chart                                                  */
/* */

const ActivityChart: React.FC<{ woChart: AdminData["wo_chart"]; wlChart: AdminData["wl_chart"] }> = React.memo(({ woChart, wlChart }) => {
  const merged = useMemo(() => {
    const days: Record<string, { wo: number; wl: number }> = {};
    woChart.forEach(d => { days[d.date] = { ...(days[d.date] || { wo: 0, wl: 0 }), wo: d.count }; });
    wlChart.forEach(d => { days[d.date] = { ...(days[d.date] || { wo: 0, wl: 0 }), wl: d.count }; });
    return Object.entries(days).sort((a, b) => a[0].localeCompare(b[0]));
  }, [woChart, wlChart]);

  const maxVal = useMemo(() => Math.max(...merged.map(([, v]) => Math.max(v.wo, v.wl)), 1), [merged]);

  return (
    <div className="bg-white rounded-xl shadow-sm p-3 sm:p-5 lg:col-span-3">
      <h3 className="text-sm font-bold text-gray-700 mb-3 sm:mb-4 flex items-center gap-2">
        <BarChart3 className="w-4 h-4" /> פעילות 14 ימים אחרונים
      </h3>
      <div className="overflow-x-auto -mx-1 px-1">
        <div className="flex items-end gap-2 sm:gap-2.5 min-w-[320px]" style={{ height: "clamp(140px, 20vw, 200px)" }}>
          {merged.length === 0 ? (
            <p className="text-sm text-gray-400 m-auto">אין נתונים</p>
          ) : merged.map(([date, v]) => {
            const barH = "calc(100% - 20px)";
            const woP = Math.max(8, (v.wo / maxVal) * 100);
            const wlP = Math.max(8, (v.wl / maxVal) * 100);
            const day = new Date(date).toLocaleDateString("he-IL", { day: "numeric", month: "numeric" });
            return (
              <div key={date} className="flex-1 flex flex-col items-center gap-1 min-w-[24px]"
                title={`${day}: ${v.wo} הזמנות, ${v.wl} דיווחים`}>
                <div className="flex gap-[3px] items-end w-full justify-center" style={{ height: barH }}>
                  <div className="flex-1 max-w-[10px] bg-blue-400 rounded-t-sm transition-all" style={{ height: `${woP}%` }} />
                  <div className="flex-1 max-w-[10px] bg-emerald-400 rounded-t-sm transition-all" style={{ height: `${wlP}%` }} />
                </div>
                <span className="text-[9px] sm:text-[10px] text-gray-400 font-medium whitespace-nowrap">{day}</span>
              </div>
            );
          })}
        </div>
      </div>
      <div className="flex gap-5 mt-3 text-xs text-gray-500">
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 bg-blue-400 rounded-sm" /> הזמנות עבודה</span>
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 bg-emerald-400 rounded-sm" /> דיווחי שעות</span>
      </div>
    </div>
  );
});

/* */
/* Event Feed                                                      */
/* */

const EventFeed: React.FC<{ events: AdminData["recent_events"] }> = React.memo(({ events }) => {
  const navigate = useNavigate();
  return (
    <div className="bg-white rounded-xl shadow-sm overflow-hidden lg:col-span-2">
      <div className="px-3 sm:px-4 py-3 border-b border-gray-100 flex items-center justify-between">
        <h3 className="text-sm font-bold text-gray-700 flex items-center gap-2">
          <Activity className="w-4 h-4" /> אירועים אחרונים
        </h3>
        <button onClick={() => navigate("/activity-log")}
          className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center gap-0.5 min-h-[44px] px-2">
          הכל <ChevronLeft className="w-3 h-3" />
        </button>
      </div>
      <div className="divide-y divide-gray-100 max-h-[340px] overflow-y-auto">
        {events.length === 0 ? (
          <div className="p-8 text-center text-sm text-gray-400">אין אירועים</div>
        ) : events.map(ev => {
          const cfg = ACTION_CFG[ev.action] || { label: ev.action, dot: "bg-gray-400" };
          return (
            <div key={ev.id} className="px-3 sm:px-4 py-3 hover:bg-blue-50/40 transition-colors">
              <div className="flex items-start gap-2.5">
                <div className={`w-2.5 h-2.5 rounded-full ${cfg.dot} mt-1 flex-shrink-0`} />
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] sm:text-sm font-semibold text-gray-800 truncate">{cfg.label}</p>
                  <p className="text-[11px] sm:text-xs text-gray-500 truncate mt-0.5">{ev.description}</p>
                  <div className="flex items-center gap-2 mt-1">
                    {ev.user_name && <span className="text-[10px] text-gray-500 font-medium">{ev.user_name}</span>}
                    <span className="text-[10px] text-gray-400">{timeAgo(ev.created_at)}</span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
});

export default AdminDashboard;
