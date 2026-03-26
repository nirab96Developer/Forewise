
// Default dashboard for unrecognized roles
// דשבורד בסגנון חילן - נקי, מודרני, צבעי Forewise
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Calendar,
  CalendarDays,
  ClipboardList,
  FileClock,
  PlusCircle,
  Briefcase,
  Bell,
  ChevronLeft,
  ChevronRight,
  MapPin,
  CheckCircle,
  TrendingUp,
  Building2,
  User,
} from "lucide-react";
import dashboardService, { DashboardProject } from "../../services/dashboardService";

// Types
interface UserInfo {
  name: string;
  role: string;
  area: string;
  lastLogin: string;
  initials: string;
}

interface QuickStats {
  pendingOrders: number;
  pendingReports: number;
  newAlerts: number;
  activeProjects: number;
}

interface CalendarDay {
  date: number;
  isToday: boolean;
  isCurrentMonth: boolean;
  hasEvents: boolean;
  events: { title: string; type: 'work_order' | 'worklog' | 'meeting' }[];
}

// Helper to get Hebrew day names
const hebrewDays = ['א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ש'];
const hebrewMonths = [
  'ינואר', 'פברואר', 'מרץ', 'אפריל', 'מאי', 'יוני',
  'יולי', 'אוגוסט', 'ספטמבר', 'אוקטובר', 'נובמבר', 'דצמבר'
];

// Get role display name in Hebrew
const getRoleDisplayName = (role: string): string => {
  const roleMap: Record<string, string> = {
    'ADMIN': 'מנהל מערכת',
    'REGION_MANAGER': 'מנהל מרחב',
    'AREA_MANAGER': 'מנהל אזור',
    'WORK_MANAGER': 'מנהל עבודה',
    'ACCOUNTANT': 'מנהלת חשבונות',
    'USER': 'משתמש',
  };
  return roleMap[role?.toUpperCase()] || role || 'משתמש';
};

const DefaultDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(new Date());
  const [isLoading, setIsLoading] = useState(true);
  const [projects, setProjects] = useState<DashboardProject[]>([]);
  
  // User info from localStorage
  const [userInfo, setUserInfo] = useState<UserInfo>({
    name: 'משתמש',
    role: 'USER',
    area: 'לא מוגדר',
    lastLogin: 'היום',
    initials: 'מ',
  });

  // Quick stats
  const [stats, setStats] = useState<QuickStats>({
    pendingOrders: 0,
    pendingReports: 0,
    newAlerts: 0,
    activeProjects: 0,
  });

  // Load user info
  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        const nameParts = (user.name || 'משתמש').split(' ');
        const initials = nameParts.length >= 2 
          ? `${nameParts[0][0]}${nameParts[1][0]}`
          : nameParts[0].substring(0, 2);
        
        setUserInfo({
          name: user.name || 'משתמש',
          role: user.role || 'USER',
          area: user.area_name || user.region_name || 'לא מוגדר',
          lastLogin: 'היום ' + new Date().toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' }),
          initials: initials.toUpperCase(),
        });
      } catch (e) {
        console.error('Error parsing user info:', e);
      }
    }
  }, []);

  // Load dashboard data
  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true);
        const [summaryData, projectsData] = await Promise.all([
          dashboardService.getSummary(),
          dashboardService.getProjects()
        ]);

        setStats({
          pendingOrders: summaryData?.pending_work_orders_count || 0,
          pendingReports: summaryData?.pending_approvals_count || 0,
          newAlerts: summaryData?.alerts_count || 0,
          activeProjects: summaryData?.active_projects_count || 0,
        });

        setProjects(projectsData || []);
      } catch (error) {
        console.error('Error loading dashboard data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, []);

  // Generate calendar days
  const generateCalendarDays = (): CalendarDay[] => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDay = firstDay.getDay();
    const daysInMonth = lastDay.getDate();
    
    const today = new Date();
    const days: CalendarDay[] = [];

    // Previous month days
    const prevMonthLastDay = new Date(year, month, 0).getDate();
    for (let i = startDay - 1; i >= 0; i--) {
      days.push({
        date: prevMonthLastDay - i,
        isToday: false,
        isCurrentMonth: false,
        hasEvents: false,
        events: [],
      });
    }

    // Current month days
    for (let i = 1; i <= daysInMonth; i++) {
      const isToday = today.getDate() === i && 
                      today.getMonth() === month && 
                      today.getFullYear() === year;
      
      // Mock events for demo
      const hasEvents = [3, 7, 12, 15, 20, 25].includes(i);
      
      days.push({
        date: i,
        isToday,
        isCurrentMonth: true,
        hasEvents,
        events: hasEvents ? [{ title: 'פעילות', type: 'work_order' }] : [],
      });
    }

    // Next month days
    const remainingDays = 42 - days.length;
    for (let i = 1; i <= remainingDays; i++) {
      days.push({
        date: i,
        isToday: false,
        isCurrentMonth: false,
        hasEvents: false,
        events: [],
      });
    }

    return days;
  };

  const goToPreviousMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  };

  const goToNextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  };

  const calendarDays = generateCalendarDays();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-kkl-bg flex items-center justify-center">
        <div className="flex items-center gap-3 bg-white p-6 rounded-xl shadow-sm">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 100" width="24" height="20" className="animate-pulse flex-shrink-0"><defs><linearGradient id="hd_t" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" style={{stopColor:'#1565c0'}}/><stop offset="100%" style={{stopColor:'#0097a7'}}/></linearGradient><linearGradient id="hd_m" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" style={{stopColor:'#0097a7'}}/><stop offset="50%" style={{stopColor:'#2e7d32'}}/><stop offset="100%" style={{stopColor:'#66bb6a'}}/></linearGradient><linearGradient id="hd_b" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" style={{stopColor:'#2e7d32'}}/><stop offset="40%" style={{stopColor:'#66bb6a'}}/><stop offset="100%" style={{stopColor:'#8B5e3c'}}/></linearGradient></defs><path d="M46 20 Q60 9 74 20" stroke="url(#hd_t)" strokeWidth="5.5" fill="none" strokeLinecap="round"/><path d="M30 47 Q42 34 60 43 Q78 34 90 47" stroke="url(#hd_m)" strokeWidth="5.5" fill="none" strokeLinecap="round"/><path d="M14 74 Q28 60 46 69 Q60 76 74 69 Q92 60 106 74" stroke="url(#hd_b)" strokeWidth="5.5" fill="none" strokeLinecap="round"/><line x1="60" y1="76" x2="60" y2="90" stroke="#8B5e3c" strokeWidth="3.5" strokeLinecap="round"/><circle cx="60" cy="95" r="5" fill="#8B5e3c"/></svg>
          <span className="text-kkl-text">טוען נתונים...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-kkl-bg" dir="rtl">
      <div className="max-w-[1600px] mx-auto p-6 space-y-6">
        
        {/* User Card - Top */}
        <div className="bg-white rounded-xl shadow-sm border border-kkl-border p-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {/* Avatar */}
              <div className="w-14 h-14 bg-gradient-to-br from-kkl-green to-kkl-green-dark rounded-full flex items-center justify-center text-white font-bold text-lg shadow-md">
                {userInfo.initials}
              </div>
              
              {/* User Info */}
              <div>
                <h1 className="text-xl font-bold text-kkl-text">{userInfo.name}</h1>
                <div className="flex items-center gap-3 text-sm text-gray-500 mt-1">
                  <span className="flex items-center gap-1">
                    <User className="w-4 h-4" />
                    {getRoleDisplayName(userInfo.role)}
                  </span>
                  <span className="text-kkl-border">|</span>
                  <span className="flex items-center gap-1">
                    <MapPin className="w-4 h-4" />
                    {userInfo.area}
                  </span>
                </div>
              </div>
            </div>

            {/* Last Login */}
            <div className="text-left text-sm text-gray-400">
              <div>חיבור אחרון:</div>
              <div className="font-medium text-kkl-text">{userInfo.lastLogin}</div>
            </div>
          </div>
        </div>

        {/* Main Grid - 3 Columns */}
        <div className="grid grid-cols-12 gap-6">
          
          {/* LEFT COLUMN - Today + Quick Actions */}
          <div className="col-span-12 lg:col-span-3 space-y-6">
            
            {/* Today Card */}
            <div className="bg-white rounded-xl shadow-sm border border-kkl-border p-5">
              <div className="flex items-center gap-2 mb-3">
                <Calendar className="w-5 h-5 text-kkl-green" />
                <h2 className="text-lg font-semibold text-kkl-green">
                  היום – {new Date().getDate()} {hebrewMonths[new Date().getMonth()]}
                </h2>
              </div>
              
              <p className="text-gray-500 text-sm mb-4">
                {selectedDate?.getDate() === new Date().getDate() 
                  ? 'אין פעילויות מתוכננות להיום'
                  : `נבחר: ${selectedDate?.getDate()} ${hebrewMonths[selectedDate?.getMonth() || 0]}`
                }
              </p>

              <button 
                onClick={() => navigate('/projects')}
                className="w-full bg-kkl-green hover:bg-kkl-green-dark text-white py-3 rounded-lg flex items-center justify-center gap-2 transition-colors font-medium shadow-sm"
              >
                <PlusCircle className="w-5 h-5" />
                הוסף פעילות
              </button>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-xl shadow-sm border border-kkl-border p-5">
              <h3 className="text-base font-semibold text-kkl-text mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-kkl-green" />
                פעולות מהירות
              </h3>

              <div className="space-y-2">
                <QuickActionButton 
                  icon={<FileClock className="w-5 h-5" />} 
                  label="דיווח שעות" 
                  onClick={() => navigate('/projects')}
                />
                <QuickActionButton 
                  icon={<Briefcase className="w-5 h-5" />} 
                  label="הזמנת עבודה חדשה" 
                  onClick={() => navigate('/work-orders/new')}
                />
                <QuickActionButton 
                  icon={<CalendarDays className="w-5 h-5" />} 
                  label="תכנון יום עבודה" 
                  onClick={() => navigate('/activity-log')}
                />
                <QuickActionButton 
                  icon={<Building2 className="w-5 h-5" />} 
                  label="צפייה בפרויקטים" 
                  onClick={() => navigate('/projects')}
                />
              </div>
            </div>

            {/* Recent Projects */}
            <div className="bg-white rounded-xl shadow-sm border border-kkl-border p-5">
              <h3 className="text-base font-semibold text-kkl-text mb-4 flex items-center gap-2">
                <Building2 className="w-5 h-5 text-kkl-green" />
                פרויקטים אחרונים
              </h3>

              <div className="space-y-2">
                {projects.slice(0, 4).map((project) => (
                  <button
                    key={project.id}
                    onClick={() => navigate(`/projects/${project.code}/workspace`)}
                    className="w-full text-right p-3 rounded-lg border border-kkl-gray-light hover:border-kkl-green hover:bg-kkl-green-light/30 transition-all group"
                  >
                    <div className="font-medium text-kkl-text group-hover:text-kkl-green truncate">
                      {project.name}
                    </div>
                    <div className="text-xs text-gray-400 mt-1">
                      {project.area_name || project.region_name || 'לא מוגדר'}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* CENTER COLUMN - Calendar */}
          <div className="col-span-12 lg:col-span-6">
            <div className="bg-white rounded-xl shadow-sm border border-kkl-border p-5">
              {/* Calendar Header */}
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-kkl-green flex items-center gap-2">
                  <CalendarDays className="w-5 h-5" />
                  יומן – {hebrewMonths[currentDate.getMonth()]} {currentDate.getFullYear()}
                </h3>
                
                <div className="flex items-center gap-2">
                  <button 
                    onClick={goToPreviousMonth}
                    className="p-2 rounded-lg hover:bg-kkl-green-light transition-colors"
                  >
                    <ChevronRight className="w-5 h-5 text-kkl-green" />
                  </button>
                  <button 
                    onClick={() => setCurrentDate(new Date())}
                    className="px-3 py-1 text-sm bg-kkl-green-light text-kkl-green rounded-lg hover:bg-kkl-green hover:text-white transition-colors"
                  >
                    היום
                  </button>
                  <button 
                    onClick={goToNextMonth}
                    className="p-2 rounded-lg hover:bg-kkl-green-light transition-colors"
                  >
                    <ChevronLeft className="w-5 h-5 text-kkl-green" />
                  </button>
                </div>
              </div>

              {/* Calendar Grid */}
              <div className="grid grid-cols-7 gap-1">
                {/* Day Headers */}
                {hebrewDays.map((day) => (
                  <div key={day} className="text-center py-2 text-sm font-semibold text-gray-500">
                    {day}
                  </div>
                ))}

                {/* Calendar Days */}
                {calendarDays.map((day, index) => (
                  <button
                    key={index}
                    onClick={() => day.isCurrentMonth && setSelectedDate(new Date(currentDate.getFullYear(), currentDate.getMonth(), day.date))}
                    className={`
                      relative p-3 rounded-lg text-center transition-all
                      ${day.isCurrentMonth ? 'hover:bg-kkl-green-light' : 'text-gray-300'}
                      ${day.isToday ? 'bg-kkl-green text-white font-bold hover:bg-kkl-green-dark' : ''}
                      ${selectedDate?.getDate() === day.date && day.isCurrentMonth && !day.isToday 
                        ? 'bg-kkl-green-light border-2 border-kkl-green' 
                        : ''
                      }
                    `}
                  >
                    <span className={day.isCurrentMonth ? 'text-kkl-text' : ''}>
                      {day.isToday ? day.date : day.date}
                    </span>
                    {day.hasEvents && day.isCurrentMonth && !day.isToday && (
                      <div className="absolute bottom-1 left-1/2 -translate-x-1/2 w-1.5 h-1.5 bg-kkl-green rounded-full" />
                    )}
                  </button>
                ))}
              </div>

              {/* Selected Day Events */}
              <div className="mt-6 pt-6 border-t border-kkl-border">
                <h4 className="text-sm font-semibold text-gray-500 mb-3">
                  פעילויות ל-{selectedDate?.getDate()} {hebrewMonths[selectedDate?.getMonth() || 0]}
                </h4>
                <div className="space-y-2">
                  <div className="p-3 bg-kkl-green-light rounded-lg flex items-center gap-3">
                    <div className="w-2 h-2 bg-kkl-green rounded-full" />
                    <span className="text-sm text-kkl-text">אין פעילויות מתוכננות</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* RIGHT COLUMN - Status Cards */}
          <div className="col-span-12 lg:col-span-3 space-y-6">
            
            {/* Pending Work Orders */}
            <StatusCard
              title="הזמנות עבודה ממתינות"
              count={stats.pendingOrders}
              icon={<ClipboardList className="w-6 h-6" />}
              color="green"
              onClick={() => navigate('/work-orders')}
            />

            {/* Pending Reports */}
            <StatusCard
              title="דיווחים ממתינים לאישור"
              count={stats.pendingReports}
              icon={<FileClock className="w-6 h-6" />}
              color="yellow"
              onClick={() => navigate('/projects')}
            />

            {/* New Alerts */}
            <StatusCard
              title="התראות חדשות"
              count={stats.newAlerts}
              icon={<Bell className="w-6 h-6" />}
              color="blue"
              onClick={() => {}}
            />

            {/* Active Projects */}
            <StatusCard
              title="פרויקטים פעילים"
              count={stats.activeProjects}
              icon={<Building2 className="w-6 h-6" />}
              color="green"
              onClick={() => navigate('/projects')}
            />

            {/* System Status */}
            <div className="bg-white rounded-xl shadow-sm border border-kkl-border p-5">
              <h3 className="text-base font-semibold text-kkl-text mb-4 flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-kkl-success" />
                סטטוס מערכת
              </h3>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">שרת API</span>
                  <span className="flex items-center gap-1 text-kkl-success">
                    <span className="w-2 h-2 bg-kkl-success rounded-full animate-pulse" />
                    פעיל
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">מסד נתונים</span>
                  <span className="flex items-center gap-1 text-kkl-success">
                    <span className="w-2 h-2 bg-kkl-success rounded-full animate-pulse" />
                    פעיל
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">עדכון אחרון</span>
                  <span className="text-kkl-text">
                    {new Date().toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Quick Action Button Component
const QuickActionButton: React.FC<{
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
}> = ({ icon, label, onClick }) => (
  <button
    onClick={onClick}
    className="w-full bg-white border border-kkl-border px-4 py-3 rounded-lg flex items-center gap-3 text-kkl-text hover:bg-kkl-green-light hover:border-kkl-green hover:text-kkl-green transition-all group"
  >
    <span className="text-gray-400 group-hover:text-kkl-green transition-colors">
      {icon}
    </span>
    <span className="font-medium">{label}</span>
  </button>
);

// Status Card Component
const StatusCard: React.FC<{
  title: string;
  count: number;
  icon: React.ReactNode;
  color: 'green' | 'yellow' | 'blue' | 'red';
  onClick: () => void;
}> = ({ title, count, icon, color, onClick }) => {
  const colorClasses = {
    green: 'text-kkl-green bg-kkl-green-light',
    yellow: 'text-kkl-warning bg-yellow-50',
    blue: 'text-kkl-info bg-blue-50',
    red: 'text-kkl-error bg-red-50',
  };

  return (
    <button
      onClick={onClick}
      className="w-full bg-white rounded-xl shadow-sm border border-kkl-border p-5 hover:shadow-md hover:border-kkl-green transition-all text-right"
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-gray-600 font-medium">{title}</span>
        <span className={`p-2 rounded-lg ${colorClasses[color]}`}>
          {icon}
        </span>
      </div>
      <div className="text-3xl font-bold text-kkl-green">{count}</div>
    </button>
  );
};

export default DefaultDashboard;

