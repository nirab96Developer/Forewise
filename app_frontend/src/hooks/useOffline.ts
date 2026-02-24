// src/hooks/useOffline.ts
import { useState, useEffect, useCallback } from 'react';
import offlineService from '../services/offlineService';

export interface UseOfflineReturn {
  isOnline: boolean;
  pendingCount: number;
  pendingOperations: any[];
  queueOperation: (type: string, data: any) => Promise<string>;
  syncAll: () => Promise<void>;
  clearSynced: () => void;
}

export const useOffline = (): UseOfflineReturn => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [pendingCount, setPendingCount] = useState(0);
  const [pendingOperations, setPendingOperations] = useState<any[]>([]);

  // עדכון סטטוס חיבור
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      // סנכרון אוטומטי כשחוזרים אונליין
      offlineService.syncAll();
    };

    const handleOffline = () => {
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // עדכון מספר פעולות ממתינות
  useEffect(() => {
    const updatePendingCount = () => {
      const count = offlineService.getPendingCount();
      const operations = offlineService.getPendingOperations();
      setPendingCount(count);
      setPendingOperations(operations);
    };

    // עדכון ראשוני
    updatePendingCount();

    // עדכון תקופתי
    const interval = setInterval(updatePendingCount, 5000);

    return () => clearInterval(interval);
  }, []);

  // הוספת פעולה לתור
  const queueOperation = useCallback(async (type: string, data: any): Promise<string> => {
    const id = await offlineService.queueOperation(type, data);
    
    // עדכון מיידי של הספירה
    setPendingCount(offlineService.getPendingCount());
    setPendingOperations(offlineService.getPendingOperations());
    
    return id;
  }, []);

  // סנכרון כל הפעולות
  const syncAll = useCallback(async () => {
    await offlineService.syncAll();
    
    // עדכון מיידי של הספירה
    setPendingCount(offlineService.getPendingCount());
    setPendingOperations(offlineService.getPendingOperations());
  }, []);

  // מחיקת פעולות משונכרנות
  const clearSynced = useCallback(() => {
    offlineService.clearSyncedOperations();
    
    // עדכון מיידי של הספירה
    setPendingCount(offlineService.getPendingCount());
    setPendingOperations(offlineService.getPendingOperations());
  }, []);

  return {
    isOnline,
    pendingCount,
    pendingOperations,
    queueOperation,
    syncAll,
    clearSynced
  };
};

