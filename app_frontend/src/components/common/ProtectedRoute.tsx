import React, { useEffect, useState, useRef, createContext, useContext } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { ShieldX, Eye, TreeDeciduous } from 'lucide-react';
import { hasPermission, getUserPermissions, normalizeRole, UserRole } from '../../utils/permissions';

// ============================================================
// Types
// ============================================================
export interface ProtectedRouteProps {
  children: React.ReactNode;
  redirectTo?: string;
  requiredPermission?: string;  // Permission code from DB (e.g., "PROJECTS.VIEW")
  requiredRole?: string;        // Fallback for role-based check
  showReadOnlyBanner?: boolean;
}

type AuthStatus = 'authenticated' | 'unauthenticated' | 'checking' | 'forbidden';

interface AuthUser {
  id: string;
  name: string;
  role?: string;
  permissions?: string[];
}

interface AuthState {
  status: AuthStatus;
  user: AuthUser | null;
  error?: string;
}

// ============================================================
// Permission Context
// ============================================================
interface PermissionContextType {
  userRole: UserRole;
  permissions: string[];
  hasPermission: (permission: string) => boolean;
}

const PermissionContext = createContext<PermissionContextType>({
  userRole: UserRole.VIEWER,
  permissions: [],
  hasPermission: () => false,
});

export const usePermissions = () => useContext(PermissionContext);

// ============================================================
// Component
// ============================================================
// Read auth state synchronously from localStorage — no async needed
function readAuthState(requiredPermission?: string, requiredRole?: string): AuthState {
  try {
    const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
    const userStr = localStorage.getItem('user');
    let user: AuthUser | null = null;

    if (userStr) {
      try {
        const parsed = JSON.parse(userStr);
        if (parsed && (parsed.id || parsed.id === 0)) {
          user = {
            id: parsed.id.toString(),
            name: parsed.name || parsed.full_name || '',
            role: parsed.role || '',
            permissions: parsed.permissions || []
          };
        }
      } catch {
        localStorage.removeItem('user');
      }
    }

    if (!isAuthenticated || !user) {
      return { status: 'unauthenticated', user: null, error: 'המשתמש לא מחובר' };
    }

    let access = true;
    let error = '';
    if (requiredPermission) {
      access = hasPermission(requiredPermission);
      if (!access) error = `חסרה הרשאה: ${requiredPermission}`;
    } else if (requiredRole) {
      const ur = normalizeRole(user.role || '');
      const rr = normalizeRole(requiredRole);
      access = ur === rr || ur === UserRole.ADMIN;
      if (!access) error = 'נדרש תפקיד מתאים';
    }

    return access
      ? { status: 'authenticated', user }
      : { status: 'forbidden', user, error };
  } catch {
    return { status: 'unauthenticated', user: null, error: 'שגיאה בבדיקת ההרשאות' };
  }
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  redirectTo = "/login",
  requiredPermission,
  requiredRole,
  showReadOnlyBanner = false,
}) => {
  const location = useLocation();

  // Lazy initial state — read auth synchronously on first render, no 'checking' phase
  const [authState, setAuthState] = useState<AuthState>(() =>
    readAuthState(requiredPermission, requiredRole)
  );

  const prevStatusRef = useRef(authState.status);

  // Only re-check when auth events fire from other tabs, NOT on every pathname change
  useEffect(() => {
    const recheck = () => {
      const next = readAuthState(requiredPermission, requiredRole);
      if (next.status !== prevStatusRef.current ||
          next.user?.id !== authState.user?.id) {
        prevStatusRef.current = next.status;
        setAuthState(next);
      }
    };

    window.addEventListener('storage', recheck);
    window.addEventListener('auth-change', recheck);
    return () => {
      window.removeEventListener('storage', recheck);
      window.removeEventListener('auth-change', recheck);
    };
  // requiredPermission and requiredRole are stable (passed as string literals from routes)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requiredPermission, requiredRole]);

  // מצב טעינה (shouldn't happen with lazy init, but kept as safety net)
  if (authState.status === 'checking') {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="relative">
          <div className="w-16 h-16 rounded-full border-[3px] border-emerald-200 border-t-emerald-500 animate-spin" />
          <div className="absolute inset-0 flex items-center justify-center">
            <TreeDeciduous size={28} className="text-emerald-600" strokeWidth={1.5} />
          </div>
        </div>
      </div>
    );
  }

  // מצב לא מאומת
  if (authState.status === 'unauthenticated') {
    if (location.pathname === '/otp') {
      return (
        <div className="animate-fadeIn transition-opacity duration-300 ease-in-out">
          {children}
        </div>
      );
    }
    
    return (
      <Navigate
        to={redirectTo}
        replace
        state={{
          from: location.pathname,
          error: authState.error
        }}
      />
    );
  }

  // מצב אין הרשאה (403)
  if (authState.status === 'forbidden') {
    return (
      <div className="flex justify-center items-center min-h-screen bg-gray-50" dir="rtl">
        <div className="bg-white p-8 rounded-lg shadow-lg flex flex-col items-center max-w-md">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
            <ShieldX className="w-8 h-8 text-red-600" />
          </div>
          <h2 className="text-xl font-bold text-gray-800 mb-2">אין הרשאה</h2>
          <p className="text-gray-600 text-center mb-4">
            {authState.error || 'אין לך הרשאה לגשת לדף זה'}
          </p>
          <button
            onClick={() => window.history.back()}
            className="px-4 py-2 bg-kkl-green text-white rounded-lg hover:bg-kkl-green-dark transition-colors"
          >
            חזור אחורה
          </button>
        </div>
      </div>
    );
  }

  // מצב מאומת
  const userRole = normalizeRole(authState.user?.role || '');
  const userPermissions = getUserPermissions();
  
  const permissionContext: PermissionContextType = {
    userRole,
    permissions: userPermissions,
    hasPermission: (permission: string) => hasPermission(permission),
  };

  return (
    <PermissionContext.Provider value={permissionContext}>
      <div className="animate-fadeIn transition-opacity duration-300 ease-in-out">
        {/* באנר קריאה בלבד */}
        {showReadOnlyBanner && (
          <div className="bg-blue-50 border-b border-blue-200 px-4 py-2 flex items-center justify-center gap-2" dir="rtl">
            <Eye className="w-4 h-4 text-blue-600" />
            <span className="text-sm text-blue-700">
              צפייה בלבד - אין אפשרות לערוך או ליצור
            </span>
          </div>
        )}
        {children}
      </div>
    </PermissionContext.Provider>
  );
};

export default ProtectedRoute;
