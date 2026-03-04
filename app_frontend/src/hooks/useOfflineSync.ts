// hooks/useOfflineSync.ts
// Replaces the old useOffline hook for offline-first features.
// Uses IndexedDB via offlineStorage, shows toast on reconnect, auto-syncs.

import { useState, useEffect, useCallback } from 'react';
import {
  getPendingItems,
  getAllPendingItems,
  removePendingItem,
  markItemFailed,
  type OfflineItem,
} from '../utils/offlineStorage';
import api from '../services/api';
import { showToast } from '../components/common/Toast';

export type { OfflineItem };

async function syncItem(item: OfflineItem): Promise<void> {
  const headers = { 'X-Offline-Sync': 'true' };
  if (item.type === 'worklog') {
    await api.post('/worklogs', item.data, { headers });
  } else if (item.type === 'scan') {
    const { equipment_id, ...rest } = item.data;
    await api.post(`/equipment/${equipment_id}/scan`, rest, {
      params: { scan_type: item.data.scan_type || 'manual_check' },
      headers,
    });
  } else if (item.type === 'work_order') {
    await api.post('/work-orders', item.data, { headers });
  }
}

export function useOfflineSync() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [pendingCount, setPendingCount] = useState(0);
  const [isSyncing, setIsSyncing] = useState(false);

  const refreshCount = useCallback(async () => {
    const items = await getPendingItems();
    setPendingCount(items.length);
  }, []);

  // Listen to network changes and custom queue events
  useEffect(() => {
    refreshCount();

    const handleOnline = async () => {
      setIsOnline(true);
      showToast('✅ החיבור חזר', 'success', 4000);
      // auto-sync in background
      const pending = await getPendingItems();
      if (pending.length === 0) return;
      setIsSyncing(true);
      let successCount = 0;
      for (const item of pending) {
        try {
          await syncItem(item);
          await removePendingItem(item.id);
          successCount++;
        } catch {
          await markItemFailed(item.id);
        }
      }
      setIsSyncing(false);
      await refreshCount();
      if (successCount > 0) {
        showToast(`✅ ${successCount} פריטים סונכרנו בהצלחה`, 'success', 5000);
      }
    };

    const handleOffline = () => setIsOnline(false);
    const handleQueueChange = () => refreshCount();

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    window.addEventListener('offline-queue-changed', handleQueueChange);

    // Refresh count every 10s
    const interval = setInterval(refreshCount, 10_000);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('offline-queue-changed', handleQueueChange);
      clearInterval(interval);
    };
  }, [refreshCount]);

  const syncAll = useCallback(async () => {
    if (!isOnline) {
      showToast('אין חיבור לאינטרנט', 'warning');
      return;
    }
    const pending = await getPendingItems();
    if (pending.length === 0) {
      showToast('אין פריטים לסנכרון', 'info');
      return;
    }
    setIsSyncing(true);
    let ok = 0;
    for (const item of pending) {
      try {
        await syncItem(item);
        await removePendingItem(item.id);
        ok++;
      } catch {
        await markItemFailed(item.id);
      }
    }
    setIsSyncing(false);
    await refreshCount();
    showToast(ok > 0 ? `✅ ${ok} פריטים סונכרנו` : '⚠️ חלק מהפריטים נכשלו', ok > 0 ? 'success' : 'warning');
  }, [isOnline, refreshCount]);

  const loadAllItems = useCallback(() => getAllPendingItems(), []);

  return { isOnline, pendingCount, isSyncing, syncAll, refreshCount, loadAllItems };
}
