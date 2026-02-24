// @ts-nocheck
// src/pages/ActivityLog/ActivityLogNew.tsx
// יומן פעילות - עיצוב נקי בסגנון קק"ל
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Calendar as CalendarIcon, Clock, ChevronRight, ChevronLeft,
  Truck, FileText, Plus, X, PenLine, TreePine, Briefcase, Hammer,
  CheckCircle, AlertTriangle, User, Send, Filter, List, Grid3X3,
  Bell, Activity, ClipboardList, Settings
} from "lucide-react";

// Services
import workOrderService, { CalendarEvent as WorkOrderEvent } from '../../services/workOrderService';
import activityLogService, { ActivityLog } from '../../services/activityLogService';

// Types
interface ActivityEvent {
  id: string;
  title: string;
  description: string;
  type: "equipment_request" | "equipment_approval" | "work_hours" | "work_hours_approval" | "project" | "system" | "personal_note";
  status: "pending" | "approved" | "rejected" | "completed";
  date: string;
  time: string;
  projectId: string;
  projectName: string;
  equipmentType?: string;
  canReport?: boolean;
  // Support ticket fields
  action?: string;
  entityType?: string;
  entityId?: number;
}

interface CalendarDay {
  date: Date;
  activities: ActivityEvent[];
  workOrders: WorkOrderEvent[];
  personalNotes: PersonalNote[];
  isCurrentMonth: boolean;
  isToday: boolean;
  isHoliday: boolean;
  holidayName?: string;
}

interface PersonalNote {
  id: string;
  title: string;
  content: string;
  date: string;
  createdAt: string;
}

// Helper functions for activity log formatting
const getActivityTitle = (action: string): string => {
  const actionTitles: Record<string, string> = {
    'work_order.created': 'הזמנת עבודה נוצרה',
    'work_order.approved': 'הזמנת עבודה אושרה',
    'work_order.rejected': 'הזמנת עבודה נדחתה',
    'work_order.started': 'עבודה החלה',
    'work_order.completed': 'עבודה הושלמה',
    'work_order.cancelled': 'הזמנה בוטלה',
    'work_order.sent_to_supplier': 'נשלח לספק',
    'work_order.supplier_changed': 'ספק שונה',
    'worklog.created': 'דיווח שעות נוצר',
    'worklog.submitted': 'דיווח נשלח לאישור',
    'worklog.approved': 'דיווח אושר',
    'worklog.rejected': 'דיווח נדחה',
    'invoice.created': 'חשבונית נוצרה',
    'invoice.approved': 'חשבונית אושרה',
    'equipment.scanned': 'ציוד נסרק',
    'equipment.mismatch_detected': 'אי התאמה בסריקה',
    'supplier.confirmed': 'ספק אישר',
    'supplier.declined': 'ספק דחה',
    'user.login': 'כניסה למערכת',
    'user.logout': 'יציאה מהמערכת',
    // Support ticket activities
    'support_ticket.created': '🎫 פנייה חדשה נפתחה',
    'support_ticket.replied': '💬 תגובה חדשה בפנייה',
    'support_ticket.status_changed': '🔄 סטטוס פנייה השתנה',
  };
  return actionTitles[action] || action.replace(/[._]/g, ' ');
};

const getActivityDescription = (item: ActivityLog): string => {
  if (item.details?.description_he) {
    return item.details.description_he;
  }
  if (item.details?.reason) {
    return `סיבה: ${item.details.reason}`;
  }
  if (item.details?.project_name) {
    return `פרויקט: ${item.details.project_name}`;
  }
  return '';
};

const mapActivityType = (activityType: string): ActivityEvent['type'] => {
  const typeMap: Record<string, ActivityEvent['type']> = {
    'work_order': 'equipment_request',
    'worklog': 'work_hours',
    'invoice': 'work_hours_approval',
    'equipment': 'equipment_approval',
    'supplier_coordination': 'equipment_request',
    'project': 'project',
    'auth': 'system',
    'support': 'system',
  };
  return typeMap[activityType] || 'system';
};

