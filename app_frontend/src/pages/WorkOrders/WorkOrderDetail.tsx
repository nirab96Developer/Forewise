
// src/pages/WorkOrders/WorkOrderDetail.tsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowRight, Printer, Edit, Trash2, Clock, XCircle, ScanLine } from 'lucide-react';
import api from '../../services/api';
import workOrderService, { WorkOrder } from '../../services/workOrderService';
import UnifiedLoader from '../../components/common/UnifiedLoader';
import { getUserRole, normalizeRole, UserRole } from '../../utils/permissions';

let ScanEquipmentModal: React.FC<any> = () => null;
try { ScanEquipmentModal = require('../../components/equipment/ScanEquipmentModal').default; } catch {}

const STATUS_MAP: Record<string, { label: string; color: string; bg: string }> = {
  'PENDING': { label: 'ממתין', color: '#854d0e', bg: '#fef9c3' },
  'DISTRIBUTING': { label: 'בהפצה לספקים', color: '#854d0e', bg: '#fef9c3' },
  'APPROVED': { label: 'אושר ונשלח', color: '#166534', bg: '#dcfce7' },
  'APPROVED_AND_SENT': { label: 'אושר ונשלח', color: '#166534', bg: '#dcfce7' },
  'COORDINATOR_APPROVED': { label: 'אושר ונשלח', color: '#166534', bg: '#dcfce7' },
  'ACTIVE': { label: 'אושר ונשלח', color: '#166534', bg: '#dcfce7' },
  'IN_PROGRESS': { label: 'בביצוע', color: '#1e40af', bg: '#dbeafe' },
  'PENDING_SUPPLIER': { label: 'בהפצה לספקים', color: '#9a3412', bg: '#fed7aa' },
  'SUPPLIER_ACCEPTED_PENDING_COORDINATOR': { label: 'ספק אישר — ממתין לאישור מתאם', color: '#1e40af', bg: '#dbeafe' },
  'COMPLETED': { label: 'הושלם', color: '#374151', bg: '#e5e7eb' },
  'REJECTED': { label: 'נדחה', color: '#991b1b', bg: '#fee2e2' },
  'CANCELLED': { label: 'בוטל', color: '#991b1b', bg: '#fee2e2' },
  'EXPIRED': { label: 'פג תוקף', color: '#6b7280', bg: '#e5e7eb' },
};

const APPROVED_STATUSES = ['APPROVED', 'APPROVED_AND_SENT', 'COORDINATOR_APPROVED', 'ACTIVE', 'IN_PROGRESS'];

function fmtDate(dateStr?: string | null): string {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  if (isNaN(d.getTime()) || d.getFullYear() < 2000) return '—';
  return d.toLocaleDateString('he-IL');
}

