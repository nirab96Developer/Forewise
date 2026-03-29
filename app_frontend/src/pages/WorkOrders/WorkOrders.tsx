
// src/pages/WorkOrders/WorkOrders.tsx
import React, { useState, useEffect, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Plus, Search, Eye, Clock, User, AlertCircle,
  Truck, ClipboardList
} from 'lucide-react';
import workOrderService, { WorkOrder, WorkOrderFilters } from '../../services/workOrderService';
import UnifiedLoader from '../../components/common/UnifiedLoader';
import { getUserRole, normalizeRole, UserRole } from '../../utils/permissions';

const STATUS_CONFIG: Record<string, { label: string; bg: string; text: string; dot: string }> = {
  PENDING:                                { label: 'ממתין לתיאום',     bg: 'bg-amber-50',  text: 'text-amber-700',  dot: 'bg-amber-400' },
  DISTRIBUTING:                           { label: 'בהפצה לספקים',    bg: 'bg-blue-50',   text: 'text-blue-700',   dot: 'bg-blue-400' },
  SUPPLIER_ACCEPTED_PENDING_COORDINATOR:  { label: 'ספק אישר — ממתין למתאם', bg: 'bg-indigo-50', text: 'text-indigo-700', dot: 'bg-indigo-400' },
  APPROVED_AND_SENT:                      { label: 'מאושר — ניתן לדווח', bg: 'bg-green-50', text: 'text-green-700', dot: 'bg-green-500' },
  COMPLETED:                              { label: 'הושלם',           bg: 'bg-gray-100',  text: 'text-gray-600',   dot: 'bg-gray-400' },
  REJECTED:                               { label: 'נדחה',            bg: 'bg-red-50',    text: 'text-red-700',    dot: 'bg-red-500' },
  CANCELLED:                              { label: 'בוטל',            bg: 'bg-red-50',    text: 'text-red-600',    dot: 'bg-red-400' },
  EXPIRED:                                { label: 'פג תוקף',         bg: 'bg-orange-50', text: 'text-orange-700', dot: 'bg-orange-400' },
  STOPPED:                                { label: 'הופסק',           bg: 'bg-gray-100',  text: 'text-gray-700',   dot: 'bg-gray-500' },
};

const getStatus = (s: string) => STATUS_CONFIG[(s || '').toUpperCase()] || { label: s || '—', bg: 'bg-gray-100', text: 'text-gray-600', dot: 'bg-gray-300' };

