// @ts-nocheck
// src/pages/Dashboard/GenericDashboard.tsx
// דשבורד גנרי עם עיצוב נקי לבן וירוק

import React, { useEffect, useState, useCallback } from "react";
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
  Download,
  ArrowUpRight,
  Calendar,
  Target,
  TrendingUp,
  Activity,
  Map,
  Eye
} from "lucide-react";
import dashboardService from "../../services/dashboardService";
import projectService from "../../services/projectService";
import authService from "../../services/authService";

// Types
interface DashboardSummary {
  active_projects: number;
  pending_work_logs: number;
  equipment_in_use: number;
  hours_this_month: number;
  hours_month_total?: number;
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

interface Activity {
  id: number;
  type: 'success' | 'warning' | 'info' | 'error';
  title: string;
  description?: string;
  time: string;
  icon: React.ReactNode;
}

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: number;
  color: 'green' | 'blue' | 'orange' | 'red' | 'purple';
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, trend, color }) => {
  const colorClasses = {
    green: 'bg-green-50 text-green-600 border-green-200',
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
    orange: 'bg-orange-50 text-orange-600 border-orange-200',
    red: 'bg-red-50 text-red-600 border-red-200',
    purple: 'bg-purple-50 text-purple-600 border-purple-200'
  };

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

const GenericDashboard: React.FC<{title?: string}> = ({ title }) => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [projects, setProjects] = useState<DashboardProject[]>([]);
  const [myTasks, setMyTasks] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const user = authService.getCurrentUser();
  
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
      
    } catch (err) {
      console.error('Error loading dashboard:', err);
      setError('שגיאה בטעינת נתוני הדאשבורד');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const firstProject = projects.length > 0 ? projects[0] : null;

  // Recent Activities - נטענות מה-API בעתיד
  const activities: Activity[] = [];

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
                  check: CheckCircle, edit: FileText, send: ArrowUpRight, headphones: Activity,
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
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {(myTasks?.actions || [
            {id:'report', label:'דיווח יום עבודה', path:'/projects', icon:'plus'},
            {id:'scan', label:'סריקת ציוד', path:'/equipment/scan', icon:'qr-code'},
            {id:'projects', label:'הפרויקטים שלי', path:'/projects', icon:'building'},
          ]).map((action: any, idx: number) => {
            const colors: Array<'green'|'blue'|'purple'> = ['green', 'blue', 'purple'];
            const iconMap: Record<string, any> = {
              'qr-code': Eye, plus: Plus, building: Target, clock: Clock,
              truck: Truck, refresh: Activity, check: CheckCircle, receipt: FileText,
              chart: BarChart3, headphones: Activity, users: Users, settings: Activity,
              rotate: Activity, map: Map, edit: FileText,
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
            {/* Recent Activity */}
            <div className="bg-white rounded-lg border border-gray-200">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">פעילות אחרונה</h2>
              </div>
              <div className="p-6 space-y-4">
                {activities.map((activity) => (
                  <div key={activity.id} className="flex items-start gap-3">
                    <div className={`p-2 rounded-lg ${
                      activity.type === 'success' ? 'bg-green-100 text-green-600' :
                      activity.type === 'warning' ? 'bg-yellow-100 text-yellow-600' :
                      activity.type === 'error' ? 'bg-red-100 text-red-600' :
                      'bg-blue-100 text-blue-600'
                    }`}>
                      {activity.icon}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{activity.title}</p>
                      {activity.description && (
                        <p className="text-sm text-gray-600">{activity.description}</p>
                      )}
                      <p className="text-xs text-gray-500 mt-1">{activity.time}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Weekly Summary */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">סיכום שבועי</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">שעות עבודה</span>
                  <span className="text-sm font-medium text-gray-900">42/45</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-green-600 h-2 rounded-full" style={{ width: '93%' }} />
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">ניצול ציוד</span>
                  <span className="text-sm font-medium text-gray-900">68%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{ width: '68%' }} />
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">תקציב מנוצל</span>
                  <span className="text-sm font-medium text-gray-900">₪45K/₪100K</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-orange-600 h-2 rounded-full" style={{ width: '45%' }} />
                </div>
                
                <button className="w-full mt-4 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center gap-2">
                  <Download className="w-4 h-4" />
                  הורד דוח מלא
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Map Section */}
        <div className="mt-8 bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">מפה אינטראקטיבית</h2>
          <div className="h-96 bg-gray-100 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <Map className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-500">מפה אינטראקטיבית תטען כאן</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GenericDashboard;