import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Clock, Briefcase, FileText, AlertTriangle, Plus, QrCode,
  ChevronLeft, ShieldAlert, Info, Play, CheckCircle, Wrench,
  ClipboardList, Send
} from "lucide-react";
import api from "../../services/api";
import UnifiedLoader from "../../components/common/UnifiedLoader";

interface WMData {
  kpis: {
    hours_today: number; open_work_orders: number;
    draft_reports: number; submitted_reports: number; approved_reports: number;
  };
  active_work: {
    work_order_id: number; order_number: number; title: string; status: string;
    project_name: string; supplier_name: string | null;
    equipment_code: string | null; license_plate: string | null;
    estimated_hours: number; used_hours: number; remaining_hours: number;
    start_date: string | null;
  } | null;
  work_orders: {
    id: number; order_number: number; title: string; status: string;
    project_name: string; supplier_name: string | null;
    license_plate: string | null; has_equipment: boolean;
  }[];
  equipment_scans: {
    equipment_id: number; code: string; license_plate: string;
    equipment_type: string; scanned_at: string | null;
  }[];
  alerts: { type: string; message: string; link: string }[];
}

const WO_STATUS: Record<string, { label: string; cls: string }> = {
  PENDING: { label: "ממתין", cls: "bg-yellow-100 text-yellow-800" },
  DISTRIBUTING: { label: "בהפצה", cls: "bg-blue-100 text-blue-800" },
  SUPPLIER_ACCEPTED_PENDING_COORDINATOR: { label: "ספק אישר", cls: "bg-blue-100 text-blue-800" },
  APPROVED_AND_SENT: { label: "מוכן לעבודה", cls: "bg-green-100 text-green-800" },
};

const WorkManagerDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<WMData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/dashboard/work-manager-overview")
      .then(r => setData(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <UnifiedLoader size="full" />;
  if (!data) return <div className="p-8 text-center text-gray-500">שגיאה בטעינת נתונים</div>;

  const k = data.kpis;
  const aw = data.active_work;

  return (
    <div className="min-h-full bg-gray-50" dir="rtl">
      <div className="p-3 sm:p-5 space-y-4 max-w-screen-lg mx-auto">

        {/* ── Active Work (Hero) ── */}
        {aw && (
          <div className="bg-gradient-to-l from-green-600 to-green-700 rounded-2xl p-4 sm:p-5 text-white shadow-lg">
            <div className="flex items-center gap-2 mb-3">
              <Play className="w-5 h-5" />
              <span className="text-sm font-bold opacity-90">עבודה פעילה</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-extrabold mb-1">#{aw.order_number} {aw.title}</h2>
            <p className="text-sm opacity-80 mb-3">{aw.project_name}{aw.supplier_name ? ` · ${aw.supplier_name}` : ""}</p>

            {/* Progress */}
            <div className="flex items-center gap-4 mb-4">
              <div className="flex-1">
                <div className="flex justify-between text-xs mb-1 opacity-80">
                  <span>{aw.used_hours.toFixed(1)} שעות בוצעו</span>
                  <span>{aw.estimated_hours} שעות מתוכנן</span>
                </div>
                <div className="w-full bg-white/20 rounded-full h-3">
                  <div className="h-3 rounded-full bg-white transition-all"
                    style={{ width: `${Math.min(100, aw.estimated_hours > 0 ? (aw.used_hours / aw.estimated_hours) * 100 : 0)}%` }} />
                </div>
              </div>
              <div className="text-center">
                <p className="text-3xl font-extrabold">{aw.remaining_hours.toFixed(1)}</p>
                <p className="text-[10px] opacity-70">שעות נותרו</p>
              </div>
            </div>

            {aw.license_plate && (
              <p className="text-xs opacity-70 mb-3">ציוד: {aw.license_plate} {aw.equipment_code ? `(${aw.equipment_code})` : ""}</p>
            )}

            <div className="flex gap-2">
              <button onClick={() => navigate(`/work-logs/new?work_order_id=${aw.work_order_id}`)}
                className="flex-1 flex items-center justify-center gap-2 min-h-[48px] bg-white text-green-700 font-bold text-sm rounded-xl hover:bg-green-50 transition-colors">
                <ClipboardList className="w-4 h-4" /> דיווח שעות
              </button>
              <button onClick={() => navigate(`/work-orders/${aw.work_order_id}`)}
                className="flex items-center justify-center gap-2 min-h-[48px] px-4 bg-white/20 text-white font-bold text-sm rounded-xl hover:bg-white/30 transition-colors">
                פרטים
              </button>
            </div>
          </div>
        )}

        {/* ── KPIs ── */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <MiniKPI icon={<Clock className="w-5 h-5 text-blue-500" />} label="שעות היום" value={k.hours_today.toFixed(1)} />
          <MiniKPI icon={<Briefcase className="w-5 h-5 text-green-500" />} label="הזמנות פתוחות" value={String(k.open_work_orders)} />
          <MiniKPI icon={<FileText className="w-5 h-5 text-amber-500" />} label="טיוטות" value={String(k.draft_reports)} alert={k.draft_reports > 0} />
          <MiniKPI icon={<CheckCircle className="w-5 h-5 text-emerald-500" />} label="אושרו" value={String(k.approved_reports)} />
        </div>

        {/* ── Alerts ── */}
        {data.alerts.length > 0 && (
          <div className="space-y-2">
            {data.alerts.map((a, i) => {
              const isErr = a.type === "error";
              const Icon = isErr ? ShieldAlert : a.type === "warning" ? AlertTriangle : Info;
              return (
                <div key={i} className={`rounded-xl border px-3 py-3 flex items-center gap-3 ${
                  isErr ? "border-red-300 bg-red-50" : "border-amber-300 bg-amber-50"}`}>
                  <Icon className={`w-5 h-5 flex-shrink-0 ${isErr ? "text-red-600" : "text-amber-600"}`} />
                  <span className={`text-sm font-semibold flex-1 ${isErr ? "text-red-800" : "text-amber-800"}`}>{a.message}</span>
                  <button onClick={() => navigate(a.link)}
                    className={`px-3 min-h-[40px] text-xs font-bold rounded-lg text-white ${
                      isErr ? "bg-red-600 hover:bg-red-700" : "bg-amber-600 hover:bg-amber-700"}`}>
                    צפה
                  </button>
                </div>
              );
            })}
          </div>
        )}

        {/* ── Quick Actions ── */}
        <div className="grid grid-cols-3 gap-2">
          <button onClick={() => navigate("/equipment/scan")}
            className="flex flex-col items-center gap-1.5 min-h-[72px] bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md active:scale-[0.97] transition-all justify-center">
            <QrCode className="w-6 h-6 text-blue-600" />
            <span className="text-xs font-bold text-gray-700">סריקת QR</span>
          </button>
          <button onClick={() => navigate("/work-logs/new")}
            className="flex flex-col items-center gap-1.5 min-h-[72px] bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md active:scale-[0.97] transition-all justify-center">
            <Plus className="w-6 h-6 text-green-600" />
            <span className="text-xs font-bold text-gray-700">דיווח חדש</span>
          </button>
          <button onClick={() => navigate("/work-logs")}
            className="flex flex-col items-center gap-1.5 min-h-[72px] bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md active:scale-[0.97] transition-all justify-center">
            <FileText className="w-6 h-6 text-gray-500" />
            <span className="text-xs font-bold text-gray-700">היסטוריה</span>
          </button>
        </div>

        {/* ── Work Orders + Equipment ── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

          {/* Work Orders (card-based) */}
          <div className="lg:col-span-2 space-y-2.5">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-gray-700 flex items-center gap-2">
                <Briefcase className="w-4 h-4" /> הזמנות עבודה
              </h3>
              <button onClick={() => navigate("/work-orders")}
                className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center gap-0.5">
                הכל <ChevronLeft className="w-3 h-3" />
              </button>
            </div>
            {data.work_orders.length === 0 ? (
              <div className="bg-white rounded-xl shadow-sm p-6 text-center text-sm text-gray-400">אין הזמנות פתוחות</div>
            ) : data.work_orders.map(wo => {
              const st = WO_STATUS[wo.status] || { label: wo.status, cls: "bg-gray-100 text-gray-600" };
              const isReady = wo.status === "APPROVED_AND_SENT";
              return (
                <div key={wo.id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-3.5 hover:shadow-md transition-all">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-sm font-bold text-gray-900">#{wo.order_number} {wo.title}</span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${st.cls}`}>{st.label}</span>
                  </div>
                  <p className="text-xs text-gray-500 mb-2.5">{wo.project_name}{wo.supplier_name ? ` · ${wo.supplier_name}` : ""}</p>
                  {isReady && (
                    <div className="flex gap-2">
                      <button onClick={() => navigate(`/work-logs/new?work_order_id=${wo.id}`)}
                        className="flex-1 flex items-center justify-center gap-1.5 min-h-[40px] bg-green-600 text-white text-xs font-bold rounded-lg hover:bg-green-700 transition-colors">
                        <ClipboardList className="w-3.5 h-3.5" /> דיווח
                      </button>
                      {!wo.has_equipment && (
                        <button onClick={() => navigate(`/equipment/scan?wo=${wo.id}`)}
                          className="flex items-center justify-center gap-1.5 min-h-[40px] px-3 bg-blue-50 text-blue-700 text-xs font-bold rounded-lg hover:bg-blue-100 transition-colors">
                          <QrCode className="w-3.5 h-3.5" /> סריקה
                        </button>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Equipment Status */}
          <div className="bg-white rounded-xl shadow-sm p-3.5">
            <h3 className="text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
              <Wrench className="w-4 h-4" /> ציוד שנסרק היום
            </h3>
            {data.equipment_scans.length === 0 ? (
              <div className="text-center py-6">
                <QrCode className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                <p className="text-xs text-gray-400">לא נסרק ציוד היום</p>
                <button onClick={() => navigate("/equipment/scan")}
                  className="mt-3 px-4 min-h-[40px] bg-blue-50 text-blue-700 text-xs font-bold rounded-lg hover:bg-blue-100 transition-colors">
                  סרוק עכשיו
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                {data.equipment_scans.map(eq => (
                  <div key={eq.equipment_id} className="flex items-center gap-2.5 p-2.5 bg-green-50 rounded-lg border border-green-200">
                    <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-bold text-gray-800 truncate">{eq.license_plate || eq.code}</p>
                      <p className="text-[10px] text-gray-500">{eq.equipment_type}</p>
                    </div>
                    <span className="text-[10px] text-gray-400">{eq.scanned_at}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* ── Quick Report ── */}
        <QuickReportCard />

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

const QuickReportCard: React.FC = () => {
  const navigate = useNavigate();
  const [hours, setHours] = useState("");
  const [breakMins, setBreakMins] = useState("");
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
      <h3 className="text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
        <Send className="w-4 h-4 text-green-600" /> דיווח מהיר
      </h3>
      <div className="flex gap-3 items-end">
        <div className="flex-1">
          <label className="text-[11px] text-gray-500 mb-1 block">שעות עבודה</label>
          <input type="number" step="0.5" min="0" max="24" value={hours} onChange={e => setHours(e.target.value)}
            className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500"
            placeholder="9.0" />
        </div>
        <div className="w-24">
          <label className="text-[11px] text-gray-500 mb-1 block">הפסקה (דק׳)</label>
          <input type="number" min="0" max="120" value={breakMins} onChange={e => setBreakMins(e.target.value)}
            className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500"
            placeholder="30" />
        </div>
        <button onClick={() => navigate(`/work-logs/new?hours=${hours}&break=${breakMins}`)}
          disabled={!hours}
          className="min-h-[44px] px-5 bg-green-600 text-white font-bold text-sm rounded-xl hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
          שלח
        </button>
      </div>
    </div>
  );
};

export default WorkManagerDashboard;
