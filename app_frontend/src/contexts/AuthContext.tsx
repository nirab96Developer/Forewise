
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import { clearAuthSession, readUserFromStorage, getRefreshTokenWithStorage } from '../utils/authStorage';

interface User {
  id: number | string;
  name?: string;
  username?: string;
  email: string;
  full_name?: string;
  role: string;
  roles?: string[];
  permissions?: string[];
}

interface AuthContextType {
  user: User | null;
  login: (credentials: any) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  refreshUser: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    // Return a default value instead of throwing error
    return {
      user: null,
      login: async () => {},
      logout: () => {},
      isAuthenticated: false,
      refreshUser: () => {}
    };
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Function to load user from localStorage
  const loadUserFromStorage = useCallback(() => {
    const { token, user } = readUserFromStorage();
    
    console.log('[AuthContext] loadUserFromStorage called');
    console.log('[AuthContext] token exists:', !!token);
    console.log('[AuthContext] user loaded:', !!user);
    
    if (token && user) {
      try {
        const userData = user as User;
        console.log('[AuthContext] Parsed user data:', JSON.stringify(userData, null, 2));
        console.log('[AuthContext] User role from storage:', userData.role);
        setUser(userData);
        setIsAuthenticated(true);
      } catch (error) {
        console.error('[AuthContext] Failed to parse user data:', error);
        setUser(null);
        setIsAuthenticated(false);
      }
    } else {
      console.log('[AuthContext] No token or user, clearing auth');
      setUser(null);
      setIsAuthenticated(false);
    }
  }, []);

  const bootstrapRefresh = useCallback(async () => {
    const { token } = getRefreshTokenWithStorage();
    const { token: accessToken, user } = readUserFromStorage();
    if (accessToken || !token || !user) return;
    try {
      const response = await api.post('/auth/refresh', { refresh_token: token });
      const newAccessToken = response.data?.access_token;
      if (!newAccessToken) return;
      const { storage } = getRefreshTokenWithStorage();
      storage.setItem('access_token', newAccessToken);
      window.dispatchEvent(new Event('auth-change'));
    } catch (_e) {
      clearAuthSession();
    }
  }, []);

  // Load on mount
  useEffect(() => {
    loadUserFromStorage();
    bootstrapRefresh();
  }, [loadUserFromStorage, bootstrapRefresh]);

  // Listen for storage changes (from Login component or other tabs)
  useEffect(() => {
    const handleStorageChange = (_e?: StorageEvent) => {
      console.log('[AuthContext] Storage event detected');
      loadUserFromStorage();
    };

    // Listen for both storage events (from other tabs) and custom events (from same tab)
    window.addEventListener('storage', handleStorageChange);
    
    // Also re-check on custom auth-change event for same-tab updates
    const handleAuthChange = () => {
      console.log('[AuthContext] Auth change event detected');
      loadUserFromStorage();
    };
    window.addEventListener('auth-change', handleAuthChange);
    
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('auth-change', handleAuthChange);
    };
  }, [loadUserFromStorage]);

  const login = async (_credentials: any) => {
    // Login is handled by the Login component
    // This is a placeholder for the interface
  };

  const logout = () => {
    clearAuthSession();
    setUser(null);
    setIsAuthenticated(false);
  };

  const refreshUser = () => {
    loadUserFromStorage();
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
};
