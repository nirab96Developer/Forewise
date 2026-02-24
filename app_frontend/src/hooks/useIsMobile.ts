// src/hooks/useIsMobile.ts
// Hook לזיהוי אם המשתמש במובייל

import { useState, useEffect } from 'react';

export const useIsMobile = (breakpoint: number = 768): boolean => {
  const [isMobile, setIsMobile] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    return window.innerWidth < breakpoint;
  });

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < breakpoint);
    };

    // בדיקה ראשונית
    handleResize();

    // האזנה לשינויי גודל חלון
    window.addEventListener('resize', handleResize);
    
    // האזנה לשינויי orientation (סיבוב מסך)
    window.addEventListener('orientationchange', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleResize);
    };
  }, [breakpoint]);

  return isMobile;
};

export default useIsMobile;




