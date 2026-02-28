// @ts-nocheck
import React, { useState, useEffect } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import {
  ArrowRight,
  Calendar,
  Clock,
  User,
  Loader2,
  CheckCircle,
  XCircle,
  AlertCircle,
  FileText,
  Wrench,
  MapPin,
  Hash,
  DollarSign,
  Send,
  Download,
} from "lucide-react";
import workLogService, { WorkLog } from "../../services/workLogService";

const WorklogDetail: React.FC = () => {
  const navigate = useNavigate();
  const { id, code } = useParams();
  const [worklog, setWorklog] = useState<WorkLog | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    if (id) {
      fetchWorklog(parseInt(id));
    }
  }, [id]);

  const fetchWorklog = async (worklogId: number) => {
    try {
      setLoading(true);
      setError(null);
      const data = await workLogService.getWorkLog(worklogId);
      setWorklog(data);
    } catch (err: any) {
      console.error("Error fetching worklog:", err);
      setError("שגיאה בטעינת פרטי הדיווח");
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!worklog) return;
    try {
      setActionLoading(true);
      await workLogService.approveWorkLog(worklog.id);
      await fetchWorklog(worklog.id);
    } catch (err) {
      console.error("Error approving:", err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!worklog) return;
    const reason = prompt("סיבת דחייה:");
    if (!reason) return;
    try {
      setActionLoading(true);
      await workLogService.rejectWorkLog(worklog.id, reason);
      await fetchWorklog(worklog.id);
    } catch (err) {
      console.error("Error rejecting:", err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!worklog) return;
    try {
      setActionLoading(true);
      await workLogService.submitWorkLog(worklog.id);
      await fetchWorklog(worklog.id);
    } catch (err) {
      console.error("Error submitting:", err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDownloadPDF = async () => {
    if (!worklog) return;
    try {
      const blob = await workLogService.downloadPDF(worklog.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `worklog-${worklog.report_number_formatted || worklog.id}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Error downloading PDF:", err);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "approved":
        return "bg-green-100 text-green-800";
      case "rejected":
        return "bg-red-100 text-red-800";
      case "pending":
      case "submitted":
        return "bg-yellow-100 text-yellow-800";
      case "draft":
        return "bg-gray-100 text-gray-800";
      case "invoiced":
        return "bg-blue-100 text-blue-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "approved":
        return "אושר";
      case "rejected":
        return "נדחה";
      case "pending":
        return "ממתין לאישור";
      case "submitted":
        return "הוגש";
      case "draft":
        return "טיוטה";
      case "invoiced":
        return "חשבונית";
      default:
        return status;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "approved":
        return <CheckCircle className="w-5 h-5" />;
      case "rejected":
        return <XCircle className="w-5 h-5" />;
      case "pending":
      case "submitted":
        return <Clock className="w-5 h-5" />;
      default:
        return <FileText className="w-5 h-5" />;
    }
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleDateString("he-IL");
  };

  const formatTime = (timeStr: string) => {
    if (!timeStr) return "-";
    try {
      return new Date(`2000-01-01T${timeStr}`).toLocaleTimeString("he-IL", {
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return timeStr;
    }
  };

  const formatCurrency = (value: string | number | undefined) => {
    if (!value) return "-";
    const num = typeof value === "string" ? parseFloat(value) : value;
    return new Intl.NumberFormat("he-IL", { style: "currency", currency: "ILS" }).format(num);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center gap-2 bg-white p-6 rounded-lg shadow-sm">
          <Loader2 className="w-5 h-5 animate-spin text-green-600" />
          <span className="text-gray-700">טוען פרטי דיווח...</span>
        </div>
      </div>
    );
  }

  if (error || !worklog) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-xl shadow-sm p-8 max-w-md text-center">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">שגיאה</h3>
          <p className="text-gray-500 mb-4">{error || "הדיווח לא נמצא"}</p>
          <button
            onClick={() => navigate(-1)}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            חזרה
          </button>
        </div>
      </div>
    );
  }

  const backPath = code
    ? `/projects/${code}/workspace/work-logs`
    : null;

  return (
    <div className="min-h-screen bg-gray-50 pt-20 pb-8 px-4 md:pr-72" dir="rtl">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center mb-4">
            {backPath ? (
              <Link to={backPath} className="text-green-600 hover:text-green-700 flex items-center text-sm">
                <ArrowRight className="w-4 h-4 ml-1" />
                חזרה לדיווחי שעות
              </Link>
            ) : (
              <button onClick={() => navigate(-1)} className="text-green-600 hover:text-green-700 flex items-center text-sm">
                <ArrowRight className="w-4 h-4 ml-1" />
                חזרה
              </button>
            )}
          </div>

          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                דיווח #{worklog.report_number_formatted || worklog.report_number || worklog.id}
              </h1>
              <p className="text-gray-500 mt-1">
                {formatDate(worklog.report_date)}
                {worklog.project_name && ` | ${worklog.project_name}`}
              </p>
            </div>
            <div className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium ${getStatusColor(worklog.status)}`}>
              {getStatusIcon(worklog.status)}
              {getStatusText(worklog.status)}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Info */}
          <div className="lg:col-span-2 space-y-6">
            {/* Time Details */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Clock className="w-5 h-5 text-green-600" />
                פרטי שעות
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="text-sm text-gray-500">התחלה</div>
                  <div className="text-lg font-semibold text-gray-900">{formatTime(worklog.start_time || "")}</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="text-sm text-gray-500">סיום</div>
                  <div className="text-lg font-semibold text-gray-900">{formatTime(worklog.end_time || "")}</div>
                </div>
                <div className="bg-green-50 rounded-lg p-3 text-center">
                  <div className="text-sm text-green-600">שעות עבודה</div>
                  <div className="text-lg font-bold text-green-700">{worklog.work_hours || "-"}</div>
                </div>
                <div className="bg-orange-50 rounded-lg p-3 text-center">
                  <div className="text-sm text-orange-600">הפסקה</div>
                  <div className="text-lg font-semibold text-orange-700">{worklog.break_hours || "-"}</div>
                </div>
              </div>
              <div className="mt-4 flex items-center justify-between bg-blue-50 rounded-lg p-3">
                <span className="text-blue-700 font-medium">סה"כ שעות</span>
                <span className="text-xl font-bold text-blue-800">{worklog.total_hours || "-"}</span>
              </div>
              {worklog.is_standard && (
                <div className="mt-3 flex items-center gap-2 text-green-700 bg-green-50 rounded-lg p-3 text-sm">
                  <CheckCircle className="w-4 h-4" />
                  <span>דיווח תקן (10.5 שעות)</span>
                </div>
              )}
              {!worklog.is_standard && worklog.non_standard_reason && (
                <div className="mt-3 bg-yellow-50 rounded-lg p-3 text-sm">
                  <span className="text-yellow-700 font-medium">סיבת חריגה: </span>
                  <span className="text-yellow-800">{worklog.non_standard_reason}</span>
                </div>
              )}
            </div>

            {/* Segments */}
            {worklog.segments && worklog.segments.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">פירוט מקטעים</h2>
                <div className="space-y-2">
                  {worklog.segments.map((seg, idx) => (
                    <div
                      key={seg.id || idx}
                      className={`flex items-center justify-between p-3 rounded-lg ${
                        seg.segment_type === "work" ? "bg-green-50" : "bg-orange-50"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span className={`text-xs font-medium px-2 py-1 rounded ${
                          seg.segment_type === "work"
                            ? "bg-green-200 text-green-800"
                            : "bg-orange-200 text-orange-800"
                        }`}>
                          {seg.segment_type === "work" ? "עבודה" : "הפסקה"}
                        </span>
                        <span className="text-sm text-gray-700">
                          {formatTime(seg.start_time)} - {formatTime(seg.end_time)}
                        </span>
                      </div>
                      <span className="text-sm font-medium text-gray-900">
                        {seg.segment_type === "work"
                          ? `${seg.work_minutes} דק'`
                          : `${seg.break_minutes} דק'`}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Work Details */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <FileText className="w-5 h-5 text-green-600" />
                פרטי עבודה
              </h2>
              <div className="space-y-4">
                {worklog.work_type && (
                  <div className="flex items-start gap-3">
                    <Wrench className="w-5 h-5 text-gray-400 mt-0.5" />
                    <div>
                      <span className="text-sm text-gray-500">סוג עבודה</span>
                      <p className="font-medium text-gray-900">{worklog.work_type}</p>
                    </div>
                  </div>
                )}
                {worklog.activity_description && (
                  <div className="flex items-start gap-3">
                    <FileText className="w-5 h-5 text-gray-400 mt-0.5" />
                    <div>
                      <span className="text-sm text-gray-500">תיאור פעילות</span>
                      <p className="font-medium text-gray-900">{worklog.activity_description}</p>
                    </div>
                  </div>
                )}
                {worklog.equipment_name && (
                  <div className="flex items-start gap-3">
                    <Wrench className="w-5 h-5 text-gray-400 mt-0.5" />
                    <div>
                      <span className="text-sm text-gray-500">ציוד</span>
                      <p className="font-medium text-gray-900">
                        {worklog.equipment_name}
                        {worklog.equipment_code && ` (${worklog.equipment_code})`}
                      </p>
                    </div>
                  </div>
                )}
                {worklog.supplier_name && (
                  <div className="flex items-start gap-3">
                    <User className="w-5 h-5 text-gray-400 mt-0.5" />
                    <div>
                      <span className="text-sm text-gray-500">ספק</span>
                      <p className="font-medium text-gray-900">{worklog.supplier_name}</p>
                    </div>
                  </div>
                )}
                {worklog.area_name && (
                  <div className="flex items-start gap-3">
                    <MapPin className="w-5 h-5 text-gray-400 mt-0.5" />
                    <div>
                      <span className="text-sm text-gray-500">אזור</span>
                      <p className="font-medium text-gray-900">{worklog.area_name}</p>
                    </div>
                  </div>
                )}
                {worklog.notes && (
                  <div className="flex items-start gap-3">
                    <FileText className="w-5 h-5 text-gray-400 mt-0.5" />
                    <div>
                      <span className="text-sm text-gray-500">הערות</span>
                      <p className="font-medium text-gray-900">{worklog.notes}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Pricing */}
            {worklog.hourly_rate_snapshot && (
              <div className="bg-white rounded-xl shadow-sm p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <DollarSign className="w-5 h-5 text-green-600" />
                  תמחור
                </h2>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div className="bg-gray-50 rounded-lg p-3">
                    <div className="text-sm text-gray-500">תעריף שעתי</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {formatCurrency(worklog.hourly_rate_snapshot)}
                    </div>
                    {worklog.rate_source_name && (
                      <div className="text-xs text-gray-400 mt-1">{worklog.rate_source_name}</div>
                    )}
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <div className="text-sm text-gray-500">עלות לפני מע"מ</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {formatCurrency(worklog.cost_before_vat)}
                    </div>
                  </div>
                  <div className="bg-green-50 rounded-lg p-3">
                    <div className="text-sm text-green-600">עלות כולל מע"מ</div>
                    <div className="text-lg font-bold text-green-700">
                      {formatCurrency(worklog.cost_with_vat)}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Rejection Reason */}
            {worklog.status === "rejected" && worklog.rejection_reason && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-6">
                <h2 className="text-lg font-semibold text-red-800 mb-2 flex items-center gap-2">
                  <XCircle className="w-5 h-5" />
                  סיבת דחייה
                </h2>
                <p className="text-red-700">{worklog.rejection_reason}</p>
                {worklog.approved_by_name && (
                  <p className="text-sm text-red-500 mt-2">נדחה ע"י: {worklog.approved_by_name}</p>
                )}
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Actions */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">פעולות</h3>
              <div className="space-y-3">
                {worklog.status === "draft" && (
                  <button
                    onClick={handleSubmit}
                    disabled={actionLoading}
                    className="w-full bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    <Send className="w-4 h-4" />
                    הגש לאישור
                  </button>
                )}
                {(worklog.status === "pending" || worklog.status === "submitted") && (
                  <>
                    <button
                      onClick={handleApprove}
                      disabled={actionLoading}
                      className="w-full bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      <CheckCircle className="w-4 h-4" />
                      אשר
                    </button>
                    <button
                      onClick={handleReject}
                      disabled={actionLoading}
                      className="w-full bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      <XCircle className="w-4 h-4" />
                      דחה
                    </button>
                  </>
                )}
                <button
                  onClick={handleDownloadPDF}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center justify-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  הורד PDF
                </button>
                <button
                  onClick={() => navigate(-1)}
                  className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg"
                >
                  חזרה
                </button>
              </div>
            </div>

            {/* Meta Info */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">מידע נוסף</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">מספר דיווח</span>
                  <span className="font-medium">{worklog.report_number_formatted || worklog.report_number || "-"}</span>
                </div>
                {worklog.user_name && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">מדווח</span>
                    <span className="font-medium">{worklog.user_name}</span>
                  </div>
                )}
                {worklog.work_order_number && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">הזמנת עבודה</span>
                    <span className="font-medium">#{worklog.work_order_number}</span>
                  </div>
                )}
                {worklog.approved_by_name && worklog.status === "approved" && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">אושר ע"י</span>
                    <span className="font-medium">{worklog.approved_by_name}</span>
                  </div>
                )}
                {worklog.approved_at && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">תאריך אישור</span>
                    <span className="font-medium">{formatDate(worklog.approved_at)}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-gray-500">נוצר</span>
                  <span className="font-medium">{formatDate(worklog.created_at)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">עודכן</span>
                  <span className="font-medium">{formatDate(worklog.updated_at)}</span>
                </div>
              </div>
            </div>

            {/* Distribution Status */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">סטטוס הפצה</h3>
              <div className="space-y-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">נשלח לספק</span>
                  {worklog.sent_to_supplier ? (
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  ) : (
                    <XCircle className="w-4 h-4 text-gray-300" />
                  )}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">נשלח לרו"ח</span>
                  {worklog.sent_to_accountant ? (
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  ) : (
                    <XCircle className="w-4 h-4 text-gray-300" />
                  )}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">נשלח למנהל אזור</span>
                  {worklog.sent_to_area_manager ? (
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  ) : (
                    <XCircle className="w-4 h-4 text-gray-300" />
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorklogDetail;