function fmtCurrency(val?: number | string | null): string {
  if (val == null) return '—';
  const n = Number(val);
  if (isNaN(n) || n === 0) return '—';
return '' + n.toLocaleString('he-IL', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}

/** מסכום מוקפא — כולל 0 */
function fmtFrozen(val?: number | string | null): string {
  if (val == null || val === '') return '—';
  const n = Number(val);
  if (isNaN(n)) return '—';
return '' + n.toLocaleString('he-IL', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}

const WorkOrderDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [workOrder, setWorkOrder] = useState<WorkOrder | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [scanModalOpen, setScanModalOpen] = useState(false);
  const _role = normalizeRole(getUserRole());
  const isAdmin = _role === UserRole.ADMIN;
  const canEdit = [UserRole.ADMIN, UserRole.AREA_MANAGER, UserRole.WORK_MANAGER].includes(_role);
  

  useEffect(() => {
    if (id) fetchWorkOrder();
  }, [id]);

  const fetchWorkOrder = async () => {
    try {
      setLoading(true);
      setError(null);
      const order = await workOrderService.getWorkOrderById(parseInt(id!));
      setWorkOrder(order);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'שגיאה בטעינת הזמנת העבודה');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <UnifiedLoader size="full" />;

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button onClick={fetchWorkOrder} className="bg-green-700 text-white px-4 py-2 rounded-lg hover:bg-green-800">
            נסה שוב
          </button>
        </div>
      </div>
    );
  }

  if (!workOrder) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-red-600">הזמנת עבודה לא נמצאה</p>
      </div>
    );
  }

  const wo = workOrder as any;
  const s = (workOrder.status || '').toUpperCase();
  const st = STATUS_MAP[s] || { label: workOrder.status || '—', color: '#374151', bg: '#e5e7eb' };
  const isApproved = APPROVED_STATUSES.includes(s);

  const rows: { label: string; value: string }[] = [
    { label: 'מספר הזמנה', value: `${wo.order_number || workOrder.id}` },
    { label: 'פרויקט', value: workOrder.project_name || '—' },
    { label: 'סוג ציוד', value: workOrder.equipment_type || '—' },
    { label: 'ספק', value: workOrder.supplier_name || (wo.supplier_id ? `ספק #${wo.supplier_id}` : 'ממתין לשיבוץ') },
    { label: 'מספר כלי', value: wo.equipment_license_plate || (wo.equipment_id ? `כלי #${wo.equipment_id}` : 'לא שויך') },
    { label: 'תאריך התחלה', value: fmtDate(wo.work_start_date) },
    { label: 'תאריך סיום', value: fmtDate(wo.work_end_date) },
    { label: 'שעות משוערות', value: wo.estimated_hours ? `${wo.estimated_hours} שעות` : '—' },
    { label: 'תעריף לשעה', value: fmtCurrency(wo.hourly_rate) },
    { label: 'עלות כוללת', value: fmtCurrency(wo.total_amount) },
    { label: 'סכום מוקפא', value: fmtCurrency(wo.frozen_amount) },
    { label: 'עדיפות', value: wo.priority === 'high' ? 'גבוהה' : wo.priority === 'medium' ? 'בינונית' : wo.priority === 'low' ? 'נמוכה' : '—' },
    { label: 'תיאור', value: workOrder.description || '—' },
    { label: 'תאריך יצירה', value: fmtDate(workOrder.created_at) },
  ];

  return (
    <div className="min-h-screen bg-gray-100 py-6 px-4 print:bg-white print:py-0" dir="rtl">
      <div className="max-w-[210mm] mx-auto">

        {/* Action bar - hidden on print */}
        <div className="print:hidden flex items-center justify-between mb-4">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-1 text-gray-500 hover:text-gray-700 text-sm"
          >
            <ArrowRight className="w-4 h-4" />
            חזרה
          </button>
          <div className="flex gap-2">
            {isApproved && (
              <button
                onClick={() => navigate(`/work-orders/${workOrder.id}/report-hours?work_order_id=${workOrder.id}&project_id=${workOrder.project_id}`)}
                className="flex items-center gap-1.5 px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm"
              >
                <Clock className="w-4 h-4" />
                דווח שעות
              </button>
            )}
            <button
              onClick={() => window.open(`/api/v1/work-orders/${workOrder.id}/pdf`, '_blank')}
              className="flex items-center gap-1.5 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm"
            >
              <Printer className="w-4 h-4" />
              הורד PDF
            </button>
            {canEdit && (
              <button
                onClick={() => navigate(`/work-orders/${workOrder.id}/edit`)}
                className="flex items-center gap-1.5 px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm"
              >
                <Edit className="w-4 h-4" />
                עריכה
              </button>
            )}
            {isAdmin && (
              <button
                type="button"
                onClick={() => setDeleteModalOpen(true)}
                disabled={processing}
                className="flex items-center gap-1.5 px-3 py-2 bg-red-50 hover:bg-red-100 text-red-600 rounded-lg text-sm disabled:opacity-50"
              >
                <Trash2 className="w-4 h-4" />
                מחיקה
              </button>
            )}
            {isApproved && wo.equipment_id && (
              <button
                onClick={() => {
                  if (window.confirm(`האם להסיר את הכלי מהפרויקט? יתרה מוקפאת של ${fmtCurrency(wo.remaining_frozen)} תשוחרר.`)) {
                    setProcessing(true);
                    api.post(`/work-orders/${workOrder.id}/remove-equipment`)
                      .then(() => { fetchWorkOrder(); (window as any).showToast?.('כלי הוסר מהפרויקט', 'success'); })
                      .catch((e: any) => { (window as any).showToast?.(e.response?.data?.detail || 'שגיאה', 'error'); })
                      .finally(() => setProcessing(false));
                  }
                }}
                disabled={processing}
                className="flex items-center gap-1.5 px-3 py-2 bg-orange-50 hover:bg-orange-100 text-orange-600 rounded-lg text-sm disabled:opacity-50"
              >
                <XCircle className="w-4 h-4" />
                הסר כלי
              </button>
            )}
            {isApproved && !wo.equipment_id && !wo.equipment_license_plate && (
              <button
                onClick={() => setScanModalOpen(true)}
                className="flex items-center gap-1.5 px-3 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm animate-pulse"
              >
                <ScanLine className="w-4 h-4" />
                סרוק ציוד
              </button>
            )}
          </div>
        </div>

        {/* PDF Document */}
        <div className="bg-white shadow-lg print:shadow-none border print:border-0 rounded-lg print:rounded-none overflow-hidden">

          {/* Header */}
          <div style={{ background: 'linear-gradient(135deg, #2d5016 0%, #3d6b1f 100%)' }} className="px-8 py-6 text-white">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-2xl font-bold tracking-wide">הזמנת עבודה</h1>
                {workOrder.project_name && (
                  <p className="text-green-200 text-sm mt-1">{workOrder.project_name}</p>
                )}
              </div>
              <div className="text-left">
                <div className="text-3xl font-bold">#{wo.order_number || workOrder.id}</div>
                <div className="text-green-200 text-xs mt-1">{fmtDate(workOrder.created_at)}</div>
              </div>
            </div>
          </div>

          {/* Status bar */}
          <div className="px-8 py-3 border-b flex items-center justify-between" style={{ backgroundColor: st.bg }}>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: st.color }}></div>
              <span className="font-semibold text-sm" style={{ color: st.color }}>סטטוס: {st.label}</span>
            </div>
          </div>

          {/* Body - Table */}
          <div className="px-8 py-6">
            <table className="w-full">
              <tbody>
                {rows.map((row, i) => (
                  <tr key={i} className={i % 2 === 0 ? 'bg-gray-50' : 'bg-white'}>
                    <td className="py-3 px-4 text-sm font-semibold text-gray-500 w-[35%] border-b border-gray-100">
                      {row.label}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-900 font-medium border-b border-gray-100">
                      {row.value}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Footer */}
          <div className="px-8 py-4 border-t bg-gray-50 text-center">
            <p className="text-xs text-gray-400">
              Forewise — מערכת ניהול יערות | מסמך הזמנת עבודה | הופק בתאריך {new Date().toLocaleDateString('he-IL')}
            </p>
          </div>
        </div>
      </div>

      {/* סריקת ציוד — Modal */}
      <ScanEquipmentModal
        isOpen={scanModalOpen}
        onClose={() => setScanModalOpen(false)}
        workOrderId={workOrder.id}
        onSuccess={(equipmentId: number, licensePlate: string, _name: string) => {
          api.post(`/work-orders/${workOrder.id}/confirm-equipment`, { equipment_id: equipmentId })
            .then(() => {
              fetchWorkOrder();
              (window as any).showToast?.(`כלי ${licensePlate} שויך להזמנה`, 'success');
            })
            .catch((e: any) => {
              (window as any).showToast?.(e.response?.data?.detail || 'שגיאה בשיוך', 'error');
            });
          setScanModalOpen(false);
        }}
      />

      {/* מחיקה — דיאלוג מאושר */}
      {deleteModalOpen && (
        <div
          className="print:hidden fixed inset-0 z-[100] flex items-center justify-center p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="wo-delete-title"
        >
          <button
            type="button"
            className="absolute inset-0 bg-black/50 backdrop-blur-[2px] animate-in fade-in duration-200"
            onClick={() => !processing && setDeleteModalOpen(false)}
            aria-label="סגור"
          />
          <div
            className="relative z-10 w-full max-w-md rounded-2xl bg-white shadow-2xl border border-gray-100 p-6 animate-in zoom-in-95 fade-in duration-200"
            dir="rtl"
          >
            <h2 id="wo-delete-title" className="text-lg font-bold text-gray-900 mb-2">
              למחוק הזמנת עבודה?
            </h2>
            <p className="text-gray-600 text-sm mb-4 leading-relaxed">
              הזמנה מספר <span className="font-semibold text-gray-900">#{wo.order_number || workOrder.id}</span>
              <br />
              <span className="text-gray-700">סכום מוקפא נותר: </span>
              <span className="font-semibold text-gray-900">{fmtFrozen(wo.frozen_amount)}</span>
            </p>
            <div className="flex gap-3 justify-end mt-6">
              <button
                type="button"
                disabled={processing}
                onClick={() => setDeleteModalOpen(false)}
                className="px-4 py-2.5 rounded-xl text-sm font-medium bg-gray-100 text-gray-800 hover:bg-gray-200 transition-colors disabled:opacity-50"
              >
                לא, חזור
              </button>
              <button
                type="button"
                disabled={processing}
                onClick={() => {
                  setProcessing(true);
                  workOrderService
                    .deleteWorkOrder(workOrder.id)
                    .then(() => navigate(-1))
                    .catch(() => {
                      setProcessing(false);
                    });
                }}
                className="px-4 py-2.5 rounded-xl text-sm font-semibold bg-red-600 text-white hover:bg-red-700 transition-colors disabled:opacity-50"
              >
                כן, מחק הזמנה
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkOrderDetail;
