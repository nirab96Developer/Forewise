// @ts-nocheck
// src/pages/WorkOrders/OrderCoordination.tsx
// מסך תיאום הזמנות - Order Coordination
import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { 
  RefreshCcw, Clock, CheckCircle, AlertTriangle, Phone, Send, 
  ArrowLeftRight, Eye, Loader2, User, Truck, Calendar,
  Timer, ChevronDown, ChevronUp, MessageSquare
} from "lucide-react";
import workOrderService, { WorkOrder } from "../../services/workOrderService";
import api from "../../services/api";

interface CoordinationOrder extends WorkOrder {
  time_remaining_minutes?: number;
  time_remaining_display?: string;
  is_urgent?: boolean;
  suggested_supplier_name?: string;
  portal_sent_at?: string;
}

const OrderCoordination: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [orders, setOrders] = useState<CoordinationOrder[]>([]);
  const [expandedOrder, setExpandedOrder] = useState<number | null>(null);
  const [processing, setProcessing] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [invitations, setInvitations] = useState<any[]>([]);
  
  // Stats
  const [stats, setStats] = useState({
    pending: 0,
    distributing: 0,
    accepted: 0,
    completed: 0,
    urgent: 0
  });

  // Load orders on mount
  useEffect(() => {
    loadOrders();
    
    // Refresh every 30 seconds for timer updates
    const interval = setInterval(loadOrders, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadOrders = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Load all coordination-relevant statuses
      const statuses = ['PENDING', 'DISTRIBUTING', 'SUPPLIER_ACCEPTED_PENDING_COORDINATOR', 'APPROVED_AND_SENT'];
      const allOrders: CoordinationOrder[] = [];
      
      for (const status of statuses) {
        try {
          const response = await workOrderService.getWorkOrders(1, 50, { status });
          const items = response.items || response || [];
          items.forEach((order: WorkOrder) => {
            allOrders.push({ ...order });
          });
        } catch {}
      }
      
      // Also load invitations
      try {
        const invResp = await api.get('/supplier-distribution/invitations');
        setInvitations(invResp.data || []);
      } catch {}
      
      // Sort: PENDING first, then DISTRIBUTING, then ACCEPTED
      const statusOrder: Record<string, number> = {
        'PENDING': 1, 'DISTRIBUTING': 2,
        'SUPPLIER_ACCEPTED_PENDING_COORDINATOR': 3, 'APPROVED_AND_SENT': 4
      };
      allOrders.sort((a, b) => (statusOrder[a.status] || 9) - (statusOrder[b.status] || 9));
      
      setOrders(allOrders);
      
      setStats({
        pending: allOrders.filter(o => o.status === 'PENDING').length,
        distributing: allOrders.filter(o => o.status === 'DISTRIBUTING').length,
        accepted: allOrders.filter(o => o.status === 'SUPPLIER_ACCEPTED_PENDING_COORDINATOR').length,
        completed: allOrders.filter(o => o.status === 'APPROVED_AND_SENT').length,
        urgent: 0,
      });
      
    } catch (err: any) {
      console.error('Error loading orders:', err);
      setError('שגיאה בטעינת הזמנות');
    } finally {
      setLoading(false);
    }
  };

  // Send order to supplier via Fair Rotation
  const handleSendToSupplier = async (orderId: number) => {
    try {
      setProcessing(orderId);
      const resp = await api.post('/supplier-distribution/distribute', { work_order_id: orderId });
      const data = resp.data;
      if ((window as any).showToast) {
        (window as any).showToast('נשלח ל' + (data.supplier_name || 'ספק') + ' בהצלחה!', 'success');
      }
      await loadOrders();
    } catch (err: any) {
      console.error('Error distributing:', err);
      if ((window as any).showToast) {
        (window as any).showToast(err.response?.data?.detail || 'שגיאה בהפצה לספק', 'error');
      }
    } finally {
      setProcessing(null);
    }
  };

  // Coordinator approve after supplier accepted
  const handleCoordinatorApprove = async (orderId: number) => {
    try {
      setProcessing(orderId);
      const inv = invitations.find(i => i.work_order_id === orderId && i.status === 'ACCEPTED');
      if (!inv) { alert('לא נמצאה הזמנה מאושרת'); return; }
      await api.post('/supplier-distribution/coordinator-approve/' + inv.id, { approved: true });
      if ((window as any).showToast) {
        (window as any).showToast('ההזמנה אושרה ונשלחה!', 'success');
      }
      await loadOrders();
    } catch (err: any) {
      console.error('Error approving:', err);
      if ((window as any).showToast) {
        (window as any).showToast(err.response?.data?.detail || 'שגיאה באישור', 'error');
      }
    } finally {
      setProcessing(null);
    }
  };

  // Re-distribute (send to next supplier)
  const handleMoveToNextSupplier = async (orderId: number) => {
    try {
      setProcessing(orderId);
      await api.post('/supplier-distribution/distribute', { work_order_id: orderId });
      if ((window as any).showToast) {
        (window as any).showToast('הועבר לספק הבא בסבב', 'success');
      }
      await loadOrders();
    } catch (err: any) {
      console.error('Error redistributing:', err);
      if ((window as any).showToast) {
        (window as any).showToast(err.response?.data?.detail || 'שגיאה בהעברה', 'error');
      }
    } finally {
      setProcessing(null);
    }
  };

  // Log coordination action
  const handleLogAction = async (orderId: number, actionType: string, note?: string) => {
    try {
      setProcessing(orderId);
      
      await api.post('/work-order-coordination-logs', {
        work_order_id: orderId,
        action_type: actionType,
        note: note || ''
      });
      
      if ((window as any).showToast) {
        (window as any).showToast('הפעולה תועדה', 'success');
      }
      
      await loadOrders();
    } catch (err: any) {
      console.error('Error logging action:', err);
    } finally {
      setProcessing(null);
    }
  };

  // Resend to supplier
  const handleResend = async (orderId: number) => {
    try {
      setProcessing(orderId);
      
      await api.post(`/work-orders/${orderId}/resend-to-supplier`);
      await handleLogAction(orderId, 'RESEND');
      
      if ((window as any).showToast) {
        (window as any).showToast('נשלח מחדש לספק', 'success');
      }
      
      await loadOrders();
    } catch (err: any) {
      console.error('Error resending:', err);
      if ((window as any).showToast) {
        (window as any).showToast(err.response?.data?.detail || 'שגיאה בשליחה מחדש', 'error');
      }
    } finally {
      setProcessing(null);
    }
  };

  // Log phone call
  const handleLogCall = async (orderId: number) => {
    const note = prompt('הערות לשיחה:');
    if (note !== null) {
      await handleLogAction(orderId, 'CALL', note || 'שיחה עם ספק');
    }
  };

  // Filter orders
  const filteredOrders = orders.filter(order => {
    if (filterStatus === 'all') return true;
    return order.status === filterStatus;
  });

  // Status helpers
  const getStatusBadge = (status: string) => {
    const map: Record<string, { text: string; color: string }> = {
      'PENDING': { text: 'ממתין לשליחה', color: 'bg-yellow-100 text-yellow-700' },
      'DISTRIBUTING': { text: 'בהפצה לספק', color: 'bg-blue-100 text-blue-700' },
      'SUPPLIER_ACCEPTED_PENDING_COORDINATOR': { text: 'ספק אישר!', color: 'bg-purple-100 text-purple-700' },
      'APPROVED_AND_SENT': { text: 'אושר ונשלח', color: 'bg-green-100 text-green-700' },
    };
    const cfg = map[status] || { text: status, color: 'bg-gray-100 text-gray-700' };
    return <span className={'px-3 py-1 rounded-full text-xs font-medium ' + cfg.color}>{cfg.text}</span>;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('he-IL');
  };

  if (loading && orders.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-green-200 border-t-green-600 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">טוען תיאומים...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pt-20 pb-8 px-4 md:pr-72" dir="rtl">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">תיאום הזמנות</h1>
              <p className="text-gray-500 mt-1">ניהול ותיאום הזמנות עבודה עם ספקים</p>
            </div>
            <button
              onClick={loadOrders}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <RefreshCcw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              רענן
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <div className="bg-white rounded-xl shadow-sm p-4 border-r-4 border-yellow-500 cursor-pointer hover:shadow-md" onClick={() => setFilterStatus('PENDING')}>
            <p className="text-xs text-gray-500">ממתינות לשליחה</p>
            <p className="text-2xl font-bold text-gray-900">{stats.pending}</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4 border-r-4 border-blue-500 cursor-pointer hover:shadow-md" onClick={() => setFilterStatus('DISTRIBUTING')}>
            <p className="text-xs text-gray-500">בהפצה לספקים</p>
            <p className="text-2xl font-bold text-gray-900">{stats.distributing}</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4 border-r-4 border-purple-500 cursor-pointer hover:shadow-md" onClick={() => setFilterStatus('SUPPLIER_ACCEPTED_PENDING_COORDINATOR')}>
            <p className="text-xs text-gray-500">ספק אישר - ממתין לך</p>
            <p className="text-2xl font-bold text-gray-900">{stats.accepted}</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4 border-r-4 border-green-500 cursor-pointer hover:shadow-md" onClick={() => setFilterStatus('APPROVED_AND_SENT')}>
            <p className="text-xs text-gray-500">אושרו ונשלחו</p>
            <p className="text-2xl font-bold text-gray-900">{stats.completed}</p>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-1">
          {[
            { key: 'all', label: 'הכל', count: orders.length, color: 'green' },
            { key: 'PENDING', label: 'ממתינות', count: stats.pending, color: 'yellow' },
            { key: 'DISTRIBUTING', label: 'בהפצה', count: stats.distributing, color: 'blue' },
            { key: 'SUPPLIER_ACCEPTED_PENDING_COORDINATOR', label: 'ספק אישר', count: stats.accepted, color: 'purple' },
            { key: 'APPROVED_AND_SENT', label: 'הושלמו', count: stats.completed, color: 'green' },
          ].map(tab => (
            <button key={tab.key} onClick={() => setFilterStatus(tab.key)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap text-sm ${
                filterStatus === tab.key
                  ? 'bg-' + tab.color + '-600 text-white shadow-sm'
                  : 'bg-white text-gray-600 hover:bg-gray-100 border'
              }`}>
              {tab.label} ({tab.count})
            </button>
          ))}
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-500" />
            <span className="text-red-700">{error}</span>
            <button onClick={loadOrders} className="mr-auto text-red-600 hover:text-red-700 font-medium">
              נסה שוב
            </button>
          </div>
        )}

        {/* Orders List */}
        {filteredOrders.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm p-12 text-center">
            <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">אין הזמנות הממתינות לתיאום</h3>
            <p className="text-gray-500">כל ההזמנות כבר תואמו או אושרו</p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredOrders.map((order) => (
              <div 
                key={order.id}
                className={`bg-white rounded-xl shadow-sm border-2 transition-all ${
                  order.is_urgent 
                    ? 'border-red-300 bg-red-50/30' 
                    : order.portal_token 
                      ? 'border-blue-200' 
                      : 'border-gray-100'
                }`}
              >
                {/* Order Header */}
                <div 
                  className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                  onClick={() => setExpandedOrder(expandedOrder === order.id ? null : order.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      {/* Urgency Indicator */}
                      {order.is_urgent && (
                        <div className="flex items-center gap-1 px-2 py-1 bg-red-100 text-red-700 rounded-full text-xs font-medium animate-pulse">
                          <AlertTriangle className="w-3 h-3" />
                          דחוף!
                        </div>
                      )}
                      
                      {/* Order Number */}
                      <div>
                        <span className="text-sm text-gray-500">הזמנה</span>
                        <span className="font-bold text-gray-900 mr-2">#{order.order_number}</span>
                      </div>
                      
                      {/* Title */}
                      <div className="hidden md:block">
                        <p className="font-medium text-gray-900">{order.title}</p>
                        <p className="text-sm text-gray-500">{order.project_name}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4">
                      {/* Timer */}
                      {order.time_remaining_display && (
                        <div className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium ${
                          order.is_urgent 
                            ? 'bg-red-100 text-red-700' 
                            : 'bg-blue-100 text-blue-700'
                        }`}>
                          <Timer className="w-4 h-4" />
                          {order.time_remaining_display}
                        </div>
                      )}
                      
                      {/* Status Badge */}
                      {getStatusBadge(order.status)}
                      
                      {/* Expand Icon */}
                      {expandedOrder === order.id 
                        ? <ChevronUp className="w-5 h-5 text-gray-400" />
                        : <ChevronDown className="w-5 h-5 text-gray-400" />
                      }
                    </div>
                  </div>
                </div>
                
                {/* Expanded Details */}
                {expandedOrder === order.id && (
                  <div className="border-t border-gray-100 p-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Order Details */}
                      <div className="space-y-3">
                        <h4 className="font-semibold text-gray-900 mb-3">פרטי ההזמנה</h4>
                        
                        <div className="flex items-center gap-2 text-sm">
                          <Truck className="w-4 h-4 text-gray-400" />
                          <span className="text-gray-500">סוג ציוד:</span>
                          <span className="font-medium">{order.equipment_type || 'לא צוין'}</span>
                        </div>
                        
                        <div className="flex items-center gap-2 text-sm">
                          <Calendar className="w-4 h-4 text-gray-400" />
                          <span className="text-gray-500">תאריכי עבודה:</span>
                          <span className="font-medium">
                            {formatDate(order.work_start_date)} - {formatDate(order.work_end_date)}
                          </span>
                        </div>
                        
                        <div className="flex items-center gap-2 text-sm">
                          <User className="w-4 h-4 text-gray-400" />
                          <span className="text-gray-500">ספק נוכחי:</span>
                          <span className="font-medium">{order.supplier_name || 'לא נבחר'}</span>
                        </div>
                        
                        {order.description && (
                          <div className="mt-3 p-3 bg-gray-50 rounded-lg text-sm text-gray-600">
                            {order.description}
                          </div>
                        )}
                      </div>
                      
                      {/* Actions */}
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-3">פעולות</h4>
                        
                        <div className="grid grid-cols-2 gap-2">
                          {/* View Details */}
                          <button
                            onClick={() => navigate(`/work-orders/${order.id}`)}
                            className="flex items-center justify-center gap-2 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
                          >
                            <Eye className="w-4 h-4" />
                            צפה בפרטים
                          </button>
                          
                          {/* Log Call */}
                          <button
                            onClick={() => handleLogCall(order.id)}
                            disabled={processing === order.id}
                            className="flex items-center justify-center gap-2 px-3 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition-colors text-sm disabled:opacity-50"
                          >
                            <Phone className="w-4 h-4" />
                            תעד שיחה
                          </button>
                          
                          {/* Action by status */}
                          {order.status === 'PENDING' && (
                            <button onClick={() => handleSendToSupplier(order.id)}
                              disabled={processing === order.id}
                              className="flex items-center justify-center gap-2 px-3 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm disabled:opacity-50 col-span-2 font-medium">
                              {processing === order.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                              שלח לספק (סבב הוגן)
                            </button>
                          )}
                          
                          {order.status === 'DISTRIBUTING' && (
                            <button onClick={() => handleMoveToNextSupplier(order.id)}
                              disabled={processing === order.id}
                              className="flex items-center justify-center gap-2 px-3 py-2 bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200 transition-colors text-sm disabled:opacity-50 col-span-2">
                              {processing === order.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowLeftRight className="w-4 h-4" />}
                              העבר לספק הבא
                            </button>
                          )}
                          
                          {order.status === 'SUPPLIER_ACCEPTED_PENDING_COORDINATOR' && (
                            <button onClick={() => handleCoordinatorApprove(order.id)}
                              disabled={processing === order.id}
                              className="flex items-center justify-center gap-2 px-3 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm disabled:opacity-50 col-span-2 font-medium animate-pulse">
                              {processing === order.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                              אשר ושלח לביצוע
                            </button>
                          )}
                          
                          {order.status === 'APPROVED_AND_SENT' && (
                            <div className="flex items-center gap-2 px-3 py-2 bg-green-50 text-green-700 rounded-lg text-sm col-span-2">
                              <CheckCircle className="w-4 h-4" />
                              הזמנה אושרה ונשלחה לביצוע
                            </div>
                          )}
                        </div>
                        
                        {/* 3 Hour Timer Info */}
                        <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                          <div className="flex items-start gap-2">
                            <Timer className="w-4 h-4 text-amber-600 mt-0.5" />
                            <div className="text-sm">
                              <p className="font-medium text-amber-800">טיימר 3 שעות</p>
                              <p className="text-amber-700">
                                אם הספק לא מגיב תוך 3 שעות, ההזמנה עוברת אוטומטית לספק הבא בסבב.
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default OrderCoordination;
