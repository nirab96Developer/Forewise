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
  roles: string[];
  email?: string;
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
      
      // הגדרת נתוני המשתמש
      const user = {
        id: data.user.id.toString(),
        name: data.user.full_name || data.user.username,
        email: data.user.email,
        roles: data.user.roles || ['user']
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
  getUserName,
  isRememberMeActive,
  getSavedUsername
};