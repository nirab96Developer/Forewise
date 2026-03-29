// hooks/useOfflineSync.ts
// Shared offline sync state backed by IndexedDB.

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

type OfflineSyncSnapshot = {
  isOnline: boolean;
  pendingCount: number;
  isSyncing: boolean;
};

let sharedState: OfflineSyncSnapshot = {
  isOnline: navigator.onLine,
  pendingCount: 0,
  isSyncing: false,
};

let listenersAttached = false;
let initialCountLoaded = false;
let syncInFlight: Promise<number> | null = null;
const subscribers = new Set<(state: OfflineSyncSnapshot) => void>();

function emitState() {
  const snapshot = { ...sharedState };
  subscribers.forEach((notify) => notify(snapshot));
}

function updateState(partial: Partial<OfflineSyncSnapshot>) {
  sharedState = { ...sharedState, ...partial };
  emitState();
}

async function refreshSharedCount() {
  const items = await getPendingItems();
  updateState({ pendingCount: items.length });
}

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

async function syncPendingItems(options?: { showSummaryToast?: boolean; showReconnectToast?: boolean }): Promise<number> {
  if (!sharedState.isOnline) {
    return 0;
  }
  if (syncInFlight) {
    return syncInFlight;
  }

  syncInFlight = (async () => {
    const pending = await getPendingItems();
    if (pending.length === 0) {
      await refreshSharedCount();
      return 0;
    }

    updateState({ isSyncing: true });

    if (options?.showReconnectToast) {
      showToast('החיבור חזר', 'success', 4000);
    }

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

    updateState({ isSyncing: false });
    await refreshSharedCount();

    if (options?.showSummaryToast) {
      if (successCount > 0) {
        showToast(`${successCount} פריטים סונכרנו בהצלחה`, 'success', 5000);
      } else {
        showToast('חלק מהפריטים לא סונכרנו', 'warning');
      }
    }

    return successCount;
  })();

  try {
    return await syncInFlight;
  } finally {
    syncInFlight = null;
    updateState({ isSyncing: false });
  }
}

function ensureOfflineListeners() {
  if (listenersAttached) return;
  listenersAttached = true;

  const handleOnline = async () => {
    updateState({ isOnline: true });
    await syncPendingItems({ showSummaryToast: true, showReconnectToast: true });
  };

  const handleOffline = () => updateState({ isOnline: false });
  const handleQueueChange = () => {
    refreshSharedCount();
  };

  window.addEventListener('online', handleOnline);
  window.addEventListener('offline', handleOffline);
  window.addEventListener('offline-queue-changed', handleQueueChange);
}

export function useOfflineSync() {
  const [state, setState] = useState<OfflineSyncSnapshot>(sharedState);

  const refreshCount = useCallback(async () => {
    await refreshSharedCount();
  }, []);

  useEffect(() => {
    ensureOfflineListeners();
    subscribers.add(setState);
    setState(sharedState);
    if (!initialCountLoaded) {
      initialCountLoaded = true;
      refreshSharedCount();
    }
    return () => {
      subscribers.delete(setState);
    };
  }, []);

  const syncAll = useCallback(async () => {
    if (!sharedState.isOnline) {
      showToast('אין חיבור לאינטרנט', 'warning');
      return;
    }
    if (sharedState.pendingCount === 0) {
      showToast('אין פריטים לסנכרון', 'info');
      return;
    }
    await syncPendingItems({ showSummaryToast: true, showReconnectToast: false });
  }, []);

  const loadAllItems = useCallback(() => getAllPendingItems(), []);

  return {
    isOnline: state.isOnline,
    pendingCount: state.pendingCount,
    isSyncing: state.isSyncing,
    syncAll,
    refreshCount,
    loadAllItems,
  };
}
