
// src/pages/Dashboard/AdminDashboard.tsx
// דשבורד מנהל מערכת - כל הפרויקטים והנתונים
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Users,
  Eye,
  Edit3,
  Trees,
  FileText,
  Wrench,
  Activity,
  Clock,
  ChevronLeft,
  ChevronRight,
  Calendar,
  Loader2
} from "lucide-react";
import api from "../../services/api";
import dashboardService, {
  DashboardSummary
} from "../../services/dashboardService";
import UnifiedLoader from "../../components/common/UnifiedLoader";

// Types for PendingTasksEngine
interface TaskKPI {
  id: string;
  label: string;
  value: number;
  icon: string;
  color: string;
  link: string;
}

interface TaskAction {
  id: string;
  label: string;
  path: string;
  icon: string;
}

interface TaskAlert {
  id: string;
  type: 'warning' | 'error' | 'info';
  message: string;
  link: string;
}

interface MyTasks {
  kpis: TaskKPI[];
  actions: TaskAction[];
  alerts: TaskAlert[];
  role: string;
}

const AdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [myTasks, setMyTasks] = useState<MyTasks | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const [summaryData, , tasksData] = await Promise.all([
          dashboardService.getSummary(),
          dashboardService.getProjects(),
          dashboardService.getMyTasks().catch(() => null),
        ]);

        setSummary(summaryData);
        setMyTasks(tasksData);
        setIsLoading(false);
      } catch (err) {
        console.error('Error loading admin dashboard data:', err);
        setError('שגיאה בטעינת נתוני הדאשבורד');
        setIsLoading(false);
      }
    };

    loadData();
  }, []);

  if (isLoading) return <UnifiedLoader size="full" />;

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h2 className="text-red-600 font-medium mb-2">שגיאה</h2>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  const activeUsers = summary?.active_users || 0;
  const activeProjects = summary?.active_projects_count || 0;

  return (
    <div className="min-h-full bg-gray-50" dir="rtl">
      {/* Main Content - parent App.tsx handles sidebar offset */}
      <div className="p-4 sm:p-6">
        <div className="space-y-4">
            
            {/* Stats Row - 3 KPI cards from PendingTasksEngine */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {(myTasks?.kpis || [
                {id:'pending', label:'דיווחים ממתינים', value: summary?.pending_approvals_count || 0, icon:'file', color:'red', link:''},
                {id:'projects', label:'פרויקטים פעילים', value: activeProjects, icon:'tree', color:'green', link:'/projects'},
                {id:'users', label:'משתמשים במערכת', value: activeUsers, icon:'users', color:'blue', link:'/settings/admin/users'},
              ]).map((kpi) => {
                const colorMap: Record<string, {bg: string, text: string, iconBg: string}> = {
                  red: {bg: 'bg-red-50', text: 'text-red-500', iconBg: 'bg-red-50'},
                  orange: {bg: 'bg-orange-50', text: 'text-orange-500', iconBg: 'bg-orange-50'},
                  green: {bg: 'bg-green-50', text: 'text-green-600', iconBg: 'bg-green-50'},
                  blue: {bg: 'bg-blue-50', text: 'text-blue-600', iconBg: 'bg-blue-50'},
                };
                const c = colorMap[kpi.color] || colorMap.blue;
                const IconMap: Record<string, any> = {headphones: Wrench, alert: Activity, users: Users, scan: Eye, clock: Clock, file: FileText, building: Trees, truck: Wrench, clipboard: FileText, receipt: FileText, check: Activity, edit: Edit3, send: ChevronLeft};
                const Icon = IconMap[kpi.icon] || FileText;
                
                return (
                  <div 
                    key={kpi.id}
                    onClick={() => kpi.link && navigate(kpi.link)}
                    className={`bg-white rounded-xl shadow-sm p-5 h-28 flex flex-col justify-between ${kpi.link ? 'cursor-pointer hover:shadow-md hover:ring-1 hover:ring-gray-200 transition-all' : ''}`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-500">{kpi.label}</span>
                      <div className={`w-8 h-8 ${c.iconBg} rounded-lg flex items-center justify-center`}>
                        <Icon className={`w-4 h-4 ${c.text}`} />
                      </div>
                    </div>
                    <div>
                      <span className="text-3xl font-bold text-gray-900">{kpi.value}</span>
                      {kpi.value > 0 && kpi.color === 'red' && (
                        <span className="text-xs text-red-500 mr-2">דורש טיפול</span>
                      )}
                      {kpi.value > 0 && kpi.color === 'orange' && (
                        <span className="text-xs text-orange-500 mr-2">לבדיקה</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
            
            {/* Alerts from Engine */}
            {myTasks?.alerts && myTasks.alerts.length > 0 && (
              <div className="space-y-2">
                {myTasks.alerts.map((alert) => (
                  <div
                    key={alert.id}
                    onClick={() => alert.link && navigate(alert.link)}
                    className={`rounded-xl p-3 flex items-center gap-3 cursor-pointer transition-all hover:shadow-sm ${
                      alert.type === 'error' ? 'bg-red-50 border border-red-200 hover:bg-red-100' :
                      alert.type === 'warning' ? 'bg-orange-50 border border-orange-200 hover:bg-orange-100' :
                      'bg-blue-50 border border-blue-200 hover:bg-blue-100'
                    }`}
                  >
                    <Activity className={`w-4 h-4 flex-shrink-0 ${
                      alert.type === 'error' ? 'text-red-600' :
                      alert.type === 'warning' ? 'text-orange-600' :
                      'text-blue-600'
                    }`} />
                    <span className={`text-sm font-medium ${
                      alert.type === 'error' ? 'text-red-800' :
                      alert.type === 'warning' ? 'text-orange-800' :
                      'text-blue-800'
                    }`}>{alert.message}</span>
                    <ChevronLeft className="w-4 h-4 text-gray-400 mr-auto" />
                  </div>
                ))}
              </div>
            )}

            {/* Quick Actions Row - from Engine */}
            <div className="bg-white rounded-xl shadow-sm p-4">
              <div className="flex items-center gap-4 flex-wrap">
                <span className="text-sm font-semibold text-gray-700">פעולות מהירות:</span>
                <div className="flex gap-2 flex-wrap">
                  {(myTasks?.actions || [
                    {id:'users', label:'ניהול משתמשים', path:'/settings/admin/users', icon:'users'},
                    {id:'projects', label:'פרויקטים', path:'/projects', icon:'building'},
                    {id:'settings', label:'הגדרות', path:'/settings', icon:'settings'},
                  ]).map((action, idx) => (
                    <button 
                      key={action.id}
                      onClick={() => navigate(action.path)} 
                      className={`inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                        idx === 0 ? 'bg-blue-600 text-white hover:bg-blue-700' :
                        idx === 1 ? 'bg-green-600 text-white hover:bg-green-700' :
                        'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {action.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Two Column Section: Calendar + Activity (NO Projects List!) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              
              {/* Mini Calendar */}
              <MiniCalendar />
              
              {/* Activity Log - real data from API */}
              <RealActivityLog />
              
            </div>

        </div>
      </div>
    </div>
  );
};

// MiniCalendar Component - לוח שנה קטן כמו ביומן הפעילות
const MiniCalendar: React.FC = () => {
  const navigate = useNavigate();
  const [currentDate, setCurrentDate] = useState(new Date());
  const today = new Date();
  
  const daysInMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0).getDate();
  const firstDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1).getDay();
  const prevMonthDays = new Date(currentDate.getFullYear(), currentDate.getMonth(), 0).getDate();
  
  const monthNames = ['ינואר', 'פברואר', 'מרץ', 'אפריל', 'מאי', 'יוני', 'יולי', 'אוגוסט', 'ספטמבר', 'אוקטובר', 'נובמבר', 'דצמבר'];
  const dayNames = ['א׳', 'ב׳', 'ג׳', 'ד׳', 'ה׳', 'ו׳', 'ש׳'];
  
  const prevMonth = () => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  const nextMonth = () => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  const goToToday = () => setCurrentDate(new Date());
  
  const isToday = (day: number) => {
    return day === today.getDate() && 
           currentDate.getMonth() === today.getMonth() && 
           currentDate.getFullYear() === today.getFullYear();
  };
  
  // Build calendar grid
  const calendarDays = [];
  
  // Previous month days
  for (let i = firstDayOfMonth - 1; i >= 0; i--) {
    calendarDays.push({ day: prevMonthDays - i, isCurrentMonth: false });
  }
  
  // Current month days
  for (let day = 1; day <= daysInMonth; day++) {
    calendarDays.push({ day, isCurrentMonth: true, isToday: isToday(day) });
  }
  
  // Next month days to fill the grid
  const remainingDays = 42 - calendarDays.length;
  for (let day = 1; day <= remainingDays; day++) {
    calendarDays.push({ day, isCurrentMonth: false });
  }
  
  return (
    <div className="bg-white rounded-xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-3 py-2 border-b border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-green-600" />
          <span className="text-sm font-semibold text-gray-900">
            יומן - {monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <button onClick={nextMonth} className="p-1 hover:bg-gray-100 rounded text-gray-500">
            <ChevronRight className="w-4 h-4" />
          </button>
          <button onClick={goToToday} className="px-2 py-0.5 text-xs bg-green-50 text-green-700 rounded hover:bg-green-100">
            היום
          </button>
          <button onClick={prevMonth} className="p-1 hover:bg-gray-100 rounded text-gray-500">
            <ChevronLeft className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {/* Days header */}
      <div className="grid grid-cols-7 border-b border-gray-100">
        {dayNames.map(day => (
          <div key={day} className="py-1 text-center text-xs font-medium text-gray-400">{day}</div>
        ))}
      </div>
      
      {/* Calendar grid */}
      <div className="grid grid-cols-7">
        {calendarDays.slice(0, 35).map((item, index) => (
          <div 
            key={index}
            onClick={() => item.isCurrentMonth && navigate('/activity-log')}
            className={`
              py-2 text-center text-xs cursor-pointer transition-colors border-b border-r border-gray-50
              ${item.isCurrentMonth ? 'text-gray-700 hover:bg-green-50' : 'text-gray-300'}
              ${item.isToday ? 'relative' : ''}
            `}
          >
            {item.isToday ? (
              <span className="inline-flex items-center justify-center w-6 h-6 bg-green-600 text-white rounded-full font-bold">
                {item.day}
              </span>
            ) : (
              item.day
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

// Real Activity Log — fetches from /activity-logs API
const ICON_MAP: Record<string, { icon: React.ElementType; bg: string; color: string }> = {
  login:                 { icon: Activity,  bg: 'bg-gray-50',   color: 'text-gray-600' },
  logout:                { icon: Activity,  bg: 'bg-gray-50',   color: 'text-gray-500' },
  create:                { icon: FileText,  bg: 'bg-green-50',  color: 'text-green-600' },
  update:                { icon: Edit3,     bg: 'bg-blue-50',   color: 'text-blue-600' },
  approve:               { icon: FileText,  bg: 'bg-green-50',  color: 'text-green-600' },
  reject:                { icon: FileText,  bg: 'bg-red-50',    color: 'text-red-600' },
  submit:                { icon: FileText,  bg: 'bg-blue-50',   color: 'text-blue-600' },
  assign:                { icon: Users,     bg: 'bg-purple-50', color: 'text-purple-600' },
  work_order_created:    { icon: Trees,     bg: 'bg-green-50',  color: 'text-green-600' },
  work_order_approved:   { icon: Trees,     bg: 'bg-green-50',  color: 'text-green-600' },
  work_order_sent:       { icon: Trees,     bg: 'bg-blue-50',   color: 'text-blue-600' },
  worklog_created:       { icon: FileText,  bg: 'bg-blue-50',   color: 'text-blue-600' },
  worklog_approved:      { icon: FileText,  bg: 'bg-green-50',  color: 'text-green-600' },
  worklog_rejected:      { icon: FileText,  bg: 'bg-red-50',    color: 'text-red-600' },
  invoice_created:       { icon: FileText,  bg: 'bg-orange-50', color: 'text-orange-600' },
  user_created:          { icon: Users,     bg: 'bg-purple-50', color: 'text-purple-600' },
  equipment_assigned:    { icon: Wrench,    bg: 'bg-orange-50', color: 'text-orange-600' },
  budget_updated:        { icon: FileText,  bg: 'bg-yellow-50', color: 'text-yellow-600' },
};

const timeAgo = (dateStr: string): string => {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'עכשיו';
  if (mins < 60) return `${mins} דק׳`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs} שע׳`;
  const days = Math.floor(hrs / 24);
  return `${days} ימים`;
};

const RealActivityLog: React.FC = () => {
  const navigate = useNavigate();
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/activity-logs', { params: { limit: 8, scope: 'system' } })
      .then(r => {
        const items = Array.isArray(r.data) ? r.data : r.data?.items || [];
        setLogs(items.slice(0, 8));
      })
      .catch(() => setLogs([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="bg-white rounded-xl shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-blue-600" />
          <h3 className="font-semibold text-gray-900">יומן פעילות</h3>
        </div>
        <button onClick={() => navigate('/activity-log')} className="text-sm text-blue-600 hover:text-blue-800 font-medium">
          לכל היומן ←
        </button>
      </div>
      <div className="divide-y divide-gray-50">
        {loading ? (
          <div className="p-8 text-center">
            <Loader2 className="w-6 h-6 animate-spin text-gray-300 mx-auto" />
          </div>
        ) : logs.length === 0 ? (
          <div className="p-6 text-center">
            <Activity className="w-8 h-8 text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-gray-400">אין פעילות אחרונה</p>
          </div>
        ) : (
          logs.map((log) => {
            const actionKey = (log.action || log.activity_type || '').toLowerCase();
            const iconCfg = ICON_MAP[actionKey] || { icon: Activity, bg: 'bg-gray-50', color: 'text-gray-500' };
            const Icon = iconCfg.icon;
            const label = log.display_name_he || log.action || '';
            const sub = log.entity_name || log.user_name || '';
            return (
              <div key={log.id} className="px-4 py-3 flex items-center gap-3 hover:bg-gray-50 cursor-pointer">
                <div className={`w-8 h-8 ${iconCfg.bg} rounded-lg flex items-center justify-center flex-shrink-0`}>
                  <Icon className={`w-4 h-4 ${iconCfg.color}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{label}</p>
                  {sub && <p className="text-xs text-gray-500 truncate">{sub}</p>}
                </div>
                <span className="text-xs text-gray-400 flex-shrink-0">{timeAgo(log.created_at)}</span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;
