// src/services/api.ts
import axios, { AxiosInstance } from 'axios';
import { debugLogger } from '../utils/debug';
import { clearAuthSession, getAccessToken, getRefreshTokenWithStorage } from '../utils/authStorage';

// קביעת base URL מה-ENV או מה-hostname הנוכחי
const API_BASE_URL =
  import.meta.env.VITE_API_URL || 
  `/api/v1`;

const TIMEOUT =
  Number(import.meta.env.VITE_API_TIMEOUT) || 60000; // 60 seconds for slow queries

// יצירת instance של axios עם הגדרות בסיסיות
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor להוספת token לכל בקשה
api.interceptors.request.use(
  (config) => {
    const startTime = Date.now();
    (config as any).startTime = startTime;
    
    // Note: Removed trailing slash addition as it causes redirect issues with FastAPI
    
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // הוספת request ID לכל בקשה
    config.headers['X-Request-ID'] = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // רישום בקשה יוצאת
    debugLogger.logAPIRequest(
      config.method?.toUpperCase() || 'GET',
      `${config.baseURL}${config.url}`,
      config.data,
      config.headers
    );
    
    return config;
  },
  (error) => {
    debugLogger.logAPIError('REQUEST', error.config?.url || 'unknown', error);
    return Promise.reject(error);
  }
);

// Interceptor לטיפול בתגובות
api.interceptors.response.use(
  (response) => {
    const startTime = (response.config as any).startTime;
    const duration = startTime ? Date.now() - startTime : undefined;
    
    // רישום תגובה מוצלחת
    debugLogger.logAPIResponse(
      response.config.method?.toUpperCase() || 'GET',
      `${response.config.baseURL}${response.config.url}`,
      response.status,
      response.data,
      duration
    );
    
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // רישום שגיאת API
    const startTime = (originalRequest as any).startTime;
    const duration = startTime ? Date.now() - startTime : undefined;
    debugLogger.logAPIError(
      originalRequest.method?.toUpperCase() || 'GET',
      `${originalRequest.baseURL}${originalRequest.url}`,
      {
        ...error,
        duration,
      }
    );
    
    // רישום שגיאת רשת אם יש
    if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
      debugLogger.logNetworkError(error.message || 'שגיאת רשת', error);
    }

    // טיפול ב-429 (Rate Limit)
    if (error.response?.status === 429) {
      const retryAfter = error.response.headers['retry-after'] || 1;
      const backoffTime = Math.min(retryAfter * 1000, 5000); // מקסימום 5 שניות
      
      // הצגת הודעה למשתמש
      if ((window as any).showToast) {
        (window as any).showToast(`יותר מדי בקשות. מנסה שוב בעוד ${Math.ceil(backoffTime/1000)} שניות...`, 'warning');
      }
      
      // המתנה לפני ניסיון חוזר
      await new Promise(resolve => setTimeout(resolve, backoffTime));
      return api(originalRequest);
    }

    // אם קיבלנו 401 (לא מאומת) ולא ניסינו כבר לרענן
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const { token: refreshToken, storage } = getRefreshTokenWithStorage();
        if (refreshToken) {
          // Use the same base URL as the API instance
          const baseURL = API_BASE_URL;
          const refreshURL = baseURL.replace('/api/v1', '') + '/api/v1/auth/refresh';
          const response = await axios.post(refreshURL, {
            refresh_token: refreshToken,
          });

          const { access_token } = response.data;
          storage.setItem('access_token', access_token);

          // חזרה לבקשה המקורית עם ה-token החדש
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // אם גם הרענון נכשל, מפנים ללוגין
        debugLogger.logAPIError('POST', '/api/v1/auth/refresh', refreshError);
        clearAuthSession();
        
        // הצגת הודעה למשתמש
        if ((window as any).showToast) {
          (window as any).showToast('התחברות פגה. אנא התחבר שוב.', 'error');
        }
        
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // טיפול בשגיאות אחרות
    if (error.response?.status >= 500) {
      if ((window as any).showToast) {
        (window as any).showToast('שגיאת שרת. אנא נסה שוב מאוחר יותר.', 'error');
      }
    } else if (error.response?.status >= 400) {
      const errorMessage = error.response?.data?.detail || error.response?.data?.message || 'שגיאה לא ידועה';
      if ((window as any).showToast) {
        (window as any).showToast(errorMessage, 'error');
      }
    }

    return Promise.reject(error);
  }
);
export default api;
