import React, { useState, useEffect, useMemo } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { LogOut, Menu, X, Upload } from "lucide-react";
import NotificationCenter from "../NotificationCenter";
import { useIsMobile } from "../../hooks/useIsMobile";
import { getRoleDisplayName, isAdmin } from "../../utils/permissions";
import { getMenuItemsForRole } from "../../config/menuConfig";
import { useOfflineSync } from "../../hooks/useOfflineSync";

// Main Navigation Component - תפריט דינמי לפי תפקיד
const Navigation: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isLoaded, setIsLoaded] = useState(false);
  const [username, setUsername] = useState<string>("");
  const [userRole, setUserRole] = useState<string>("");
  const [userId, setUserId] = useState<number>(0);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const isMobile = useIsMobile();
  const [_isAdmin, setIsAdmin] = useState(false);
  const { pendingCount } = useOfflineSync();

  // פונקציה לטעינת נתוני משתמש מה-localStorage
  const loadUserData = () => {
    const userStr = localStorage.getItem("user");
    if (userStr) {
      try {
        const userData = JSON.parse(userStr);
        setUsername(userData.name || userData.full_name || userData.username || "משתמש");
        const roleStr = typeof userData.role === 'string' 
          ? userData.role 
          : userData.role?.name || userData.roles?.[0] || "משתמש";
        setUserRole(roleStr);
        setUserId(userData.id ? parseInt(userData.id) : 0);
        setIsAdmin(isAdmin());
      } catch (error) {
        console.error("Error parsing user data:", error);
        setUsername("משתמש");
        setUserId(0);
        setIsAdmin(false);
      }
    } else {
      setUsername("משתמש");
      setUserRole("");
      setUserId(0);
      setIsAdmin(false);
    }
    setIsLoaded(true);
  };

  // Load user data once on mount only — NOT on every pathname change
  useEffect(() => {
    loadUserData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'user' || e.key === 'isAuthenticated') {
        loadUserData();
      }
    };
    const handleAuthChange = () => loadUserData();
    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('auth-change', handleAuthChange);
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('auth-change', handleAuthChange);
    };
  }, []);
  
  // Close mobile menu on route change
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [location.pathname]);

  // קבלת פריטי תפריט לפי תפקיד המשתמש
  const menuItems = useMemo(() => {
    return getMenuItemsForRole(userRole);
  }, [userRole]);

  const handleLogout = async (): Promise<void> => {
    try {
      localStorage.removeItem("user");
      localStorage.removeItem("isAuthenticated");
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      navigate("/login");
    } catch (error) {
      console.error("Logout error:", error);
    }
  };

  const isActive = (path?: string) => {
    if (!path) return false;
    if (path === "/") return location.pathname === "/";
    return location.pathname.startsWith(path);
  };

  if (!isLoaded) return null;

  return (
    <>
      {/* Header */}
      <header className={`text-white h-16 shadow-lg z-50 fixed top-0 left-0 right-0 transition-all duration-300 ${
        isMobile 
          ? 'bg-gradient-to-r from-green-600 via-kkl-green to-green-700' 
          : 'bg-kkl-green'
      }`}>
        <div className="h-full flex items-center justify-between px-6 md:px-8">
          {/* Left side - Logo & App Name */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="md:hidden w-12 h-12 flex items-center justify-center rounded-lg hover:bg-white/20 active:bg-white/30 transition-colors touch-manipulation min-h-[44px] min-w-[44px]"
              aria-label="תפריט"
            >
              {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
            
            <div className="flex items-center gap-2.5">
              <div className="w-10 h-10 md:w-9 md:h-9 rounded-xl bg-white flex items-center justify-center shadow-sm">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 105" className="w-7 h-7 md:w-6 md:h-6">
                  <defs>
                    <linearGradient id="nav_t" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#1565c0"/><stop offset="100%" stopColor="#0097a7"/></linearGradient>
                    <linearGradient id="nav_m" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#0097a7"/><stop offset="50%" stopColor="#2e7d32"/><stop offset="100%" stopColor="#66bb6a"/></linearGradient>
                    <linearGradient id="nav_b" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#2e7d32"/><stop offset="40%" stopColor="#66bb6a"/><stop offset="100%" stopColor="#8B5e3c"/></linearGradient>
                  </defs>
                  <path d="M46 20 Q60 9 74 20" stroke="url(#nav_t)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                  <path d="M30 47 Q42 34 60 43 Q78 34 90 47" stroke="url(#nav_m)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                  <path d="M14 74 Q28 60 46 69 Q60 76 74 69 Q92 60 106 74" stroke="url(#nav_b)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                  <line x1="60" y1="76" x2="60" y2="90" stroke="#8B5e3c" strokeWidth="3.5" strokeLinecap="round"/>
                  <circle cx="60" cy="95" r="5" fill="#8B5e3c"/>
                </svg>
              </div>
              <div className="flex flex-col leading-tight">
                <span className="text-[13px] font-bold text-white">מערכת ניהול יערות</span>
                <span className="text-[10px] text-white/60 font-light hidden sm:block">Forewise</span>
              </div>
            </div>

            <button
              onClick={() => window.location.reload()}
              className="md:hidden w-9 h-9 bg-white/15 rounded-full flex items-center justify-center hover:bg-white/25 active:bg-white/35 transition-colors touch-manipulation mr-1"
              aria-label="רענן"
            >
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>

          {/* Right side - User Info */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-bold">{username.charAt(0)}</span>
                </div>
                <div className="hidden sm:flex flex-col text-right">
                  <span className="text-sm font-medium">{username}</span>
                  <span className="text-xs text-white/80">{getRoleDisplayName(userRole)}</span>
                </div>
              </div>
              <div className="hidden sm:block w-px h-8 bg-white/30"></div>
            </div>

            {userId > 0 && (
              <div className="relative">
                <NotificationCenter userId={userId} />
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Mobile Overlay */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed right-0 top-16 bottom-0 w-64 z-40 shadow-xl
          transform transition-all duration-300 ease-in-out
          ${isMobile 
            ? 'bg-gradient-to-b from-white via-green-50/30 to-white border-l border-green-200' 
            : 'bg-white border-l border-gray-200'
          }
          ${isMobileMenuOpen ? 'translate-x-0 opacity-100 pointer-events-auto' : 'translate-x-full md:translate-x-0 opacity-0 md:opacity-100 pointer-events-none md:pointer-events-auto'}
        `}
        dir="rtl"
        role="navigation"
        aria-label="תפריט ניווט ראשי"
      >
        <div className="h-full flex flex-col overflow-hidden bg-gradient-to-b from-white via-gray-50/30 to-white">
          {/* Navigation Links - Dynamic based on role */}
          <nav className="p-4 flex-1 overflow-y-auto custom-scrollbar">
            <div className="space-y-1">
              {menuItems.map((item, index) => {
                const active = isActive(item.path);
                const IconComponent = item.icon;
                
                return (
                  <React.Fragment key={item.id}>
                    <button
                      onClick={() => {
                        navigate(item.path);
                        setIsMobileMenuOpen(false);
                      }}
                      className={`
                        w-full flex items-center gap-2 px-3 py-2.5 mb-1 rounded-xl relative
                        transition-all duration-300 ease-out
                        transform hover:scale-[1.02] hover:shadow-md touch-manipulation
                        ${active 
                          ? isMobile
                            ? 'bg-gradient-to-r from-green-600 to-kkl-green text-white shadow-lg scale-[1.02]'
                            : 'bg-kkl-green text-white shadow-lg scale-[1.02]'
                          : isMobile
                            ? 'text-gray-700 hover:bg-green-50 hover:text-green-800'
                            : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                        }
                        animate-slideIn group
                      `}
                      aria-label={item.label}
                      role="menuitem"
                      style={{
                        animationDelay: `${index * 50}ms`,
                        animationFillMode: 'both'
                      }}
                    >
                      {active && (
                        <div className="absolute right-0 top-0 bottom-0 w-1 bg-white rounded-r-xl"></div>
                      )}
                      
                      <span className={`
                        transition-all duration-300 flex-shrink-0
                        ${active ? 'text-white scale-110' : 'text-gray-600 group-hover:text-kkl-green'}
                      `}>
                        <IconComponent size={20} />
                      </span>
                      
                      <span className={`text-sm font-medium flex-1 text-right ${active ? 'text-white' : 'text-gray-700 group-hover:text-gray-900'}`}>
                        {item.label}
                      </span>

                      {item.badge && (
                        <span className="bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                          {item.badge}
                        </span>
                      )}
                    </button>
                    
                    {item.dividerAfter && (
                      <div className="my-2 border-t border-gray-200"></div>
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          </nav>

          {/* Offline Pending Badge — WORK_MANAGER only */}
          {(userRole === 'WORK_MANAGER' || userRole === 'FIELD_WORKER') && pendingCount > 0 && (
            <div className="px-4 pb-2">
              <button
                onClick={() => navigate('/pending-sync')}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-xl bg-orange-50 border border-orange-200 text-orange-700 hover:bg-orange-100 transition-colors text-sm font-medium"
              >
                <Upload className="w-4 h-4 flex-shrink-0" />
                <span className="flex-1 text-right">📤 ממתינים לסנכרון</span>
                <span className="bg-orange-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
                  {pendingCount}
                </span>
              </button>
            </div>
          )}

          {/* Logout Button — mt-auto pushes it to bottom without extra spacer */}
          <div className="p-4 border-t border-gray-200 flex-shrink-0 bg-gradient-to-t from-white to-gray-50 mt-auto">
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-2 px-3 py-2.5 rounded-xl text-gray-700 hover:bg-red-50 hover:text-red-600 transition-all duration-300 transform hover:scale-[1.02] hover:shadow-md group"
            >
              <LogOut size={18} className="transition-transform duration-300 group-hover:rotate-12" />
              <span className="text-sm font-medium flex-1 text-right">התנתק</span>
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Navigation;
