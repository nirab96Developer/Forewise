
import React, { useState, useEffect } from "react";
import {
  BarChart3,
  FileText,
  Download,
  AlertCircle,
  DollarSign,
  Clock,
  Users,
  Briefcase,
  Wrench,
  Filter,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import api from "../../services/api";

interface WorklogDetail {
  worklog_id: number;
  report_date: string | null;
  work_hours: number;
  cost_before_vat: number | null;
  cost_with_vat: number | null;
  hourly_rate_snapshot: number | null;
  supplier_name: string | null;
  equipment_license_plate: string | null;
  equipment_type: string | null;
  status: string;
  is_verified: boolean;
}

interface PricingReportItem {
  id: number;
  name: string;
  total_hours: number;
  total_cost: number;
  total_cost_with_vat: number;
  worklog_count: number;
  unverified_count: number;
  worklogs_detail?: WorklogDetail[];
}

interface PricingReportResponse {
  items: PricingReportItem[];
  summary: {
    total_hours: number;
    total_cost: number;
    total_cost_with_vat: number;
    average_hourly_rate: number;
    total_unverified_worklogs?: number;
    total_projects?: number;
    total_suppliers?: number;
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
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());

  useEffect(() => {
    fetchReport();
  }, [reportType]);

  const fetchReport = async () => {
    try {
      setLoading(true);
      setError(null);
      setExpandedRows(new Set());

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

  const toggleRow = (id: number) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat("he-IL", {
      style: "currency",
      currency: "ILS",
      maximumFractionDigits: 0,
    }).format(value);

  const formatNumber = (value: number) =>
    new Intl.NumberFormat("he-IL", { maximumFractionDigits: 1 }).format(value);

  const fmtNull = (v: number | null | undefined) =>
    v != null ? formatCurrency(v) : "—";

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

  const generatePrintHTML = () => {
    const summary = data?.summary;
    const items = data?.items ?? [];
    const now = new Date().toLocaleDateString("he-IL");

    const unverifiedBanner =
      (summary?.total_unverified_worklogs ?? 0) > 0
? `<div class="warning-banner"> ${summary!.total_unverified_worklogs} דיווחים ללא תעריף מאומת — הסכומים המוצגים הם הערכה בלבד</div>`
        : "";

    const projectRows = items.map((item) => {
      const detailRows = (item.worklogs_detail ?? [])
        .map(
          (w) => `
        <tr class="${!w.is_verified ? "unverified-row" : ""}">
          <td>${w.report_date ?? "—"}</td>
          <td>${w.supplier_name ?? "—"}</td>
          <td class="license">${w.equipment_license_plate ?? "—"}</td>
          <td>${w.work_hours}</td>
<td>${w.hourly_rate_snapshot != null ? "" + w.hourly_rate_snapshot : " לא מאומת"}</td>
<td>${w.cost_before_vat != null ? "" + Number(w.cost_before_vat).toLocaleString("he-IL") : "—"}</td>
<td>${w.cost_with_vat != null ? "" + Number(w.cost_with_vat).toLocaleString("he-IL") : "—"}</td>
        </tr>`
        )
        .join("");

      return `
      <tr class="project-row ${item.unverified_count > 0 ? "has-unverified" : ""}">
        <td colspan="6">
          <div class="project-header">
            <span class="project-name">${item.name}</span>
${item.unverified_count > 0 ? `<span class="badge"> ${item.unverified_count} ללא אימות תעריף</span>` : ""}
<span class="project-stats">${item.worklog_count} דיווחים · ${item.total_hours} שעות · ${Number(item.total_cost_with_vat).toLocaleString("he-IL")} כולל מע"מ</span>
          </div>
          <table class="detail-table">
            <thead><tr><th>תאריך</th><th>ספק</th><th>מספר כלי</th><th>שעות</th><th>תעריף</th><th>לפני מע"מ</th><th>כולל מע"מ</th></tr></thead>
            <tbody>${detailRows}</tbody>
          </table>
        </td>
      </tr>`;
    }).join("");

    return `<!DOCTYPE html>
<html dir="rtl" lang="he"><head><meta charset="UTF-8"><title>דוח תמחור — Forewise</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:Arial,Helvetica,sans-serif;direction:rtl;color:#1a1a1a;padding:28px;font-size:13px}
  .header{border-bottom:3px solid #16a34a;padding-bottom:14px;margin-bottom:20px;display:flex;justify-content:space-between;align-items:flex-end}
  .header h1{font-size:20px;color:#15803d}.header .sub{font-size:11px;color:#6b7280;margin-top:3px}
  .date{font-size:11px;color:#9ca3af}
  .warning-banner{background:#fff7ed;border:1px solid #fed7aa;border-radius:6px;padding:9px 13px;margin-bottom:18px;color:#9a3412;font-size:12px}
  .summary-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:22px}
  .summary-card{background:#f9fafb;border:1px solid #e5e7eb;border-radius:7px;padding:11px;text-align:center}
  .summary-card .label{font-size:10px;color:#6b7280;margin-bottom:3px}
  .summary-card .value{font-size:17px;font-weight:bold;color:#111827}
  .summary-card .hint{font-size:9px;color:#9ca3af;margin-top:2px}
  .project-row td{padding:14px 0 6px}
  .project-header{display:flex;align-items:center;gap:10px;margin-bottom:8px;flex-wrap:wrap}
  .project-name{font-size:14px;font-weight:700;color:#111827}
  .project-stats{font-size:11px;color:#6b7280;margin-right:auto}
  .badge{background:#fed7aa;color:#9a3412;border-radius:9999px;padding:2px 9px;font-size:10px;font-weight:600}
  .detail-table{width:100%;border-collapse:collapse;font-size:11px;border:1px solid #e5e7eb;margin-bottom:8px}
  .detail-table thead tr{background:#f0fdf4}
  .detail-table th{padding:6px 9px;text-align:right;font-weight:600;color:#166534;font-size:10px;border-bottom:1px solid #d1fae5}
  .detail-table td{padding:7px 9px;border-bottom:1px solid #f3f4f6}
  .license{font-weight:700;color:#1e40af}
  .unverified-row{background:#fff7ed !important}
  .has-unverified .project-name{color:#92400e}
  .footer{margin-top:28px;padding-top:10px;border-top:1px solid #e5e7eb;font-size:10px;color:#9ca3af;display:flex;justify-content:space-between}
  @media print{body{padding:12px}@page{margin:12mm;size:A4}}
</style></head><body>
  <div class="header">
    <div><h1>דוח תמחור — Forewise</h1><div class="sub">סיכום עלויות דיווחי שעות לפי פרויקט, ספק ומספר כלי</div></div>
    <div class="date">הופק: ${now}</div>
  </div>
  ${unverifiedBanner}
  <div class="summary-grid">
    <div class="summary-card"><div class="label">פרויקטים</div><div class="value">${summary?.total_projects ?? 0}</div></div>
    <div class="summary-card"><div class="label">שעות</div><div class="value">${summary?.total_hours ?? 0}</div></div>
<div class="summary-card"><div class="label">לפני מע"מ</div><div class="value">${Number(summary?.total_cost ?? 0).toLocaleString("he-IL")}</div></div>
<div class="summary-card"><div class="label">כולל מע"מ</div><div class="value" style="color:#15803d">${Number(summary?.total_cost_with_vat ?? 0).toLocaleString("he-IL")}</div><div class="hint">ממוצע ${Math.round(summary?.average_hourly_rate ?? 0)}/שעה</div></div>
  </div>
  <table style="width:100%"><tbody>${projectRows}</tbody></table>
  <div class="footer"><span>מערכת ניהול יערות — Forewise</span><span>forewise.co</span></div>
</body></html>`;
  };

  const handleExportPDF = () => {
    const printWindow = window.open("", "_blank", "width=1000,height=750");
    if (!printWindow) return;
    printWindow.document.write(generatePrintHTML());
    printWindow.document.close();
    printWindow.onload = () => {
      printWindow.focus();
      printWindow.print();
      printWindow.close();
    };
  };

  const handleExportExcel = async () => {
    try {
      const response = await api.get(
        `/reports/export/excel?type=worklogs`,
        { responseType: "blob" }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `worklogs_${new Date().toISOString().slice(0, 10)}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      (window as any).showToast?.("שגיאה בייצוא Excel", "error");
    }
  };

  const reportTabs = [
    { key: "by-project" as ReportType, label: "לפי פרויקט", icon: Briefcase },
    { key: "by-supplier" as ReportType, label: "לפי ספק", icon: Users },
    { key: "by-equipment-type" as ReportType, label: "לפי סוג כלי", icon: Wrench },
  ];

  const isExpandable = reportType === "by-project";

  return (
    <div className="min-h-screen bg-gray-50 pt-4 sm:pt-6 pb-8 px-2 sm:px-4" dir="rtl">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">דוחות תמחור</h1>
          <p className="text-gray-500 mt-1">סיכום עלויות דיווחי שעות לפי פרויקט, ספק וסוג כלי</p>
        </div>

        {/* Report Type Tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto">
          {reportTabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setReportType(tab.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
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
        <div className="bg-white rounded-xl shadow-sm p-3 sm:p-4 mb-6">
          <div className="flex flex-wrap items-end gap-3 sm:gap-4 overflow-x-auto">
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
              <div className="flex flex-wrap items-center gap-2 mr-auto w-full sm:w-auto mt-2 sm:mt-0">
                <button
                  onClick={exportCSV}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                >
                  <Download className="w-4 h-4" />
                  ייצוא CSV
                </button>
                <button
                  onClick={handleExportPDF}
                  className="inline-flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-100 transition-colors"
                >
ייצוא PDF
                </button>
                <button
                  onClick={handleExportExcel}
                  className="inline-flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 px-4 py-2 text-sm font-medium text-green-700 hover:bg-green-100 transition-colors"
                >
                  <Download className="w-4 h-4" />
ייצוא Excel
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-16">
            <div className="flex items-center gap-2 bg-white p-6 rounded-lg shadow-sm">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 100" width="20" height="17">
                <defs>
                  <linearGradient id="pr1_t" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#1565c0"/><stop offset="100%" stopColor="#0097a7"/></linearGradient>
                  <linearGradient id="pr1_m" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#0097a7"/><stop offset="50%" stopColor="#2e7d32"/><stop offset="100%" stopColor="#66bb6a"/></linearGradient>
                  <linearGradient id="pr1_b" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#2e7d32"/><stop offset="40%" stopColor="#66bb6a"/><stop offset="100%" stopColor="#8B5e3c"/></linearGradient>
                </defs>
                <path d="M46 20 Q60 9 74 20" stroke="url(#pr1_t)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <path d="M30 47 Q42 34 60 43 Q78 34 90 47" stroke="url(#pr1_m)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <path d="M14 74 Q28 60 46 69 Q60 76 74 69 Q92 60 106 74" stroke="url(#pr1_b)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <line x1="60" y1="76" x2="60" y2="90" stroke="#8B5e3c" strokeWidth="3.5" strokeLinecap="round"/>
                <circle cx="60" cy="95" r="5" fill="#8B5e3c"/>
              </svg>
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
{data.summary.total_unverified_worklogs} דיווחים ללא תעריף מאומת —
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
                <div className="overflow-x-auto -mx-0">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        {isExpandable && (
                          <th className="w-10 px-2 py-3" />
                        )}
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
                        <React.Fragment key={item.id}>
                          {/* Main row */}
                          <tr
                            className={`hover:bg-gray-50 transition-colors ${
                              item.unverified_count > 0 ? "bg-orange-50/40" : ""
                            }`}
                          >
                            {isExpandable && (
                              <td className="px-2 py-3 text-center">
                                <button
                                  onClick={() => toggleRow(item.id)}
                                  className="p-1 rounded hover:bg-gray-200 text-gray-500 transition-colors"
                                  title={expandedRows.has(item.id) ? "סגור" : "פרטים"}
                                >
                                  {expandedRows.has(item.id) ? (
                                    <ChevronUp className="w-4 h-4" />
                                  ) : (
                                    <ChevronDown className="w-4 h-4" />
                                  )}
                                </button>
                              </td>
                            )}
                            <td className="px-4 py-3 font-medium text-gray-900">
                              <span>{item.name}</span>
                              {item.unverified_count > 0 && (
                                <span className="mr-2 inline-flex items-center gap-1 rounded-full bg-orange-100 text-orange-700 text-xs font-semibold px-2 py-0.5">
{item.unverified_count} ללא אימות תעריף
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
                                : "—"}
                            </td>
                          </tr>

                          {/* Expanded sub-table */}
                          {isExpandable && expandedRows.has(item.id) && (
                            <tr>
                              <td colSpan={7} className="bg-gray-50 px-6 pb-4 pt-0">
                                {(item.worklogs_detail ?? []).length === 0 ? (
                                  <p className="text-xs text-gray-400 py-3 text-center">אין פרטי דיווחים</p>
                                ) : (
                                  <table className="w-full text-xs border border-gray-200 rounded-lg overflow-hidden mt-2">
                                    <thead className="bg-green-50">
                                      <tr>
                                        <th className="text-right px-3 py-2 font-semibold text-green-800">תאריך</th>
                                        <th className="text-right px-3 py-2 font-semibold text-green-800">ספק</th>
                                        <th className="text-right px-3 py-2 font-semibold text-green-800">מספר כלי</th>
                                        <th className="text-right px-3 py-2 font-semibold text-green-800">שעות</th>
                                        <th className="text-right px-3 py-2 font-semibold text-green-800">תעריף</th>
                                        <th className="text-right px-3 py-2 font-semibold text-green-800">לפני מע"מ</th>
                                        <th className="text-right px-3 py-2 font-semibold text-green-800">כולל מע"מ</th>
                                      </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-100">
                                      {(item.worklogs_detail ?? []).map((w) => (
                                        <tr
                                          key={w.worklog_id}
                                          className={`${!w.is_verified ? "bg-orange-50" : "bg-white"}`}
                                        >
                                          <td className="px-3 py-2 text-gray-700">{w.report_date ?? "—"}</td>
                                          <td className="px-3 py-2 text-gray-700">{w.supplier_name ?? "—"}</td>
                                          <td className="px-3 py-2 font-bold text-blue-800">
                                            {w.equipment_license_plate ?? "—"}
                                          </td>
                                          <td className="px-3 py-2 text-gray-700">{w.work_hours}</td>
                                          <td className="px-3 py-2">
                                            {w.hourly_rate_snapshot != null ? (
<span className="text-gray-700">{w.hourly_rate_snapshot}</span>
                                            ) : (
<span className="text-orange-600 font-semibold"> ללא תעריף</span>
                                            )}
                                          </td>
                                          <td className="px-3 py-2 text-gray-700">{fmtNull(w.cost_before_vat)}</td>
                                          <td className="px-3 py-2 text-gray-700">{fmtNull(w.cost_with_vat)}</td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                )}
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      ))}
                    </tbody>
                    <tfoot className="bg-gray-50 border-t-2 border-gray-200">
                      <tr className="font-bold">
                        {isExpandable && <td />}
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
                            : "—"}
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
