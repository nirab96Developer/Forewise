// src/services/authService.ts
import api from './api';

// קבועים לשימוש ב-localStorage, מותאמים לפורמט הקיים של הלוגין
const AUTH_STATUS_KEY = 'isAuthenticated';
const USER_DATA_KEY = 'user';
const USER_NAME_KEY = 'userName';
const REMEMBER_ME_KEY = 'rememberMe';
const SAVED_USERNAME_KEY = 'savedUsername';
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

// ממשק המשתמש המוחזר
interface User {
  id: string;
  name: string;
  role: string;
  roles: string[];
  permissions?: string[];
  email?: string;
  region_id?: number;
  area_id?: number;
}

// פונקציה לכניסה למערכת - מתחברת ל-Backend האמיתי
const login = async (username: string, password: string, remember?: boolean): Promise<{ user: User; success: boolean }> => {
  try {
    // קריאה לשרת האמיתי
    const response = await api.post('/auth/login', {
      username: username,
      password: password
    });

    if (response.data) {
      const data = response.data;
      
      // הגדרת נתוני המשתמש — role from backend is a string code (e.g. "ADMIN")
      const roleCode = data.user.role_code || data.user.role || 'USER';
      const user = {
        id: data.user.id.toString(),
        name: data.user.full_name || data.user.username,
        email: data.user.email,
        role: roleCode,
        roles: data.user.roles || [roleCode],
        permissions: data.user.permissions || [],
        region_id: data.user.region_id,
        area_id: data.user.area_id,
      };
      
      // שמירה בלוקל סטורג'
      localStorage.setItem(AUTH_STATUS_KEY, 'true');
      localStorage.setItem(USER_DATA_KEY, JSON.stringify(user));
      localStorage.setItem(USER_NAME_KEY, user.name);
      localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token);
      if (data.refresh_token) {
        localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
      }
      
      // שמירת זכור אותי אם נבחר
      if (remember) {
        localStorage.setItem(REMEMBER_ME_KEY, 'true');
        localStorage.setItem(SAVED_USERNAME_KEY, username);
      } else {
        localStorage.removeItem(REMEMBER_ME_KEY);
        localStorage.removeItem(SAVED_USERNAME_KEY);
      }
      
      return { user, success: true };
    } else {
      throw new Error('Invalid response from server');
    }
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

// פונקציה ליציאה מהמערכת - חשוב מאוד לנקות את כל הנתונים הרלוונטיים
const logout = () => {
  try {
    // מחיקת האימות והפרטים האישיים
    localStorage.removeItem(AUTH_STATUS_KEY);
    localStorage.removeItem(USER_DATA_KEY);
    localStorage.removeItem(USER_NAME_KEY);
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    
    // לא מוחקים את 'זכור אותי' כדי לשמור על הנוחות למשתמש
    // אבל אפשר להוסיף פרמטר כדי למחוק גם את זה במידת הצורך
    
    // ניקוי נוסף של מטמון אופציונלי
    // sessionStorage.clear();
    
    return true;
  } catch (error) {
    console.error('Logout error:', error);
    return false;
  }
};

// בדיקה האם המשתמש מחובר - בדיקה על פי המפתח הרלוונטי
const isAuthenticated = (): boolean => {
  const isAuth = localStorage.getItem(AUTH_STATUS_KEY);
  return isAuth === 'true';
};

// קבלת פרטי המשתמש הנוכחי
const getCurrentUser = (): User | null => {
  const userDataStr = localStorage.getItem(USER_DATA_KEY);
  if (!userDataStr) return null;
  
  try {
    return JSON.parse(userDataStr);
  } catch (error) {
    console.error('Error parsing user data:', error);
    return null;
  }
};

// Refresh the cached user from the BE (`GET /users/me`).
//
// Phase 2.2 — until now `getCurrentUser()` only ever read localStorage.
// If an admin changed someone's role/region/area while they were logged
// in, the user kept their stale permissions until logout. After every
// successful login (and on demand from the UI) we re-pull the canonical
// user record so the FE caches reflect DB truth.
//
// Returns the freshly-fetched user, or null if the request fails (we
// keep the existing cached user on failure rather than wiping it).
const refreshCurrentUser = async (): Promise<User | null> => {
  try {
    const response = await api.get('/users/me');
    const data = response.data || {};

    // Backend returns role as either a string code or an object with .code
    // (depending on whether the relationship was eager-loaded). Normalise
    // here so callers always see a flat string.
    const roleCode =
      (typeof data.role === 'object' && data.role?.code) ||
      data.role_code ||
      data.role ||
      'USER';

    // Permissions can come from `data.permissions` or nested under role.
    let permissions: string[] = data.permissions || [];
    if (typeof data.role === 'object' && Array.isArray(data.role?.permissions)) {
      permissions = data.role.permissions.map((p: any) =>
        typeof p === 'object' && p?.code ? p.code : p
      );
    }

    // Preserve the existing cached `name` if BE doesn't echo full_name back
    // (some role-only updates strip it out of the response payload).
    const cached = getCurrentUser();
    const user: User = {
      id: String(data.id ?? cached?.id ?? ''),
      name: data.full_name || data.username || cached?.name || '',
      email: data.email ?? cached?.email,
      role: roleCode,
      roles: data.roles || [roleCode],
      permissions,
      region_id: data.region_id ?? cached?.region_id,
      area_id: data.area_id ?? cached?.area_id,
    };

    localStorage.setItem(USER_DATA_KEY, JSON.stringify(user));
    if (user.name) {
      localStorage.setItem(USER_NAME_KEY, user.name);
    }

    // Notify any listeners (Navigation, route guards) that the cached
    // user just refreshed.
    window.dispatchEvent(new Event('auth-change'));

    return user;
  } catch (error) {
    console.error('refreshCurrentUser failed:', error);
    return null;
  }
};

// קבלת שם המשתמש הנוכחי - לנוחות
const getUserName = (): string => {
  return localStorage.getItem(USER_NAME_KEY) || '';
};

// בדיקה האם המשתמש ביקש לזכור אותו
const isRememberMeActive = (): boolean => {
  return localStorage.getItem(REMEMBER_ME_KEY) === 'true';
};

// קבלת שם המשתמש השמור
const getSavedUsername = (): string => {
  return localStorage.getItem(SAVED_USERNAME_KEY) || '';
};

// ייצוא כל הפונקציות
export default {
  login,
  logout,
  isAuthenticated,
  getCurrentUser,
  refreshCurrentUser,
  getUserName,
  isRememberMeActive,
  getSavedUsername
};