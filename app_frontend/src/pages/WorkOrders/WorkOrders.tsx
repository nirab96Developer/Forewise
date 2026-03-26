
// src/pages/WorkOrders/WorkOrders.tsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Search, Eye, Edit, Calendar, Clock, User, AlertCircle } from 'lucide-react';
import workOrderService, { WorkOrder, WorkOrderFilters } from '../../services/workOrderService';
import UnifiedLoader from '../../components/common/UnifiedLoader';
import { useOffline } from '../../hooks/useOffline';
import { getUserRole, normalizeRole, UserRole } from '../../utils/permissions';

const WorkOrders: React.FC = () => {
  const _role = normalizeRole(getUserRole());
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [error, setError] = useState<string | null>(null);
  const { isOnline, pendingCount } = useOffline();

  // Fetch work orders only once on initial load
  useEffect(() => {
    let isCancelled = false;
    
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const filters: WorkOrderFilters = {
          status: filterStatus !== 'all' ? filterStatus : undefined
        };
        
        const response = await workOrderService.getWorkOrders(1, 50, filters);
        
        if (!isCancelled) {
          setWorkOrders(response?.items || response?.data || response || []);
        }
      } catch (error: any) {
        console.error('[WorkOrders] Error:', error?.message || error);
        if (!isCancelled) {
          setError('שגיאה בטעינת הזמנות העבודה. אנא נסה שוב.');
          setWorkOrders([]);
        }
      } finally {
        if (!isCancelled) {
          setLoading(false);
        }
      }
    };
    
    fetchData();
    
    return () => {
      isCancelled = true;
    };
  }, [filterStatus]); // Only re-fetch when filter changes

  const getStatusColor = (status: string) => {
    const upper = (status || '').toUpperCase();
    if (['APPROVED_AND_SENT'].includes(upper)) return 'bg-green-100 text-green-800';
    if (['DISTRIBUTING', 'SUPPLIER_ACCEPTED_PENDING_COORDINATOR'].includes(upper)) return 'bg-blue-100 text-blue-800';
    if (['PENDING'].includes(upper)) return 'bg-yellow-100 text-yellow-800';
    if (['COMPLETED'].includes(upper)) return 'bg-gray-200 text-gray-800';
    if (['REJECTED', 'CANCELLED', 'EXPIRED', 'STOPPED'].includes(upper)) return 'bg-red-100 text-red-800';
    return 'bg-gray-100 text-gray-800';
  };

  const getStatusText = (status: string) => {
    const s = (status || '').toUpperCase();
    switch (s) {
      case 'PENDING':        return 'ממתין לתיאום';
      case 'DISTRIBUTING':   return 'בתיאום';
      case 'DRAFT':          return 'טיוטה';
      case 'ACCEPTED':
      case 'APPROVED':
      case 'COORDINATOR_APPROVED':
      case 'APPROVED_AND_SENT': return 'אושר — ניתן לדווח';
      case 'SENT_TO_SUPPLIER':
      case 'SUPPLIER_ACCEPTED_PENDING_COORDINATOR': return 'אצל הספק';
      case 'REJECTED':       return 'נדחה';
      case 'COMPLETED':      return 'הושלם';
      case 'CANCELLED':      return 'בוטל';
      case 'ACTIVE':
      case 'IN_PROGRESS':    return 'בביצוע';
      case 'SENT':           return 'נשלח לספק';
      default:               return status || '—';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('he-IL');
  };


  if (loading) return <UnifiedLoader size="full" />;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 animate-fadeIn">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">ניהול הזמנות עבודה</h1>
              <p className="text-gray-600">ניהול ועקיבה אחר הזמנות עבודה לספקים</p>
            </div>
            <div className="flex items-center gap-4">
              {!isOnline && (
                <div className="flex items-center gap-2 bg-yellow-100 text-yellow-800 px-3 py-2 rounded-lg">
                  <AlertCircle className="w-4 h-4" />
                  <span>מצב לא מקוון</span>
                  {pendingCount > 0 && (
                    <span className="bg-yellow-200 text-yellow-900 px-2 py-1 rounded text-sm">
                      {pendingCount} ממתינות
                    </span>
                  )}
                </div>
              )}
              {[UserRole.ADMIN, UserRole.AREA_MANAGER, UserRole.WORK_MANAGER].includes(_role) && (
                <Link
                  to="/work-orders/new"
                  className="bg-gradient-to-r from-kkl-green to-green-600 hover:from-green-600 hover:to-green-700 text-white px-6 py-3 rounded-lg flex items-center shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105"
                >
                  <Plus className="w-5 h-5 ml-2" />
                  הזמנה חדשה
                </Link>
              )}
            </div>
          </div>

          {/* Search and Filter */}
          <div className="flex flex-col sm:flex-row gap-4 animate-slideIn">
            <div className="relative flex-1">
              <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="חיפוש הזמנות עבודה..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pr-12 pl-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent shadow-sm hover:shadow-md transition-shadow"
              />
            </div>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="pr-4 pl-10 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent shadow-sm hover:shadow-md transition-shadow min-w-[150px]"
            >
              <option value="all">כל הסטטוסים</option>
              <option value="PENDING">ממתין</option>
              <option value="DISTRIBUTING">בהפצה לספקים</option>
              <option value="APPROVED_AND_SENT">אושר ונשלח</option>
              <option value="COMPLETED">הושלם</option>
              <option value="REJECTED">נדחה</option>
              <option value="CANCELLED">בוטל</option>
              <option value="EXPIRED">פג תוקף</option>
              <option value="STOPPED">הופסק</option>
            </select>
          </div>
        </div>

        {/* Work Orders Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {workOrders.map((workOrder, index) => (
            <div 
              key={workOrder.id} 
              className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all duration-300 hover:scale-105 animate-fadeIn"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-bold text-gray-900">{workOrder.title}</h3>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(workOrder.status)}`}>
                  {getStatusText(workOrder.status)}
                </span>
              </div>
              
              <p className="text-gray-600 text-sm mb-6 leading-relaxed">{workOrder.description}</p>
              
              <div className="space-y-3 mb-6">
                {workOrder.project_name && (
                  <div className="flex items-center text-sm">
                    <Calendar className="w-4 h-4 text-gray-400 ml-2" />
                    <span className="text-gray-600">פרויקט:</span>
                    <span className="font-medium mr-auto">{workOrder.project_name}</span>
                  </div>
                )}
                <div className="flex items-center text-sm">
                  <Calendar className="w-4 h-4 text-gray-400 ml-2" />
                  <span className="text-gray-600">תאריך:</span>
                  <span className="font-medium mr-auto">{formatDate(workOrder.work_start_date)}</span>
                </div>
                <div className="flex items-center text-sm">
                  <Clock className="w-4 h-4 text-gray-400 ml-2" />
                  <span className="text-gray-600">שעות משוערות:</span>
                  <span className="font-medium mr-auto">{workOrder.estimated_hours || 'לא מוגדר'}</span>
                </div>
                <div className="flex items-center text-sm">
                  <User className="w-4 h-4 text-gray-400 ml-2" />
                  <span className="text-gray-600">ספק:</span>
                  <span className="font-medium mr-auto">{workOrder.supplier_name || (workOrder.supplier_id ? `ספק #${workOrder.supplier_id}` : 'לא מוגדר')}</span>
                </div>
              </div>

              {/* Portal Status */}
              {workOrder.supplier_id && (
                <div className="mb-6 p-3 bg-blue-50 rounded-lg">
                  <div className="flex items-center text-sm text-blue-800">
                    <AlertCircle className="w-4 h-4 ml-2" />
                    <span>פורטל ספק פעיל</span>
                  </div>
                  {workOrder.supplier_name && (
                    <div className="text-xs text-blue-600 mt-1">
                      ספק: {workOrder.supplier_name}
                    </div>
                  )}
                </div>
              )}

              <div className="flex gap-3">
                <Link
                  to={`/work-orders/${workOrder.id}`}
                  className="flex-1 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white px-4 py-3 rounded-lg text-sm flex items-center justify-center font-medium shadow-md hover:shadow-lg transition-all duration-300"
                >
                  <Eye className="w-4 h-4 ml-1" />
                  צפייה
                </Link>
                <Link
                  to={`/work-orders/${workOrder.id}/edit`}
                  className="flex-1 bg-gradient-to-r from-gray-600 to-gray-700 hover:from-gray-700 hover:to-gray-800 text-white px-4 py-3 rounded-lg text-sm flex items-center justify-center font-medium shadow-md hover:shadow-lg transition-all duration-300"
                >
                  <Edit className="w-4 h-4 ml-1" />
                  עריכה
                </Link>
              </div>
            </div>
          ))}
        </div>

        {workOrders.length === 0 && !loading && (
          <div className="text-center py-16 animate-fadeIn">
            <div className="bg-white rounded-xl shadow-lg p-12 max-w-md mx-auto">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Search className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">לא נמצאו הזמנות עבודה</h3>
              <p className="text-gray-600 mb-6">לא נמצאו הזמנות עבודה המתאימות לחיפוש שלך</p>
              <button 
                onClick={() => {
                  setSearchTerm('');
                  setFilterStatus('all');
                }}
                className="bg-kkl-green hover:bg-green-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
              >
                נקה מסננים
              </button>
            </div>
          </div>
        )}

        {error && (
          <div className="text-center py-16 animate-fadeIn">
            <div className="bg-red-50 border border-red-200 rounded-xl shadow-lg p-12 max-w-md mx-auto">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <AlertCircle className="w-8 h-8 text-red-400" />
              </div>
              <h3 className="text-lg font-semibold text-red-900 mb-2">שגיאה</h3>
              <p className="text-red-600 mb-6">{error}</p>
                <button 
                  onClick={() => window.location.reload()}
                  className="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
                >
                  נסה שוב
                </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkOrders;