const WorkOrders: React.FC = () => {
  const navigate = useNavigate();
  const _role = normalizeRole(getUserRole());
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        setLoading(true);
        setError(null);
        const filters: WorkOrderFilters = { status: filterStatus !== 'all' ? filterStatus : undefined };
        const res = await workOrderService.getWorkOrders(1, 100, filters);
        if (!cancelled) setWorkOrders(res?.items || res?.data || res || []);
      } catch {
        if (!cancelled) { setError('שגיאה בטעינת הזמנות.'); setWorkOrders([]); }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [filterStatus]);

  // Stats
  const stats = useMemo(() => {
    const all = workOrders;
    return {
      total: all.length,
      pending: all.filter(o => (o.status || '').toUpperCase() === 'PENDING').length,
      distributing: all.filter(o => ['DISTRIBUTING', 'SUPPLIER_ACCEPTED_PENDING_COORDINATOR'].includes((o.status || '').toUpperCase())).length,
      approved: all.filter(o => (o.status || '').toUpperCase() === 'APPROVED_AND_SENT').length,
      terminal: all.filter(o => ['EXPIRED', 'STOPPED', 'REJECTED', 'CANCELLED', 'COMPLETED'].includes((o.status || '').toUpperCase())).length,
    };
  }, [workOrders]);

  // Search filter
  const filtered = useMemo(() => {
    if (!searchTerm.trim()) return workOrders;
    const q = searchTerm.toLowerCase();
    return workOrders.filter(o =>
      (o.title || '').toLowerCase().includes(q) ||
      (o.description || '').toLowerCase().includes(q) ||
      (o.project_name || '').toLowerCase().includes(q) ||
      (o.supplier_name || '').toLowerCase().includes(q) ||
      (o.equipment_type || '').toLowerCase().includes(q) ||
      String(o.order_number || '').includes(q)
    );
  }, [workOrders, searchTerm]);

  const formatDate = (d: string) => d ? new Date(d).toLocaleDateString('he-IL') : '—';

  if (loading) return <UnifiedLoader size="full" />;

  return (
    <div className="min-h-screen bg-gray-50" dir="rtl">
      {/* Header */}
      <div className="bg-white border-b shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
                <ClipboardList className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">הזמנות עבודה</h1>
                <p className="text-sm text-gray-500">{stats.total} הזמנות</p>
              </div>
            </div>
            {[UserRole.ADMIN, UserRole.AREA_MANAGER, UserRole.WORK_MANAGER].includes(_role) && (
              <Link to="/projects"
                className="flex items-center gap-2 px-4 py-2.5 bg-green-600 hover:bg-green-700 text-white rounded-xl text-sm font-medium shadow-sm transition-colors min-h-[44px]">
                <Plus className="w-4 h-4" /> הזמנה חדשה
              </Link>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-5">

        {/* Stats Row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
          <button onClick={() => setFilterStatus('PENDING')}
            className={`p-3 rounded-xl border text-center transition-all ${filterStatus === 'PENDING' ? 'border-amber-400 bg-amber-50 ring-2 ring-amber-200' : 'border-gray-200 bg-white hover:border-amber-200'}`}>
            <div className="text-2xl font-bold text-amber-600">{stats.pending}</div>
            <div className="text-xs text-gray-500 mt-0.5">ממתינים</div>
          </button>
          <button onClick={() => setFilterStatus('DISTRIBUTING')}
            className={`p-3 rounded-xl border text-center transition-all ${filterStatus === 'DISTRIBUTING' ? 'border-blue-400 bg-blue-50 ring-2 ring-blue-200' : 'border-gray-200 bg-white hover:border-blue-200'}`}>
            <div className="text-2xl font-bold text-blue-600">{stats.distributing}</div>
            <div className="text-xs text-gray-500 mt-0.5">בתיאום</div>
          </button>
          <button onClick={() => setFilterStatus('APPROVED_AND_SENT')}
            className={`p-3 rounded-xl border text-center transition-all ${filterStatus === 'APPROVED_AND_SENT' ? 'border-green-400 bg-green-50 ring-2 ring-green-200' : 'border-gray-200 bg-white hover:border-green-200'}`}>
            <div className="text-2xl font-bold text-green-600">{stats.approved}</div>
            <div className="text-xs text-gray-500 mt-0.5">מאושרים</div>
          </button>
          <button onClick={() => setFilterStatus('all')}
            className={`p-3 rounded-xl border text-center transition-all ${filterStatus === 'all' ? 'border-gray-400 bg-gray-50 ring-2 ring-gray-200' : 'border-gray-200 bg-white hover:border-gray-300'}`}>
            <div className="text-2xl font-bold text-gray-700">{stats.total}</div>
            <div className="text-xs text-gray-500 mt-0.5">סה"כ</div>
          </button>
        </div>

        {/* Search */}
        <div className="relative mb-5">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input type="text" value={searchTerm} onChange={e => setSearchTerm(e.target.value)}
            placeholder="חיפוש לפי פרויקט, ספק, ציוד..."
            className="w-full pr-10 pl-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-blue-200 focus:border-blue-400"
            style={{ fontSize: '16px' }} />
        </div>

        {/* Error */}
        {error && (
          <div className="mb-5 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-700 text-sm">{error}</span>
            <button onClick={() => window.location.reload()} className="mr-auto text-red-600 underline text-sm">נסה שוב</button>
          </div>
        )}

        {/* Orders List */}
        {filtered.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
            <ClipboardList className="w-14 h-14 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 mb-4">לא נמצאו הזמנות</p>
            {filterStatus !== 'all' && (
              <button onClick={() => { setFilterStatus('all'); setSearchTerm(''); }}
                className="text-blue-600 text-sm underline">נקה מסננים</button>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {filtered.map(wo => {
              const st = getStatus(wo.status);
              return (
                <div key={wo.id}
                  onClick={() => navigate(`/work-orders/${wo.id}`)}
                  className="bg-white rounded-xl border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer">
                  
                  {/* Top row: status + order number + date */}
                  <div className="flex items-center justify-between px-4 pt-3 pb-2">
                    <div className="flex items-center gap-2">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${st.bg} ${st.text}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${st.dot}`} />
                        {st.label}
                      </span>
                      {wo.order_number && (
                        <span className="text-xs text-gray-400 font-mono">#{wo.order_number}</span>
                      )}
                    </div>
                    <span className="text-xs text-gray-400">{formatDate(wo.work_start_date)}</span>
                  </div>

                  {/* Content */}
                  <div className="px-4 pb-3">
                    {/* Project + Equipment type */}
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div>
                        <div className="font-semibold text-gray-900 text-sm">
                          {wo.project_name || wo.title || `הזמנה #${wo.id}`}
                        </div>
                        {wo.equipment_type && (
                          <div className="text-xs text-gray-500 mt-0.5 flex items-center gap-1">
                            <Truck className="w-3 h-3" />
                            {wo.equipment_type}
                          </div>
                        )}
                      </div>
                      <button onClick={e => { e.stopPropagation(); navigate(`/work-orders/${wo.id}`); }}
                        className="flex items-center gap-1 px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg text-xs font-medium transition-colors min-h-[36px]">
                        <Eye className="w-3.5 h-3.5" /> צפייה
                      </button>
                    </div>

                    {/* Info row */}
                    <div className="flex items-center gap-4 text-xs text-gray-500 flex-wrap">
                      {wo.supplier_name && (
                        <span className="flex items-center gap-1">
                          <User className="w-3 h-3" />
                          {wo.supplier_name}
                        </span>
                      )}
                      {wo.estimated_hours && wo.estimated_hours > 0 && (
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {wo.estimated_hours} שעות
                        </span>
                      )}
                      {(wo as any).equipment_license_plate && (
                        <span className="flex items-center gap-1 font-mono bg-gray-100 px-1.5 py-0.5 rounded">
                          {(wo as any).equipment_license_plate}
                        </span>
                      )}
                      {wo.description && (
                        <span className="text-gray-400 truncate max-w-[200px]">
                          {wo.description}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkOrders;
