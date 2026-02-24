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
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  redirectTo = "/login",
  requiredPermission,
  requiredRole,
  showReadOnlyBanner = false,
}) => {
  const location = useLocation();
  const [authState, setAuthState] = useState<AuthState>({
    status: 'checking',
    user: null
  });
  
  const isFirstRender = useRef(true);
  const prevAuthStateRef = useRef<AuthState | null>(null);

  useEffect(() => {
    const checkAuth = () => {
      try {
        // בדיקת אותנטיקציה
        const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
        
        // בדיקת המשתמש
        const userStr = localStorage.getItem('user');
        let user: AuthUser | null = null;
        
        try {
          if (userStr) {
            const parsedUser = JSON.parse(userStr);
            if (parsedUser && (parsedUser.id || parsedUser.id === 0)) {
              user = {
                id: parsedUser.id.toString(),
                name: parsedUser.name || parsedUser.full_name || '',
                role: parsedUser.role || '',
                permissions: parsedUser.permissions || []
              };
            }
          }
        } catch (parseError) {
          console.error('Error parsing user data:', parseError);
          localStorage.removeItem('user');
        }
        
        // לא מחובר
        if (!isAuthenticated || !user) {
          updateState({
            status: 'unauthenticated',
            user: null,
            error: !isAuthenticated ? 'המשתמש לא מחובר' : 'פרטי המשתמש לא תקינים'
          });
          return;
        }
        
        // בדיקת הרשאות
        let hasAccess = true;
        let errorMessage = '';
        
        // 1. בדיקת permission ספציפי
        if (requiredPermission) {
          hasAccess = hasPermission(requiredPermission);
          if (!hasAccess) {
            errorMessage = `חסרה הרשאה: ${requiredPermission}`;
          }
        }
        // 2. בדיקת role (fallback)
        else if (requiredRole) {
          const userRole = normalizeRole(user.role || '');
          const reqRole = normalizeRole(requiredRole);
          hasAccess = userRole === reqRole || userRole === UserRole.ADMIN;
          if (!hasAccess) {
            errorMessage = 'נדרש תפקיד מתאים';
          }
        }
        
        // קביעת הסטייט הסופי
        if (hasAccess) {
          updateState({
            status: 'authenticated',
            user
          });
        } else {
          updateState({
            status: 'forbidden',
            user,
            error: errorMessage
          });
        }
        
      } catch (error) {
        console.error('Auth check failed:', error);
        updateState({
          status: 'unauthenticated',
          user: null,
          error: 'שגיאה בבדיקת ההרשאות'
        });
      }
    };
    
    const updateState = (newState: AuthState) => {
      const prevState = prevAuthStateRef.current;
      const hasChanged = !prevState || 
        prevState.status !== newState.status ||
        prevState.user?.id !== newState.user?.id ||
        prevState.error !== newState.error;
      
      if (hasChanged) {
        prevAuthStateRef.current = newState;
        setAuthState(newState);
      }
      
      if (isFirstRender.current) {
        isFirstRender.current = false;
      }
    };
    
    checkAuth();
    
    const handleStorageChange = () => {
      setTimeout(checkAuth, 50);
    };
    
    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
    
  }, [requiredPermission, requiredRole, location.pathname]);

  // מצב טעינה - לואדר יפה ומאוחד
  if (authState.status === 'checking' && isFirstRender.current) {
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
