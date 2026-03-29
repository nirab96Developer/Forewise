
// src/pages/WorkLogs/WorkLogs.tsx
import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Plus, Search, Eye, Edit, Calendar, Clock, User, CheckCircle, XCircle, ArrowRight } from 'lucide-react';
import workLogService, { WorkLog, WorkLogFilters } from '../../services/workLogService';
import UnifiedLoader from '../../components/common/UnifiedLoader';
import { useOffline } from '../../hooks/useOffline';

const WorkLogs: React.FC = () => {
  const [searchParams] = useSearchParams();
  const projectCode = searchParams.get('project_code');
  const [workLogs, setWorkLogs] = useState<WorkLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [error, setError] = useState<string | null>(null);
  const { isOnline, pendingCount } = useOffline();

  let userData: any = {};
  try { userData = JSON.parse(localStorage.getItem('user') || '{}'); } catch {}
  const userRole = (userData.role || userData.role_code || '').toUpperCase();
  const isManager = ['ADMIN', 'AREA_MANAGER', 'REGION_MANAGER'].includes(userRole);

  useEffect(() => {
    fetchWorkLogs();
  }, []);

  const fetchWorkLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const filters: WorkLogFilters = {
        q: searchTerm || undefined,
        status: filterStatus !== 'all' ? filterStatus : undefined,
        page_size: 100
      };

      let response;
      if (isManager) {
        const res = await workLogService.getWorkLogs(filters);
        response = res;
      } else {
        response = await workLogService.getMyWorkLogs(filters);
      }
      setWorkLogs(response.work_logs || response.items || []);
    } catch (error: any) {
      console.error('Error fetching work logs:', error);
      setError('שגיאה בטעינת דיווחי השעות. אנא נסה שוב.');
    } finally {
      setLoading(false);
    }
  };

  // טעינה מחדש כשמשנים את החיפוש או הסינון
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      fetchWorkLogs();
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [searchTerm, filterStatus]);

  const getStatusColor = (status: string) => {
    const upper = (status || '').toUpperCase();
    if (upper === 'APPROVED') return 'bg-green-100 text-green-800';
    if (upper === 'REJECTED') return 'bg-red-100 text-red-800';
    if (upper === 'SUBMITTED') return 'bg-blue-100 text-blue-800';
    if (upper === 'INVOICED') return 'bg-purple-100 text-purple-800';
    if (upper === 'PENDING') return 'bg-yellow-100 text-yellow-800';
    return 'bg-gray-100 text-gray-800';
  };

  const getStatusText = (status: string) => {
    const map: Record<string, string> = {
      PENDING: 'ממתין', SUBMITTED: 'הוגש', APPROVED: 'אושר',
      REJECTED: 'נדחה', INVOICED: 'הופק חשבון',
    };
    return map[(status || '').toUpperCase()] || status;
  };

  const getStatusIcon = (status: string) => {
    const upper = (status || '').toUpperCase();
    if (upper === 'APPROVED') return <CheckCircle className="w-4 h-4" />;
    if (upper === 'REJECTED') return <XCircle className="w-4 h-4" />;
    return <Clock className="w-4 h-4" />;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('he-IL');
  };

  const formatTime = (timeString: string) => {
    return new Date(`2000-01-01T${timeString}`).toLocaleTimeString('he-IL', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  if (loading) return <UnifiedLoader size="full" />;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 animate-fadeIn">
          {projectCode && (
            <Link 
              to={`/projects/${projectCode}`}
              className="text-kkl-green hover:text-green-700 flex items-center mb-4"
            >
              <ArrowRight className="w-4 h-4 ml-1" />
              חזרה לפרויקט
            </Link>
          )}
          <div className="flex justify-between items-center mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">דיווחי שעות</h1>
              <p className="text-gray-600">ניהול ועקיבה אחר דיווחי השעות שלי</p>
            </div>
            <div className="flex items-center gap-4">
              {!isOnline && (
                <div className="flex items-center gap-2 bg-yellow-100 text-yellow-800 px-3 py-2 rounded-lg">
                  <Clock className="w-4 h-4" />
                  <span>מצב לא מקוון</span>
                  {pendingCount > 0 && (
                    <span className="bg-yellow-200 text-yellow-900 px-2 py-1 rounded text-sm">
                      {pendingCount} ממתינות
                    </span>
                  )}
                </div>
              )}
              {!isManager && (
              <div className="flex gap-2">
                <Link
                  to={projectCode ? `/work-logs/standard?project_code=${projectCode}` : "/work-logs/standard"}
                  className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white px-4 py-3 rounded-lg flex items-center shadow-lg hover:shadow-xl transition-all duration-300 text-sm"
                >
                  <Plus className="w-4 h-4 ml-1" />
                  דיווח תקן
                </Link>
                <Link
                  to={projectCode ? `/work-logs/manual?project_code=${projectCode}` : "/work-logs/manual"}
                  className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white px-4 py-3 rounded-lg flex items-center shadow-lg hover:shadow-xl transition-all duration-300 text-sm"
                >
                  <Plus className="w-4 h-4 ml-1" />
                  דיווח ידני
                </Link>
                <Link
                  to={projectCode ? `/work-logs/storage?project_code=${projectCode}` : "/work-logs/storage"}
                  className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white px-4 py-3 rounded-lg flex items-center shadow-lg hover:shadow-xl transition-all duration-300 text-sm"
                >
                  <Plus className="w-4 h-4 ml-1" />
                  אחסון כלים
                </Link>
              </div>
              )}
            </div>
          </div>

          {/* Search and Filter */}
          <div className="flex gap-4 animate-slideIn">
            <div className="relative flex-1">
              <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="חיפוש דיווחי שעות..."
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
              <option value="pending">ממתין לאישור</option>
              <option value="approved">אושר</option>
              <option value="rejected">נדחה</option>
              <option value="draft">טיוטה</option>
            </select>
          </div>
        </div>

        {/* Work Logs Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {workLogs.map((workLog, index) => (
            <div 
              key={workLog.id} 
              className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all duration-300 hover:scale-105 animate-fadeIn"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-bold text-gray-900">{workLog.work_type}</h3>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(workLog.status)} flex items-center gap-1`}>
                  {getStatusIcon(workLog.status)}
                  {getStatusText(workLog.status)}
                </span>
              </div>
              
              <p className="text-gray-600 text-sm mb-6 leading-relaxed">{workLog.activity_description || workLog.notes || ""}</p>
              
              <div className="space-y-3 mb-6">
                <div className="flex items-center text-sm">
                  <Calendar className="w-4 h-4 text-gray-400 ml-2" />
                  <span className="text-gray-600">תאריך:</span>
                  <span className="font-medium mr-auto">{formatDate(workLog.report_date)}</span>
                </div>
                <div className="flex items-center text-sm">
                  <Clock className="w-4 h-4 text-gray-400 ml-2" />
                  <span className="text-gray-600">שעות:</span>
                  <span className="font-medium mr-auto">
                    {formatTime(workLog.start_time || '')} - {formatTime(workLog.end_time || '')}
                  </span>
                </div>
                <div className="flex items-center text-sm">
                  <User className="w-4 h-4 text-gray-400 ml-2" />
                  <span className="text-gray-600">סה"כ שעות:</span>
                  <span className="font-medium mr-auto">{workLog.total_hours}</span>
                </div>
              </div>

              {/* Standard Work Log Indicator */}
              {workLog.is_standard && (
                <div className="mb-6 p-3 bg-green-50 rounded-lg">
                  <div className="flex items-center text-sm text-green-800">
                    <CheckCircle className="w-4 h-4 ml-2" />
                    <span>דיווח תקן (10.5 שעות)</span>
                  </div>
                </div>
              )}

              {/* Segments */}
              {workLog.segments && workLog.segments.length > 0 && (
                <div className="mb-6">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">פירוט שעות:</h4>
                  <div className="space-y-2">
                    {workLog.segments.map((segment, idx) => (
                      <div key={idx} className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                        {formatTime(segment.start_time)} - {formatTime(segment.end_time)} 
                        ({segment.work_minutes} שעות) - {segment.segment_type}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex gap-3">
                <Link
                  to={`/work-logs/${workLog.id}`}
                  className="flex-1 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white px-4 py-3 rounded-lg text-sm flex items-center justify-center font-medium shadow-md hover:shadow-lg transition-all duration-300"
                >
                  <Eye className="w-4 h-4 ml-1" />
                  צפייה
                </Link>
                {workLog.status === 'draft' && (
                  <button className="flex-1 bg-gradient-to-r from-gray-600 to-gray-700 hover:from-gray-700 hover:to-gray-800 text-white px-4 py-3 rounded-lg text-sm flex items-center justify-center font-medium shadow-md hover:shadow-lg transition-all duration-300">
                    <Edit className="w-4 h-4 ml-1" />
                    עריכה
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>

        {workLogs.length === 0 && !loading && !error && (
          <div className="text-center py-16 animate-fadeIn">
            <div className="bg-white rounded-xl shadow-lg p-12 max-w-md mx-auto">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Search className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">לא נמצאו דיווחי שעות</h3>
              <p className="text-gray-600 mb-6">לא נמצאו דיווחי שעות המתאימים לחיפוש שלך</p>
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

        {error && !loading && (
          <div className="text-center py-16 animate-fadeIn">
            <div className="bg-red-50 border border-red-200 rounded-xl shadow-lg p-12 max-w-md mx-auto">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <XCircle className="w-8 h-8 text-red-400" />
              </div>
              <h3 className="text-lg font-semibold text-red-900 mb-2">שגיאה</h3>
              <p className="text-red-600 mb-6">{error}</p>
              <button 
                onClick={fetchWorkLogs}
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

export default WorkLogs;

