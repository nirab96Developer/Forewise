// src/services/offlineService.ts
import api from './api';

export interface OfflineOperation {
  id: string;
  type: string;
  data: any;
  created_at: string;
  synced: boolean;
  error?: string;
}

export interface SyncResult {
  success: boolean;
  synced_count: number;
  failed_count: number;
  errors: string[];
}

class OfflineService {
  private queue: OfflineOperation[] = [];
  private isOnline: boolean = navigator.onLine;
  private syncInterval: NodeJS.Timeout | null = null;

  constructor() {
    this.loadQueueFromStorage();
    this.setupEventListeners();
    this.startPeriodicSync();
  }

  /**
   * הוספת פעולה לתור הסנכרון
   */
  async queueOperation(type: string, data: any): Promise<string> {
    const operation: OfflineOperation = {
      id: this.generateId(),
      type,
      data,
      created_at: new Date().toISOString(),
      synced: false
    };

    this.queue.push(operation);
    this.saveQueueToStorage();

    // אם אנחנו אונליין, ננסה לסנכרן מיד
    if (this.isOnline) {
      await this.syncOperation(operation);
    }

    return operation.id;
  }

  /**
   * סנכרון פעולה בודדת
   */
  private async syncOperation(operation: OfflineOperation): Promise<boolean> {
    try {
      const endpoint = this.getEndpointForType(operation.type);
      if (!endpoint) {
        throw new Error(`Unknown operation type: ${operation.type}`);
      }

      await api.post(endpoint, operation.data);
      
      // סימון כמשונכרן
      operation.synced = true;
      operation.error = undefined;
      this.saveQueueToStorage();
      
      return true;
    } catch (error: any) {
      operation.error = error.message;
      this.saveQueueToStorage();
      console.error('Sync operation failed:', error);
      return false;
    }
  }

  /**
   * סנכרון כל הפעולות הממתינות
   */
  async syncAll(): Promise<SyncResult> {
    const result: SyncResult = {
      success: true,
      synced_count: 0,
      failed_count: 0,
      errors: []
    };

    const pendingOperations = this.queue.filter(op => !op.synced);
    
    for (const operation of pendingOperations) {
      const success = await this.syncOperation(operation);
      if (success) {
        result.synced_count++;
      } else {
        result.failed_count++;
        result.errors.push(operation.error || 'Unknown error');
      }
    }

    result.success = result.failed_count === 0;
    return result;
  }

  /**
   * קבלת פעולות ממתינות
   */
  getPendingOperations(): OfflineOperation[] {
    return this.queue.filter(op => !op.synced);
  }

  /**
   * קבלת כל הפעולות
   */
  getAllOperations(): OfflineOperation[] {
    return [...this.queue];
  }

  /**
   * מחיקת פעולות משונכרנות
   */
  clearSyncedOperations(): void {
    this.queue = this.queue.filter(op => !op.synced);
    this.saveQueueToStorage();
  }

  /**
   * בדיקת סטטוס חיבור
   */
  isConnected(): boolean {
    return this.isOnline;
  }

  /**
   * קבלת מספר פעולות ממתינות
   */
  getPendingCount(): number {
    return this.queue.filter(op => !op.synced).length;
  }

  /**
   * קבלת endpoint לפי סוג פעולה
   */
  private getEndpointForType(type: string): string | null {
    const endpoints: { [key: string]: string } = {
      'work_log': '/worklogs/',
      'work_order': '/work-orders/',
      'project': '/projects/',
      'equipment': '/equipment/',
      'supplier': '/suppliers/',
      'notification': '/notifications/'
    };

    return endpoints[type] || null;
  }

  /**
   * יצירת ID ייחודי
   */
  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * שמירת התור ל-localStorage
   */
  private saveQueueToStorage(): void {
    try {
      localStorage.setItem('offline_queue', JSON.stringify(this.queue));
    } catch (error) {
      console.error('Failed to save queue to storage:', error);
    }
  }

  /**
   * טעינת התור מ-localStorage
   */
  private loadQueueFromStorage(): void {
    try {
      const stored = localStorage.getItem('offline_queue');
      if (stored) {
        this.queue = JSON.parse(stored);
      }
    } catch (error) {
      console.error('Failed to load queue from storage:', error);
      this.queue = [];
    }
  }

  /**
   * הגדרת מאזיני אירועים
   */
  private setupEventListeners(): void {
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.syncAll();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
    });
  }

  /**
   * התחלת סנכרון תקופתי
   */
  private startPeriodicSync(): void {
    this.syncInterval = setInterval(() => {
      if (this.isOnline && this.getPendingCount() > 0) {
        this.syncAll();
      }
    }, 30000); // כל 30 שניות
  }

  /**
   * עצירת סנכרון תקופתי
   */
  destroy(): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
    }
  }
}

const offlineService = new OfflineService();
export default offlineService;

