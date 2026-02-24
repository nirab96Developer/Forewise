// @ts-nocheck
// src/pages/Notifications/Notifications.tsx
import React, { useState, useEffect } from 'react';
import { Bell, AlertTriangle, Info, CheckCircle, XCircle, Loader2, Eye, Trash2 } from 'lucide-react';
import notificationService from '../../services/notificationService';

interface Notification {
  id: number;
  title: string;
  message: string;
  type: 'info' | 'warning' | 'error' | 'success';
  is_read: boolean;
  created_at: string;
}

const Notifications: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('all');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await notificationService.getNotifications();
      
      // Handle both array and object response
      const notificationsList = Array.isArray(response) 
        ? response 
        : (response.notifications || response.items || []);
      
      // Transform API response to component format
      const transformed: Notification[] = notificationsList.map((notif: any) => ({
        id: notif.id,
        title: notif.title || 'התראה',
        message: notif.message || notif.description || '',
        type: (notif.type || 'info') as 'info' | 'warning' | 'error' | 'success',
        is_read: notif.is_read || false,
        created_at: notif.created_at || notif.createdAt || new Date().toISOString()
      }));
      
      setNotifications(transformed);
    } catch (error) {
      console.error('Error fetching notifications:', error);
      setError('שגיאה בטעינת התראות');
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (id: number) => {
    try {
      await notificationService.markAsRead(id);
      setNotifications(prev => prev.map(notification => 
        notification.id === id ? { ...notification, is_read: true } : notification
      ));
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await notificationService.markAllAsRead();
      setNotifications(prev => prev.map(notification => 
        ({ ...notification, is_read: true })
      ));
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
    }
  };

  const deleteNotification = async (id: number) => {
    try {
      await notificationService.deleteNotification(id);
      setNotifications(prev => prev.filter(notification => notification.id !== id));
    } catch (error) {
      console.error('Error deleting notification:', error);
    }
  };
  
  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);
      
      if (diffMins < 1) return 'עכשיו';
      if (diffMins < 60) return `לפני ${diffMins} דקות`;
      if (diffHours < 24) return `לפני ${diffHours} שעות`;
      if (diffDays < 7) return `לפני ${diffDays} ימים`;
      return date.toLocaleDateString('he-IL', { day: 'numeric', month: 'short', year: 'numeric' });
    } catch (e) {
      return timestamp;
    }
  };

  const filteredNotifications = notifications.filter(notification => 
    filterType === 'all' || notification.type === filterType
  );

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'info':
      default:
        return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'warning':
        return 'border-l-yellow-500 bg-yellow-50';
      case 'error':
        return 'border-l-red-500 bg-red-50';
      case 'success':
        return 'border-l-green-500 bg-green-50';
      case 'info':
      default:
        return 'border-l-blue-500 bg-blue-50';
    }
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-white p-8 rounded-lg shadow-lg flex flex-col items-center">
          <Loader2 className="w-8 h-8 text-kkl-green animate-spin mb-4" />
          <p className="text-gray-600 font-medium">טוען התראות...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8 animate-fadeIn">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center">
                <Bell className="w-8 h-8 ml-3 text-kkl-green" />
                התראות
                {unreadCount > 0 && (
                  <span className="bg-red-500 text-white text-sm rounded-full px-3 py-1 mr-3 animate-pulse">
                    {unreadCount}
                  </span>
                )}
              </h1>
              <p className="text-gray-600">ניהול התראות ומסרים במערכת</p>
            </div>
            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                className="bg-gradient-to-r from-kkl-green to-green-600 hover:from-green-600 hover:to-green-700 text-white px-6 py-3 rounded-lg flex items-center shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105"
              >
                <Eye className="w-5 h-5 ml-2" />
                סמן הכל כנקרא
              </button>
            )}
          </div>

          {/* Filter */}
          <div className="animate-slideIn">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent shadow-sm hover:shadow-md transition-shadow min-w-[200px]"
            >
              <option value="all">כל ההתראות</option>
              <option value="info">מידע</option>
              <option value="warning">אזהרה</option>
              <option value="error">שגיאה</option>
              <option value="success">הצלחה</option>
            </select>
          </div>
        </div>

        {/* Notifications List */}
        <div className="space-y-4">
          {filteredNotifications.map((notification, index) => (
            <div 
              key={notification.id} 
              className={`bg-white rounded-xl shadow-lg p-6 border-l-4 ${getTypeColor(notification.type)} ${
                !notification.is_read ? 'ring-2 ring-blue-200' : ''
              } hover:shadow-xl transition-all duration-300 hover:scale-[1.02] animate-fadeIn`}
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="flex justify-between items-start">
                <div className="flex items-start space-x-3 space-x-reverse">
                  <div className="mt-1">
                    {getTypeIcon(notification.type)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 space-x-reverse">
                      <h3 className={`text-lg font-bold ${
                        !notification.is_read ? 'text-gray-900' : 'text-gray-700'
                      }`}>
                        {notification.title}
                      </h3>
                      {!notification.is_read && (
                        <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
                      )}
                    </div>
                    <p className="text-gray-600 mt-2 leading-relaxed">{notification.message}</p>
                    <p className="text-sm text-gray-500 mt-3 font-medium">{formatTimestamp(notification.created_at)}</p>
                  </div>
                </div>
                
                <div className="flex space-x-2 space-x-reverse">
                  {!notification.is_read && (
                    <button
                      onClick={() => markAsRead(notification.id)}
                      className="bg-blue-100 hover:bg-blue-200 text-blue-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center"
                    >
                      <Eye className="w-4 h-4 ml-1" />
                      סמן כנקרא
                    </button>
                  )}
                  <button
                    onClick={() => deleteNotification(notification.id)}
                    className="bg-red-100 hover:bg-red-200 text-red-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center"
                  >
                    <Trash2 className="w-4 h-4 ml-1" />
                    מחק
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {filteredNotifications.length === 0 && (
          <div className="text-center py-16 animate-fadeIn">
            <div className="bg-white rounded-xl shadow-lg p-12 max-w-md mx-auto">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Bell className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">אין התראות</h3>
              <p className="text-gray-600 mb-6">אין התראות להצגה לפי הסינון הנוכחי</p>
              <button 
                onClick={() => setFilterType('all')}
                className="bg-kkl-green hover:bg-green-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
              >
                הצג הכל
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Notifications;
