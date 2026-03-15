// src/components/common/PageLoader.tsx
import React, { useState, useEffect } from 'react';
import { RefreshCw, AlertCircle } from 'lucide-react';

interface PageLoaderProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
  timeout?: number;
}

const PageLoader: React.FC<PageLoaderProps> = ({
  message = 'טוען...',
  size = 'md',
  timeout = 10000,
}) => {
  const [showRetry, setShowRetry] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setShowRetry(true), timeout);
    return () => clearTimeout(timer);
  }, [timeout]);

  const sizeClasses = {
    sm: { container: 'min-h-[200px]', ring: 'w-10 h-10', svgW: 20, svgH: 17, text: 'text-sm' },
    md: { container: 'min-h-[400px]', ring: 'w-14 h-14', svgW: 28, svgH: 24, text: 'text-base' },
    lg: { container: 'min-h-screen',  ring: 'w-16 h-16', svgW: 32, svgH: 27, text: 'text-lg' },
  };

  const c = sizeClasses[size];

  if (showRetry) {
    return (
      <div className={`${c.container} flex items-center justify-center`}>
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-orange-500 mx-auto mb-4" />
          <p className="text-gray-700 font-medium mb-2">הטעינה לוקחת יותר מדי זמן</p>
          <p className="text-gray-500 text-sm mb-4">ייתכן שיש בעיית חיבור</p>
          <button
            onClick={() => window.location.reload()}
            className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            נסה שוב
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`${c.container} flex items-center justify-center`}>
      <div className="text-center">
        <div className="relative mx-auto mb-4" style={{ width: 'fit-content' }}>
          <div
            className={`${c.ring} rounded-full border-[3px] border-emerald-200 border-t-emerald-500 animate-spin mx-auto`}
            style={{ animationDuration: '0.9s' }}
          />
          <div className="absolute inset-0 flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 100" width={c.svgW} height={c.svgH}>
              <defs>
                <linearGradient id="pl_t" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#1565c0"/>
                  <stop offset="100%" stopColor="#0097a7"/>
                </linearGradient>
                <linearGradient id="pl_m" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#0097a7"/>
                  <stop offset="50%" stopColor="#2e7d32"/>
                  <stop offset="100%" stopColor="#66bb6a"/>
                </linearGradient>
                <linearGradient id="pl_b" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#2e7d32"/>
                  <stop offset="40%" stopColor="#66bb6a"/>
                  <stop offset="100%" stopColor="#8B5e3c"/>
                </linearGradient>
              </defs>
              <path d="M46 20 Q60 9 74 20" stroke="url(#pl_t)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
              <path d="M30 47 Q42 34 60 43 Q78 34 90 47" stroke="url(#pl_m)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
              <path d="M14 74 Q28 60 46 69 Q60 76 74 69 Q92 60 106 74" stroke="url(#pl_b)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
              <line x1="60" y1="76" x2="60" y2="90" stroke="#8B5e3c" strokeWidth="3.5" strokeLinecap="round"/>
              <circle cx="60" cy="95" r="5" fill="#8B5e3c"/>
            </svg>
          </div>
        </div>
        <p className={`${c.text} text-gray-600 font-medium`}>{message}</p>
      </div>
    </div>
  );
};

export default PageLoader;
