
// src/App.tsx
import React, { useState, useEffect } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { Bug } from "lucide-react";

// שירותים
import authService from "./services/authService";

// דפים ורכיבים
import Navigation from "./components/Navigation/Navigation";
import AppRoutes from "./routes";
import { ToastProvider } from "./components/common/Toast";
import { OfflineBanner } from "./components/common/OfflineBanner";
import HumanSupportChat from "./components/HelpWidget/HumanSupportChat";
import { FullScreenLoader } from "./components/common/UnifiedLoader";
import { debugLogger } from "./utils/debug";
import { useIsMobile } from "./hooks/useIsMobile";
import PWAInstallBanner from "./components/PWAInstallBanner";
import { useOfflineSync } from "./hooks/useOfflineSync";

const OfflineSyncOnReconnect: React.FC = () => {
  useOfflineSync();
  return null;
};

const App: React.FC = () => {
  const [globalLoading, setGlobalLoading] = useState(false);
  const location = useLocation();
  const [isLoggedIn, setIsLoggedIn] = useState(authService.isAuthenticated());
  const [errorCount, setErrorCount] = useState(0);
  const isMobile = useIsMobile();
  const { isOnline } = useOfflineSync();
  
  // הוסף class למובייל ב-body
  useEffect(() => {
    if (isMobile) {
      document.body.classList.add('is-mobile');
      document.documentElement.setAttribute('data-device', 'mobile');
    } else {
      document.body.classList.remove('is-mobile');
      document.documentElement.setAttribute('data-device', 'desktop');
    }
    
    return () => {
      document.body.classList.remove('is-mobile');
      document.documentElement.removeAttribute('data-device');
    };
  }, [isMobile]);

  // globalShowToast is wired inside OfflineBanner (needs ToastContext)

  // Keyboard shortcut for debug panel (Ctrl+Shift+D or F12)
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Ctrl+Shift+D or F12
      if ((e.ctrlKey && e.shiftKey && e.key === 'D') || e.key === 'F12') {
        e.preventDefault();
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  // Initialize debug logger
  useEffect(() => {
    debugLogger.addLog('info', 'האפליקציה הופעלה', {
      userAgent: navigator.userAgent,
      url: window.location.href,
      timestamp: new Date().toISOString(),
    });

    // Subscribe to log updates for error count
    const unsubscribe = debugLogger.subscribe((logs) => {
      const errors = logs.filter(log => log.type === 'error').length;
      setErrorCount(errors);
    });

    return () => { unsubscribe(); };
  }, []);

  // Read auth status once on mount, then only on actual storage/auth events
  useEffect(() => {
    setIsLoggedIn(authService.isAuthenticated());
  }, []);

  useEffect(() => {
    const handleAuthUpdate = () => setIsLoggedIn(authService.isAuthenticated());
    window.addEventListener('storage', handleAuthUpdate);
    window.addEventListener('auth-change', handleAuthUpdate);
    return () => {
      window.removeEventListener('storage', handleAuthUpdate);
      window.removeEventListener('auth-change', handleAuthUpdate);
    };
  }, []);

  // בדיקה אם הנתיב הנוכחי הוא דף ציבורי (ללא ניווט)
  const isLoginPage = location.pathname === "/login";
  const isSupplierPortal = location.pathname.startsWith("/supplier-portal");
  const isChangePassword = location.pathname === "/change-password";
  const isWelcomeSplash = location.pathname === "/welcome";
  const isForgotPassword = location.pathname === "/forgot-password";
  const isResetPassword = location.pathname === "/reset-password";
  const isOtpPage = location.pathname === "/otp";
  const isOfflineFallbackPage = location.pathname === "/offline";
  const isPublicPage = isLoginPage || isSupplierPortal || isChangePassword || isWelcomeSplash || isForgotPassword || isResetPassword || isOtpPage;
  const needsLiveConnectionPage = isLoginPage || isForgotPassword || isResetPassword || isOtpPage;

  if (!isOnline && needsLiveConnectionPage && !isOfflineFallbackPage) {
    return (
      <ToastProvider>
        <OfflineSyncOnReconnect />
        <OfflineBanner />
        <Navigate to="/offline" replace />
      </ToastProvider>
    );
  }

  return (
    <ToastProvider>
      <OfflineSyncOnReconnect />
      <OfflineBanner />
      <div className={`font-sans min-h-screen text-right transition-all duration-300 ${
        isMobile 
          ? 'bg-gradient-to-br from-green-50 via-emerald-50 to-green-100' 
          : 'bg-gray-50'
      }`} dir="rtl">
        {globalLoading && <FullScreenLoader />}
        
        {isLoggedIn && !isPublicPage && <Navigation />}
        
        {/* Main Content Area - offset from sidebar */}
        <div className={isLoggedIn && !isPublicPage ? "pt-16 md:mr-64 min-h-screen bg-gray-50" : ""}>
          <AppRoutes setGlobalLoading={setGlobalLoading} />
        </div>

        {/* iOS PWA Install Banner */}
        <PWAInstallBanner />

        {/* Debug Panel Toggle Button */}
        {import.meta.env.DEV && (
          <button
            className="fixed bottom-4 left-4 z-40 p-3 bg-gray-800 hover:bg-gray-700 text-white rounded-full shadow-lg transition-all"
            title="פאנל Debug (Ctrl+Shift+D או F12)"
          >
            <Bug className="w-5 h-5" />
            {errorCount > 0 && (
              <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center text-xs font-bold animate-pulse">
                {errorCount > 9 ? '9+' : errorCount}
              </span>
            )}
          </button>
        )}

        {/* Debug Panel */}
        
        {/* Human Support Chat - בוט תמיכה (לא מוצג לאדמין — הוא עונה לקריאות, לא פותח) */}
        {isLoggedIn && !isPublicPage && (() => {
          try {
            const u = JSON.parse(localStorage.getItem('user') || '{}');
            const r = (u.role || u.role_code || '').toUpperCase();
            if (r === 'ADMIN' || r === 'SUPER_ADMIN') return null;
          } catch {}
          return <HumanSupportChat />;
        })()}
      </div>
    </ToastProvider>
  );
};

export default App;