// חגים ישראליים
const ISRAELI_HOLIDAYS = [
  { name: 'ראש השנה', date: '2025-09-23' },
  { name: 'יום כיפור', date: '2025-10-02' },
  { name: 'סוכות', date: '2025-10-07' },
  { name: 'שמחת תורה', date: '2025-10-14' },
  { name: 'חנוכה', date: '2025-12-14' },
  { name: 'פורים', date: '2026-03-03' },
  { name: 'פסח', date: '2026-04-02' },
  { name: 'יום העצמאות', date: '2026-04-23' },
];

const ActivityLogNew: React.FC = () => {
  const navigate = useNavigate();
  const today = new Date();
  
  // State
  const [activities, setActivities] = useState<ActivityEvent[]>([]);
  const [workOrders, setWorkOrders] = useState<WorkOrderEvent[]>([]);
  const [personalNotes, setPersonalNotes] = useState<PersonalNote[]>([]);
  const [currentMonth, setCurrentMonth] = useState<number>(today.getMonth());
  const [currentYear, setCurrentYear] = useState<number>(today.getFullYear());
  const [calendarDays, setCalendarDays] = useState<CalendarDay[]>([]);
  const [selectedDay, setSelectedDay] = useState<CalendarDay | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [showAddNote, setShowAddNote] = useState<boolean>(false);
  const [newNote, setNewNote] = useState<{title: string; content: string}>({title: '', content: ''});
  
  // Filters and view options
  const [viewMode, setViewMode] = useState<'calendar' | 'list'>('calendar');
  const [activeFilter, setActiveFilter] = useState<'all' | 'orders' | 'worklogs' | 'support' | 'system'>('all');
  const [statusFilter, setStatusFilter] = useState<'all' | 'pending' | 'approved' | 'completed'>('all');
  
  // Filter tabs configuration
  const filterTabs = [
    { id: 'all', label: 'הכל', icon: <Activity className="w-4 h-4" /> },
    { id: 'orders', label: 'הזמנות עבודה', icon: <Truck className="w-4 h-4" /> },
    { id: 'worklogs', label: 'דיווחי שעות', icon: <Clock className="w-4 h-4" /> },
    { id: 'support', label: 'פניות תמיכה', icon: <Bell className="w-4 h-4" /> },
    { id: 'system', label: 'מערכת', icon: <Settings className="w-4 h-4" /> },
  ];
  
  const statusTabs = [
    { id: 'all', label: 'הכל' },
    { id: 'pending', label: 'ממתין', color: 'text-yellow-600' },
    { id: 'approved', label: 'אושר', color: 'text-green-600' },
    { id: 'completed', label: 'הושלם', color: 'text-blue-600' },
  ];
  
  const getMonthName = (monthIndex: number): string => {
    const months = [
      "ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני",
      "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"
    ];
    return months[monthIndex];
  };
  
  const getDayName = (date: Date): string => {
    const days = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"];
    return days[date.getDay()];
  };
  
  // Load data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        
        const startDate = new Date(currentYear, currentMonth, 1).toISOString().split('T')[0];
        const endDate = new Date(currentYear, currentMonth + 1, 0).toISOString().split('T')[0];
        const token = localStorage.getItem('token');
        
        // טעינת הזמנות עבודה
        try {
          const workOrdersData = await workOrderService.getWorkOrdersForCalendar(startDate, endDate);
          setWorkOrders(workOrdersData);
        } catch (error) {
          console.warn('Could not load work orders:', error);
          setWorkOrders([]);
        }
        
        // טעינת הערות אישיות מ-localStorage
        const savedNotes = localStorage.getItem('personalNotes');
        if (savedNotes) {
          setPersonalNotes(JSON.parse(savedNotes));
        }
        
        // טעינת פעילויות מה-API באמצעות Service
        try {
          const response = await activityLogService.getActivityLogs({
            start_date: startDate,
            end_date: endDate,
            per_page: 100
          });
          
          const formattedActivities: ActivityEvent[] = response.activities.map((item: ActivityLog) => ({
            id: item.id?.toString() || Math.random().toString(),
            title: getActivityTitle(item.action),
            description: getActivityDescription(item),
            type: mapActivityType(item.activity_type),
            status: item.details?.status || 'completed',
            date: item.created_at?.split('T')[0] || new Date().toISOString().split('T')[0],
            time: item.created_at?.split('T')[1]?.substring(0, 5) || '00:00',
            projectId: item.details?.project_id?.toString() || '',
            projectName: item.details?.project_name || '',
            equipmentType: item.details?.equipment_type,
            canReport: false,
            action: item.action,
            entityType: item.entity_type,
            entityId: item.entity_id,
          }));
          setActivities(formattedActivities);
        } catch (error) {
          console.warn('Could not load activities:', error);
          setActivities([]);
        }
        
        setIsLoading(false);
      } catch (error) {
        console.error("Error fetching data:", error);
        setIsLoading(false);
      }
    };
    
    fetchData();
  }, [currentMonth, currentYear]);
  
  // Generate calendar days
  useEffect(() => {
    const generateCalendarDays = () => {
      const days: CalendarDay[] = [];
      const firstDayOfMonth = new Date(currentYear, currentMonth, 1);
      const firstDayOfWeek = firstDayOfMonth.getDay();
      const startDate = new Date(firstDayOfMonth);
      startDate.setDate(firstDayOfMonth.getDate() - firstDayOfWeek);
      
      for (let i = 0; i < 42; i++) {
        const currentDay = new Date(startDate);
        currentDay.setDate(startDate.getDate() + i);
        
        const isCurrentMonth = currentDay.getMonth() === currentMonth;
        const isToday = currentDay.toDateString() === new Date().toDateString();
        const dateStr = currentDay.toISOString().split('T')[0];
        const holiday = ISRAELI_HOLIDAYS.find(h => h.date === dateStr);
        const dayActivities = activities.filter(a => a.date === dateStr);
        const dayWorkOrders = workOrders.filter(wo => wo.date === dateStr);
        const dayPersonalNotes = personalNotes.filter(note => note.date === dateStr);
        
        days.push({
          date: currentDay,
          activities: dayActivities,
          workOrders: dayWorkOrders,
          personalNotes: dayPersonalNotes,
          isCurrentMonth,
          isToday,
          isHoliday: !!holiday,
          holidayName: holiday?.name
        });
      }
      
      setCalendarDays(days);
      
      if (currentMonth === today.getMonth() && currentYear === today.getFullYear()) {
        const todayDay = days.find(day => day.isToday);
        if (todayDay) setSelectedDay(todayDay);
      }
    };
    
    generateCalendarDays();
  }, [activities, workOrders, personalNotes, currentMonth, currentYear]);
  
  const goToPreviousMonth = () => {
    const newDate = new Date(currentYear, currentMonth - 1, 1);
    setCurrentMonth(newDate.getMonth());
    setCurrentYear(newDate.getFullYear());
  };
  
  const goToNextMonth = () => {
    const newDate = new Date(currentYear, currentMonth + 1, 1);
    setCurrentMonth(newDate.getMonth());
    setCurrentYear(newDate.getFullYear());
  };
  
  const goToToday = () => {
    setCurrentMonth(today.getMonth());
    setCurrentYear(today.getFullYear());
    const todayDay = calendarDays.find(day => day.isToday);
    if (todayDay) setSelectedDay(todayDay);
  };
  
  const addPersonalNote = () => {
    if (!newNote.title.trim() || !selectedDay) return;
    
    const note: PersonalNote = {
      id: Date.now().toString(),
      title: newNote.title,
      content: newNote.content,
      date: selectedDay.date.toISOString().split('T')[0],
      createdAt: new Date().toISOString()
    };
    
    const updatedNotes = [...personalNotes, note];
    setPersonalNotes(updatedNotes);
    localStorage.setItem('personalNotes', JSON.stringify(updatedNotes));
    setNewNote({title: '', content: ''});
    setShowAddNote(false);
  };
  
  const deletePersonalNote = (noteId: string) => {
    const updatedNotes = personalNotes.filter(note => note.id !== noteId);
    setPersonalNotes(updatedNotes);
    localStorage.setItem('personalNotes', JSON.stringify(updatedNotes));
  };
  
  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'equipment_approval':
      case 'equipment_request':
        return <Truck className="w-4 h-4" />;
      case 'work_hours':
      case 'work_hours_approval':
        return <Clock className="w-4 h-4" />;
      case 'project':
        return <TreePine className="w-4 h-4" />;
      case 'system':
        return <User className="w-4 h-4" />;
      default:
        return <Briefcase className="w-4 h-4" />;
    }
  };
  
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return <span className="inline-block px-2 py-0.5 text-xs rounded-full bg-yellow-100 text-yellow-700">ממתין</span>;
      case 'approved':
        return <span className="inline-block px-2 py-0.5 text-xs rounded-full bg-green-100 text-green-700">אושר</span>;
      case 'rejected':
        return <span className="inline-block px-2 py-0.5 text-xs rounded-full bg-red-100 text-red-700">נדחה</span>;
      case 'completed':
        return <span className="inline-block px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-700">הושלם</span>;
      default:
        return null;
    }
  };

  const weekDays = ["א'", "ב'", "ג'", "ד'", "ה'", "ו'", "ש'"];
  
  // Filter activities based on selected filters
  const getFilteredActivities = (dayActivities: ActivityEvent[]) => {
    return dayActivities.filter(activity => {
      // Filter by type
      if (activeFilter !== 'all') {
        if (activeFilter === 'orders' && activity.type !== 'equipment_request' && activity.type !== 'equipment_approval') return false;
        if (activeFilter === 'worklogs' && activity.type !== 'work_hours' && activity.type !== 'work_hours_approval') return false;
        if (activeFilter === 'support' && activity.entityType !== 'support_ticket') return false;
        if (activeFilter === 'system' && activity.type !== 'system') return false;
      }
      // Filter by status
      if (statusFilter !== 'all' && activity.status !== statusFilter) return false;
      return true;
    });
  };
  
  // Get all activities for list view (sorted by date)
  const allActivitiesSorted = [...activities].sort((a, b) => 
    new Date(b.date + 'T' + b.time).getTime() - new Date(a.date + 'T' + a.time).getTime()
  );
  
  const filteredActivitiesList = getFilteredActivities(allActivitiesSorted);
  
  if (isLoading) {
    return (
      <div className="min-h-screen bg-kkl-bg flex items-center justify-center" dir="rtl">
        <div className="flex items-center gap-3 bg-white p-6 rounded-xl shadow-sm">
          <div className="w-6 h-6 border-2 border-kkl-green border-t-transparent rounded-full animate-spin" />
          <span className="text-kkl-text">טוען יומן פעילות...</span>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-kkl-bg" dir="rtl">
      {/* Header with Filters */}
      <div className="sticky top-0 z-20 bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Title Row */}
          <div className="py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-lg flex items-center justify-center text-white">
                <Activity className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">יומן פעילות</h1>
                <p className="text-sm text-gray-500">כל העדכונים והפעילויות במקום אחד</p>
              </div>
            </div>
            
            {/* View Toggle */}
            <div className="flex items-center gap-2 bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('calendar')}
                className={`p-2 rounded-md transition-colors ${viewMode === 'calendar' ? 'bg-white shadow-sm text-green-600' : 'text-gray-500 hover:text-gray-700'}`}
                title="תצוגת לוח שנה"
              >
                <Grid3X3 className="w-5 h-5" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded-md transition-colors ${viewMode === 'list' ? 'bg-white shadow-sm text-green-600' : 'text-gray-500 hover:text-gray-700'}`}
                title="תצוגת רשימה"
              >
                <List className="w-5 h-5" />
              </button>
            </div>
          </div>
          
          {/* Filter Tabs */}
          <div className="pb-3 flex items-center gap-4 overflow-x-auto">
            <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
              {filterTabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveFilter(tab.id as any)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    activeFilter === tab.id 
                      ? 'bg-white shadow-sm text-green-600' 
                      : 'text-gray-600 hover:text-gray-800'
                  }`}
                >
                  {tab.icon}
                  <span className="hidden sm:inline">{tab.label}</span>
                </button>
              ))}
            </div>
            
            <div className="h-6 w-px bg-gray-200" />
            
            <div className="flex items-center gap-1">
              {statusTabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setStatusFilter(tab.id as any)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    statusFilter === tab.id 
                      ? 'bg-green-100 text-green-700' 
                      : 'text-gray-600 hover:bg-gray-100'
                  } ${tab.color || ''}`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {viewMode === 'list' ? (
          /* List View */
          <div className="space-y-3">
            {filteredActivitiesList.length === 0 ? (
              <div className="bg-white rounded-xl shadow-sm border p-12 text-center">
                <Activity className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">אין פעילויות להצגה</p>
              </div>
            ) : (
              filteredActivitiesList.map((activity) => (
                <div
                  key={activity.id}
                  onClick={() => {
                    if (activity.projectId) navigate(`/projects/${activity.projectId}`);
                    else if (activity.type === 'equipment_request') navigate('/work-orders');
                    else if (activity.type === 'work_hours') navigate('/projects');
                  }}
                  className="bg-white rounded-xl shadow-sm border p-4 hover:shadow-md hover:border-green-300 transition-all cursor-pointer"
                >
                  <div className="flex items-start gap-4">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                      activity.status === 'approved' ? 'bg-green-100 text-green-600' :
                      activity.status === 'rejected' ? 'bg-red-100 text-red-600' :
                      activity.status === 'pending' ? 'bg-yellow-100 text-yellow-600' :
                      'bg-blue-100 text-blue-600'
                    }`}>
                      {getActivityIcon(activity.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <h3 className="font-medium text-gray-900">{activity.title}</h3>
                        {getStatusBadge(activity.status)}
                      </div>
                      {activity.description && (
                        <p className="text-sm text-gray-600 mt-1">{activity.description}</p>
                      )}
                      <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <CalendarIcon className="w-3 h-3" />
                          {new Date(activity.date).toLocaleDateString('he-IL')}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {activity.time}
                        </span>
                        {activity.projectName && (
                          <span className="text-green-600 font-medium">{activity.projectName}</span>
                        )}
                      </div>
                      {/* Support ticket: quick reply button */}
                      {activity.entityType === 'support_ticket' && activity.action === 'support_ticket.created' && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/support`);
                          }}
                          className="mt-2 inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg text-xs font-medium hover:bg-blue-100 transition-colors"
                        >
                          <Send className="w-3 h-3" />
                          ענה בצ׳אט
                        </button>
                      )}
                    </div>
                    <ChevronLeft className="w-5 h-5 text-gray-400 flex-shrink-0" />
                  </div>
                </div>
              ))
            )}
          </div>
        ) : (
        /* Calendar View */
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Calendar Section */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-sm border border-kkl-border overflow-hidden">
              {/* Calendar Header */}
              <div className="px-6 py-4 flex items-center justify-between border-b border-kkl-border">
                <div className="flex items-center gap-3">
                  <CalendarIcon className="w-5 h-5 text-kkl-green" />
                  <h2 className="text-lg font-semibold text-kkl-green">
                    יומן – {getMonthName(currentMonth)} {currentYear}
                  </h2>
                </div>
                
                <div className="flex items-center gap-2">
                  <button 
                    onClick={goToPreviousMonth}
                    className="p-2 hover:bg-kkl-green-light rounded-lg transition-colors"
                  >
                    <ChevronRight className="w-5 h-5 text-kkl-green" />
                  </button>
                  <button
                    onClick={goToToday}
                    className="px-3 py-1.5 text-sm bg-kkl-green-light text-kkl-green rounded-lg hover:bg-kkl-green hover:text-white transition-colors font-medium"
                  >
                    היום
                  </button>
                  <button 
                    onClick={goToNextMonth}
                    className="p-2 hover:bg-kkl-green-light rounded-lg transition-colors"
                  >
                    <ChevronLeft className="w-5 h-5 text-kkl-green" />
                  </button>
                </div>
              </div>
              
              {/* Week Days Header */}
              <div className="grid grid-cols-7 border-b border-kkl-border">
                {weekDays.map((day, index) => (
                  <div 
                    key={index} 
                    className={`py-3 text-center text-sm font-semibold ${
                      index === 6 ? 'text-red-400' : 'text-gray-500'
                    }`}
                  >
                    {day}
                  </div>
                ))}
              </div>
              
              {/* Calendar Grid */}
              <div className="grid grid-cols-7">
                {calendarDays.map((day, index) => {
                  const hasEvents = day.activities.length > 0 || day.workOrders.length > 0 || day.personalNotes.length > 0;
                  const isSelected = selectedDay && day.date.toDateString() === selectedDay.date.toDateString();
                  
                  return (
                    <button
                      key={index}
                      onClick={() => setSelectedDay(day)}
                      className={`
                        min-h-[90px] p-2 border-b border-l border-kkl-border text-right transition-all
                        ${!day.isCurrentMonth ? 'bg-gray-50' : 'bg-white hover:bg-kkl-green-light/30'}
                        ${day.isToday ? 'bg-kkl-green-light' : ''}
                        ${isSelected ? 'ring-2 ring-inset ring-kkl-green' : ''}
                      `}
                    >
                      {/* Day Number */}
                      <div className="flex items-center justify-between mb-1">
                        <span className={`
                          text-sm font-medium
                          ${!day.isCurrentMonth ? 'text-gray-300' : 'text-kkl-text'}
                          ${day.isToday ? 'w-7 h-7 bg-kkl-green text-white rounded-full flex items-center justify-center' : ''}
                          ${day.date.getDay() === 6 && day.isCurrentMonth ? 'text-red-400' : ''}
                        `}>
                          {day.date.getDate()}
                        </span>
                        {day.isHoliday && day.isCurrentMonth && (
                          <span className="text-[10px] text-red-400 font-medium truncate max-w-[60px]">
                            {day.holidayName}
                          </span>
                        )}
                      </div>
                      
                      {/* Event Indicators - נקודות ירוקות פשוטות */}
                      {hasEvents && day.isCurrentMonth && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {day.workOrders.length > 0 && (
                            <span className="w-2 h-2 bg-kkl-green rounded-full" />
                          )}
                          {day.activities.length > 0 && (
                            <span className="w-2 h-2 bg-kkl-green rounded-full" />
                          )}
                          {day.personalNotes.length > 0 && (
                            <span className="w-2 h-2 bg-kkl-green rounded-full" />
                          )}
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
          
          {/* Day Details Sidebar */}
          <div className="space-y-6">
            {/* Selected Day Info */}
            <div className="bg-white rounded-xl shadow-sm border border-kkl-border overflow-hidden">
              <div className="bg-kkl-green p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-white/70 text-sm">יום נבחר</p>
                    <h3 className="text-lg font-bold text-white">
                      {selectedDay ? (
                        <>
                          יום {getDayName(selectedDay.date)}
                          <span className="text-white/70 font-normal mr-2 text-sm">
                            {selectedDay.date.getDate()} {getMonthName(selectedDay.date.getMonth())}
                          </span>
                        </>
                      ) : 'בחר יום'}
                    </h3>
                  </div>
                  <button
                    onClick={() => setShowAddNote(true)}
                    className="p-2 bg-white/20 rounded-lg hover:bg-white/30 transition-colors"
                    title="הוסף הערה"
                  >
                    <Plus className="w-5 h-5 text-white" />
                  </button>
                </div>
              </div>
              
              <div className="p-4 space-y-3 max-h-[400px] overflow-y-auto">
                {selectedDay ? (
                  <>
                    {/* Holiday Notice */}
                    {selectedDay.isHoliday && (
                      <div className="bg-kkl-green-light border border-kkl-green/20 rounded-lg p-3 flex items-center gap-3">
                        <CalendarIcon className="w-5 h-5 text-kkl-green" />
                        <div>
                          <p className="font-medium text-kkl-green">{selectedDay.holidayName}</p>
                          <p className="text-sm text-gray-500">חג</p>
                        </div>
                      </div>
                    )}
                    
                    {/* Work Orders */}
                    {selectedDay.workOrders.map((wo) => (
                      <button
                        key={wo.id}
                        onClick={() => navigate(`/work-orders/${wo.data.id || wo.id}`)}
                        className="w-full text-right bg-white border border-kkl-border rounded-lg p-3 hover:border-kkl-green hover:shadow-sm transition-all cursor-pointer group"
                      >
                        <div className="flex items-start gap-3">
                          <div className="w-8 h-8 bg-kkl-green-light rounded-lg flex items-center justify-center flex-shrink-0">
                            <Hammer className="w-4 h-4 text-kkl-green" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <h4 className="font-medium text-kkl-text text-sm truncate group-hover:text-kkl-green transition-colors">{wo.title}</h4>
                            <p className="text-xs text-gray-500 mt-1 line-clamp-1">{wo.data.description}</p>
                            <span className="inline-block mt-2 text-xs px-2 py-0.5 rounded-full bg-kkl-green-light text-kkl-green">
                              {workOrderService.getStatusText(wo.data.status)}
                            </span>
                          </div>
                          <ChevronLeft className="w-4 h-4 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 self-center" />
                        </div>
                      </button>
                    ))}
                    
                    {/* Activities from Backend API */}
                    {selectedDay.activities.map((activity) => (
                      <button
                        key={activity.id}
                        onClick={() => {
                          // Navigate to related entity
                          if (activity.projectId) {
                            navigate(`/projects/${activity.projectId}`);
                          } else if (activity.type === 'equipment_request' || activity.type === 'equipment_approval') {
                            navigate('/work-orders');
                          } else if (activity.type === 'work_hours' || activity.type === 'work_hours_approval') {
                            navigate('/projects');
                          }
                        }}
                        className="w-full text-right bg-white border border-kkl-border rounded-lg p-3 hover:border-kkl-green hover:shadow-sm transition-all cursor-pointer group"
                      >
                        <div className="flex items-start gap-3">
                          <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                            activity.status === 'approved' ? 'bg-green-100 text-green-600' :
                            activity.status === 'rejected' ? 'bg-red-100 text-red-600' :
                            activity.status === 'pending' ? 'bg-yellow-100 text-yellow-600' :
                            'bg-kkl-green-light text-kkl-green'
                          }`}>
                            {getActivityIcon(activity.type)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between gap-2">
                              <h4 className="font-medium text-kkl-text text-sm truncate group-hover:text-kkl-green transition-colors">{activity.title}</h4>
                              {getStatusBadge(activity.status)}
                            </div>
                            <p className="text-xs text-gray-500 mt-1 line-clamp-2">{activity.description}</p>
                            <div className="flex items-center gap-2 mt-2">
                              <span className="text-xs text-gray-400 flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {activity.time}
                              </span>
                              {activity.projectName && (
                                <span className="text-xs text-kkl-green font-medium">{activity.projectName}</span>
                              )}
                            </div>
                          </div>
                          <ChevronLeft className="w-4 h-4 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 self-center" />
                        </div>
                      </button>
                    ))}
                    
                    {/* Personal Notes */}
                    {selectedDay.personalNotes.map((note) => (
                      <div
                        key={note.id}
                        className="bg-white border border-kkl-border rounded-lg p-3"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex items-start gap-3 flex-1 min-w-0">
                            <div className="w-8 h-8 bg-kkl-green-light rounded-lg flex items-center justify-center flex-shrink-0">
                              <PenLine className="w-4 h-4 text-kkl-green" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <h4 className="font-medium text-kkl-text text-sm">{note.title}</h4>
                              <p className="text-xs text-gray-500 mt-1">{note.content}</p>
                            </div>
                          </div>
                          <button
                            onClick={() => deletePersonalNote(note.id)}
                            className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                    
                    {/* Empty State */}
                    {selectedDay.activities.length === 0 && 
                     selectedDay.workOrders.length === 0 && 
                     selectedDay.personalNotes.length === 0 &&
                     !selectedDay.isHoliday && (
                      <div className="text-center py-8">
                        <div className="w-14 h-14 bg-kkl-green-light rounded-full flex items-center justify-center mx-auto mb-3">
                          <CalendarIcon className="w-7 h-7 text-kkl-green" />
                        </div>
                        <p className="text-gray-500 text-sm">אין אירועים ליום זה</p>
                        <button
                          onClick={() => setShowAddNote(true)}
                          className="mt-3 text-kkl-green hover:text-kkl-green-dark font-medium text-sm"
                        >
                          + הוסף הערה
                        </button>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-gray-500">בחר יום מהלוח שנה</p>
                  </div>
                )}
              </div>
            </div>
            
            {/* Quick Stats */}
            <div className="bg-white rounded-xl shadow-sm border border-kkl-border p-4">
              <h3 className="font-semibold text-kkl-text mb-4">סיכום החודש</h3>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-kkl-green-light rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-kkl-green">
                    {activities.filter(a => a.status === 'completed').length}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">משימות הושלמו</p>
                </div>
                <div className="bg-kkl-green-light rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-kkl-green">
                    {activities.filter(a => a.status === 'pending').length}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">ממתינות לאישור</p>
                </div>
                <div className="bg-kkl-green-light rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-kkl-green">
                    {workOrders.length}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">הזמנות עבודה</p>
                </div>
                <div className="bg-kkl-green-light rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-kkl-green">
                    {personalNotes.length}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">הערות אישיות</p>
                </div>
              </div>
            </div>
          </div>
        </div>
        )}
      </div>
      
      {/* Add Note Modal */}
      {showAddNote && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          onClick={() => setShowAddNote(false)}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden"
          >
            <div className="bg-kkl-green p-4 flex items-center justify-between">
              <h3 className="text-lg font-bold text-white">הערה חדשה</h3>
              <button
                onClick={() => setShowAddNote(false)}
                className="p-1 hover:bg-white/20 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-white" />
              </button>
            </div>
            
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-kkl-text mb-2">כותרת</label>
                <input
                  type="text"
                  value={newNote.title}
                  onChange={(e) => setNewNote({...newNote, title: e.target.value})}
                  className="w-full px-4 py-3 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent transition-all"
                  placeholder="הכנס כותרת..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-kkl-text mb-2">תוכן</label>
                <textarea
                  value={newNote.content}
                  onChange={(e) => setNewNote({...newNote, content: e.target.value})}
                  className="w-full px-4 py-3 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent transition-all resize-none"
                  rows={4}
                  placeholder="הכנס תוכן..."
                />
              </div>
              
              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => setShowAddNote(false)}
                  className="flex-1 px-4 py-3 border border-kkl-border text-kkl-text rounded-lg hover:bg-gray-50 transition-colors font-medium"
                >
                  ביטול
                </button>
                <button
                  onClick={addPersonalNote}
                  disabled={!newNote.title.trim()}
                  className="flex-1 px-4 py-3 bg-kkl-green text-white rounded-lg hover:bg-kkl-green-dark transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  שמור
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ActivityLogNew;
