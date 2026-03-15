
// src/pages/WorkOrders/WorkOrderDetail.tsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowRight, Calendar, Wrench, Edit, CheckCircle, XCircle,
  Clock, User, ClipboardList
} from 'lucide-react';
import workOrderService, { WorkOrder } from '../../services/workOrderService';
import UnifiedLoader from '../../components/common/UnifiedLoader';

const APPROVED_STATUSES = ['APPROVED', 'APPROVED_AND_SENT', 'COORDINATOR_APPROVED', 'ACTIVE', 'IN_PROGRESS'];

function woStatusBadge(status: string): { label: string; cls: string } {
  const s = (status || '').toUpperCase();
  if (['PENDING', 'DISTRIBUTING'].includes(s))
    return { label: 'ממתין לתיאום', cls: 'bg-yellow-100 text-yellow-700' };
  if (['SENT_TO_SUPPLIER', 'SUPPLIER_ACCEPTED_PENDING_COORDINATOR'].includes(s))
    return { label: 'אצל הספק', cls: 'bg-blue-100 text-blue-700' };
  if (APPROVED_STATUSES.includes(s))
    return { label: 'אושר — ניתן לדווח', cls: 'bg-green-100 text-green-700' };
  if (s === 'COMPLETED')
    return { label: 'הושלם', cls: 'bg-gray-100 text-gray-500' };
  if (['REJECTED', 'CANCELLED'].includes(s))
    return { label: 'נדחה', cls: 'bg-red-100 text-red-700' };
  return { label: status || '—', cls: 'bg-gray-100 text-gray-600' };
}

function safeDate(dateStr?: string | null, fallback?: string | null): string {
  const raw = dateStr || fallback;
  if (!raw) return '—';
  const d = new Date(raw);
  if (Number.isNaN(d.getTime()) || d.getFullYear() < 2000) return '—';
  return d.toLocaleDateString('he-IL');
}

const WorkOrderDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [workOrder, setWorkOrder] = useState<WorkOrder | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);

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

  const handleApprove = async () => {
    if (!workOrder) return;
    try {
      setProcessing(true);
      await workOrderService.approveWorkOrder(workOrder.id);
      await fetchWorkOrder();
      (window as any).showToast?.('הזמנת העבודה אושרה בהצלחה!', 'success');
    } catch (err: any) {
      (window as any).showToast?.(err.response?.data?.detail || 'שגיאה באישור הזמנה', 'error');
    } finally {
      setProcessing(false);
    }
  };

  const handleReject = async () => {
    if (!workOrder) return;
    const reason = prompt('סיבת דחייה:');
    if (!reason) return;
    try {
      setProcessing(true);
      await workOrderService.rejectWorkOrder(workOrder.id, reason);
      await fetchWorkOrder();
      (window as any).showToast?.('הזמנת העבודה נדחתה', 'success');
    } catch (err: any) {
      (window as any).showToast?.(err.response?.data?.detail || 'שגיאה בדחיית הזמנה', 'error');
    } finally {
      setProcessing(false);
    }
  };

  const handleStart = async () => {
    if (!workOrder) return;
    try {
      setProcessing(true);
      await workOrderService.startWorkOrder(workOrder.id);
      await fetchWorkOrder();
      (window as any).showToast?.('עבודה החלה', 'success');
    } catch (err: any) {
      (window as any).showToast?.(err.response?.data?.detail || 'שגיאה בהתחלת עבודה', 'error');
    } finally {
      setProcessing(false);
    }
  };

  const handleComplete = async () => {
    if (!workOrder) return;
    try {
      setProcessing(true);
      await workOrderService.completeWorkOrder(workOrder.id);
      await fetchWorkOrder();
      (window as any).showToast?.('העבודה הושלמה', 'success');
    } catch (err: any) {
      (window as any).showToast?.(err.response?.data?.detail || 'שגיאה בהשלמת עבודה', 'error');
    } finally {
      setProcessing(false);
    }
  };

  if (loading) return <UnifiedLoader size="full" />;

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button onClick={fetchWorkOrder} className="bg-kkl-green text-white px-4 py-2 rounded-lg hover:bg-green-700">
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

  const { label: statusLabel, cls: statusCls } = woStatusBadge(workOrder.status);
  const isApproved = APPROVED_STATUSES.includes((workOrder.status || '').toUpperCase());
  const wo = workOrder as any;
  const displayDate = safeDate(wo.work_start_date, workOrder.created_at);

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-6" dir="rtl">
      <div className="max-w-2xl mx-auto">

        {/* חזרה */}
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-1 text-gray-500 hover:text-gray-700 mb-6 text-sm"
        >
          <ArrowRight className="w-4 h-4" />
          חזרה
        </button>

        {/* כרטיס ראשי */}
        <div className="bg-white rounded-2xl border shadow-sm p-6 space-y-5">

          {/* כותרת + סטטוס */}
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs text-gray-400 mb-1">מספר דרישה</p>
              <h1 className="text-2xl font-bold text-gray-900">
                #{wo.order_number || workOrder.id}
              </h1>
              {workOrder.project_name && (
                <p className="text-sm text-gray-500 mt-1">פרויקט: {workOrder.project_name}</p>
              )}
            </div>
            <span className={`px-3 py-1.5 rounded-full text-sm font-medium whitespace-nowrap ${statusCls}`}>
              {statusLabel}
            </span>
          </div>

          <hr />

          {/* שדות פרטים */}
          <div className="space-y-3">
            {/* תאריך */}
            <div className="flex items-center gap-3">
              <Calendar className="w-5 h-5 text-gray-400 flex-shrink-0" />
              <div>
                <p className="text-xs text-gray-400">תאריך</p>
                <p className="font-medium text-gray-800">{displayDate}</p>
              </div>
            </div>

            {/* סוג ציוד */}
            {workOrder.equipment_type && (
              <div className="flex items-center gap-3">
                <Wrench className="w-5 h-5 text-gray-400 flex-shrink-0" />
                <div>
                  <p className="text-xs text-gray-400">סוג ציוד</p>
                  <p className="font-medium text-gray-800">{workOrder.equipment_type}</p>
                </div>
              </div>
            )}

            {/* ספק — רק אחרי אישור */}
            {isApproved && (
              <div className="flex items-center gap-3">
                <User className="w-5 h-5 text-gray-400 flex-shrink-0" />
                <div>
                  <p className="text-xs text-gray-400">ספק</p>
                  <p className="font-medium text-gray-800">
                    {workOrder.supplier_name || 'ממתין לשיבוץ'}
                  </p>
                </div>
              </div>
            )}

            {/* תיאור */}
            {workOrder.description && (
              <div className="flex items-start gap-3">
                <ClipboardList className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-xs text-gray-400">תיאור</p>
                  <p className="text-gray-700 text-sm leading-relaxed">{workOrder.description}</p>
                </div>
              </div>
            )}
          </div>

          <hr />

          {/* כפתורי פעולה */}
          <div className="flex flex-wrap gap-2">
            {/* דווח שעות — רק כשמאושר */}
            {isApproved && (
              <button
                onClick={() => navigate(
                  `/work-orders/${workOrder.id}/report-hours?work_order_id=${workOrder.id}&project_id=${workOrder.project_id}`
                )}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium text-sm"
              >
                <Clock className="w-4 h-4" />
                דווח שעות
              </button>
            )}

            {/* אשר / דחה (מתאם / מנהל) */}
            {(workOrder.status || '').toLowerCase() === 'pending' && (
              <>
                <button
                  onClick={handleApprove}
                  disabled={processing}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm disabled:opacity-50"
                >
                  <CheckCircle className="w-4 h-4" />
                  אשר
                </button>
                <button
                  onClick={handleReject}
                  disabled={processing}
                  className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm disabled:opacity-50"
                >
                  <XCircle className="w-4 h-4" />
                  דחה
                </button>
              </>
            )}

            {/* התחל עבודה */}
            {(workOrder.status || '').toLowerCase() === 'approved' && (
              <button
                onClick={handleStart}
                disabled={processing}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm disabled:opacity-50"
              >
                <Clock className="w-4 h-4" />
                התחל עבודה
              </button>
            )}

            {/* השלם עבודה */}
            {(workOrder.status || '').toLowerCase() === 'in_progress' && (
              <button
                onClick={handleComplete}
                disabled={processing}
                className="flex items-center gap-2 px-4 py-2 bg-kkl-green hover:bg-green-700 text-white rounded-lg text-sm disabled:opacity-50"
              >
                <CheckCircle className="w-4 h-4" />
                השלם עבודה
              </button>
            )}

            {/* עריכה */}
            <button
              onClick={() => navigate(`/work-orders/${workOrder.id}/edit`)}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm"
            >
              <Edit className="w-4 h-4" />
              עריכה
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorkOrderDetail;
