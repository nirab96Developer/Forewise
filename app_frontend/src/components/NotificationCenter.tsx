// src/components/NotificationCenter.tsx
// פעמון התראות עם Polling אמיתי מהשרת
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Bell, X, Check, Trash2, AlertCircle, Info, CheckCircle, ExternalLink, RefreshCw, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';

interface Notification {
  id: number;
  title: string;
  message: string;
  description?: string;
  time?: Date | string;
  notification_type: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  is_read: boolean;
  created_at: string;
  project_name?: string;
  project_code?: string;
  work_order_id?: number;
  work_order_number?: string;
  worklog_id?: number;
  supplier_name?: string;
  entity_type?: string;
  entity_id?: number;
  action_url?: string;
}

interface NotificationCenterProps {
  userId: number;
}

// Polling interval in milliseconds (30 seconds)
const POLLING_INTERVAL = 30000;

const NotificationCenter: React.FC<NotificationCenterProps> = ({ userId }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [lastPoll, setLastPoll] = useState<Date | null>(null);
  const location = useLocation();
  const navigate = useNavigate();
  const notificationRef = useRef<HTMLDivElement>(null);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  // סגירת הדרופדאון כשעוברים בין דפים
  useEffect(() => {
    setIsOpen(false);
  }, [location.pathname]);

  // סגירת הדרופדאון כשלוחצים מחוץ
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (notificationRef.current && !notificationRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  // Load notifications from API
  const loadNotifications = useCallback(async (silent = false) => {
    try {
      if (!silent) setIsLoading(true);
      const token = localStorage.getItem('access_token');
      if (!token) {
        console.warn('No access token found');
        return;
      }
      
      // Try to fetch from notifications API
      try {
        const response = await api.get('/notifications/', {
          params: { limit: 20, unread_only: false }
        });
        
        if (response.data && Array.isArray(response.data.items || response.data)) {
          const items = response.data.items || response.data;
          setNotifications(items);
          setUnreadCount(items.filter((n: Notification) => !n.is_read).length);
          setLastPoll(new Date());
          return;
        }
      } catch (notifError: any) {
        // Notifications API might not be ready, try activity logs as fallback
        if (notifError?.response?.status === 404 || notifError?.response?.status === 307) {
          console.log('Notifications API not available, using activity logs as fallback');
        } else {
          console.warn('Notifications fetch error:', notifError?.message);
        }
      }
      
      // Fallback: Use activity logs as notifications
      try {
        const activityResponse = await api.get('/activity-logs/', {
          params: { limit: 10, user_id: userId }
        });
        
        if (activityResponse.data && Array.isArray(activityResponse.data.items || activityResponse.data)) {
          const items = activityResponse.data.items || activityResponse.data;
          // Convert activity logs to notification format
          const notifs: Notification[] = items.slice(0, 10).map((log: any) => ({
            id: log.id,
            title: getActivityTitle(log.action || log.activity_type),
            message: log.details?.description_he || log.action || 'פעילות במערכת',
            notification_type: log.activity_type || 'activity',
            priority: 'medium' as const,
            is_read: true, // Activity logs don't have read status
            created_at: log.created_at,
            entity_type: log.entity_type,
            entity_id: log.entity_id,
            project_code: log.details?.project_code,
            work_order_id: log.details?.work_order_id,
            worklog_id: log.details?.worklog_id,
          }));
          
          setNotifications(notifs);
          setUnreadCount(0); // No unread for activity logs
          setLastPoll(new Date());
        }
      } catch (activityError) {
        console.warn('Activity logs fetch error:', activityError);
        setNotifications([]);
        setUnreadCount(0);
      }
      
    } catch (error) {
      console.error('Error loading notifications:', error);
      setNotifications([]);
      setUnreadCount(0);
    } finally {
      if (!silent) setIsLoading(false);
    }
  }, [userId]);

  // Helper to generate activity titles in Hebrew
  const getActivityTitle = (action: string): string => {
    const titles: Record<string, string> = {
      'work_order.created': 'הזמנת עבודה נוצרה',
      'work_order.approved': 'הזמנת עבודה אושרה',
      'work_order.rejected': 'הזמנת עבודה נדחתה',
      'work_order.sent_to_supplier': 'הזמנה נשלחה לספק',
      'worklog.created': 'דיווח שעות נוצר',
      'worklog.submitted': 'דיווח שעות הוגש',
      'worklog.approved': 'דיווח שעות אושר',
      'worklog.rejected': 'דיווח שעות נדחה',
      'supplier.confirmed': 'ספק אישר הזמנה',
      'supplier.declined': 'ספק דחה הזמנה',
      'equipment.scanned': 'ציוד נסרק',
      'invoice.created': 'חשבונית נוצרה',
      'invoice.approved': 'חשבונית אושרה',
      'user.login': 'כניסה למערכת',
    };
    return titles[action] || 'פעילות במערכת';
  };

  // Initial load + Polling setup
  useEffect(() => {
    if (userId > 0) {
      loadNotifications();
      
      // Setup polling
      pollingRef.current = setInterval(() => {
        loadNotifications(true); // Silent refresh
      }, POLLING_INTERVAL);
    }
    
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, [userId, loadNotifications]);

  const markAsRead = async (notificationId: number) => {
    try {
      // Try to mark as read on server
      try {
        await api.patch(`/notifications/${notificationId}/read`);
      } catch {
        // Ignore if endpoint doesn't exist
      }
      
      setNotifications(prev => 
        prev.map(n => 
          n.id === notificationId ? { ...n, is_read: true } : n
        )
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      // Try to mark all as read on server
      try {
        await api.patch('/notifications/read-all');
      } catch {
        // Ignore if endpoint doesn't exist
      }
      
      setNotifications(prev => 
        prev.map(n => ({ ...n, is_read: true }))
      );
      setUnreadCount(0);
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
    }
  };

  const deleteNotification = async (notificationId: number) => {
    try {
      // Try to delete on server
      try {
        await api.delete(`/notifications/${notificationId}`);
      } catch {
        // Ignore if endpoint doesn't exist
      }
      
      setNotifications(prev => prev.filter(n => n.id !== notificationId));
      setUnreadCount(prev => {
        const notification = notifications.find(n => n.id === notificationId);
        return notification && !notification.is_read ? prev - 1 : prev;
      });
    } catch (error) {
      console.error('Error deleting notification:', error);
    }
  };
  
  // Navigate to the related entity
  const openNotification = (notification: Notification) => {
    markAsRead(notification.id);
    setIsOpen(false);
    
    // Determine where to navigate based on entity type
    if (notification.action_url) {
      navigate(notification.action_url);
      return;
    }
    
    if (notification.project_code) {
      if (notification.worklog_id) {
        navigate(`/projects/${notification.project_code}/workspace/work-logs/${notification.worklog_id}`);
      } else {
        navigate(`/projects/${notification.project_code}/workspace`);
      }
      return;
    }
    
    if (notification.work_order_id) {
      navigate(`/work-orders/${notification.work_order_id}`);
      return;
    }
    
    if (notification.worklog_id) {
      navigate('/projects');
      return;
    }
    
    if (notification.entity_type && notification.entity_id) {
      const routes: Record<string, string> = {
        'work_order': '/work-orders',
        'worklog': '/projects',
        'project': '/projects',
        'equipment': '/equipment',
        'invoice': '/invoices',
        'supplier': '/suppliers',
      };
      const basePath = routes[notification.entity_type];
      if (basePath) {
        navigate(`${basePath}/${notification.entity_id}`);
        return;
      }
    }
    
    // Default: go to activity log
    navigate('/activity-log');
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'text-red-600 bg-red-50 border-red-200';
      case 'high': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'medium': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'low': return 'text-gray-600 bg-gray-50 border-gray-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'critical': return <AlertCircle className="w-4 h-4" />;
      case 'high': return <AlertCircle className="w-4 h-4" />;
      case 'medium': return <Info className="w-4 h-4" />;
      case 'low': return <CheckCircle className="w-4 h-4" />;
      default: return <Info className="w-4 h-4" />;
    }
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
      
      if (diffInHours < 1) return 'לפני כמה דקות';
      if (diffInHours < 24) return `לפני ${diffInHours} שעות`;
      if (diffInHours < 48) return 'אתמול';
      return date.toLocaleDateString('he-IL');
    } catch (error) {
      console.error('Error formatting date:', error);
      return 'לא ידוע';
    }
  };

  return (
    <div className="relative" ref={notificationRef}>
      {/* Notification Bell - עם Badge מספרי */}
      <button
        data-testid="topbar-notifications"
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-white hover:bg-white/10 rounded-lg transition-colors"
        aria-label={`התראות${unreadCount > 0 ? ` (${unreadCount} חדשות)` : ''}`}
      >
        <Bell className="w-6 h-6" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full min-w-[20px] h-5 flex items-center justify-center px-1 border-2 border-white shadow-lg animate-pulse">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Overlay - לסגירה כשלוחצים מחוץ */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Notification Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="fixed left-4 top-20 w-96 max-w-[calc(100vw-2rem)] bg-white rounded-lg shadow-xl border border-gray-200 z-50 max-h-[calc(100vh-6rem)] overflow-hidden flex flex-col"
          >
            {/* Header */}
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">התראות</h3>
                <div className="flex items-center gap-2">
                  {unreadCount > 0 && (
                    <button
                      onClick={markAllAsRead}
                      className="text-sm text-blue-600 hover:text-blue-800"
                    >
                      סמן הכל כנקרא
                    </button>
                  )}
                  <button
                    onClick={() => setIsOpen(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            {/* Notifications List */}
            <div className="flex-1 overflow-y-auto min-h-0">
              {isLoading ? (
                <div className="p-8 text-center">
                  <RefreshCw className="w-8 h-8 text-gray-400 animate-spin mx-auto mb-3" />
                  <p className="text-gray-500">טוען התראות...</p>
                </div>
              ) : notifications.length === 0 ? (
                <div className="p-8 text-center">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <CheckCircle className="w-8 h-8 text-green-500" />
                  </div>
                  <h4 className="text-lg font-medium text-gray-900 mb-2">הכול מעודכן!</h4>
                  <p className="text-gray-500 text-sm">אין התראות חדשות כרגע</p>
                  {lastPoll && (
                    <p className="text-xs text-gray-400 mt-3">
                      עודכן לאחרונה: {lastPoll.toLocaleTimeString('he-IL')}
                    </p>
                  )}
                </div>
              ) : (
                notifications.map((notification) => {
                  // בדיקה שההתראה תקינה
                  if (!notification || typeof notification !== 'object') {
                    return null;
                  }
                  
                  return (
                    <motion.div
                      key={notification.id || Math.random()}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className={`p-4 border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                        !notification.is_read ? 'bg-blue-50' : ''
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        {/* Priority Icon */}
                        <div className={`p-1 rounded-full ${getPriorityColor(notification.priority || 'low')}`}>
                          {getPriorityIcon(notification.priority || 'low')}
                        </div>

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between">
                            <h4 className={`text-sm font-medium ${
                              !notification.is_read ? 'text-gray-900' : 'text-gray-700'
                            }`}>
                              {notification.title || 'התראה ללא כותרת'}
                            </h4>
                            <div className="flex items-center gap-1 ml-2">
                              {!notification.is_read && (
                                <button
                                  onClick={() => markAsRead(notification.id)}
                                  className="text-gray-400 hover:text-gray-600"
                                  title="סמן כנקרא"
                                >
                                  <Check className="w-3 h-3" />
                                </button>
                              )}
                              <button
                                onClick={() => deleteNotification(notification.id)}
                                className="text-gray-400 hover:text-red-600"
                                title="מחק"
                              >
                                <Trash2 className="w-3 h-3" />
                              </button>
                            </div>
                          </div>
                          
                          <p className="text-sm text-gray-600 mt-1">
                            {notification.message || notification.description || 'אין תיאור'}
                          </p>
                          
                          {/* Metadata */}
                          <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
                            <span>{formatDate(notification.created_at || (typeof notification.time === 'string' ? notification.time : notification.time?.toISOString()) || new Date().toISOString())}</span>
                            {notification.project_name && (
                              <>
                                <span>•</span>
                                <span>{notification.project_name}</span>
                              </>
                            )}
                            {notification.work_order_number && (
                              <>
                                <span>•</span>
                                <span>{notification.work_order_number}</span>
                              </>
                            )}
                          </div>
                          
                          {/* Open Button */}
                          <button
                            onClick={() => openNotification(notification)}
                            className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
                          >
                            <ExternalLink className="w-3 h-3" />
                            פתח
                          </button>
                        </div>
                      </div>
                    </motion.div>
                  );
                })
              )}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-gray-200 bg-gray-50">
              <div className="flex items-center justify-between gap-3">
                <button
                  onClick={() => {
                    setIsOpen(false);
                    navigate('/activity-log');
                  }}
                  className="text-sm font-medium text-gray-700 hover:text-gray-900 flex items-center gap-1"
                >
                  <Activity className="w-4 h-4" />
                  יומן פעילות מלא
                </button>
                <button
                  onClick={() => loadNotifications()}
                  disabled={isLoading}
                  className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1 disabled:opacity-50"
                >
                  <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                  רענן
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default NotificationCenter;
