// src/components/common/PageLoader.tsx
// קומפוננט טעינה אחיד לדף שלם - עם timeout
import React, { useState, useEffect } from 'react';
import { Loader2, RefreshCw, AlertCircle } from 'lucide-react';

interface PageLoaderProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
  timeout?: number; // timeout in ms, default 10 seconds
}

const PageLoader: React.FC<PageLoaderProps> = ({ 
  message = 'טוען...',
  size = 'md',
  timeout = 10000
}) => {
  const [showRetry, setShowRetry] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowRetry(true);
    }, timeout);

    return () => clearTimeout(timer);
  }, [timeout]);

  const handleRetry = () => {
    window.location.reload();
  };

  const sizeClasses = {
    sm: {
      container: 'min-h-[200px]',
      spinner: 'w-8 h-8',
      text: 'text-sm'
    },
    md: {
      container: 'min-h-[400px]',
      spinner: 'w-12 h-12',
      text: 'text-base'
    },
    lg: {
      container: 'min-h-screen',
      spinner: 'w-16 h-16',
      text: 'text-lg'
    }
  };

  const classes = sizeClasses[size];

  // אם עבר הזמן - הצג אפשרות לרענון
  if (showRetry) {
    return (
      <div className={`${classes.container} flex items-center justify-center`}>
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-orange-500 mx-auto mb-4" />
          <p className="text-gray-700 font-medium mb-2">הטעינה לוקחת יותר מדי זמן</p>
          <p className="text-gray-500 text-sm mb-4">ייתכן שיש בעיית חיבור</p>
          <button
            onClick={handleRetry}
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
    <div className={`${classes.container} flex items-center justify-center`}>
      <div className="text-center">
        <Loader2 className={`${classes.spinner} text-green-600 animate-spin mx-auto`} />
        <p className={`${classes.text} text-gray-600 mt-4 font-medium`}>{message}</p>
      </div>
    </div>
  );
};

export default PageLoader;

