
// src/pages/Dashboard/GenericDashboard.tsx
// דשבורד גנרי עם עיצוב נקי לבן וירוק

import React, { useEffect, useState, useCallback, Suspense, lazy } from "react";
import { useNavigate } from "react-router-dom";
import { 
  BarChart3, 
  Plus, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  Truck,
  FileText,
  Users,
  ArrowUpRight,
  Target,
  TrendingUp,
  Activity as ActivityIcon,
  Map,
  Eye,
  MapPin,
} from "lucide-react";
import dashboardService from "../../services/dashboardService";
import api from "../../services/api";
import UnifiedLoader from "../../components/common/UnifiedLoader";

const LeafletMap = lazy(() => import("../../components/Map/LeafletMap"));

// Types
interface DashboardSummary {
  active_projects?: number;
  active_projects_count?: number;
  pending_work_logs?: number;
  equipment_in_use?: number;
  hours_this_month?: number;
  hours_month_total?: number;
  avg_progress_pct?: number;
  open_alerts_count?: number;
  can_report_hours?: boolean;
  can_create_order?: boolean;
  can_scan_equipment?: boolean;
  can_open_ticket?: boolean;
  [key: string]: any;
}

interface DashboardProject {
  id: number;
  code: string;
  name: string;
  status?: string;
  area_name?: string;
  manager_name?: string;
  progress_percentage?: number;
}


interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: number;
  color: 'green' | 'blue' | 'orange' | 'red' | 'purple';
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, trend, color }) => {
  const iconBgClasses = {
    green: 'bg-green-100',
    blue: 'bg-blue-100',
    orange: 'bg-orange-100',
    red: 'bg-red-100',
    purple: 'bg-purple-100'
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-2">{value}</p>
          {trend !== undefined && (
            <div className="flex items-center mt-2">
              <TrendingUp className={`w-4 h-4 ${trend > 0 ? 'text-green-600' : 'text-red-600'}`} />
              <span className={`text-sm font-medium mr-1 ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
                {Math.abs(trend)}%
              </span>
              <span className="text-sm text-gray-500">מהחודש הקודם</span>
            </div>
          )}
        </div>
        <div className={`p-3 rounded-lg ${iconBgClasses[color]}`}>
          {icon}
        </div>
      </div>
    </div>
  );
};

interface QuickActionProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  onClick: () => void;
  color: 'green' | 'blue' | 'purple';
}

const QuickActionCard: React.FC<QuickActionProps> = ({ icon, title, description, onClick, color }) => {
  const colorClasses = {
    green: 'hover:bg-green-50 hover:border-green-300 text-green-600',
    blue: 'hover:bg-blue-50 hover:border-blue-300 text-blue-600',
    purple: 'hover:bg-purple-50 hover:border-purple-300 text-purple-600'
  };

  return (
    <button
      onClick={onClick}
      className={`p-6 bg-white rounded-lg border border-gray-200 hover:shadow-md transition-all text-right ${colorClasses[color]}`}
    >
      <div className="flex items-start gap-4">
        <div className={`p-3 rounded-lg bg-gray-50`}>
          {icon}
        </div>
        <div>
          <h3 className="font-semibold text-gray-900">{title}</h3>
          <p className="text-sm text-gray-600 mt-1">{description}</p>
        </div>
      </div>
    </button>
  );
};

interface WorkManagerSummary {
  hours_this_week: number;
  hours_this_month: number;
  active_work_orders: number;
  equipment_in_use: number;
  pending_worklogs: number;
}

interface ActivityLogEntry {
  id: number;
  action: string;
  description?: string;
  project_name?: string;
  created_at: string;
  category?: string;
}

interface MapProject {
  id: number;
  code: string;
  name: string;
  lat?: number;
  lng?: number;
}

const GenericDashboard: React.FC<{title?: string}> = ({ title }) => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [projects, setProjects] = useState<DashboardProject[]>([]);
  const [myTasks, setMyTasks] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [wmSummary, setWmSummary] = useState<WorkManagerSummary | null>(null);
  const [activities, setActivities] = useState<ActivityLogEntry[]>([]);
  const [mapProjects, setMapProjects] = useState<MapProject[]>([]);

  const userRole = (() => { try { return JSON.parse(localStorage.getItem('user') || '{}').role || ''; } catch { return ''; } })();
  const isWorkManager = userRole === 'WORK_MANAGER' || userRole === 'FIELD_WORKER';

  const loadDashboardData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const [summaryData, projectsData, tasksData] = await Promise.all([
        dashboardService.getSummary(),
        dashboardService.getProjects(),
        dashboardService.getMyTasks().catch(() => null),
      ]);

      setSummary(summaryData);
      setProjects(projectsData);
      setMyTasks(tasksData);

      // Work Manager specific data
      if (isWorkManager) {
        // Weekly summary
        api.get('/dashboard/work-manager-summary')
          .then(r => setWmSummary(r.data))
          .catch(() => null);

        // Recent activity logs
        api.get('/activity-logs', { params: { scope: 'my', limit: 5 } })
          .then(r => {
            const items = Array.isArray(r.data) ? r.data : r.data?.items || [];
            setActivities(items.slice(0, 5));
          })
          .catch(() => null);

        // My projects for map — uses dashboard/projects which returns lat/lng
        api.get('/dashboard/projects')
          .then(r => {
            const items: any[] = Array.isArray(r.data) ? r.data : r.data?.items || [];
            const withGeo = items
              .filter((p: any) => (p.lat && p.lng) || p.latitude || p.center_lat)
              .map((p: any) => ({
                id: p.id,
                code: p.code,
                name: p.name,
                lat: p.lat ?? p.latitude ?? p.center_lat,
                lng: p.lng ?? p.longitude ?? p.center_lng,
              }));
            setMapProjects(withGeo);
          })
          .catch(() => null);
      }
    } catch (err) {
      console.error('Error loading dashboard:', err);
      setError('שגיאה בטעינת נתוני הדאשבורד');
    } finally {
      setIsLoading(false);
    }
  }, [isWorkManager]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-7xl mx-auto">
        
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">{title || 'לוח בקרה'}</h1>
          <p className="text-gray-600 mt-2">סקירה כללית של הפעילות השוטפת</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex items-center">
              <AlertCircle className="w-5 h-5 text-red-600 ml-2" />
              <p className="text-red-800">{error}</p>
            </div>
          </div>
        )}

        {/* Stats Grid - KPIs from Engine */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="bg-white rounded-lg border border-gray-200 p-6 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-24 mb-3"></div>
                <div className="h-8 bg-gray-200 rounded w-20"></div>
              </div>
            ))}
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
              {(myTasks?.kpis || [
                {id:'projects', label:'פרויקטים פעילים', value: summary?.active_projects || 0, color:'green', link:'/projects'},
                {id:'hours', label:'שעות החודש', value: summary?.hours_this_month || 0, color:'blue', link:''},
                {id:'pending', label:'דיווחים ממתינים', value: summary?.pending_work_logs || 0, color:'red', link:'/projects'},
              ]).map((kpi: any) => {
                const iconMap: Record<string, any> = {
                  scan: Eye, clock: Clock, truck: Truck, file: FileText, building: Target,
                  users: Users, alert: AlertCircle, clipboard: FileText, receipt: FileText,
                  check: CheckCircle, edit: FileText, send: ArrowUpRight, headphones: ActivityIcon,
                };
                const Icon = iconMap[kpi.icon] || Target;
                return (
                  <div key={kpi.id} onClick={() => kpi.link && navigate(kpi.link)} className={kpi.link ? 'cursor-pointer' : ''}>
                    <StatCard title={kpi.label} value={kpi.value} icon={<Icon className={`w-6 h-6`} />} color={kpi.color || 'blue'} />
                  </div>
                );
              })}
            </div>
            
            {myTasks?.alerts && myTasks.alerts.length > 0 && (
              <div className="space-y-2 mb-6">
                {myTasks.alerts.map((alert: any) => (
                  <div key={alert.id} onClick={() => alert.link && navigate(alert.link)}
                    className={`rounded-lg p-3 flex items-center gap-3 cursor-pointer hover:shadow-sm ${
                      alert.type === 'error' ? 'bg-red-50 border border-red-200' :
                      alert.type === 'warning' ? 'bg-orange-50 border border-orange-200' :
                      'bg-blue-50 border border-blue-200'
                    }`}>
                    <AlertCircle className={`w-4 h-4 ${alert.type === 'error' ? 'text-red-600' : alert.type === 'warning' ? 'text-orange-600' : 'text-blue-600'}`} />
                    <span className={`text-sm font-medium ${alert.type === 'error' ? 'text-red-800' : alert.type === 'warning' ? 'text-orange-800' : 'text-blue-800'}`}>{alert.message}</span>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* Quick Actions - from Engine */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-6 mb-8">
          {(myTasks?.actions || [
            {id:'report', label:'דיווח יום עבודה', path:'/projects', icon:'plus'},
            {id:'scan', label:'סריקת ציוד', path:'/equipment/scan', icon:'qr-code'},
            {id:'projects', label:'הפרויקטים שלי', path:'/projects', icon:'building'},
          ]).map((action: any, idx: number) => {
            const colors: Array<'green'|'blue'|'purple'> = ['green', 'blue', 'purple'];
            const iconMap: Record<string, any> = {
              'qr-code': Eye, plus: Plus, building: Target, clock: Clock,
              truck: Truck, refresh: ActivityIcon, check: CheckCircle, receipt: FileText,
              chart: BarChart3, headphones: ActivityIcon, users: Users, settings: ActivityIcon,
              rotate: ActivityIcon, map: Map, edit: FileText,
            };
            const Icon = iconMap[action.icon] || Plus;
            return (
              <QuickActionCard
                key={action.id}
                icon={<Icon className="w-6 h-6" />}
                title={action.label}
                description=""
                color={colors[idx % 3]}
                onClick={() => navigate(action.path)}
              />
            );
          })}
        </div>

        {/* Legacy quick actions removed - now dynamic from Engine */}
        <div className="hidden">
          <QuickActionCard
            icon={<Truck className="w-6 h-6" />}
            title="סריקת ציוד"
            description="סרוק QR או הזן מספר רישוי"
            color="blue"
            onClick={() => navigate('/equipment')}
          />
          <QuickActionCard
            icon={<Users className="w-6 h-6" />}
            title="הזמנת ספק"
            description="שלח הזמנה לספק חדש"
            color="purple"
            onClick={() => navigate('/suppliers')}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Projects */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg border border-gray-200">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-gray-900">פרויקטים אחרונים</h2>
                  <button
                    onClick={() => navigate('/projects')}
                    className="text-sm font-medium text-green-600 hover:text-green-700 flex items-center gap-1"
                  >
                    הצג הכל
                    <ArrowUpRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
              
              <div className="divide-y divide-gray-200">
                {projects.slice(0, 5).map((project) => (
                  <div
                    key={project.id}
                    className="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/projects/${project.code}/workspace`)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <h3 className="font-medium text-gray-900">{project.name}</h3>
                          <span className="text-sm text-gray-500">#{project.code}</span>
                        </div>
                        <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                          {project.area_name && (
                            <span className="flex items-center gap-1">
                              <Map className="w-3 h-3" />
                              {project.area_name}
                            </span>
                          )}
                          {project.manager_name && (
                            <span className="flex items-center gap-1">
                              <Users className="w-3 h-3" />
                              {project.manager_name}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="text-left">
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            project.status === 'active' || project.status === 'ACTIVE'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            {project.status === 'active' || project.status === 'ACTIVE' ? 'פעיל' : project.status}
                          </span>
                        </div>
                        {project.progress_percentage !== undefined && (
                          <div className="mt-2">
                            <div className="flex items-center gap-2">
                              <div className="w-24 bg-gray-200 rounded-full h-2">
                                <div
                                  className="bg-green-600 h-2 rounded-full"
                                  style={{ width: `${project.progress_percentage}%` }}
                                />
                              </div>
                              <span className="text-xs text-gray-600">{project.progress_percentage}%</span>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Side Panel */}
          <div className="space-y-6">
            {/* Recent Activity — real data */}
            <div className="bg-white rounded-lg border border-gray-200">
              <div className="p-4 border-b border-gray-200">
                <h2 className="text-base font-semibold text-gray-900">פעילות אחרונה</h2>
              </div>
              <div className="divide-y divide-gray-100">
                {activities.length === 0 ? (
                  <div className="p-6 text-center">
                    <ActivityIcon className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                    <p className="text-sm text-gray-400">אין פעילות אחרונה עדיין</p>
                  </div>
                ) : (
                  activities.map((act) => {
                    const actionLabel = (act as any).display_name_he || (act.action || '').replace(/_/g, ' ');
                    const timeStr = act.created_at
                      ? new Date(act.created_at).toLocaleDateString('he-IL') + ' ' +
                        new Date(act.created_at).toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' })
                      : '';
                    return (
                      <div key={act.id} className="flex items-start gap-3 px-4 py-3 hover:bg-gray-50">
                        <div className="p-1.5 bg-green-100 text-green-600 rounded-lg flex-shrink-0 mt-0.5">
                          <ActivityIcon className="w-3.5 h-3.5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-gray-800 leading-snug">
                            {act.description || actionLabel}
                          </p>
                          {act.project_name && (
                            <p className="text-xs text-gray-500 truncate">{act.project_name}</p>
                          )}
                          <p className="text-xs text-gray-400 mt-0.5">{timeStr}</p>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* Weekly Summary — real API data for Work Manager, hidden for others */}
            {isWorkManager && (
              <div className="bg-white rounded-lg border border-gray-200 p-5">
                <h3 className="text-base font-semibold text-gray-900 mb-4">סיכום שבועי</h3>
                {wmSummary ? (
                  <div className="space-y-4">
                    {/* Hours this week */}
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-gray-600">שעות השבוע</span>
                        <span className="text-sm font-semibold text-gray-900">{wmSummary.hours_this_week.toFixed(1)} שע׳</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-green-600 h-2 rounded-full transition-all"
                          style={{ width: `${Math.min((wmSummary.hours_this_week / 45) * 100, 100)}%` }}
                        />
                      </div>
                    </div>

                    {/* Active work orders */}
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-gray-600">הזמנות פעילות</span>
                        <span className="text-sm font-semibold text-gray-900">{wmSummary.active_work_orders}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: `${Math.min(wmSummary.active_work_orders * 20, 100)}%` }}
                        />
                      </div>
                    </div>

                    {/* Equipment in use */}
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-gray-600">ציוד בשימוש</span>
                        <span className="text-sm font-semibold text-gray-900">{wmSummary.equipment_in_use} כלים</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-orange-500 h-2 rounded-full"
                          style={{ width: `${Math.min(wmSummary.equipment_in_use * 25, 100)}%` }}
                        />
                      </div>
                    </div>

                    {/* Pending worklogs badge */}
                    {wmSummary.pending_worklogs > 0 && (
                      <div className="flex items-center justify-between bg-yellow-50 border border-yellow-200 rounded-lg px-3 py-2 mt-2">
                        <span className="text-sm text-yellow-800">דיווחים ממתינים לאישור</span>
                        <span className="bg-yellow-400 text-yellow-900 text-xs font-bold px-2 py-0.5 rounded-full">{wmSummary.pending_worklogs}</span>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {[1, 2, 3].map(i => (
                      <div key={i} className="animate-pulse">
                        <div className="flex justify-between mb-1">
                          <div className="h-3 bg-gray-200 rounded w-24" />
                          <div className="h-3 bg-gray-200 rounded w-12" />
                        </div>
                        <div className="h-2 bg-gray-200 rounded-full" />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Map Section — real projects for Work Manager */}
        <div className="mt-8 bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <MapPin className="w-5 h-5 text-green-600" />
              {isWorkManager ? 'הפרויקטים שלי על המפה' : 'מפה אינטראקטיבית'}
            </h2>
            {isWorkManager && mapProjects.length > 0 && (
              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">{mapProjects.length} פרויקטים</span>
            )}
          </div>
          {isWorkManager && mapProjects.length > 0 ? (
            <div className="h-80 rounded-xl overflow-hidden border border-gray-100" style={{ isolation: 'isolate' }}>
              <Suspense fallback={<UnifiedLoader size="md" />}>
                <LeafletMap
                  center={[mapProjects[0].lat!, mapProjects[0].lng!]}
                  zoom={9}
                  points={mapProjects.map((p, idx) => ({
                    id: p.id || idx,
                    name: p.name,
                    lat: p.lat!,
                    lng: p.lng!,
                    popupContent: `<b>${p.name}</b>`,
                    color: '#16a34a',
                  }))}
                  fitBounds={mapProjects.length > 1}
                  height="100%"
                />
              </Suspense>
            </div>
          ) : isWorkManager ? (
            <div className="h-80 bg-gray-50 rounded-xl flex flex-col items-center justify-center gap-3 border border-gray-100">
              <MapPin className="w-10 h-10 text-gray-300" />
              <p className="text-sm text-gray-400">לא נמצאו פרויקטים עם נתוני מיקום</p>
              <button onClick={() => navigate('/projects')} className="text-sm text-green-600 hover:underline">
                הצג פרויקטים
              </button>
            </div>
          ) : (
            <div className="h-80 bg-gray-100 rounded-lg flex items-center justify-center">
              <div className="text-center">
                <Map className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-500">מפה אינטראקטיבית</p>
                <p className="text-xs text-gray-400 mt-1">זמין למנהלי עבודה</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default GenericDashboard;