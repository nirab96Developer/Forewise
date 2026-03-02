
import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Briefcase,
  Clock,
  DollarSign,
  AlertCircle,
  ArrowUpRight,
  Loader2,
  TrendingUp,
  FileText,
  Wrench,
  Users,
  Calendar,
  Truck,
} from "lucide-react";
import dashboardService from "../../services/dashboardService";
import api from "../../services/api";

const AreaManagerDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<any>(null);
  const [projects, setProjects] = useState<any[]>([]);
  const [equipment, setEquipment] = useState<any[]>([]);
  const [monthlyCosts, setMonthlyCosts] = useState<any[]>([]);
  const [financial, setFinancial] = useState<any>(null);
  const [hours, setHours] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [summaryData, projectsData, equipmentData, costsData, financialData, hoursData, alertsData] =
        await Promise.all([
          dashboardService.getSummary(),
          dashboardService.getProjects(),
          dashboardService.getActiveEquipment(),
          api.get("/dashboard/monthly-costs").then((r) => r.data).catch(() => []),
          api.get("/dashboard/financial-summary").then((r) => r.data).catch(() => null),
          dashboardService.getHoursData("month").catch(() => null),
          dashboardService.getAlerts().catch(() => []),
        ]);
      setSummary(summaryData);
      setProjects(projectsData);
      setEquipment(equipmentData);
      setMonthlyCosts(costsData);
      setFinancial(financialData);
      setHours(hoursData);
      setAlerts(alertsData);
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

  const areaName = summary?.user?.area || "האזור";

  return (
    <div className="min-h-screen p-6" dir="rtl">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">לוח בקרה - מנהל אזור</h1>
          <p className="text-gray-600 mt-1">אזור: {areaName}</p>
        </div>

        {/* Alerts */}
        {alerts.length > 0 && (
          <div className="space-y-2 mb-6">
            {alerts.map((alert, i) => (
              <div
                key={i}
                className={`rounded-lg p-3 flex items-center gap-3 ${
                  alert.type === "error"
                    ? "bg-red-50 border border-red-200"
                    : "bg-orange-50 border border-orange-200"
                }`}
              >
                <AlertCircle
                  className={`w-4 h-4 ${alert.type === "error" ? "text-red-600" : "text-orange-600"}`}
                />
                <span
                  className={`text-sm font-medium ${
                    alert.type === "error" ? "text-red-800" : "text-orange-800"
                  }`}
                >
                  {alert.message || alert.title}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <div
            className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => navigate("/projects")}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">פרויקטים</span>
              <Briefcase className="w-5 h-5 text-green-600" />
            </div>
            <div className="text-2xl font-bold text-gray-900">{summary?.active_projects_count || 0}</div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">הזמנות פתוחות</span>
              <FileText className="w-5 h-5 text-orange-600" />
            </div>
            <div className="text-2xl font-bold text-gray-900">{summary?.pending_work_orders_count || 0}</div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">ממתינים לאישור</span>
              <Clock className="w-5 h-5 text-red-600" />
            </div>
            <div className="text-2xl font-bold text-gray-900">{summary?.pending_approvals_count || 0}</div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">ציוד פעיל</span>
              <Truck className="w-5 h-5 text-blue-600" />
            </div>
            <div className="text-2xl font-bold text-gray-900">{summary?.equipment_in_use_count || equipment.length}</div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">שעות החודש</span>
              <Clock className="w-5 h-5 text-purple-600" />
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {hours ? Math.round(hours.total_work_hours) : Math.round(summary?.hours_month_total || 0)}
            </div>
          </div>
        </div>

        {/* Budget vs Actual */}
        {financial?.budgets && (
          <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-green-600" />
              תקציב מול ביצוע
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-500">תקציב</div>
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
              <div>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-500">ניצול תקציב</span>
                  <span className="font-medium">{financial.budgets.utilization_pct}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full ${
                      financial.budgets.utilization_pct > 90
                        ? "bg-red-500"
                        : financial.budgets.utilization_pct > 70
                        ? "bg-orange-500"
                        : "bg-green-500"
                    }`}
                    style={{ width: `${Math.min(financial.budgets.utilization_pct, 100)}%` }}
                  />
                </div>
                {financial.budgets.overrun_count > 0 && (
                  <div className="mt-2 flex items-center gap-2 text-red-600 text-sm">
                    <AlertCircle className="w-4 h-4" />
                    <span>{financial.budgets.overrun_count} פרויקטים בחריגה תקציבית</span>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* Projects */}
          <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200">
            <div className="p-6 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">פרויקטים באזור</h2>
              <button
                onClick={() => navigate("/projects")}
                className="text-sm text-green-600 hover:text-green-700 flex items-center gap-1"
              >
                הצג הכל <ArrowUpRight className="w-4 h-4" />
              </button>
            </div>
            <div className="divide-y divide-gray-100">
              {projects.slice(0, 6).map((p) => (
                <div
                  key={p.id}
                  className="p-4 hover:bg-gray-50 cursor-pointer"
                  onClick={() => navigate(`/projects/${p.code}/workspace`)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-900">{p.name}</span>
                        <span className="text-sm text-gray-400">#{p.code}</span>
                      </div>
                      <div className="text-sm text-gray-500 mt-1 flex items-center gap-3">
                        {p.manager_name && (
                          <span className="flex items-center gap-1">
                            <Users className="w-3 h-3" />
                            {p.manager_name}
                          </span>
                        )}
                        {p.allocated_budget > 0 && (
                          <span className="flex items-center gap-1">
                            <DollarSign className="w-3 h-3" />
                            {formatCurrency(p.spent_budget || 0)} / {formatCurrency(p.allocated_budget)}
                          </span>
                        )}
                      </div>
                    </div>
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${
                        p.status === "active" ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {p.status === "active" ? "פעיל" : p.status}
                    </span>
                  </div>
                </div>
              ))}
              {projects.length === 0 && (
                <div className="p-8 text-center text-gray-400">אין פרויקטים באזור</div>
              )}
            </div>
          </div>

          {/* Monthly Costs */}
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
                      className="bg-green-500 h-2 rounded-full"
                      style={{ width: `${(m.cost / maxCost) * 100}%` }}
                    />
                  </div>
                  <div className="text-xs text-gray-400 mt-0.5">{m.count} דיווחים | {Math.round(m.hours)} שעות</div>
                </div>
              ))}
              {monthlyCosts.length === 0 && (
                <p className="text-gray-400 text-sm text-center py-4">אין נתונים</p>
              )}
            </div>
          </div>
        </div>

        {/* Equipment & Work Hours */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Active Equipment */}
          <div className="bg-white rounded-xl border border-gray-200">
            <div className="p-6 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Wrench className="w-5 h-5 text-blue-600" />
                ציוד פעיל באזור
              </h2>
              <button
                onClick={() => navigate("/equipment")}
                className="text-sm text-green-600 hover:text-green-700 flex items-center gap-1"
              >
                הצג הכל <ArrowUpRight className="w-4 h-4" />
              </button>
            </div>
            <div className="divide-y divide-gray-100">
              {equipment.slice(0, 5).map((e) => (
                <div key={e.id} className="p-4 hover:bg-gray-50 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                      <Truck className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <div className="font-medium text-gray-900">{e.name}</div>
                      {e.code && <div className="text-sm text-gray-500">{e.code}</div>}
                    </div>
                  </div>
                  <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium">
                    בשימוש
                  </span>
                </div>
              ))}
              {equipment.length === 0 && (
                <div className="p-8 text-center text-gray-400">אין ציוד פעיל</div>
              )}
            </div>
          </div>

          {/* Hours Summary */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Calendar className="w-5 h-5 text-purple-600" />
              דיווחי שעות - החודש
            </h2>
            {hours ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-green-50 rounded-lg p-4 text-center">
                    <div className="text-sm text-green-600">שעות עבודה</div>
                    <div className="text-2xl font-bold text-green-700">{Math.round(hours.total_work_hours)}</div>
                  </div>
                  <div className="bg-orange-50 rounded-lg p-4 text-center">
                    <div className="text-sm text-orange-600">שעות הפסקה</div>
                    <div className="text-2xl font-bold text-orange-700">{Math.round(hours.total_break_hours)}</div>
                  </div>
                </div>
                <div className="bg-blue-50 rounded-lg p-4 text-center">
                  <div className="text-sm text-blue-600">סה"כ שעות</div>
                  <div className="text-3xl font-bold text-blue-700">{Math.round(hours.total_hours)}</div>
                </div>
                <div className="text-center text-sm text-gray-500">
                  {hours.worklog_count} דיווחים החודש
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-400">אין נתונים</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AreaManagerDashboard;
