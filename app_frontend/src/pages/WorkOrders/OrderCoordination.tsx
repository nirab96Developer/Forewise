
// src/pages/WorkOrders/OrderCoordination.tsx
// מסך תיאום הזמנות
import React, { useEffect, useState, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  RefreshCcw, CheckCircle, AlertTriangle, Phone, Send,
  ArrowLeftRight, Eye, Loader2, User, Truck, Calendar,
  Timer, ChevronDown, ChevronUp, Zap, RotateCcw, Search,
  ClipboardList, Clock, Building2, XCircle, Trash2, CheckSquare, Square
} from "lucide-react";
import workOrderService, { WorkOrder } from "../../services/workOrderService";
import api from "../../services/api";
import authService from "../../services/authService";
import UnifiedLoader from "../../components/common/UnifiedLoader";
import { normalizeRole, UserRole } from "../../utils/permissions";
import { getWorkOrderStatusLabel, getWorkOrderStatusTone, toneClasses } from "../../strings";

interface CoordinationOrder extends Omit<WorkOrder, 'status'> {
  status: string;
  time_remaining_minutes?: number;
  time_remaining_display?: string;
  is_urgent?: boolean;
  suggested_supplier_name?: string;
  portal_sent_at?: string;
  portal_token?: string;
  order_number?: number;
  is_forced_selection?: boolean;
  requested_equipment_model_id?: number;
  work_days?: number;
  constraint_notes?: string;
  area_name?: string;
  region_name?: string;
}

interface EquipmentCategory {
  id: number;
  name: string;
}

interface EquipmentModel {
  id: number;
  name: string;
  category_id?: number;
}

