// @ts-nocheck
// src/components/DebugPanel.tsx
// פאנל debug לצפייה בלוגים ומידע מערכת

import React, { useState, useEffect, useRef } from 'react';
import { debugLogger, LogEntry } from '../utils/debug';
import { X, Download, Trash2, Filter, Search, ChevronDown, ChevronUp } from 'lucide-react';

interface DebugPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

const DebugPanel: React.FC<DebugPanelProps> = ({ isOpen, onClose }) => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filter, setFilter] = useState<{ type?: LogEntry['type']; search?: string }>({});
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [isMinimized, setIsMinimized] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const unsubscribe = debugLogger.subscribe((newLogs) => {
      setLogs(newLogs);
    });

    // טעינה ראשונית
    setLogs(debugLogger.getLogs(filter));

    return unsubscribe;
  }, [filter]);

  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  const filteredLogs = debugLogger.getLogs(filter);

  const getLogColor = (type: LogEntry['type']) => {
    switch (type) {
      case 'error': return 'text-red-400 bg-red-900/20';
      case 'warn': return 'text-yellow-400 bg-yellow-900/20';
      case 'info': return 'text-blue-400 bg-blue-900/20';
      case 'api': return 'text-purple-400 bg-purple-900/20';
      case 'network': return 'text-orange-400 bg-orange-900/20';
      default: return 'text-gray-300 bg-gray-800/20';
    }
  };

  const getLogIcon = (type: LogEntry['type']) => {
    switch (type) {
      case 'error': return '❌';
      case 'warn': return '⚠️';
      case 'info': return 'ℹ️';
      case 'api': return '🌐';
      case 'network': return '📡';
      default: return '📝';
    }
  };

  const getTypeLabel = (type: LogEntry['type']) => {
    switch (type) {
      case 'error': return 'שגיאה';
      case 'warn': return 'אזהרה';
      case 'info': return 'מידע';
      case 'api': return 'API';
      case 'network': return 'רשת';
      case 'log': return 'לוג';
      default: return type;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed bottom-0 right-0 w-full md:w-1/2 lg:w-1/3 h-[70vh] md:h-[600px] bg-gray-900 border-t border-gray-700 shadow-2xl z-50 flex flex-col" dir="rtl">
      {/* כותרת */}
      <div className="bg-gray-800 px-4 py-2 flex items-center justify-between border-b border-gray-700">
        <div className="flex items-center gap-2">
          <span className="text-green-400 font-bold">🐛 פאנל Debug</span>
          <span className="text-xs text-gray-400">({filteredLogs.length} לוגים)</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-1 hover:bg-gray-700 rounded"
            title={isMinimized ? 'הרחב' : 'מזער'}
          >
            {isMinimized ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
          <button
            onClick={() => debugLogger.downloadLogs()}
            className="p-1 hover:bg-gray-700 rounded"
            title="הורד לוגים"
          >
            <Download className="w-4 h-4" />
          </button>
          <button
            onClick={() => {
              debugLogger.clearLogs();
              setSelectedLog(null);
            }}
            className="p-1 hover:bg-gray-700 rounded"
            title="נקה לוגים"
          >
            <Trash2 className="w-4 h-4" />
          </button>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-700 rounded"
            title="סגור"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* מסננים */}
          <div className="bg-gray-800 px-4 py-2 border-b border-gray-700 flex gap-2 flex-wrap">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute right-2 top-2.5 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="חפש בלוגים..."
                  value={filter.search || ''}
                  onChange={(e) => setFilter({ ...filter, search: e.target.value })}
                  className="w-full pr-8 pl-2 py-1 bg-gray-700 text-white text-sm rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                  dir="rtl"
                />
              </div>
            </div>
            <select
              value={filter.type || 'all'}
              onChange={(e) => setFilter({ ...filter, type: e.target.value === 'all' ? undefined : e.target.value as LogEntry['type'] })}
              className="px-2 py-1 bg-gray-700 text-white text-sm rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
              dir="rtl"
            >
              <option value="all">כל הסוגים</option>
              <option value="log">לוג</option>
              <option value="info">מידע</option>
              <option value="warn">אזהרה</option>
              <option value="error">שגיאה</option>
              <option value="api">API</option>
              <option value="network">רשת</option>
            </select>
            <label className="flex items-center gap-1 text-xs text-gray-400" dir="rtl">
              <input
                type="checkbox"
                checked={autoScroll}
                onChange={(e) => setAutoScroll(e.target.checked)}
                className="rounded"
              />
              גלילה אוטומטית
            </label>
          </div>

          {/* רשימת לוגים */}
          <div className="flex-1 overflow-auto bg-gray-900">
            <div className="p-2 space-y-1">
              {filteredLogs.length === 0 ? (
                <div className="text-center text-gray-500 py-8">אין לוגים להצגה</div>
              ) : (
                filteredLogs.map((log) => (
                  <div
                    key={log.id}
                    onClick={() => setSelectedLog(log)}
                    className={`p-2 rounded cursor-pointer hover:bg-gray-800 border-r-2 ${
                      selectedLog?.id === log.id ? 'bg-gray-800 border-blue-500' : 'border-transparent'
                    } ${getLogColor(log.type)}`}
                    dir="rtl"
                  >
                    <div className="flex items-start gap-2">
                      <span className="text-xs">{getLogIcon(log.type)}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-400">
                            {log.timestamp.toLocaleTimeString('he-IL')}
                          </span>
                          <span className="text-xs font-semibold uppercase">{getTypeLabel(log.type)}</span>
                        </div>
                        <div className="text-sm mt-1 break-words">{log.message}</div>
                      </div>
                    </div>
                  </div>
                ))
              )}
              <div ref={logsEndRef} />
            </div>
          </div>

          {/* פרטי לוג */}
          {selectedLog && (
            <div className="bg-gray-800 border-t border-gray-700 p-4 max-h-48 overflow-auto" dir="rtl">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-bold text-sm">פרטי לוג</h3>
                <button
                  onClick={() => setSelectedLog(null)}
                  className="text-gray-400 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <div className="text-xs space-y-2" dir="rtl">
                <div>
                  <span className="text-gray-400">זמן:</span>{' '}
                  <span className="text-white">{selectedLog.timestamp.toLocaleString('he-IL')}</span>
                </div>
                <div>
                  <span className="text-gray-400">סוג:</span>{' '}
                  <span className="text-white">{getTypeLabel(selectedLog.type)}</span>
                </div>
                <div>
                  <span className="text-gray-400">הודעה:</span>{' '}
                  <span className="text-white">{selectedLog.message}</span>
                </div>
                {selectedLog.data && (
                  <div>
                    <span className="text-gray-400">נתונים:</span>
                    <pre className="mt-1 p-2 bg-gray-900 rounded text-white overflow-auto text-left">
                      {JSON.stringify(selectedLog.data, null, 2)}
                    </pre>
                  </div>
                )}
                {selectedLog.stack && (
                  <div>
                    <span className="text-gray-400">Stack Trace:</span>
                    <pre className="mt-1 p-2 bg-gray-900 rounded text-white overflow-auto text-xs text-left">
                      {selectedLog.stack}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default DebugPanel;
