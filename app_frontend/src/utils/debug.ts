// src/utils/debug.ts
// מערכת debug ל-frontend - רישום וניטור

interface LogEntry {
  id: string;
  timestamp: Date;
  type: 'log' | 'info' | 'warn' | 'error' | 'api' | 'network';
  message: string;
  data?: any;
  stack?: string;
}

class DebugLogger {
  private logs: LogEntry[] = [];
  private maxLogs: number = 1000;
  private isEnabled: boolean = true;
  private listeners: Set<(logs: LogEntry[]) => void> = new Set();

  constructor() {
    // הפעלת debug mode מ-environment או localStorage
    this.isEnabled = 
      import.meta.env.VITE_DEBUG === 'true' || 
      import.meta.env.DEV ||
      localStorage.getItem('debug_enabled') === 'true';
    
    // Override console methods
    this.overrideConsole();
  }

  private overrideConsole() {
    if (!this.isEnabled) return;

    const originalLog = console.log;
    const originalInfo = console.info;
    const originalWarn = console.warn;
    const originalError = console.error;

    console.log = (...args: any[]) => {
      this.addLog('log', args.join(' '), args);
      originalLog.apply(console, args);
    };

    console.info = (...args: any[]) => {
      this.addLog('info', args.join(' '), args);
      originalInfo.apply(console, args);
    };

    console.warn = (...args: any[]) => {
      this.addLog('warn', args.join(' '), args);
      originalWarn.apply(console, args);
    };

    console.error = (...args: any[]) => {
      const error = args[0] instanceof Error ? args[0] : null;
      this.addLog('error', args.join(' '), {
        ...args,
        stack: error?.stack,
      });
      originalError.apply(console, args);
    };
  }

  addLog(type: LogEntry['type'], message: string, data?: any) {
    if (!this.isEnabled) return;

    const entry: LogEntry = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      type,
      message,
      data,
    };

    this.logs.push(entry);
    
    // שמירה רק על 1000 לוגים אחרונים
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs);
    }

    // עדכון listeners
    this.notifyListeners();
  }

  logAPIRequest(method: string, url: string, data?: any, headers?: any) {
    this.addLog('api', `[${method}] ${url}`, {
      method,
      url,
      data,
      headers,
      direction: 'יוצא',
    });
  }

  logAPIResponse(method: string, url: string, status: number, data?: any, duration?: number) {
    this.addLog('api', `[${method}] ${url} → ${status}${duration ? ` (${duration}ms)` : ''}`, {
      method,
      url,
      status,
      data,
      duration,
      direction: 'נכנס',
    });
  }

  logAPIError(method: string, url: string, error: any) {
    this.addLog('error', `[${method}] ${url} → שגיאה`, {
      method,
      url,
      error: error.message || error,
      response: error.response?.data,
      status: error.response?.status,
      stack: error.stack,
    });
  }

  logNetworkError(message: string, error: any) {
    this.addLog('network', `שגיאת רשת: ${message}`, {
      message,
      error: error.message || error,
      code: error.code,
      stack: error.stack,
    });
  }

  getLogs(filter?: { type?: LogEntry['type']; search?: string }): LogEntry[] {
    let filtered = [...this.logs];

    if (filter?.type) {
      filtered = filtered.filter(log => log.type === filter.type);
    }

    if (filter?.search) {
      const search = filter.search.toLowerCase();
      filtered = filtered.filter(log => 
        log.message.toLowerCase().includes(search) ||
        JSON.stringify(log.data).toLowerCase().includes(search)
      );
    }

    return filtered;
  }

  clearLogs() {
    this.logs = [];
    this.notifyListeners();
  }

  subscribe(callback: (logs: LogEntry[]) => void) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  private notifyListeners() {
    // Use setTimeout to defer notifications to avoid updating state during render
    setTimeout(() => {
      this.listeners.forEach(callback => callback([...this.logs]));
    }, 0);
  }

  enable() {
    this.isEnabled = true;
    localStorage.setItem('debug_enabled', 'true');
    this.overrideConsole();
  }

  disable() {
    this.isEnabled = false;
    localStorage.setItem('debug_enabled', 'false');
  }

  isDebugEnabled(): boolean {
    return this.isEnabled;
  }

  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }

  downloadLogs() {
    const data = this.exportLogs();
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `debug-logs-${new Date().toISOString()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
}

// Export singleton instance
export const debugLogger = new DebugLogger();
export type { LogEntry };
