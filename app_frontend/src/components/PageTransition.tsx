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
            <div className="w-20 h-20 border-4 border-green-500/30 rounded-full animate-spin" />
            <div className="absolute inset-0 w-20 h-20 border-4 border-t-green-600 border-r-transparent border-b-transparent border-l-transparent rounded-full animate-spin" />
            <div className="absolute inset-2 w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full opacity-20 animate-pulse" />
          </div>
        </div>
      )}
    </div>
  );
};

export default PageTransition;
