
import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Map,
  Briefcase,
  Clock,
  DollarSign,
  ArrowUpRight,
  Loader2,
  TrendingUp,
  Building2,
  FileText,
  CheckCircle,
} from "lucide-react";
import dashboardService from "../../services/dashboardService";
import api from "../../services/api";

const RegionManagerDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<any>(null);
  const [areas, setAreas] = useState<any[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [monthlyCosts, setMonthlyCosts] = useState<any[]>([]);
  const [financial, setFinancial] = useState<any>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [summaryData, projectsData, suppliersData, costsData, financialData, areasData] =
        await Promise.all([
          dashboardService.getSummary(),
          dashboardService.getProjects(),
          dashboardService.getActiveSuppliers(),
          api.get("/dashboard/monthly-costs").then((r) => r.data).catch(() => []),
          api.get("/dashboard/financial-summary").then((r) => r.data).catch(() => null),
          api.get("/dashboard/region-areas").then((r) => r.data).catch(() => []),
        ]);
      setSummary(summaryData);
      setProjects(projectsData);
      setSuppliers(suppliersData);
      setMonthlyCosts(costsData);
      setFinancial(financialData);
      setAreas(areasData);
    } catch (err) {
      console.error("Error loading dashboard:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const formatCurrency = (v: number) =>
    new Intl.NumberFormat("he-IL", { style: "currency", currency: "ILS", maximumFractionDigits: 0 }).format(v);

  const maxCost = Math.max(...monthlyCosts.map((m) => m.cost), 1);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex items-center gap-2 bg-white p-6 rounded-lg shadow-sm">
          <Loader2 className="w-5 h-5 animate-spin text-green-600" />
          <span>טוען לוח בקרה...</span>
        </div>
      </div>
    );
  }

  const regionName = summary?.user?.region || "המרחב";
  const totalOpenWO = areas.reduce((s, a) => s + a.open_work_orders, 0);
  const totalAreaProjects = areas.reduce((s, a) => s + a.active_projects, 0);

  return (
    <div className="min-h-screen p-6" dir="rtl">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">לוח בקרה - מנהל מרחב</h1>
          <p className="text-gray-600 mt-1">מרחב: {regionName}</p>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div
            className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => navigate("/projects")}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">פרויקטים פעילים</span>
              <div className="p-2 bg-green-100 rounded-lg">
                <Briefcase className="w-5 h-5 text-green-600" />
              </div>
            </div>
            <div className="text-3xl font-bold text-gray-900">
              {summary?.active_projects_count || totalAreaProjects}
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">אזורים במרחב</span>
              <div className="p-2 bg-blue-100 rounded-lg">
                <Map className="w-5 h-5 text-blue-600" />
              </div>
            </div>
            <div className="text-3xl font-bold text-gray-900">{areas.length}</div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">הזמנות פתוחות</span>
              <div className="p-2 bg-orange-100 rounded-lg">
                <FileText className="w-5 h-5 text-orange-600" />
              </div>
            </div>
            <div className="text-3xl font-bold text-gray-900">{totalOpenWO}</div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">שעות החודש</span>
              <div className="p-2 bg-purple-100 rounded-lg">
                <Clock className="w-5 h-5 text-purple-600" />
              </div>
            </div>
            <div className="text-3xl font-bold text-gray-900">
              {Math.round(summary?.hours_month_total || 0)}
            </div>
          </div>
        </div>

        {/* Budget Overview */}
        {financial?.budgets && (
          <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-green-600" />
              תקציב מרחב
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-500">תקציב כולל</div>
                <div className="text-xl font-bold text-gray-900">{formatCurrency(financial.budgets.total)}</div>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <div className="text-sm text-green-600">ביצוע</div>
                <div className="text-xl font-bold text-green-700">{formatCurrency(financial.budgets.spent)}</div>
              </div>
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="text-sm text-blue-600">התחייבויות</div>
                <div className="text-xl font-bold text-blue-700">{formatCurrency(financial.budgets.committed)}</div>
              </div>
              <div className="bg-orange-50 rounded-lg p-4">
                <div className="text-sm text-orange-600">יתרה</div>
                <div className="text-xl font-bold text-orange-700">{formatCurrency(financial.budgets.remaining)}</div>
              </div>
            </div>
            {financial.budgets.total > 0 && (
              <div className="mt-4">
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-500">ניצול תקציב</span>
                  <span className="font-medium">{financial.budgets.utilization_pct}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full ${
                      financial.budgets.utilization_pct > 90 ? "bg-red-500" : financial.budgets.utilization_pct > 70 ? "bg-orange-500" : "bg-green-500"
                    }`}
                    style={{ width: `${Math.min(financial.budgets.utilization_pct, 100)}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* Areas Breakdown */}
          <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">אזורים במרחב</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="text-right px-4 py-3 font-medium text-gray-600">אזור</th>
                    <th className="text-right px-4 py-3 font-medium text-gray-600">מנהל</th>
                    <th className="text-center px-4 py-3 font-medium text-gray-600">פרויקטים</th>
                    <th className="text-center px-4 py-3 font-medium text-gray-600">הזמנות</th>
                    <th className="text-center px-4 py-3 font-medium text-gray-600">שעות החודש</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {areas.map((area) => (
                    <tr key={area.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium text-gray-900">{area.name}</td>
                      <td className="px-4 py-3 text-gray-600">{area.manager_name || "-"}</td>
                      <td className="px-4 py-3 text-center">
                        <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium">
                          {area.active_projects}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          area.open_work_orders > 0 ? "bg-orange-100 text-orange-800" : "bg-gray-100 text-gray-600"
                        }`}>
                          {area.open_work_orders}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center text-gray-700">{Math.round(area.hours_this_month)}</td>
                    </tr>
                  ))}
                  {areas.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                        לא נמצאו אזורים
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Monthly Costs Chart */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-600" />
              עלויות חודשי
            </h2>
            <div className="space-y-3">
              {monthlyCosts.map((m) => (
                <div key={m.month}>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-gray-600">{m.month}</span>
                    <span className="font-medium text-gray-900">{formatCurrency(m.cost)}</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2">
                    <div
                      className="bg-green-500 h-2 rounded-full transition-all"
                      style={{ width: `${(m.cost / maxCost) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
              {monthlyCosts.length === 0 && (
                <p className="text-gray-400 text-sm text-center py-4">אין נתונים</p>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Projects */}
          <div className="bg-white rounded-xl border border-gray-200">
            <div className="p-6 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">פרויקטים אחרונים</h2>
              <button
                onClick={() => navigate("/projects")}
                className="text-sm text-green-600 hover:text-green-700 flex items-center gap-1"
              >
                הצג הכל <ArrowUpRight className="w-4 h-4" />
              </button>
            </div>
            <div className="divide-y divide-gray-100">
              {projects.slice(0, 5).map((p) => (
                <div
                  key={p.id}
                  className="p-4 hover:bg-gray-50 cursor-pointer"
                  onClick={() => navigate(`/projects/${p.code}/workspace`)}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-gray-900">{p.name}</div>
                      <div className="text-sm text-gray-500 mt-1">
                        {p.area_name && <span>{p.area_name}</span>}
                        {p.manager_name && <span className="mr-3">{p.manager_name}</span>}
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      p.status === "active" ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-600"
                    }`}>
                      {p.status === "active" ? "פעיל" : p.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Active Suppliers */}
          <div className="bg-white rounded-xl border border-gray-200">
            <div className="p-6 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">ספקים פעילים במרחב</h2>
              <button
                onClick={() => navigate("/suppliers")}
                className="text-sm text-green-600 hover:text-green-700 flex items-center gap-1"
              >
                הצג הכל <ArrowUpRight className="w-4 h-4" />
              </button>
            </div>
            <div className="divide-y divide-gray-100">
              {suppliers.slice(0, 6).map((s) => (
                <div key={s.id} className="p-4 hover:bg-gray-50 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                      <Building2 className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <div className="font-medium text-gray-900">{s.name}</div>
                      {s.contact_name && <div className="text-sm text-gray-500">{s.contact_name}</div>}
                    </div>
                  </div>
                  <CheckCircle className="w-5 h-5 text-green-500" />
                </div>
              ))}
              {suppliers.length === 0 && (
                <div className="p-8 text-center text-gray-400">אין ספקים פעילים</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegionManagerDashboard;
