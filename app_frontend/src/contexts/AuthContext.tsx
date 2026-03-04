
import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
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

// Read once synchronously — used for lazy initial state and comparisons
function readAuth(): { user: User | null; isAuthenticated: boolean } {
  const { token, user } = readUserFromStorage();
  if (token && user) {
    return { user: user as User, isAuthenticated: true };
  }
  return { user: null, isAuthenticated: false };
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Lazy initial state — reads localStorage exactly once, avoids useEffect on mount
  const [user, setUser] = useState<User | null>(() => readAuth().user);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => readAuth().isAuthenticated);

  // Ref to track current user id for equality check (avoids object comparison)
  const userIdRef = useRef<string | number | null>(user?.id ?? null);

  // Only update state when auth data actually changes
  const syncFromStorage = useCallback(() => {
    const next = readAuth();
    const nextId = next.user?.id ?? null;
    // Skip setState if nothing actually changed (prevents cascade re-renders)
    if (nextId === userIdRef.current && next.isAuthenticated === (userIdRef.current !== null)) return;
    userIdRef.current = nextId;
    setUser(next.user);
    setIsAuthenticated(next.isAuthenticated);
  }, []);

  // Bootstrap: silently try to refresh token on first mount, only if no access token exists
  const didBootstrap = useRef(false);
  useEffect(() => {
    if (didBootstrap.current) return;
    didBootstrap.current = true;

    const { token } = getRefreshTokenWithStorage();
    const { token: accessToken } = readUserFromStorage();
    if (accessToken || !token) return;

    api.post('/auth/refresh', { refresh_token: token })
      .then(response => {
        const newAccessToken = response.data?.access_token;
        if (!newAccessToken) return;
        const { storage } = getRefreshTokenWithStorage();
        storage.setItem('access_token', newAccessToken);
        syncFromStorage();
      })
      .catch(() => {
        clearAuthSession();
        setUser(null);
        setIsAuthenticated(false);
        userIdRef.current = null;
      });
  }, [syncFromStorage]);

  // Listen for auth changes from other tabs (storage) and same tab (auth-change event)
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      // Only react to access_token or user changes, ignore unrelated keys
      if (e.key && !['access_token', 'user', 'refresh_token'].includes(e.key)) return;
      syncFromStorage();
    };
    const handleAuthChange = () => syncFromStorage();

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('auth-change', handleAuthChange);
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('auth-change', handleAuthChange);
    };
  }, [syncFromStorage]);

  const login = async (_credentials: any) => {
    // Login is handled by the Login component; refresh context after
  };

  const logout = () => {
    clearAuthSession();
    userIdRef.current = null;
    setUser(null);
    setIsAuthenticated(false);
  };

  const refreshUser = useCallback(() => {
    syncFromStorage();
  }, [syncFromStorage]);

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
};
