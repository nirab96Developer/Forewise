import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle, Truck, Users,
  Activity, ChevronLeft,
  FolderOpen, UserPlus,
  ShieldAlert, Settings, Wrench, Shield, RefreshCw
} from "lucide-react";
import api from "../../services/api";
import UnifiedLoader from "../../components/common/UnifiedLoader";
import { getActivityLabel } from "../../strings";

interface AdminData {
  kpis: {
    open_work_orders: number; stuck_orders: number; pending_worklogs: number;
    pending_invoices: number; budget_overrun: number;
    total_users: number; total_suppliers: number; total_projects: number;
  };
  alerts: { type: string; message: string; link: string }[];
  recent_events: {
    id: number; action: string; description: string;
    entity_type: string; entity_id: number; user_id: number;
    created_at: string; metadata: string | null; user_name: string | null;
  }[];
}

const timeAgo = (d: string) => {
  if (!d) return "";
  const mins = Math.floor((Date.now() - new Date(d).getTime()) / 60000);
  if (mins < 1) return "עכשיו";
  if (mins < 60) return `לפני ${mins} דק׳`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `לפני ${hrs} שע׳`;
  return `לפני ${Math.floor(hrs / 24)} ימים`;
};

// The dot colour is a UI choice and stays here; the label always comes from
// the central activity dictionary so a new backend action never leaks raw.
const ACTION_DOT: Record<string, string> = {
  'work_order.created':   'bg-green-500',
  'work_order.approved':  'bg-green-600',
  'work_order.deleted':   'bg-red-500',
  'work_order.cancelled': 'bg-red-400',
  'work_order.updated':   'bg-blue-400',
  'worklog.created':      'bg-emerald-400',
  'worklog.approved':     'bg-emerald-500',
  'worklog.rejected':     'bg-red-400',
  'invoice.created':      'bg-orange-500',
  'invoice.paid':         'bg-purple-500',
  'budget.frozen':        'bg-amber-500',
  'budget.released':      'bg-emerald-400',
  'user.login':           'bg-gray-400',
  'user.logout':          'bg-gray-400',
};
const actionDot = (action: string) => {
  if (!action) return 'bg-gray-400';
  // Try direct, then alias (legacy SCREAMING_SNAKE / underscore variants)
  const lower = action.toLowerCase();
  return ACTION_DOT[action] || ACTION_DOT[lower] || 'bg-gray-400';
};

const AdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<AdminData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/dashboard/admin-overview")
      .then(r => setData(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <UnifiedLoader size="full" />;
  if (!data) return <div className="p-8 text-center text-gray-500">שגיאה בטעינת נתונים</div>;

  const k = data.kpis;
  const alertCount = (k.stuck_orders || 0) + (k.budget_overrun || 0) + (k.pending_worklogs || 0);

  return (
    <div className="min-h-full bg-gray-50" dir="rtl">
      <div className="p-4 sm:p-6 space-y-4 max-w-5xl mx-auto">

        {/* Header */}
        <div className="bg-gradient-to-l from-green-700 to-green-800 rounded-2xl p-5 sm:p-6 text-white shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-200 text-sm mb-1">{new Date().getHours() < 12 ? 'בוקר טוב' : new Date().getHours() < 17 ? 'צהריים טובים' : 'ערב טוב'}</p>
              <h1 className="text-xl sm:text-2xl font-extrabold flex items-center gap-2.5">
                <Shield className="w-6 h-6 text-green-300" />
                ניהול מערכת
              </h1>
              <p className="text-green-200 text-sm mt-1">
                {alertCount > 0 ? `${alertCount} פריטים דורשים תשומת לב` : 'הכל תקין — המערכת פועלת כסדרה'}
              </p>
            </div>
            <button onClick={() => window.location.reload()}
              className="flex items-center gap-1.5 px-4 py-2.5 text-xs font-bold bg-white/15 hover:bg-white/25 text-white rounded-xl backdrop-blur-sm transition-colors">
              <RefreshCw className="w-3.5 h-3.5" /> רענן
            </button>
          </div>
        </div>

        {/* ── KPI Row: 4 cards ── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <div onClick={() => navigate("/settings/admin/users")}
            className="bg-white rounded-xl border border-gray-200 p-4 cursor-pointer hover:shadow-md transition-all">
            <Users className="w-5 h-5 text-blue-600 mb-2" />
            <p className="text-2xl font-bold text-gray-900">{k.total_users}</p>
            <p className="text-xs text-gray-500">משתמשים</p>
          </div>
          <div onClick={() => navigate("/settings/suppliers")}
            className="bg-white rounded-xl border border-gray-200 p-4 cursor-pointer hover:shadow-md transition-all">
            <Truck className="w-5 h-5 text-green-600 mb-2" />
            <p className="text-2xl font-bold text-gray-900">{k.total_suppliers}</p>
            <p className="text-xs text-gray-500">ספקים</p>
          </div>
          <div onClick={() => navigate("/projects")}
            className="bg-white rounded-xl border border-gray-200 p-4 cursor-pointer hover:shadow-md transition-all">
            <FolderOpen className="w-5 h-5 text-purple-600 mb-2" />
            <p className="text-2xl font-bold text-gray-900">{k.total_projects}</p>
            <p className="text-xs text-gray-500">פרויקטים</p>
          </div>
          <div className={`rounded-xl border p-4 ${alertCount > 0 ? 'bg-red-50 border-red-200' : 'bg-white border-gray-200'}`}>
            <AlertTriangle className={`w-5 h-5 mb-2 ${alertCount > 0 ? 'text-red-600' : 'text-gray-400'}`} />
            <p className="text-2xl font-bold text-gray-900">{alertCount}</p>
            <p className="text-xs text-gray-500">התראות</p>
          </div>
        </div>

        {/* ── Alerts ── */}
        {(data.alerts?.length || 0) > 0 && (
          <div className="space-y-2">
            {data.alerts.map((a, i) => {
              const isErr = a.type === "error";
              return (
                <div key={i} className={`rounded-xl border px-4 py-3 flex items-center justify-between ${isErr ? 'border-red-200 bg-red-50' : 'border-amber-200 bg-amber-50'}`}>
                  <div className="flex items-center gap-3">
                    {isErr ? <ShieldAlert className="w-5 h-5 text-red-600" /> : <AlertTriangle className="w-5 h-5 text-amber-600" />}
                    <span className="text-sm font-medium text-gray-800">{a.message}</span>
                  </div>
                  <button onClick={() => navigate(a.link)} className="text-xs font-bold text-blue-600 min-h-[36px]">צפה</button>
                </div>
              );
            })}
          </div>
        )}

        {/* ── Main: Activity Feed + Quick Actions ── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

          {/* Activity Feed — main focus */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden lg:col-span-2">
            <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 className="text-sm font-bold text-gray-700 flex items-center gap-2">
                <Activity className="w-4 h-4" /> פעילות מערכת אחרונה
              </h3>
              <button onClick={() => navigate("/activity-log")}
                className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center gap-0.5 min-h-[36px]">
                הכל <ChevronLeft className="w-3 h-3" />
              </button>
            </div>
            <div className="divide-y divide-gray-50 max-h-[400px] overflow-y-auto">
              {(data.recent_events || []).length === 0 ? (
                <div className="p-10 text-center text-sm text-gray-400">אין פעולות אחרונות</div>
              ) : data.recent_events.map(ev => {
                const label = getActivityLabel(ev.action);
                const dot = actionDot(ev.action);
                return (
                  <div key={ev.id} className="px-4 py-3 hover:bg-gray-50 transition-colors">
                    <div className="flex items-start gap-3">
                      <div className={`w-2 h-2 rounded-full ${dot} mt-2 flex-shrink-0`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-800">{label}</p>
                        <p className="text-xs text-gray-500 truncate mt-0.5">{ev.description}</p>
                        <div className="flex items-center gap-2 mt-1">
                          {ev.user_name && <span className="text-[10px] text-gray-500">{ev.user_name}</span>}
                          <span className="text-[10px] text-gray-400">{timeAgo(ev.created_at)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-3 self-start">
            <h3 className="text-sm font-bold text-gray-700">פעולות מהירות</h3>
            <div className="space-y-2">
              <button onClick={() => navigate("/settings/admin/users/new")}
                className="w-full flex items-center gap-3 px-3 min-h-[44px] text-sm font-medium rounded-lg bg-gray-50 text-gray-700 hover:bg-gray-100 transition-colors">
                <UserPlus className="w-4 h-4 text-blue-600" /> יצירת משתמש
              </button>
              <button onClick={() => navigate("/settings/suppliers?action=new")}
                className="w-full flex items-center gap-3 px-3 min-h-[44px] text-sm font-medium rounded-lg bg-gray-50 text-gray-700 hover:bg-gray-100 transition-colors">
                <Truck className="w-4 h-4 text-green-600" /> יצירת ספק
              </button>
              <button onClick={() => navigate("/settings")}
                className="w-full flex items-center gap-3 px-3 min-h-[44px] text-sm font-medium rounded-lg bg-gray-50 text-gray-700 hover:bg-gray-100 transition-colors">
                <Settings className="w-4 h-4 text-gray-600" /> הגדרות מערכת
              </button>
              <button onClick={() => navigate("/support")}
                className="w-full flex items-center gap-3 px-3 min-h-[44px] text-sm font-medium rounded-lg bg-gray-50 text-gray-700 hover:bg-gray-100 transition-colors">
                <Wrench className="w-4 h-4 text-gray-600" /> קריאות תמיכה
              </button>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
