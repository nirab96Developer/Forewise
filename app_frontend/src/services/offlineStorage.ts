/**
 * Sync queue — localStorage key `fw_sync_queue`
 * (IndexedDB offline helpers live in `utils/offlineStorage.ts`)
 */

const QUEUE_KEY = "fw_sync_queue";

export interface SyncQueueItem {
  id: string;
  action: string;
  endpoint: string;
  payload: unknown;
  status: "pending" | "synced";
}

function loadQueue(): SyncQueueItem[] {
  try {
    const raw = localStorage.getItem(QUEUE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    return Array.isArray(parsed) ? (parsed as SyncQueueItem[]) : [];
  } catch {
    return [];
  }
}

function saveQueue(items: SyncQueueItem[]): void {
  localStorage.setItem(QUEUE_KEY, JSON.stringify(items));
}

/** Default endpoint for generic actions (override via third argument). */
export function addToSyncQueue(action: string, payload: unknown, endpoint = "/worklogs"): string {
  const id = `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
  const items = loadQueue();
  items.push({ id, action, endpoint, payload, status: "pending" });
  saveQueue(items);
  return id;
}

export function getSyncQueue(): SyncQueueItem[] {
  return loadQueue();
}

export function markSynced(id: string): void {
  const items = loadQueue().filter((i) => i.id !== id);
  saveQueue(items);
}
