import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';

interface PageTransitionProps {
  children: React.ReactNode;
}

const PageTransition: React.FC<PageTransitionProps> = ({ children }) => {
  const location = useLocation();
  const [isTransitioning, setIsTransitioning] = useState(false);
  
  useEffect(() => {
    setIsTransitioning(true);
    const timer = setTimeout(() => {
      setIsTransitioning(false);
    }, 500);
    
    return () => clearTimeout(timer);
  }, [location.pathname]);

  return (
    <div className="relative min-h-screen">
      {/* אנימציית רקע מתקדמת */}
      <div 
        className={`fixed inset-0 bg-gradient-to-br from-emerald-500/10 via-green-500/5 to-teal-500/10 pointer-events-none transition-all duration-1000 ${
          isTransitioning ? 'opacity-100' : 'opacity-0'
        }`}
      >
        {/* פולסים מעגליים */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-green-400/20 rounded-full filter blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-emerald-400/20 rounded-full filter blur-3xl animate-pulse animation-delay-1000" />
      </div>

      {/* תוכן הדף עם אנימציה */}
      <div
        className={`relative transition-all duration-500 ease-out transform ${
          isTransitioning 
            ? 'opacity-0 scale-95 translate-y-4' 
            : 'opacity-100 scale-100 translate-y-0'
        }`}
      >
        {children}
      </div>

      {/* לוגו מסתובב בזמן המעבר */}
      {isTransitioning && (
        <div className="fixed inset-0 flex items-center justify-center pointer-events-none z-50">
          <div className="relative">
            <div className="w-20 h-20 border-4 border-emerald-200 border-t-emerald-500 rounded-full animate-spin" style={{animationDuration:'0.8s'}} />
            <div className="absolute inset-0 flex items-center justify-center animate-pulse">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 100" width="36" height="30">
                <defs>
                  <linearGradient id="pt_t" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#1565c0"/><stop offset="100%" stopColor="#0097a7"/></linearGradient>
                  <linearGradient id="pt_m" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#0097a7"/><stop offset="50%" stopColor="#2e7d32"/><stop offset="100%" stopColor="#66bb6a"/></linearGradient>
                  <linearGradient id="pt_b" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#2e7d32"/><stop offset="40%" stopColor="#66bb6a"/><stop offset="100%" stopColor="#8B5e3c"/></linearGradient>
                </defs>
                <path d="M46 20 Q60 9 74 20" stroke="url(#pt_t)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <path d="M30 47 Q42 34 60 43 Q78 34 90 47" stroke="url(#pt_m)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <path d="M14 74 Q28 60 46 69 Q60 76 74 69 Q92 60 106 74" stroke="url(#pt_b)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <line x1="60" y1="76" x2="60" y2="90" stroke="#8B5e3c" strokeWidth="3.5" strokeLinecap="round"/>
                <circle cx="60" cy="95" r="5" fill="#8B5e3c"/>
              </svg>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PageTransition;
