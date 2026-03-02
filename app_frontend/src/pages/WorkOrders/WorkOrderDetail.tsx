
// src/pages/WorkOrders/WorkOrderDetail.tsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowRight, Calendar, Clock, User, Wrench, Edit, CheckCircle, XCircle, Loader2,
  Send, Truck, FileText, Play, CircleDot, Package
} from 'lucide-react';
import workOrderService, { WorkOrder } from '../../services/workOrderService';
import activityLogService, { ActivityLog } from '../../services/activityLogService';

// Timeline step interface
interface TimelineStep {
  id: string;
  title: string;
  description: string;
  status: 'completed' | 'current' | 'pending';
  date?: string;
  icon: React.ReactNode;
}

const WorkOrderDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [workOrder, setWorkOrder] = useState<WorkOrder | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [activities, setActivities] = useState<ActivityLog[]>([]);
  const [timeline, setTimeline] = useState<TimelineStep[]>([]);

  useEffect(() => {
    if (id) {
      fetchWorkOrder();
      fetchActivities();
    }
  }, [id]);

  const fetchActivities = async () => {
    try {
      const logs = await activityLogService.getActivitiesByEntity('work_order', parseInt(id!));
      setActivities(logs);
    } catch (err) {
      console.warn('Could not load activities:', err);
    }
  };

  // Build timeline based on work order status and activities
  useEffect(() => {
    if (workOrder) {
      buildTimeline();
    }
  }, [workOrder, activities]);

  const buildTimeline = () => {
    const steps: TimelineStep[] = [
      {
        id: 'created',
        title: 'נוצרה',
        description: 'הזמנת עבודה נוצרה במערכת',
        status: 'completed',
        date: workOrder?.created_at,
        icon: <FileText className="w-4 h-4" />
      },
      {
        id: 'sent_to_coordinator',
        title: 'נשלחה למתאם',
        description: 'הזמנה נשלחה לתיאום עם ספק',
        status: getStepStatus('sent_to_coordinator'),
        icon: <Send className="w-4 h-4" />
      },
      {
        id: 'sent_to_supplier',
        title: 'נשלחה לספק',
        description: 'ממתין לתשובת הספק',
        status: getStepStatus('sent_to_supplier'),
        icon: <Truck className="w-4 h-4" />
      },
      {
        id: 'supplier_confirmed',
        title: 'ספק אישר',
        description: 'הספק אישר את ההזמנה',
        status: getStepStatus('supplier_confirmed'),
        date: workOrder?.approved_at,
        icon: <CheckCircle className="w-4 h-4" />
      },
      {
        id: 'equipment_scanned',
        title: 'ציוד נסרק',
        description: 'סריקת ציוד בשטח',
        status: getStepStatus('equipment_scanned'),
        icon: <Package className="w-4 h-4" />
      },
      {
        id: 'in_progress',
        title: 'בביצוע',
        description: 'עבודה בביצוע',
        status: getStepStatus('in_progress'),
        icon: <Play className="w-4 h-4" />
      },
      {
        id: 'completed',
        title: 'הושלמה',
        description: 'העבודה הושלמה',
        status: getStepStatus('completed'),
        icon: <CheckCircle className="w-4 h-4" />
      }
    ];
    setTimeline(steps);
  };

  const getStepStatus = (step: string): TimelineStep['status'] => {
    const statusOrder = ['pending', 'approved', 'in_progress', 'completed'];
    const currentIndex = statusOrder.indexOf(workOrder?.status || 'pending');
    
    const stepMapping: Record<string, number> = {
      'created': 0,
      'sent_to_coordinator': 0,
      'sent_to_supplier': 1,
      'supplier_confirmed': 1,
      'equipment_scanned': 2,
      'in_progress': 2,
      'completed': 3
    };
    
    const stepIndex = stepMapping[step] ?? 0;
    
    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return 'current';
    return 'pending';
  };

  const fetchWorkOrder = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const order = await workOrderService.getWorkOrderById(parseInt(id!));
      setWorkOrder(order);
    } catch (error: any) {
      console.error('Error fetching work order:', error);
      setError(error.response?.data?.detail || 'שגיאה בטעינת הזמנת העבודה');
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
      
      if ((window as any).showToast) {
        (window as any).showToast('הזמנת העבודה אושרה בהצלחה!', 'success');
      }
    } catch (error: any) {
      console.error('Error approving work order:', error);
      if ((window as any).showToast) {
        (window as any).showToast(error.response?.data?.detail || 'שגיאה באישור הזמנה', 'error');
      }
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
      
      if ((window as any).showToast) {
        (window as any).showToast('הזמנת העבודה נדחתה', 'success');
      }
    } catch (error: any) {
      console.error('Error rejecting work order:', error);
      if ((window as any).showToast) {
        (window as any).showToast(error.response?.data?.detail || 'שגיאה בדחיית הזמנה', 'error');
      }
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
      
      if ((window as any).showToast) {
        (window as any).showToast('העבודה החלה', 'success');
      }
    } catch (error: any) {
      console.error('Error starting work order:', error);
      if ((window as any).showToast) {
        (window as any).showToast(error.response?.data?.detail || 'שגיאה בהתחלת עבודה', 'error');
      }
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
      
      if ((window as any).showToast) {
        (window as any).showToast('העבודה הושלמה', 'success');
      }
    } catch (error: any) {
      console.error('Error completing work order:', error);
      if ((window as any).showToast) {
        (window as any).showToast(error.response?.data?.detail || 'שגיאה בהשלמת עבודה', 'error');
      }
    } finally {
      setProcessing(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'pending':
      case 'ממתין':
        return 'bg-yellow-100 text-yellow-800';
      case 'approved':
      case 'מאושר':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
      case 'בביצוע':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
      case 'הושלם':
        return 'bg-gray-100 text-gray-800';
      case 'cancelled':
      case 'בוטל':
      case 'rejected':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'pending':
        return 'ממתין לאישור';
      case 'approved':
        return 'מאושר';
      case 'in_progress':
        return 'בביצוע';
      case 'completed':
        return 'הושלם';
      case 'cancelled':
        return 'בוטל';
      case 'rejected':
        return 'נדחה';
      default:
        return status;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('he-IL');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex items-center gap-2">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span>טוען פרטי הזמנת עבודה...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl text-red-600 mb-4">{error}</div>
          <button 
            onClick={() => fetchWorkOrder()}
            className="bg-kkl-green text-white px-4 py-2 rounded-lg hover:bg-green-700"
          >
            נסה שוב
          </button>
        </div>
      </div>
    );
  }

  if (!workOrder) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl text-red-600">הזמנת עבודה לא נמצאה</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center mb-4">
            <button 
              onClick={() => navigate('/work-orders')}
              className="text-kkl-green hover:text-green-700 flex items-center"
            >
              <ArrowRight className="w-4 h-4 ml-1" />
              חזרה לרשימת הזמנות עבודה
            </button>
          </div>
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{workOrder.title}</h1>
              {workOrder.project_name && (
                <p className="text-gray-600 mt-2">פרויקט: {workOrder.project_name}</p>
              )}
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(workOrder.status)}`}>
              {getStatusText(workOrder.status)}
            </span>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* Description */}
            {workOrder.description && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">תיאור העבודה</h2>
                <p className="text-gray-600">{workOrder.description}</p>
              </div>
            )}

            {/* Timeline */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">התקדמות ההזמנה</h2>
              <div className="space-y-1">
                {timeline.map((step, index) => (
                  <div key={step.id} className="flex items-center gap-3 py-2">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                      step.status === 'completed' ? 'bg-green-500 text-white' :
                      step.status === 'current' ? 'bg-blue-500 text-white animate-pulse' :
                      'bg-gray-200 text-gray-400'
                    }`}>
                      {step.icon}
                    </div>
                    <div className="flex-1">
                      <span className={`font-medium ${
                        step.status === 'completed' ? 'text-green-700' :
                        step.status === 'current' ? 'text-blue-700' : 'text-gray-400'
                      }`}>{step.title}</span>
                      {step.status === 'current' && (
                        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full mr-2">נוכחי</span>
                      )}
                      <p className="text-sm text-gray-500">{step.description}</p>
                    </div>
                    {index < timeline.length - 1 && (
                      <div className={`w-4 h-0.5 ${step.status === 'completed' ? 'bg-green-500' : 'bg-gray-200'}`} />
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Activity Log */}
            {activities.length > 0 && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">יומן פעילות</h2>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {activities.map((act) => (
                    <div key={act.id} className="flex items-start gap-2 p-2 bg-gray-50 rounded-lg text-sm">
                      <CircleDot className="w-3 h-3 text-gray-400 mt-1" />
                      <div>
                        <span className="font-medium">{act.action.replace(/[._]/g, ' ')}</span>
                        <span className="text-gray-400 mr-2">{new Date(act.created_at).toLocaleString('he-IL')}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">פעולות</h2>
              <div className="flex flex-wrap gap-3">
                {workOrder.status === 'pending' && (
                  <>
                    <button
                      onClick={handleApprove}
                      disabled={processing}
                      className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 disabled:opacity-50"
                    >
                      <CheckCircle className="w-4 h-4" />
                      אשר
                    </button>
                    <button
                      onClick={handleReject}
                      disabled={processing}
                      className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 disabled:opacity-50"
                    >
                      <XCircle className="w-4 h-4" />
                      דחה
                    </button>
                  </>
                )}
                {workOrder.status === 'approved' && (
                  <button
                    onClick={handleStart}
                    disabled={processing}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 disabled:opacity-50"
                  >
                    <Clock className="w-4 h-4" />
                    התחל עבודה
                  </button>
                )}
                {workOrder.status === 'in_progress' && (
                  <button
                    onClick={handleComplete}
                    disabled={processing}
                    className="bg-kkl-green hover:bg-green-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 disabled:opacity-50"
                  >
                    <CheckCircle className="w-4 h-4" />
                    השלם עבודה
                  </button>
                )}
                <button
                  onClick={() => navigate(`/work-orders/${workOrder.id}/edit`)}
                  className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg flex items-center gap-2"
                >
                  <Edit className="w-4 h-4" />
                  עריכה
                </button>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Info Card */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">פרטי ההזמנה</h3>
              <div className="space-y-4">
                <div className="flex items-center">
                  <Calendar className="w-5 h-5 text-gray-500 ml-2" />
                  <div>
                    <span className="text-gray-600 text-sm">תאריכים:</span>
                    <div className="font-medium">
                      {formatDate(workOrder.work_start_date)} - {formatDate(workOrder.work_end_date)}
                    </div>
                  </div>
                </div>
                
                {workOrder.estimated_hours && (
                  <div className="flex items-center">
                    <Clock className="w-5 h-5 text-gray-500 ml-2" />
                    <div>
                      <span className="text-gray-600 text-sm">שעות משוערות:</span>
                      <div className="font-medium">{workOrder.estimated_hours}</div>
                    </div>
                  </div>
                )}
                
                {workOrder.hourly_rate && (
                  <div className="flex items-center">
                    <span className="text-gray-600 text-sm">תעריף לשעה:</span>
                    <div className="font-medium mr-auto">{workOrder.hourly_rate} ש"ח</div>
                  </div>
                )}
                
                {workOrder.equipment_type && (
                  <div className="flex items-center">
                    <Wrench className="w-5 h-5 text-gray-500 ml-2" />
                    <div>
                      <span className="text-gray-600 text-sm">סוג ציוד:</span>
                      <div className="font-medium">{workOrder.equipment_type}</div>
                    </div>
                  </div>
                )}
                
                {workOrder.supplier_name && (
                  <div className="flex items-center">
                    <User className="w-5 h-5 text-gray-500 ml-2" />
                    <div>
                      <span className="text-gray-600 text-sm">ספק:</span>
                      <div className="font-medium">{workOrder.supplier_name}</div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Dates */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">תאריכים</h3>
              <div className="space-y-3 text-sm">
                <div>
                  <span className="text-gray-600">נוצר:</span>
                  <div className="font-medium">{formatDate(workOrder.created_at)}</div>
                </div>
                {workOrder.approved_at && (
                  <div>
                    <span className="text-gray-600">אושר:</span>
                    <div className="font-medium">{formatDate(workOrder.approved_at)}</div>
                  </div>
                )}
                {workOrder.updated_at && (
                  <div>
                    <span className="text-gray-600">עודכן:</span>
                    <div className="font-medium">{formatDate(workOrder.updated_at)}</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorkOrderDetail;


















