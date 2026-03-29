import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  MapPin, AlertTriangle, BarChart3, Info, ShieldAlert, RefreshCw
} from "lucide-react";
import api from "../../services/api";
import UnifiedLoader from "../../components/common/UnifiedLoader";

interface AreaRow {
  id: number; name: string; projects: number;
  budget_total: number; budget_committed: number; budget_spent: number; budget_remaining: number;
  utilization_pct: number; open_work_orders: number; pending_worklogs: number; manager_name: string;
}
interface RegionData {
  region_name: string;
  kpis: {
    total_areas: number; total_projects: number;
    total_budget: number; total_spent: number; total_committed: number; total_remaining: number;
    utilization_pct: number; open_work_orders: number; pending_worklogs: number; overrun_areas: number;
  };
  areas: AreaRow[];
  alerts: { type: string; message: string; link: string }[];
  wo_trend: { date: string; count: number }[];
}

const fmtK = (n: number) => n >= 1e6 ? `${(n/1e6).toFixed(1)}M` : n >= 1e3 ? `${(n/1e3).toFixed(0)}K` : `${n}`;
const fmtCurrency = (n: number) => `${fmtK(n)}`;

const RegionManagerDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<RegionData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/dashboard/region-overview")
      .then(r => setData(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <UnifiedLoader size="full" />;
  if (!data) return <div className="p-8 text-center text-gray-500">שגיאה בטעינת נתונים</div>;

  const k = data.kpis;
  const maxChart = Math.max(...data.wo_trend.map(d => d.count), 1);

  return (
    <div className="min-h-full bg-gray-50" dir="rtl">
      <div className="p-3 sm:p-5 lg:p-6 space-y-4 sm:space-y-5 max-w-screen-2xl mx-auto">

        {/* Header */}
        <div className="bg-gradient-to-l from-green-700 to-green-800 rounded-2xl p-5 sm:p-6 text-white shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-200 text-sm mb-1">{new Date().getHours() < 12 ? 'בוקר טוב' : new Date().getHours() < 17 ? 'צהריים טובים' : 'ערב טוב'}</p>
              <h1 className="text-xl sm:text-2xl font-extrabold flex items-center gap-2.5">
                <MapPin className="w-6 h-6 text-green-300" />
                מרחב {data.region_name}
              </h1>
              <p className="text-green-200 text-sm mt-1">{k.total_areas} אזורים · {k.total_projects} פרויקטים</p>
            </div>
            <button onClick={() => window.location.reload()}
              className="flex items-center gap-1.5 px-4 py-2.5 text-xs font-bold bg-white/15 hover:bg-white/25 text-white rounded-xl backdrop-blur-sm transition-colors">
              <RefreshCw className="w-3.5 h-3.5" /> רענן
            </button>
          </div>
        </div>

        {/* KPIs */}
        {(() => {
          const areasAtRisk = data.areas.filter(a =>
            a.utilization_pct > 85 || a.pending_worklogs > 5 || a.open_work_orders > 3
          ).length;
          return (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              <KPI label="תקציב כולל" value={fmtCurrency(k.total_budget)} sub={`${k.utilization_pct}% ניצול`} color="blue" />
              <KPI label="הוצא" value={fmtCurrency(k.total_spent)} color="red" />
              <KPI label="מוקפא" value={fmtCurrency(k.total_committed)} color="amber" />
              <KPI label="הזמנות פתוחות" value={String(k.open_work_orders)} color={k.open_work_orders > 0 ? "blue" : "gray"} />
              <KPI label="חריגות תקציב" value={String(k.overrun_areas)} color={k.overrun_areas > 0 ? "red" : "green"} pulse={k.overrun_areas > 0} />
              <KPI label="אזורים בסיכון" value={String(areasAtRisk)} color={areasAtRisk > 0 ? "red" : "green"} sub="תקציב / עומס / עיכוב" pulse={areasAtRisk > 0} />
            </div>
          );
        })()}

        {/* Alerts */}
        {data.alerts.length > 0 && (
          <div className="space-y-2">
            {data.alerts.map((a, i) => {
              const isErr = a.type === "error";
              const Icon = isErr ? ShieldAlert : a.type === "warning" ? AlertTriangle : Info;
              return (
                <div key={i} className={`rounded-xl border px-3 sm:px-4 py-3.5 flex flex-col sm:flex-row sm:items-center gap-2.5 sm:gap-3 ${
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

        {/* Areas Table (main section) */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
            <h2 className="text-sm font-bold text-gray-700 flex items-center gap-2">
              <MapPin className="w-4 h-4" /> אזורים במרחב
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-gray-500 text-xs">
                  <th className="text-right px-4 py-3 font-semibold">אזור</th>
                  <th className="text-right px-3 py-3 font-semibold">מנהל</th>
                  <th className="text-center px-3 py-3 font-semibold">פרויקטים</th>
                  <th className="text-right px-3 py-3 font-semibold">תקציב</th>
                  <th className="text-center px-3 py-3 font-semibold">ניצול</th>
                  <th className="text-center px-3 py-3 font-semibold">הזמנות</th>
                  <th className="text-center px-3 py-3 font-semibold">דיווחים</th>
                  <th className="px-2 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.areas.map(a => {
                  const isRisk = a.utilization_pct > 85 || a.pending_worklogs > 5 || a.open_work_orders > 3;
                  return (
                  <tr key={a.id} onClick={() => navigate(`/areas/${a.id}`)}
                    className={`cursor-pointer transition-colors group ${isRisk ? "hover:bg-red-50/50" : "hover:bg-blue-50/40"}`}>
                    <td className="px-4 py-3.5 font-semibold text-gray-900">
                      <div className="flex items-center gap-2">
                        {isRisk && <span className="w-2 h-2 rounded-full bg-red-500 flex-shrink-0" />}
                        {a.name}
                      </div>
                    </td>
                    <td className="px-3 py-3.5 text-gray-600 text-xs">{a.manager_name || "—"}</td>
                    <td className="px-3 py-3.5 text-center">{a.projects}</td>
<td className="px-3 py-3.5 text-right font-medium">{a.budget_total.toLocaleString("he-IL", {maximumFractionDigits:0})}</td>
                    <td className="px-3 py-3.5 text-center">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                        a.utilization_pct > 90 ? "bg-red-100 text-red-700" :
                        a.utilization_pct > 60 ? "bg-amber-100 text-amber-700" :
                        "bg-green-100 text-green-700"}`}>
                        {a.utilization_pct}%
                      </span>
                    </td>
                    <td className="px-3 py-3.5 text-center">{a.open_work_orders > 0 ? <span className="font-bold text-blue-600">{a.open_work_orders}</span> : "—"}</td>
                    <td className="px-3 py-3.5 text-center">{a.pending_worklogs > 0 ? <span className="font-bold text-amber-600">{a.pending_worklogs}</span> : "—"}</td>
                    <td className="px-2 py-3.5 text-left">
                      <span className="text-xs text-blue-500 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
כניסה לאזור 
                      </span>
                    </td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Trend Chart */}
        {data.wo_trend.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm p-4 sm:p-5">
            <h3 className="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
              <BarChart3 className="w-4 h-4" /> הזמנות עבודה — 14 ימים אחרונים
            </h3>
            <div className="overflow-x-auto">
              <div className="flex items-end gap-2 sm:gap-3 min-w-[320px]" style={{ height: "160px" }}>
                {data.wo_trend.map(d => {
                  const h = Math.max(8, (d.count / maxChart) * 100);
                  const day = new Date(d.date).toLocaleDateString("he-IL", { day: "numeric", month: "numeric" });
                  return (
                    <div key={d.date} className="flex-1 flex flex-col items-center gap-1 min-w-[24px]">
                      <div className="w-full flex justify-center" style={{ height: "130px", alignItems: "flex-end" }}>
                        <div className="w-4 bg-blue-400 rounded-t transition-all" style={{ height: `${h}%` }} />
                      </div>
                      <span className="text-[10px] text-gray-400">{day}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

const KPI: React.FC<{ label: string; value: string; sub?: string; color: string; pulse?: boolean }> = ({ label, value, sub, color, pulse }) => {
  const bg: Record<string, string> = { blue: "bg-blue-50 border-r-blue-500", red: "bg-red-50 border-r-red-500", amber: "bg-amber-50 border-r-amber-500", green: "bg-white border-r-green-400", gray: "bg-white border-r-gray-200" };
  const fg: Record<string, string> = { blue: "text-blue-700", red: "text-red-700", amber: "text-amber-700", green: "text-green-600", gray: "text-gray-500" };
  return (
    <div className={`rounded-xl border border-gray-200 border-r-4 shadow-sm p-3 sm:p-4 min-h-[80px] ${bg[color] || bg.gray}`}>
      <p className="text-[11px] text-gray-500 mb-1">{label}</p>
      <div className="flex items-center gap-2">
        <p className={`text-2xl font-extrabold ${fg[color] || "text-gray-900"}`}>{value}</p>
        {pulse && <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />}
      </div>
      {sub && <p className="text-[10px] text-gray-400 mt-0.5">{sub}</p>}
    </div>
  );
};

export default RegionManagerDashboard;
