// src/context/LoadingContext.tsx
// קונטקסט גלובלי לטעינה - לואדר אחד בלבד לכל האפליקציה
import React, { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react';
import { TreeDeciduous } from 'lucide-react';

interface LoadingContextType {
  isLoading: boolean;
  startLoading: () => void;
  stopLoading: () => void;
  setLoading: (loading: boolean) => void;
}

const LoadingContext = createContext<LoadingContextType>({
  isLoading: false,
  startLoading: () => {},
  stopLoading: () => {},
  setLoading: () => {},
});

export const useLoading = () => useContext(LoadingContext);

// הלואדר הגלובלי היחיד
const GlobalLoader: React.FC<{ show: boolean }> = ({ show }) => {
  const [visible, setVisible] = useState(false);
  const [shouldRender, setShouldRender] = useState(false);

  useEffect(() => {
    if (show) {
      setShouldRender(true);
      // Small delay for smooth animation
      requestAnimationFrame(() => setVisible(true));
    } else {
      setVisible(false);
      // Wait for fade out animation
      const timer = setTimeout(() => setShouldRender(false), 200);
      return () => clearTimeout(timer);
    }
  }, [show]);

  if (!shouldRender) return null;

  return (
    <div 
      className={`
        fixed inset-0 z-[9999] flex items-center justify-center
        bg-white/70 backdrop-blur-[2px]
        transition-opacity duration-200 ease-out
        ${visible ? 'opacity-100' : 'opacity-0'}
      `}
    >
      <div className="flex flex-col items-center">
        {/* Spinning ring with tree icon */}
        <div className="relative">
          <div 
            className="w-16 h-16 rounded-full border-[3px] border-emerald-200 border-t-emerald-500"
            style={{ animation: 'spin 0.8s linear infinite' }}
          />
          <div className="absolute inset-0 flex items-center justify-center">
            <TreeDeciduous 
              size={28} 
              className="text-emerald-600" 
              strokeWidth={1.5}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export const LoadingProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [loadingCount, setLoadingCount] = useState(0);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const startLoading = useCallback(() => {
    // Clear any pending stop timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setLoadingCount(prev => prev + 1);
  }, []);

  const stopLoading = useCallback(() => {
    // Small delay to prevent flicker for quick operations
    timeoutRef.current = setTimeout(() => {
      setLoadingCount(prev => Math.max(0, prev - 1));
    }, 100);
  }, []);

  const setLoading = useCallback((loading: boolean) => {
    if (loading) {
      startLoading();
    } else {
      stopLoading();
    }
  }, [startLoading, stopLoading]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const isLoading = loadingCount > 0;

  return (
    <LoadingContext.Provider value={{ isLoading, startLoading, stopLoading, setLoading }}>
      <GlobalLoader show={isLoading} />
      {children}
    </LoadingContext.Provider>
  );
};

// Hook לשימוש בקומפוננטות שטוענות נתונים
export const useDataLoading = () => {
  const { startLoading, stopLoading } = useLoading();
  
  const withLoading = useCallback(async <T,>(promise: Promise<T>): Promise<T> => {
    startLoading();
    try {
      return await promise;
    } finally {
      stopLoading();
    }
  }, [startLoading, stopLoading]);

  return { withLoading, startLoading, stopLoading };
};

export default LoadingContext;

