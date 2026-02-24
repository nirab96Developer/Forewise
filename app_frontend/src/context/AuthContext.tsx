// src/context/AuthContext.tsx
import React, { createContext, useState, useEffect } from 'react';
import authService from '../services/authService';

interface AuthContextType {
  isAuthenticated: boolean;
  user: any | null;
  login: (username: string, password: string, remember?: boolean) => Promise<boolean>;
  logout: () => void;
  loading: boolean;
}

const defaultContext: AuthContextType = {
  isAuthenticated: false,
  user: null,
  login: async () => false,
  logout: () => {},
  loading: true
};

export const AuthContext = createContext<AuthContextType>(defaultContext);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [user, setUser] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    // בדיקת אימות בטעינה ראשונית
    const checkAuth = async () => {
      setLoading(true);
      const authenticated = authService.isAuthenticated();
      setIsAuthenticated(authenticated);
      
      if (authenticated) {
        try {
          const userData = authService.getCurrentUser();
          setUser(userData);
        } catch (error) {
          console.error("שגיאה בטעינת נתוני משתמש:", error);
          // במקרה של שגיאה בטעינת המשתמש, ננקה את האימות
          authService.logout();
          setIsAuthenticated(false);
          setUser(null);
        }
      }
      
      setLoading(false);
    };
    
    checkAuth();
  }, []);

  const login = async (username: string, password: string, remember: boolean = false) => {
    setLoading(true);
    try {
      const result = await authService.login(username, password, remember);
      
      if (result && typeof result === 'object' && result.success) {
        setIsAuthenticated(true);
        setUser(result.user);
        setLoading(false);
        return true;
      } else {
        setLoading(false);
        return false;
      }
    } catch (error) {
      console.error("שגיאה בהתחברות:", error);
      setLoading(false);
      return false;
    }
  };

  const logout = () => {
    setLoading(true);
    authService.logout();
    setIsAuthenticated(false);
    setUser(null);
    setLoading(false);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};