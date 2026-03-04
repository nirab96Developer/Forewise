
import React, { useState, useEffect } from "react";
import {
  BarChart3,
  FileText,
  Download,
  Loader2,
  AlertCircle,
  DollarSign,
  Clock,
  Users,
  Briefcase,
  Wrench,
  Filter,
} from "lucide-react";
import api from "../../services/api";

interface PricingReportItem {
  id: number;
  name: string;
  total_hours: number;
  total_cost: number;
  total_cost_with_vat: number;
  worklog_count: number;
  unverified_count: number;
}

interface PricingReportResponse {
  items: PricingReportItem[];
  summary: {
    total_hours: number;
    total_cost: number;
    total_cost_with_vat: number;
    average_hourly_rate: number;
    total_unverified_worklogs?: number;
    [key: string]: number | undefined;
  };
}

type ReportType = "by-project" | "by-supplier" | "by-equipment-type";

const PricingReports: React.FC = () => {
  const [reportType, setReportType] = useState<ReportType>("by-project");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<PricingReportResponse | null>(null);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    fetchReport();
  }, [reportType]);

  const fetchReport = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: Record<string, string> = {};
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      if (statusFilter !== "all") params.status = statusFilter;

      const response = await api.get(`/pricing/reports/${reportType}`, { params });
      setData(response.data);
    } catch (err: any) {
      console.error("Error fetching pricing report:", err);
      setError("שגיאה בטעינת דוח התמחור");
    } finally {
      setLoading(false);
    }
  };

  const handleFilter = () => {
    fetchReport();
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("he-IL", {
      style: "currency",
      currency: "ILS",
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat("he-IL", { maximumFractionDigits: 1 }).format(value);
  };

  const exportCSV = () => {
    if (!data || data.items.length === 0) return;

    const reportLabel =
      reportType === "by-project" ? "פרויקט" : reportType === "by-supplier" ? "ספק" : "סוג כלי";

    const headers = [reportLabel, "מספר דיווחים", "סה\"כ שעות", "עלות לפני מע\"מ", "עלות כולל מע\"מ"];
    const rows = data.items.map((item) => [
      item.name,
      item.worklog_count,
      item.total_hours.toFixed(1),
      item.total_cost.toFixed(2),
      item.total_cost_with_vat.toFixed(2),
    ]);

    // Add summary row
    rows.push([
      "סה\"כ",
      data.items.reduce((s, i) => s + i.worklog_count, 0),
      data.summary.total_hours.toFixed(1),
      data.summary.total_cost.toFixed(2),
      data.summary.total_cost_with_vat.toFixed(2),
    ]);

    const BOM = "\uFEFF";
    const csvContent = BOM + [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `pricing-report-${reportType}-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const reportTabs = [
    { key: "by-project" as ReportType, label: "לפי פרויקט", icon: Briefcase },
    { key: "by-supplier" as ReportType, label: "לפי ספק", icon: Users },
    { key: "by-equipment-type" as ReportType, label: "לפי סוג כלי", icon: Wrench },
  ];

  return (
    <div className="min-h-screen bg-gray-50 pt-6 pb-8 px-4 " dir="rtl">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">דוחות תמחור</h1>
          <p className="text-gray-500 mt-1">סיכום עלויות דיווחי שעות לפי פרויקט, ספק וסוג כלי</p>
        </div>

        {/* Report Type Tabs */}
        <div className="flex gap-2 mb-6">
          {reportTabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setReportType(tab.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                reportType === tab.key
                  ? "bg-green-600 text-white shadow-sm"
                  : "bg-white text-gray-600 hover:bg-gray-100 shadow-sm"
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
          <div className="flex flex-wrap items-end gap-4">
            <div>
              <label className="block text-xs text-gray-500 mb-1.5">מתאריך</label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1.5">עד תאריך</label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1.5">סטטוס דיווח</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="pr-3 pl-10 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:border-transparent min-w-[130px]"
              >
                <option value="all">הכל</option>
                <option value="approved">אושר</option>
                <option value="submitted">הוגש</option>
                <option value="pending">ממתין</option>
              </select>
            </div>
            <button
              onClick={handleFilter}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
            >
              <Filter className="w-4 h-4" />
              סנן
            </button>
            {data && data.items.length > 0 && (
              <button
                onClick={exportCSV}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm mr-auto"
              >
                <Download className="w-4 h-4" />
                ייצוא CSV
              </button>
            )}
          </div>
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-16">
            <div className="flex items-center gap-2 bg-white p-6 rounded-lg shadow-sm">
              <Loader2 className="w-5 h-5 animate-spin text-green-600" />
              <span className="text-gray-700">טוען דוח...</span>
            </div>
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-8 text-center">
            <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-red-900 mb-2">שגיאה</h3>
            <p className="text-red-600 mb-4">{error}</p>
            <button
              onClick={fetchReport}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              נסה שוב
            </button>
          </div>
        )}

        {/* Data */}
        {!loading && !error && data && (
          <>
            {/* Unverified rates banner */}
            {(data.summary.total_unverified_worklogs ?? 0) > 0 && (
              <div className="mb-4 flex items-center gap-2 rounded-lg border border-orange-200 bg-orange-50 px-4 py-3 text-sm text-orange-800">
                ⚠️ {data.summary.total_unverified_worklogs} דיווחים ללא תעריף מאומת —
                הסכומים המוצגים הם הערכה בלבד
              </div>
            )}

            {/* Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-white rounded-xl shadow-sm p-4">
                <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
                  <FileText className="w-4 h-4" />
                  סה"כ דיווחים
                </div>
                <div className="text-2xl font-bold text-gray-900">
                  {data.items.reduce((s, i) => s + i.worklog_count, 0)}
                </div>
              </div>
              <div className="bg-white rounded-xl shadow-sm p-4">
                <div className="flex items-center gap-2 text-blue-600 text-sm mb-1">
                  <Clock className="w-4 h-4" />
                  סה"כ שעות
                </div>
                <div className="text-2xl font-bold text-blue-700">
                  {formatNumber(data.summary.total_hours)}
                </div>
              </div>
              <div className="bg-white rounded-xl shadow-sm p-4">
                <div className="flex items-center gap-2 text-green-600 text-sm mb-1">
                  <DollarSign className="w-4 h-4" />
                  עלות לפני מע"מ
                </div>
                <div className="text-xl font-bold text-green-700">
                  {formatCurrency(data.summary.total_cost)}
                </div>
              </div>
              <div className="bg-white rounded-xl shadow-sm p-4">
                <div className="flex items-center gap-2 text-purple-600 text-sm mb-1">
                  <DollarSign className="w-4 h-4" />
                  כולל מע"מ
                </div>
                <div className="text-xl font-bold text-purple-700">
                  {formatCurrency(data.summary.total_cost_with_vat)}
                </div>
                {data.summary.average_hourly_rate > 0 && (
                  <div className="text-xs text-gray-400 mt-1">
                    ממוצע: {formatCurrency(data.summary.average_hourly_rate)}/שעה
                  </div>
                )}
              </div>
            </div>

            {/* Table */}
            {data.items.length > 0 ? (
              <div className="bg-white rounded-xl shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        <th className="text-right px-4 py-3 font-medium text-gray-600">
                          {reportType === "by-project"
                            ? "פרויקט"
                            : reportType === "by-supplier"
                            ? "ספק"
                            : "סוג כלי"}
                        </th>
                        <th className="text-right px-4 py-3 font-medium text-gray-600">דיווחים</th>
                        <th className="text-right px-4 py-3 font-medium text-gray-600">שעות</th>
                        <th className="text-right px-4 py-3 font-medium text-gray-600">עלות לפני מע"מ</th>
                        <th className="text-right px-4 py-3 font-medium text-gray-600">כולל מע"מ</th>
                        <th className="text-right px-4 py-3 font-medium text-gray-600">ממוצע/שעה</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {data.items.map((item) => (
                        <tr
                          key={item.id}
                          className={`hover:bg-gray-50 transition-colors ${item.unverified_count > 0 ? 'bg-orange-50/40' : ''}`}
                        >
                          <td className="px-4 py-3 font-medium text-gray-900">
                            <span>{item.name}</span>
                            {item.unverified_count > 0 && (
                              <span className="mr-2 inline-flex items-center gap-1 rounded-full bg-orange-100 text-orange-700 text-xs font-semibold px-2 py-0.5">
                                ⚠️ {item.unverified_count} ללא אימות תעריף
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-gray-600">{item.worklog_count}</td>
                          <td className="px-4 py-3 text-gray-600">{formatNumber(item.total_hours)}</td>
                          <td className="px-4 py-3 text-gray-900 font-medium">
                            {formatCurrency(item.total_cost)}
                          </td>
                          <td className="px-4 py-3 text-gray-900 font-medium">
                            {formatCurrency(item.total_cost_with_vat)}
                          </td>
                          <td className="px-4 py-3 text-gray-600">
                            {item.total_hours > 0
                              ? formatCurrency(item.total_cost / item.total_hours)
                              : "-"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-gray-50 border-t-2 border-gray-200">
                      <tr className="font-bold">
                        <td className="px-4 py-3 text-gray-900">סה"כ</td>
                        <td className="px-4 py-3 text-gray-900">
                          {data.items.reduce((s, i) => s + i.worklog_count, 0)}
                        </td>
                        <td className="px-4 py-3 text-gray-900">
                          {formatNumber(data.summary.total_hours)}
                        </td>
                        <td className="px-4 py-3 text-green-700">
                          {formatCurrency(data.summary.total_cost)}
                        </td>
                        <td className="px-4 py-3 text-green-700">
                          {formatCurrency(data.summary.total_cost_with_vat)}
                        </td>
                        <td className="px-4 py-3 text-gray-600">
                          {data.summary.average_hourly_rate > 0
                            ? formatCurrency(data.summary.average_hourly_rate)
                            : "-"}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-xl shadow-sm p-12 text-center">
                <BarChart3 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">אין נתונים</h3>
                <p className="text-gray-500">
                  לא נמצאו דיווחים עם תמחור לפי המסננים שנבחרו
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default PricingReports;
