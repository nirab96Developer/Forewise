// utils/offlineStorage.ts — IndexedDB offline queue

const DB_NAME = 'forewise-offline';
const STORE = 'pending_items';
const DB_VERSION = 1;

export interface OfflineItem {
  id: string;
  type: 'worklog' | 'scan' | 'work_order';
  data: Record<string, any>;
  created_at: number; // timestamp ms
  status: 'pending' | 'syncing' | 'failed';
  error?: string;
}

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE)) {
        const store = db.createObjectStore(STORE, { keyPath: 'id' });
        store.createIndex('status', 'status');
        store.createIndex('type', 'type');
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

function uuid(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

async function save(item: OfflineItem): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, 'readwrite');
    tx.objectStore(STORE).put(item);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function saveOfflineWorklog(data: Record<string, any>): Promise<string> {
  const id = uuid();
  await save({ id, type: 'worklog', data, created_at: Date.now(), status: 'pending' });
  window.dispatchEvent(new CustomEvent('offline-queue-changed'));
  return id;
}

export async function saveOfflineScan(data: Record<string, any>): Promise<string> {
  const id = uuid();
  await save({ id, type: 'scan', data, created_at: Date.now(), status: 'pending' });
  window.dispatchEvent(new CustomEvent('offline-queue-changed'));
  return id;
}

export async function saveOfflineWorkOrder(data: Record<string, any>): Promise<string> {
  const id = uuid();
  await save({ id, type: 'work_order', data, created_at: Date.now(), status: 'pending' });
  window.dispatchEvent(new CustomEvent('offline-queue-changed'));
  return id;
}

export async function getPendingItems(): Promise<OfflineItem[]> {
  try {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, 'readonly');
      const req = tx.objectStore(STORE).index('status').getAll('pending');
      req.onsuccess = () => resolve(req.result || []);
      req.onerror = () => reject(req.error);
    });
  } catch {
    return [];
  }
}

export async function getAllPendingItems(): Promise<OfflineItem[]> {
  try {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, 'readonly');
      const req = tx.objectStore(STORE).getAll();
      req.onsuccess = () =>
        resolve((req.result || []).filter((i: OfflineItem) => i.status !== 'syncing'));
      req.onerror = () => reject(req.error);
    });
  } catch {
    return [];
  }
}

export async function removePendingItem(id: string): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, 'readwrite');
    tx.objectStore(STORE).delete(id);
    tx.oncomplete = () => {
      window.dispatchEvent(new CustomEvent('offline-queue-changed'));
      resolve();
    };
    tx.onerror = () => reject(tx.error);
  });
}

export async function markItemFailed(id: string, error?: string): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, 'readwrite');
    const store = tx.objectStore(STORE);
    const req = store.get(id);
    req.onsuccess = () => {
      const item = req.result;
      if (item) {
        item.status = 'failed';
        item.error = error || 'שגיאה לא ידועה';
        store.put(item);
      }
    };
    tx.oncomplete = () => {
      window.dispatchEvent(new CustomEvent('offline-queue-changed'));
      resolve();
    };
    tx.onerror = () => reject(tx.error);
  });
}

export async function getPendingCount(): Promise<number> {
  const items = await getPendingItems();
  return items.length;
}
