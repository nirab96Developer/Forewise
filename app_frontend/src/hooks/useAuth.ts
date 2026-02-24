// src/hooks/useAuth.ts
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  permissions?: string[];
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export const useAuth = () => {
  const navigate = useNavigate();
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    error: null
  });

  // טעינת נתוני משתמש מ-localStorage
  useEffect(() => {
    const loadUser = () => {
      try {
        const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
        const userStr = localStorage.getItem('user');
        
        if (isAuthenticated && userStr) {
          const user = JSON.parse(userStr);
          setAuthState({
            user,
            isAuthenticated: true,
            isLoading: false,
            error: null
          });
        } else {
          setAuthState({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null
          });
        }
      } catch (error) {
        console.error('Error loading user:', error);
        setAuthState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: 'שגיאה בטעינת נתוני המשתמש'
        });
      }
    };

    loadUser();
  }, []);

  // התנתקות
  const logout = useCallback(() => {
    localStorage.removeItem('isAuthenticated');
    localStorage.removeItem('user');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setAuthState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null
    });
    navigate('/login');
  }, [navigate]);

  // עדכון נתוני משתמש
  const updateUser = useCallback((userData: Partial<User>) => {
    if (authState.user) {
      const updatedUser = { ...authState.user, ...userData };
      setAuthState(prev => ({
        ...prev,
        user: updatedUser
      }));
      localStorage.setItem('user', JSON.stringify(updatedUser));
    }
  }, [authState.user]);

  // בדיקת הרשאה
  const hasPermission = useCallback((permission: string) => {
    if (!authState.user?.permissions) return false;
    return authState.user.permissions.includes(permission);
  }, [authState.user?.permissions]);

  // בדיקת תפקיד
  const hasRole = useCallback((role: string) => {
    return authState.user?.role === role;
  }, [authState.user?.role]);

  return {
    user: authState.user,
    isAuthenticated: authState.isAuthenticated,
    isLoading: authState.isLoading,
    error: authState.error,
    logout,
    updateUser,
    hasPermission,
    hasRole
  };
};

