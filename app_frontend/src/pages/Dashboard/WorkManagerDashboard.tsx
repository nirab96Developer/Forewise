import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Clock, Briefcase, FileText,
  ChevronLeft, Info, Wrench,
  ClipboardList, RefreshCw, FolderOpen, TreeDeciduous
} from "lucide-react";
import api from "../../services/api";
import UnifiedLoader from "../../components/common/UnifiedLoader";

const WorkManagerDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);
  const [projects, setProjects] = useState<any[]>([]);

  useEffect(() => {
    loadAll();
  }, []);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [dRes, pRes] = await Promise.all([
        api.get("/dashboard/work-manager-overview").catch(() => ({ data: {} })),
        api.get("/projects", { params: { page_size: 50, my_projects: true } }).catch(() => ({ data: { items: [] } })),
      ]);
      setData(dRes.data || {});
      setProjects(pRes.data?.items || pRes.data || []);
    } catch {}
    setLoading(false);
  };

  if (loading) return <UnifiedLoader size="full" />;

  const hours = Number(data.hours_this_week ?? 0);
  const openWO = Number(data.active_work_orders ?? 0);
  const pendingWL = Number(data.pending_worklogs ?? 0);
  const eqInUse = Number(data.equipment_in_use ?? 0);
  const greeting = new Date().getHours() < 12 ? 'בוקר טוב' : new Date().getHours() < 17 ? 'צהריים טובים' : 'ערב טוב';

  const activeProjects = projects.filter(p => p.is_active !== false);

  return (
    <div className="min-h-full bg-gray-50" dir="rtl">
      <div className="p-3 sm:p-5 space-y-4 max-w-screen-lg mx-auto">

        {/* Header */}
        <div className="bg-gradient-to-l from-green-700 to-green-800 rounded-2xl p-5 sm:p-6 text-white shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-200 text-sm mb-1">{greeting}</p>
              <h1 className="text-xl sm:text-2xl font-extrabold flex items-center gap-2.5">
                <Wrench className="w-6 h-6 text-green-300" />
                ניהול עבודה
              </h1>
              <p className="text-green-200 text-sm mt-1">
                {activeProjects.length} פרויקטים
                {openWO > 0 ? ` · ${openWO} הזמנות פתוחות` : ''}
                {pendingWL > 0 ? ` · ${pendingWL} דיווחים ממתינים` : ''}
              </p>
            </div>
            <button onClick={loadAll}
              className="flex items-center gap-1.5 px-4 py-2.5 text-xs font-bold bg-white/15 hover:bg-white/25 text-white rounded-xl backdrop-blur-sm transition-colors">
              <RefreshCw className="w-3.5 h-3.5" /> רענן
            </button>
          </div>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <MiniKPI icon={<Clock className="w-5 h-5 text-blue-500" />} label="שעות השבוע" value={hours.toFixed(1)} />
          <MiniKPI icon={<Briefcase className="w-5 h-5 text-green-500" />} label="הזמנות פתוחות" value={String(openWO)} />
          <MiniKPI icon={<Wrench className="w-5 h-5 text-purple-500" />} label="כלים בשטח" value={String(eqInUse)} />
          <MiniKPI icon={<FileText className="w-5 h-5 text-amber-500" />} label="דיווחים ממתינים" value={String(pendingWL)} alert={pendingWL > 0} />
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-2 gap-3">
          <button onClick={() => navigate("/projects")}
            className="flex items-center gap-3 p-4 bg-green-600 hover:bg-green-700 text-white rounded-xl shadow-sm transition-colors">
            <FolderOpen className="w-6 h-6" />
            <div className="text-right">
              <p className="text-sm font-bold">הפרויקטים שלי</p>
              <p className="text-xs text-green-200">הזמנות · סריקה · דיווח</p>
            </div>
          </button>
          <button onClick={() => navigate("/work-logs")}
            className="flex items-center gap-3 p-4 bg-white hover:bg-gray-50 border border-gray-200 rounded-xl shadow-sm transition-colors">
            <ClipboardList className="w-6 h-6 text-blue-600" />
            <div className="text-right">
              <p className="text-sm font-bold text-gray-900">הדיווחים שלי</p>
              <p className="text-xs text-gray-500">צפייה בכל הדיווחים</p>
            </div>
          </button>
        </div>

        {/* My Projects */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-gray-700 flex items-center gap-2">
              <TreeDeciduous className="w-4 h-4 text-green-600" /> הפרויקטים שלי
            </h3>
            <button onClick={() => navigate("/projects")}
              className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center gap-0.5">
              הכל <ChevronLeft className="w-3 h-3" />
            </button>
          </div>

          {activeProjects.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border p-8 text-center">
              <FolderOpen className="w-10 h-10 text-gray-300 mx-auto mb-3" />
              <p className="text-sm text-gray-500 mb-1">אין פרויקטים משויכים</p>
              <p className="text-xs text-gray-400">פנה למנהל האזור לשיוך פרויקטים</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {activeProjects.slice(0, 6).map(p => {
                const statusCfg: Record<string, { label: string; cls: string }> = {
                  active: { label: "פעיל", cls: "bg-green-100 text-green-700" },
                  planning: { label: "בתכנון", cls: "bg-blue-100 text-blue-700" },
                  completed: { label: "הושלם", cls: "bg-gray-100 text-gray-600" },
                };
                const st = statusCfg[(p.status || 'active').toLowerCase()] || statusCfg.active;
                return (
                  <button key={p.id} onClick={() => navigate(`/projects/${p.code}/workspace`)}
                    className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 text-right hover:shadow-md hover:border-green-300 transition-all group">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-bold text-gray-900 truncate group-hover:text-green-700 transition-colors">{p.name}</p>
                        <p className="text-xs text-gray-400 font-mono">{p.code}</p>
                      </div>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold flex-shrink-0 ${st.cls}`}>{st.label}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>{p.region_name || p.area_name || ''}</span>
                      <span className="text-green-600 font-medium flex items-center gap-1 group-hover:underline">
                        כניסה <ChevronLeft className="w-3 h-3" />
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Area Manager Info */}
        {data.area_manager && (
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-center gap-3">
            <Info className="w-5 h-5 text-blue-600 flex-shrink-0" />
            <div className="text-sm">
              <span className="text-blue-800 font-medium">מנהל אזור: </span>
              <span className="text-blue-700">{data.area_manager.name}</span>
              {data.area_manager.phone && <span className="text-blue-500 mr-2">· {data.area_manager.phone}</span>}
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

const MiniKPI: React.FC<{ icon: React.ReactNode; label: string; value: string; alert?: boolean }> = ({ icon, label, value, alert }) => (
  <div className={`bg-white rounded-xl shadow-sm border p-3 min-h-[72px] flex flex-col justify-between ${
    alert ? "border-amber-300 bg-amber-50" : "border-gray-200"}`}>
    <div className="flex items-center justify-between">
      {icon}
      {alert && <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />}
    </div>
    <div>
      <p className="text-2xl font-extrabold text-gray-900">{value}</p>
      <p className="text-[10px] text-gray-500">{label}</p>
    </div>
  </div>
);

export default WorkManagerDashboard;