const OrderCoordination: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const focusedFromUrl = Number(searchParams.get("focus")) || null;
  const [loading, setLoading] = useState(true);
  const [orders, setOrders] = useState<CoordinationOrder[]>([]);
  const [expandedOrder, setExpandedOrder] = useState<number | null>(focusedFromUrl);
  const [processing, setProcessing] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [_invitations, setInvitations] = useState<any[]>([]);
  const [categories, setCategories] = useState<Record<number, string>>({});
  const [equipmentModels, setEquipmentModels] = useState<Record<number, EquipmentModel>>({});
  const [cancelModal, setCancelModal] = useState<{ orderId: number; orderNumber: string | number } | null>(null);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [bulkDeleteModal, setBulkDeleteModal] = useState(false);
  const [bulkDeleting, setBulkDeleting] = useState(false);

  // Check if current user is admin
  const currentUserData = authService.getCurrentUser();
  const currentRole = normalizeRole(currentUserData?.role || '');
  const isAdmin = currentRole === UserRole.ADMIN || (currentUserData?.roles?.some((r: string) => ['admin', 'ADMIN', 'system_admin'].includes(r)) ?? false);
  const canCoordinate = isAdmin || currentRole === UserRole.ORDER_COORDINATOR;

  // Stats
  const [stats, setStats] = useState({
    pending: 0,
    distributing: 0,
    accepted: 0,
    needsReCoordination: 0,
    expired: 0,
    completed: 0,
  });

  // Load equipment categories AND models for name lookup
  // (orders carry requested_equipment_model_id, not category_id, so we need both)
  const loadCategories = useCallback(async () => {
    try {
      const [catResp, modelResp] = await Promise.all([
        api.get('/equipment-categories'),
        // Endpoint moved out of /suppliers/* (it has nothing to do with a
        // specific supplier — it's the global active equipment-model lookup).
        api.get('/equipment-models/active').catch(() => ({ data: { items: [] } })),
      ]);

      const categoryItems: EquipmentCategory[] = catResp.data?.items || catResp.data || [];
      const catMap: Record<number, string> = {};
      categoryItems.forEach(c => { catMap[c.id] = c.name; });
      setCategories(catMap);

      const modelItems: EquipmentModel[] = modelResp.data?.items || modelResp.data || [];
      const modelMap: Record<number, EquipmentModel> = {};
      modelItems.forEach(m => { modelMap[m.id] = m; });
      setEquipmentModels(modelMap);
    } catch {
      // non-critical
    }
  }, []);

  // Load orders on mount
  useEffect(() => {
    loadCategories();
    loadOrders();
    const interval = setInterval(loadOrders, 30000);
    return () => clearInterval(interval);
  }, []);

  // When the dashboard sends us here with ?focus=<woId>, scroll the row
  // into view and clear the param so a manual refresh later doesn't keep
  // re-focusing on a stale WO. Runs once after the first load completes.
  useEffect(() => {
    if (!focusedFromUrl || loading) return;
    const el = document.querySelector(
      `[data-wo-id="${focusedFromUrl}"]`
    ) as HTMLElement | null;
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
      setSearchParams({}, { replace: true });
    }
  }, [focusedFromUrl, loading]);

  const loadOrders = async () => {
    try {
      setLoading(true);
      setError(null);

      const statuses = [
        'PENDING',
        'DISTRIBUTING',
        'SUPPLIER_ACCEPTED_PENDING_COORDINATOR',
        'NEEDS_RE_COORDINATION',
        'APPROVED_AND_SENT',
        // Expired tokens still belong on the coordinator queue — they need a
        // resend or a manual decision (move-next-supplier).
        'EXPIRED',
      ];
      const allOrders: CoordinationOrder[] = [];

      const fetchErrors: string[] = [];
      for (const status of statuses) {
        try {
          const response = await workOrderService.getWorkOrders(1, 50, { status });
          const items = response.items || response || [];
          items.forEach((order: WorkOrder) => {
            allOrders.push({ ...order } as CoordinationOrder);
          });
        } catch (e) {
          // A single status failing shouldn't block the whole queue, but the
          // coordinator MUST know the list is partial — otherwise WOs simply
          // disappear from the screen with no explanation.
          console.warn(`[OrderCoordination] failed to load status=${status}:`, e);
          fetchErrors.push(status);
        }
      }
      if (fetchErrors.length) {
        console.warn(
          `[OrderCoordination] partial load — missing statuses: ${fetchErrors.join(', ')}`
        );
      }

      // Load invitations - use work-orders endpoint with SUPPLIER_ACCEPTED status
      try {
        const invResp = await api.get('/work-orders', { params: { status: 'SUPPLIER_ACCEPTED_PENDING_COORDINATOR', page_size: 50 } });
        const invItems = invResp.data?.items || invResp.data || [];
        // Map work orders to invitation-like structure for coordinator approval flow
        setInvitations(invItems.map((o: any) => ({ id: o.id, work_order_id: o.id, status: 'ACCEPTED' })));
      } catch (e) {
        console.warn('[OrderCoordination] failed to load supplier-accepted invitations:', e);
      }

      // Re-coordination + expired items go FIRST (most urgent — coordinator
      // owns the decision and the SLA clock is already running)
      const statusOrder: Record<string, number> = {
        'NEEDS_RE_COORDINATION': 0,
        'EXPIRED': 0,
        'PENDING': 1,
        'DISTRIBUTING': 2,
        'SUPPLIER_ACCEPTED_PENDING_COORDINATOR': 3,
        'APPROVED_AND_SENT': 4,
      };
      allOrders.sort((a, b) => (statusOrder[a.status] || 9) - (statusOrder[b.status] || 9));

      setOrders(allOrders);
      setStats({
        pending: allOrders.filter(o => o.status === 'PENDING').length,
        distributing: allOrders.filter(o => o.status === 'DISTRIBUTING').length,
        accepted: allOrders.filter(o => o.status === 'SUPPLIER_ACCEPTED_PENDING_COORDINATOR').length,
        needsReCoordination: allOrders.filter(o => o.status === 'NEEDS_RE_COORDINATION').length,
        expired: allOrders.filter(o => o.status === 'EXPIRED').length,
        completed: allOrders.filter(o => o.status === 'APPROVED_AND_SENT').length,
      });
    } catch (err: any) {
      setError('שגיאה בטעינת הזמנות');
    } finally {
      setLoading(false);
    }
  };

  // Resolve equipment type name. Priority:
  //   1. equipment_type string straight off the order (if BE supplied it)
  //   2. equipment-model lookup (requested_equipment_model_id is the model PK,
  //      NOT a category id — earlier code mixed them up and printed "לא צוין")
  //   3. category name fallback (model.category_id → categories map)
  const resolveEquipmentType = (order: CoordinationOrder): string => {
    if (order.equipment_type) return order.equipment_type;
    const modelId = order.requested_equipment_model_id;
    if (modelId) {
      const model = equipmentModels[modelId];
      if (model?.name) return model.name;
      if (model?.category_id && categories[model.category_id]) {
        return categories[model.category_id];
      }
    }
    return 'לא צוין';
  };

  // Send to supplier
  const handleSendToSupplier = async (orderId: number) => {
    try {
      setProcessing(orderId);
      const resp = await api.post(`/work-orders/${orderId}/send-to-supplier`);
      const data = resp.data;
      if ((window as any).showToast) {
        (window as any).showToast(data.message || 'ההזמנה נשלחה לספק! הקישור תקף ל-3 שעות.', 'success');
      }
      if (data.portal_url) console.info('[Supplier Portal]', data.portal_url);
      await loadOrders();
    } catch (err: any) {
      if ((window as any).showToast) {
        (window as any).showToast(err.response?.data?.detail || 'שגיאה בשליחה לספק', 'error');
      }
    } finally {
      setProcessing(null);
    }
  };

  // Final approval by order coordinator/admin
  const handleCoordinatorApprove = async (orderId: number) => {
    try {
      setProcessing(orderId);
      await api.post(`/work-orders/${orderId}/approve`);
      if ((window as any).showToast) (window as any).showToast('ההזמנה אושרה ונשלחה לביצוע!', 'success');
      await loadOrders();
    } catch (err: any) {
      if ((window as any).showToast) {
        (window as any).showToast(err.response?.data?.detail || 'שגיאה באישור', 'error');
      }
    } finally {
      setProcessing(null);
    }
  };

  // Move to next supplier
  const handleMoveToNextSupplier = async (orderId: number) => {
    try {
      setProcessing(orderId);
      await api.post(`/work-orders/${orderId}/move-to-next-supplier`);
      if ((window as any).showToast) (window as any).showToast('הועבר לספק הבא בסבב', 'success');
      await loadOrders();
    } catch (err: any) {
      if ((window as any).showToast) {
        (window as any).showToast(err.response?.data?.detail || 'שגיאה בהעברה', 'error');
      }
    } finally {
      setProcessing(null);
    }
  };

  // Coordinator-side rejection with mandatory reason (e.g. ספק לא מתאים, שינוי דרישה)
  const handleCoordinatorReject = async (orderId: number) => {
    const reason = prompt('סיבת דחיית ההזמנה (חובה):');
    if (!reason || !reason.trim()) {
      if ((window as any).showToast) (window as any).showToast('חובה לציין סיבה לדחייה', 'warning');
      return;
    }
    try {
      setProcessing(orderId);
      await api.post(`/work-orders/${orderId}/reject`, { reason: reason.trim() });
      if ((window as any).showToast) (window as any).showToast('ההזמנה נדחתה', 'success');
      await loadOrders();
    } catch (err: any) {
      if ((window as any).showToast) {
        (window as any).showToast(err.response?.data?.detail || 'שגיאה בדחייה', 'error');
      }
    } finally {
      setProcessing(null);
    }
  };

  // Resend an EXPIRED invitation — re-issues a fresh portal token (3h TTL) to
  // the current supplier without rotating to the next one.
  const handleResend = async (orderId: number) => {
    try {
      setProcessing(orderId);
      await api.post(`/work-orders/${orderId}/send-to-supplier`);
      if ((window as any).showToast) (window as any).showToast('ההזמנה נשלחה מחדש לספק', 'success');
      await loadOrders();
    } catch (err: any) {
      if ((window as any).showToast) {
        (window as any).showToast(err.response?.data?.detail || 'שגיאה בשליחה מחדש', 'error');
      }
    } finally {
      setProcessing(null);
    }
  };

  // Bulk delete (admin only)
  const handleBulkDelete = async () => {
    if (selectedIds.length === 0) return;
    setBulkDeleting(true);
    let deleted = 0;
    for (const id of selectedIds) {
      try {
        await api.delete(`/work-orders/${id}`);
        deleted++;
      } catch (err: any) {
        console.error(`Failed to delete order ${id}:`, err);
      }
    }
    setBulkDeleting(false);
    setBulkDeleteModal(false);
    setSelectedIds([]);
    if ((window as any).showToast) {
      (window as any).showToast(`נמחקו ${deleted} מתוך ${selectedIds.length} הזמנות`, deleted === selectedIds.length ? 'success' : 'warning');
    }
    await loadOrders();
  };

  const toggleSelect = (id: number) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  const toggleSelectAll = () => {
    if (selectedIds.length === filteredOrders.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(filteredOrders.map(o => o.id));
    }
  };

  // Cancel order (admin only)
  const handleCancelOrder = async (orderId: number) => {
    try {
      setProcessing(orderId);
      await api.post(`/work-orders/${orderId}/cancel`, null, { params: { notes: 'בוטל על ידי מנהל מערכת' } });
      if ((window as any).showToast) (window as any).showToast('ההזמנה בוטלה בהצלחה', 'success');
      setCancelModal(null);
      await loadOrders();
    } catch (err: any) {
      if ((window as any).showToast) {
        (window as any).showToast(err.response?.data?.detail || 'שגיאה בביטול ההזמנה', 'error');
      }
    } finally {
      setProcessing(null);
    }
  };

  // Log call
  const handleLogCall = async (orderId: number) => {
    const note = prompt('הערות לשיחה:');
    if (note !== null) {
      try {
        setProcessing(orderId);
        await api.post('/work-order-coordination-logs', {
          work_order_id: orderId,
          action_type: 'CALL',
          note: note || 'שיחה עם ספק'
        });
        if ((window as any).showToast) (window as any).showToast('השיחה תועדה', 'success');
        await loadOrders();
      } catch {} finally {
        setProcessing(null);
      }
    }
  };

  // Filter & search
  const filteredOrders = orders.filter(order => {
    const statusMatch = filterStatus === 'all' || order.status === filterStatus;
    const search = searchTerm.toLowerCase();
    const searchMatch = !search || (
      String(order.order_number || '').includes(search) ||
      (order.project_name || '').toLowerCase().includes(search) ||
      (order.supplier_name || '').toLowerCase().includes(search) ||
      resolveEquipmentType(order).includes(search)
    );
    return statusMatch && searchMatch;
  });

  // Status badge — labels and tones live in `src/strings`, never hard-coded
  // here. Adding/renaming a status only ever requires editing `statuses.ts`.
  const getStatusBadge = (status: string) => {
    const label = getWorkOrderStatusLabel(status);
    const cls = toneClasses(getWorkOrderStatusTone(status));
    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${cls.bg} ${cls.text} ${cls.border}`}>
        <span className={`w-1.5 h-1.5 rounded-full ${cls.dot}`} />
        {label}
      </span>
    );
  };

  const getSelectionTag = (order: CoordinationOrder) => {
    if (order.is_forced_selection) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-700 border border-orange-200">
          <Zap className="w-3 h-3" />
          אילוץ
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700 border border-green-200">
        <RotateCcw className="w-3 h-3" />
        סבב הוגן
      </span>
    );
  };

  const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    if (d.getFullYear() <= 1970) return '—';
    return d.toLocaleDateString('he-IL', { day: '2-digit', month: '2-digit', year: '2-digit' });
  };

  if (loading && orders.length === 0) {
    return <UnifiedLoader size="full" message="טוען תיאומים..." />;
  }

  if (!canCoordinate) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6" dir="rtl">
        <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-6 max-w-md text-center">
          <AlertTriangle className="w-10 h-10 text-amber-500 mx-auto mb-3" />
          <h2 className="text-lg font-bold text-gray-900 mb-2">אין גישה למסך זה</h2>
          <p className="text-sm text-gray-600">המסך מיועד למתאם הזמנות או למנהל מערכת בלבד.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pt-4 sm:pt-6 pb-10 px-3 md:px-6" dir="rtl">
      <div className="max-w-6xl mx-auto">

        {/* ===== HEADER ===== */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 sm:mb-6">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <ClipboardList className="w-5 h-5 sm:w-6 sm:h-6 text-green-600 flex-shrink-0" />
              <h1 className="text-xl sm:text-2xl font-bold text-gray-900 truncate">תיאום הזמנות</h1>
            </div>
            <p className="hidden sm:block text-sm text-gray-500 mt-0.5 mr-8">ניהול ותיאום הזמנות עבודה מול ספקים — סבב הוגן ואילוצים</p>
          </div>
          <div className="flex items-center gap-2 flex-wrap self-stretch sm:self-auto">
            {/* Bulk delete button - admin only, shown when items selected */}
            {isAdmin && selectedIds.length > 0 && (
              <button
                onClick={() => setBulkDeleteModal(true)}
                className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-3 sm:px-4 py-2.5 bg-red-600 text-white rounded-xl shadow-sm hover:bg-red-700 transition-colors text-sm font-semibold"
              >
                <Trash2 className="w-4 h-4" />
                <span className="sm:hidden">מחק ({selectedIds.length})</span>
                <span className="hidden sm:inline">מחק נבחרים ({selectedIds.length})</span>
              </button>
            )}
            <button
              onClick={loadOrders}
              disabled={loading}
              className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-3 sm:px-4 py-2.5 bg-white border border-gray-200 rounded-xl shadow-sm hover:bg-gray-50 transition-colors text-sm font-medium text-gray-700"
            >
              <RefreshCcw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              רענן
            </button>
          </div>
        </div>

        {/* ===== STATS ===== */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-2 sm:gap-3 mb-4 sm:mb-6">
          {[
            { key: 'all',       label: 'סה"כ',             shortLabel: 'סה"כ',          count: orders.length, color: 'border-gray-400',   icon: <ClipboardList className="w-4 h-4 sm:w-5 sm:h-5 text-gray-400" /> },
            { key: 'NEEDS_RE_COORDINATION', label: 'דורש החלטה — סוג כלי שגוי', shortLabel: 'דורש החלטה', count: stats.needsReCoordination, color: 'border-red-500', icon: <AlertTriangle className="w-4 h-4 sm:w-5 sm:h-5 text-red-500" /> },
            { key: 'EXPIRED',   label: 'פג תוקף',           shortLabel: 'פג תוקף',        count: stats.expired, color: 'border-orange-400', icon: <AlertTriangle className="w-4 h-4 sm:w-5 sm:h-5 text-orange-500" /> },
            { key: 'PENDING',   label: 'ממתינות לשליחה',    shortLabel: 'ממתינות',        count: stats.pending, color: 'border-yellow-400', icon: <Clock className="w-4 h-4 sm:w-5 sm:h-5 text-yellow-500" /> },
            { key: 'DISTRIBUTING', label: 'בהפצה לספקים',   shortLabel: 'בהפצה',          count: stats.distributing, color: 'border-blue-400', icon: <Send className="w-4 h-4 sm:w-5 sm:h-5 text-blue-500" /> },
            { key: 'SUPPLIER_ACCEPTED_PENDING_COORDINATOR', label: 'ספק אישר — ממתין', shortLabel: 'ספק אישר', count: stats.accepted, color: 'border-purple-400', icon: <CheckCircle className="w-4 h-4 sm:w-5 sm:h-5 text-purple-500" /> },
          ].map(stat => (
            <button
              key={stat.key}
              onClick={() => setFilterStatus(stat.key)}
              className={`bg-white rounded-xl shadow-sm p-2.5 sm:p-4 border-r-4 ${stat.color} text-right hover:shadow-md transition-shadow min-w-0 ${filterStatus === stat.key ? 'ring-2 ring-offset-1 ring-green-500' : ''}`}
            >
              <div className="flex items-center justify-between mb-0.5 sm:mb-1">
                {stat.icon}
              </div>
              <p className="text-xl sm:text-2xl font-bold text-gray-900 leading-none">{stat.count}</p>
              <p className="text-[11px] sm:text-xs text-gray-500 mt-1 leading-tight break-words">
                <span className="sm:hidden">{stat.shortLabel}</span>
                <span className="hidden sm:inline">{stat.label}</span>
              </p>
            </button>
          ))}
        </div>

        {/* ===== SEARCH + FILTER ===== */}
        <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 mb-4 sm:mb-5">
          <div className="relative flex-1">
            <Search className="absolute top-1/2 -translate-y-1/2 right-3 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="חיפוש: מספר / פרויקט / ספק / ציוד"
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="w-full pr-9 pl-3 py-2.5 text-sm border border-gray-200 rounded-xl bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>
          <div className="flex gap-2 overflow-x-auto pb-1 sm:pb-0 -mx-3 px-3 sm:mx-0 sm:px-0 tabs-row">
            {[
              { key: 'all', label: 'הכל' },
              { key: 'NEEDS_RE_COORDINATION', label: 'דורש החלטה' },
              { key: 'EXPIRED', label: 'פג תוקף' },
              { key: 'PENDING', label: 'ממתינות' },
              { key: 'DISTRIBUTING', label: 'בהפצה' },
              { key: 'SUPPLIER_ACCEPTED_PENDING_COORDINATOR', label: 'ספק אישר' },
              { key: 'APPROVED_AND_SENT', label: 'הושלמו' },
            ].map(tab => (
              <button
                key={tab.key}
                onClick={() => setFilterStatus(tab.key)}
                className={`px-3 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                  filterStatus === tab.key
                    ? 'bg-green-600 text-white shadow-sm'
                    : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* ===== ERROR ===== */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-5 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0" />
            <span className="text-red-700 text-sm">{error}</span>
            <button onClick={loadOrders} className="mr-auto text-red-600 hover:text-red-700 text-sm font-medium underline">
              נסה שוב
            </button>
          </div>
        )}

        {/* ===== EMPTY STATE ===== */}
        {filteredOrders.length === 0 && !loading ? (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-16 text-center">
            <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">אין הזמנות הממתינות לתיאום</h3>
            <p className="text-gray-500 text-sm">כל ההזמנות כבר תואמו או אושרו</p>
          </div>
        ) : (

        /* ===== SELECT ALL + ORDER CARDS ===== */
        <>
        {isAdmin && filteredOrders.length > 0 && (
          <div className="flex items-center gap-3 mb-2 px-1">
            <button
              onClick={toggleSelectAll}
              className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
            >
              {selectedIds.length === filteredOrders.length && filteredOrders.length > 0
                ? <CheckSquare className="w-4 h-4 text-red-600" />
                : <Square className="w-4 h-4 text-gray-400" />
              }
              {selectedIds.length === filteredOrders.length && filteredOrders.length > 0
                ? 'בטל בחירת הכל'
                : 'בחר הכל'
              }
            </button>
            {selectedIds.length > 0 && (
              <span className="text-xs text-gray-500">{selectedIds.length} נבחרו</span>
            )}
          </div>
        )}
        <div className="space-y-3">
          {filteredOrders.map((order) => {
            const isExpanded = expandedOrder === order.id;
            const equipmentType = resolveEquipmentType(order);
            const borderColor =
              order.is_urgent
                ? 'border-red-300'
                : order.status === 'SUPPLIER_ACCEPTED_PENDING_COORDINATOR'
                  ? 'border-purple-300'
                  : order.status === 'DISTRIBUTING'
                    ? 'border-blue-200'
                    : 'border-gray-200';

            const isSelected = selectedIds.includes(order.id);
            return (
              <div
                key={order.id}
                data-wo-id={order.id}
                className={`bg-white rounded-2xl shadow-sm border-2 overflow-hidden transition-all hover:shadow-md ${isSelected ? 'border-red-400 bg-red-50/20' : borderColor}`}
              >
                {/* ---- Card Header (always visible) ---- */}
                <div
                  className="px-3 sm:px-4 py-3 cursor-pointer"
                  onClick={() => setExpandedOrder(isExpanded ? null : order.id)}
                >
                  {/* Row 1: Checkbox (admin) + Order number + chevron + status + tags
                       On mobile: anchor row holds checkbox/#/chevron; badges wrap below.
                       On desktop: everything inline. */}
                  <div className="flex items-start gap-2 mb-2">
                    {isAdmin && (
                      <button
                        onClick={e => { e.stopPropagation(); toggleSelect(order.id); }}
                        className="flex-shrink-0 p-0.5 hover:opacity-70 transition-opacity"
                        title={isSelected ? 'בטל בחירה' : 'בחר להזמנה'}
                      >
                        {isSelected
                          ? <CheckSquare className="w-5 h-5 text-red-600" />
                          : <Square className="w-5 h-5 text-gray-400" />
                        }
                      </button>
                    )}
                    <span className="text-xs text-gray-400 font-mono pt-1 flex-shrink-0">#{order.order_number}</span>
                    <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 flex-1 min-w-0">
                      {getStatusBadge(order.status)}
                      {getSelectionTag(order)}
                      {order.is_urgent && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-red-100 text-red-700 rounded-full text-xs font-medium animate-pulse">
                          <AlertTriangle className="w-3 h-3" />
                          דחוף!
                        </span>
                      )}
                      {order.time_remaining_display && (
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                          order.is_urgent ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'
                        }`}>
                          <Timer className="w-3 h-3" />
                          {order.time_remaining_display}
                        </span>
                      )}
                    </div>
                    <div className="flex-shrink-0 pt-1">
                      {isExpanded
                        ? <ChevronUp className="w-4 h-4 text-gray-400" />
                        : <ChevronDown className="w-4 h-4 text-gray-400" />
                      }
                    </div>
                  </div>

                  {/* Row 2: Main info — single column on phones for readability,
                       4-up on desktop. */}
                  <div className="grid grid-cols-1 sm:grid-cols-4 gap-x-4 gap-y-1.5 text-sm">
                    {/* Project Area Region breadcrumb */}
                    <div className="flex items-start gap-1.5 text-gray-700 sm:col-span-1 min-w-0">
                      <Building2 className="w-3.5 h-3.5 text-gray-400 flex-shrink-0 mt-0.5" />
                      <div className="min-w-0 flex-1">
                        <span className="font-medium block truncate">{order.project_name || '—'}</span>
                        {(order.area_name || order.region_name) && (
                          <span className="text-xs text-gray-400 block truncate">
                            {[order.region_name, order.area_name].filter(Boolean).join(' › ')}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-1.5 text-gray-700 min-w-0">
                      <Truck className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                      <span className="truncate">{equipmentType}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-gray-700 min-w-0">
                      <User className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                      {order.supplier_name
                        ? <span className="truncate text-green-700 font-medium">{order.supplier_name}</span>
                        : <span className="truncate text-gray-400 italic">טרם נבחר</span>
                      }
                    </div>
                    <div className="flex items-center gap-1.5 text-gray-700 min-w-0">
                      <Calendar className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                      <span className="truncate">{formatDate(order.work_start_date)} – {formatDate(order.work_end_date)}</span>
                    </div>
                  </div>
                </div>

                {/* ---- Expanded Details ---- */}
                {isExpanded && (
                  <div className="border-t border-gray-100 bg-gray-50/50 px-3 sm:px-4 py-3 sm:py-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-5">

                      {/* Details */}
                      <div>
                        <h4 className="text-sm font-semibold text-gray-700 mb-3">פרטי ההזמנה</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex gap-2">
                            <Truck className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                            <div>
                              <span className="text-gray-500">סוג ציוד: </span>
                              <span className="font-medium">{equipmentType}</span>
                              {(order as any).equipment_license_plate && (
                                <span className="mr-2 text-green-700 font-mono font-bold text-sm">
                                  | לוחית: {(order as any).equipment_license_plate}
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <Calendar className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                            <div>
                              <span className="text-gray-500">תאריכי עבודה: </span>
                              <span className="font-medium">
                                {formatDate(order.work_start_date)} – {formatDate(order.work_end_date)}
                              </span>
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <User className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                            <div>
                              <span className="text-gray-500">ספק: </span>
                              {order.supplier_name
                                ? <span className="font-medium text-green-700">{order.supplier_name}</span>
                                : <span className="text-gray-400 italic">טרם נבחר</span>
                              }
                            </div>
                          </div>
                          {(order.area_name || order.region_name) && (
                            <div className="flex gap-2">
                              <Building2 className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                              <div>
                                <span className="text-gray-500">מיקום: </span>
                                <span className="font-medium">
                                  {[order.region_name, order.area_name, order.project_name].filter(Boolean).join(' › ')}
                                </span>
                              </div>
                            </div>
                          )}
                          {order.description && (
                            <div className="mt-2 p-2.5 bg-white border border-gray-200 rounded-lg text-gray-600 text-xs leading-relaxed">
                              {order.description}
                            </div>
                          )}
                          {order.constraint_notes && (
                            <div className="mt-2 p-2.5 bg-orange-50 border border-orange-200 rounded-lg text-orange-800 text-xs">
                              <span className="font-medium">סיבת אילוץ: </span>
                              {order.constraint_notes}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Actions */}
                      <div>
                        <h4 className="text-sm font-semibold text-gray-700 mb-3">פעולות</h4>
                        {/* Mobile: 2-col for short utility buttons, primary actions span both. */}
                        <div className="grid grid-cols-2 gap-2">

                          <button
                            onClick={() => navigate(`/work-orders/${order.id}`)}
                            className="flex items-center justify-center gap-2 px-3 py-2.5 bg-white border border-gray-200 text-gray-700 rounded-xl hover:bg-gray-50 transition-colors text-sm font-medium min-h-[44px]"
                          >
                            <Eye className="w-4 h-4" />
                            <span className="truncate">צפה בפרטים</span>
                          </button>

                          <button
                            onClick={() => handleLogCall(order.id)}
                            disabled={processing === order.id}
                            className="flex items-center justify-center gap-2 px-3 py-2.5 bg-purple-50 border border-purple-200 text-purple-700 rounded-xl hover:bg-purple-100 transition-colors text-sm font-medium disabled:opacity-50 min-h-[44px]"
                          >
                            <Phone className="w-4 h-4" />
                            <span className="truncate">תעד שיחה</span>
                          </button>

                          {order.status === 'PENDING' && (
                            <button
                              onClick={() => handleSendToSupplier(order.id)}
                              disabled={processing === order.id}
                              className="col-span-2 flex items-center justify-center gap-2 px-4 py-3 bg-green-600 text-white rounded-xl hover:bg-green-700 transition-colors text-sm font-semibold disabled:opacity-50 shadow-sm"
                            >
                              {processing === order.id
                                ? <Loader2 className="w-4 h-4 animate-spin" />
                                : <Send className="w-4 h-4" />
                              }
                              שלח לספק (סבב הוגן)
                            </button>
                          )}

                          {order.status === 'DISTRIBUTING' && (
                            <button
                              onClick={() => handleMoveToNextSupplier(order.id)}
                              disabled={processing === order.id}
                              className="col-span-2 flex items-center justify-center gap-2 px-4 py-2.5 bg-orange-50 border border-orange-200 text-orange-700 rounded-xl hover:bg-orange-100 transition-colors text-sm font-medium disabled:opacity-50"
                            >
                              {processing === order.id
                                ? <Loader2 className="w-4 h-4 animate-spin" />
                                : <ArrowLeftRight className="w-4 h-4" />
                              }
                              העבר לספק הבא
                            </button>
                          )}

                          {order.status === 'SUPPLIER_ACCEPTED_PENDING_COORDINATOR' && (
                            <>
                              <button
                                onClick={() => handleCoordinatorApprove(order.id)}
                                disabled={processing === order.id}
                                className="col-span-2 flex items-center justify-center gap-2 px-4 py-3 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors text-sm font-semibold disabled:opacity-50 shadow-sm animate-pulse"
                              >
                                {processing === order.id
                                  ? <Loader2 className="w-4 h-4 animate-spin" />
                                  : <CheckCircle className="w-4 h-4" />
                                }
                                אשר ושלח לביצוע
                              </button>
                              <button
                                onClick={() => handleCoordinatorReject(order.id)}
                                disabled={processing === order.id}
                                className="col-span-2 flex items-center justify-center gap-2 px-4 py-2.5 bg-red-50 border border-red-200 text-red-700 rounded-xl hover:bg-red-100 transition-colors text-sm font-medium disabled:opacity-50"
                              >
                                <XCircle className="w-4 h-4" />
                                דחה (עם סיבה)
                              </button>
                            </>
                          )}

                          {order.status === 'EXPIRED' && (
                            <>
                              <div className="col-span-2 flex items-start gap-2 px-3 py-2.5 bg-orange-50 border border-orange-200 text-orange-800 rounded-xl text-sm">
                                <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                                <div className="flex-1">
                                  <p className="font-semibold">פג תוקף הקישור לספק</p>
                                  <p className="text-xs mt-0.5 leading-snug">
                                    אפשר לשלוח שוב לאותו ספק או להעביר לספק הבא בתור.
                                  </p>
                                </div>
                              </div>
                              <button
                                onClick={() => handleResend(order.id)}
                                disabled={processing === order.id}
                                className="col-span-2 sm:col-span-1 flex items-center justify-center gap-2 px-3 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors text-sm font-semibold disabled:opacity-50 min-h-[44px]"
                              >
                                {processing === order.id
                                  ? <Loader2 className="w-4 h-4 animate-spin" />
                                  : <Send className="w-4 h-4" />
                                }
                                <span className="truncate">שלח שוב לאותו ספק</span>
                              </button>
                              <button
                                onClick={() => handleMoveToNextSupplier(order.id)}
                                disabled={processing === order.id}
                                className="col-span-2 sm:col-span-1 flex items-center justify-center gap-2 px-3 py-2.5 bg-orange-50 border border-orange-200 text-orange-700 rounded-xl hover:bg-orange-100 transition-colors text-sm font-medium disabled:opacity-50 min-h-[44px]"
                              >
                                <ArrowLeftRight className="w-4 h-4" />
                                <span className="truncate">לספק הבא</span>
                              </button>
                            </>
                          )}

                          {order.status === 'APPROVED_AND_SENT' && (
                            <div className="col-span-2 flex items-center gap-2 px-4 py-2.5 bg-green-50 border border-green-200 text-green-700 rounded-xl text-sm font-medium">
                              <CheckCircle className="w-4 h-4 flex-shrink-0" />
                              הזמנה אושרה ונשלחה לביצוע
                            </div>
                          )}

                          {order.status === 'NEEDS_RE_COORDINATION' && (
                            <>
                              <div className="col-span-2 flex items-start gap-2 px-3 py-2.5 bg-red-50 border border-red-200 text-red-800 rounded-xl text-sm">
                                <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                                <div className="flex-1">
                                  <p className="font-semibold">סוג כלי שגוי דווח בשטח</p>
                                  <p className="text-xs mt-0.5 leading-snug">
                                    מנהל העבודה ניסה לקלוט כלי שאינו תואם להזמנה.
                                    קליטה בשטח חסומה. נדרשת החלטה: הפצה מחדש לספק חדש,
                                    אישור חריג (אדמין), או ביטול.
                                  </p>
                                </div>
                              </div>
                              <button
                                onClick={() => handleSendToSupplier(order.id)}
                                disabled={processing === order.id}
                                className="col-span-2 flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors text-sm font-semibold disabled:opacity-50 shadow-sm"
                              >
                                {processing === order.id
                                  ? <Loader2 className="w-4 h-4 animate-spin" />
                                  : <Send className="w-4 h-4" />
                                }
                                הפץ מחדש (סבב הוגן — ספק אחר)
                              </button>
                            </>
                          )}

                          {/* Admin-only cancel button */}
                          {isAdmin && order.status !== 'APPROVED_AND_SENT' && (
                            <button
                              onClick={() => setCancelModal({ orderId: order.id, orderNumber: order.order_number || order.id })}
                              disabled={processing === order.id}
                              className="col-span-2 flex items-center justify-center gap-2 px-3 py-2.5 bg-red-50 border border-red-200 text-red-700 rounded-xl hover:bg-red-100 transition-colors text-sm font-medium disabled:opacity-50 mt-1"
                            >
                              <Trash2 className="w-4 h-4" />
                              בטל הזמנה (מנהל)
                            </button>
                          )}
                        </div>

                        {/* Timer info */}
                        {(order.status === 'DISTRIBUTING') && (
                          <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-xl">
                            <div className="flex items-start gap-2 text-sm">
                              <Timer className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                              <div>
                                <p className="font-medium text-amber-800">טיימר 3 שעות</p>
                                <p className="text-amber-700 text-xs mt-0.5">
                                  אם הספק לא מגיב תוך 3 שעות, ההזמנה עוברת אוטומטית לספק הבא בסבב.
                                </p>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
        </>
        )}

        {/* Loading overlay — sits above iOS home-indicator on phones */}
        {loading && orders.length > 0 && (
          <div
            className="fixed left-1/2 -translate-x-1/2 flex items-center gap-2 bg-white border border-gray-200 rounded-full px-4 py-2 shadow-lg text-sm text-gray-600 z-30"
            style={{ bottom: 'max(1.5rem, calc(env(safe-area-inset-bottom) + 1rem))' }}
          >
            <Loader2 className="w-4 h-4 animate-spin text-green-600" />
            מרענן...
          </div>
        )}
      </div>

      {/* Bulk Delete Modal - Admin Only */}
      {bulkDeleteModal && isAdmin && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-3 sm:p-4" dir="rtl">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-5 sm:p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-red-100 rounded-full">
                <Trash2 className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900">מחיקת הזמנות מרובות</h3>
                <p className="text-xs text-red-500 font-medium">פעולה זו לא ניתנת לביטול</p>
              </div>
            </div>
            <p className="text-gray-700 mb-2">
              האם למחוק <span className="font-bold text-red-700">{selectedIds.length}</span> הזמנות?
            </p>
            <div className="mb-5 p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">
              כל ההזמנות שנבחרו יסומנו כמחוקות ולא יופיעו יותר במערכת.
              פעולת המחיקה תתועד ביומן הפעילות.
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setBulkDeleteModal(false)}
                disabled={bulkDeleting}
                className="flex-1 px-4 py-2.5 border border-gray-200 rounded-xl text-gray-700 hover:bg-gray-50 font-medium disabled:opacity-50"
              >
                ביטול
              </button>
              <button
                onClick={handleBulkDelete}
                disabled={bulkDeleting}
                className="flex-1 px-4 py-2.5 bg-red-600 text-white rounded-xl hover:bg-red-700 font-semibold disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {bulkDeleting ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> מוחק...</>
                ) : (
                  <><Trash2 className="w-4 h-4" /> כן, מחק {selectedIds.length} הזמנות</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Cancel Confirmation Modal */}
      {cancelModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-3 sm:p-4" dir="rtl">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-5 sm:p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-red-100 rounded-full">
                <XCircle className="w-6 h-6 text-red-600" />
              </div>
              <h3 className="text-lg font-bold text-gray-900">ביטול הזמנה</h3>
            </div>
            <p className="text-gray-600 mb-2">
              האם לבטל את הזמנה <span className="font-bold text-gray-900">#{cancelModal.orderNumber}</span>?
            </p>
            <p className="text-sm text-red-600 mb-6">
              פעולה זו תשנה את סטטוס ההזמנה ל-CANCELLED ולא ניתן לבטל אותה.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setCancelModal(null)}
                className="flex-1 px-4 py-2.5 border border-gray-200 rounded-xl text-gray-700 hover:bg-gray-50 font-medium"
              >
                חזור
              </button>
              <button
                onClick={() => handleCancelOrder(cancelModal.orderId)}
                disabled={processing === cancelModal.orderId}
                className="flex-1 px-4 py-2.5 bg-red-600 text-white rounded-xl hover:bg-red-700 font-medium disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {processing === cancelModal.orderId
                  ? <Loader2 className="w-4 h-4 animate-spin" />
                  : <Trash2 className="w-4 h-4" />
                }
                כן, בטל הזמנה
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OrderCoordination;
