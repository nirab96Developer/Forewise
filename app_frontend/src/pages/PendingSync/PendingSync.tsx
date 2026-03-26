// pages/PendingSync/PendingSync.tsx
// דף ממתינים לסנכרון — מציג פריטים שנשמרו offline

import React, { useEffect, useState, useCallback } from 'react';
import { Wifi, WifiOff, RefreshCw, Trash2, Clock, FileText, Scan } from 'lucide-react';
import { useOfflineSync, type OfflineItem } from '../../hooks/useOfflineSync';
import { removePendingItem } from '../../utils/offlineStorage';

const TYPE_META: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  worklog: {
    label: 'דיווח שעות',
    icon: <Clock className="w-4 h-4" />,
    color: 'text-blue-600 bg-blue-50',
  },
  scan: {
    label: 'סריקת ציוד',
    icon: <Scan className="w-4 h-4" />,
    color: 'text-purple-600 bg-purple-50',
  },
  work_order: {
    label: 'הזמנת ציוד',
    icon: <FileText className="w-4 h-4" />,
    color: 'text-orange-600 bg-orange-50',
  },
};

function formatTime(ts: number): string {
  const d = new Date(ts);
  const now = new Date();
  const sameDay = d.toDateString() === now.toDateString();
  const time = d.toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' });
  if (sameDay) return `היום ${time}`;
  return d.toLocaleDateString('he-IL') + ' ' + time;
}

function getItemSummary(item: OfflineItem): string {
  const d = item.data;
  if (item.type === 'worklog') {
    const parts = [];
    if (d.total_hours) parts.push(`${d.total_hours} שעות`);
    if (d.activity_type) parts.push(d.activity_type);
    return parts.join(' | ') || 'דיווח שעות';
  }
  if (item.type === 'scan') {
    return `ציוד #${d.equipment_id || '?'}`;
  }
  if (item.type === 'work_order') {
    const parts = [];
    if (d.equipment_type) parts.push(d.equipment_type);
    if (d.estimated_hours) parts.push(`${d.estimated_hours} שעות`);
    return parts.join(' | ') || 'הזמנה חדשה';
  }
  return 'פריט לא ידוע';
}

const PendingSync: React.FC = () => {
  const { isOnline, isSyncing, syncAll, loadAllItems, refreshCount } = useOfflineSync();
  const [items, setItems] = useState<OfflineItem[]>([]);
  const [loadingItems, setLoadingItems] = useState(true);

  const load = useCallback(async () => {
    setLoadingItems(true);
    const all = await loadAllItems();
    // Sort newest first
    all.sort((a, b) => b.created_at - a.created_at);
    setItems(all);
    setLoadingItems(false);
  }, [loadAllItems]);

  useEffect(() => {
    load();
    window.addEventListener('offline-queue-changed', load);
    return () => window.removeEventListener('offline-queue-changed', load);
  }, [load]);

  const handleDelete = async (id: string) => {
    await removePendingItem(id);
    await refreshCount();
    load();
  };

  const handleSyncAll = async () => {
    await syncAll();
    load();
  };

  const pending = items.filter(i => i.status === 'pending');
  const failed = items.filter(i => i.status === 'failed');

  return (
    <div className="min-h-screen p-6" dir="rtl">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-1">
            {isOnline ? (
              <Wifi className="w-6 h-6 text-green-600" />
            ) : (
              <WifiOff className="w-6 h-6 text-orange-500" />
            )}
            <h1 className="text-2xl font-bold text-gray-900">ממתינים לסנכרון</h1>
            {items.length > 0 && (
              <span className="bg-orange-100 text-orange-700 text-sm font-semibold px-2.5 py-0.5 rounded-full">
                {items.length}
              </span>
            )}
          </div>
          <p className="text-sm text-gray-500 mr-9">
            {isOnline
              ? 'מחובר לאינטרנט — ניתן לסנכרן עכשיו'
              : 'אין חיבור — הפריטים יסונכרנו כשהחיבור יחזור'}
          </p>
        </div>

        {/* Sync Button */}
        <div className="mb-6">
          {isOnline ? (
            <button
              onClick={handleSyncAll}
              disabled={isSyncing || pending.length === 0}
              className="flex items-center gap-2 px-5 py-2.5 bg-green-600 text-white rounded-xl font-medium hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw className={`w-4 h-4 ${isSyncing ? 'animate-spin' : ''}`} />
{isSyncing ? 'מסנכרן...' : ` סנכרן הכל עכשיו (${pending.length})`}
            </button>
          ) : (
            <div className="flex items-center gap-2 px-5 py-2.5 bg-orange-100 text-orange-700 rounded-xl font-medium border border-orange-200">
              <WifiOff className="w-4 h-4" />
אין חיבור — הסנכרון יתבצע אוטומטית
            </div>
          )}
        </div>

        {/* Items list */}
        {loadingItems ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="animate-pulse bg-gray-100 rounded-xl h-20 border border-gray-200" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="bg-white rounded-2xl border border-gray-200 p-12 text-center">
<div className="text-4xl mb-3"></div>
            <p className="text-gray-600 font-medium">הכל מסונכרן — אין פריטים ממתינים</p>
          </div>
        ) : (
          <div className="space-y-3">
            {/* Pending */}
            {pending.length > 0 && (
              <>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide px-1">ממתינים ({pending.length})</p>
                {pending.map(item => {
                  const meta = TYPE_META[item.type] || TYPE_META.worklog;
                  return (
                    <div
                      key={item.id}
                      className="bg-white rounded-xl border border-gray-200 px-4 py-3 flex items-center gap-3 hover:shadow-sm transition-shadow"
                    >
                      {/* Type badge */}
                      <div className={`flex-shrink-0 flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium ${meta.color}`}>
                        {meta.icon}
                        {meta.label}
                      </div>

                      {/* Summary */}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-800 truncate">{getItemSummary(item)}</p>
                        <p className="text-xs text-gray-400 mt-0.5">{formatTime(item.created_at)}</p>
                      </div>

                      {/* Status dot */}
                      <span className="flex-shrink-0 w-2 h-2 rounded-full bg-orange-400" title="ממתין" />

                      {/* Delete */}
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="flex-shrink-0 p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                        title="מחק"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  );
                })}
              </>
            )}

            {/* Failed */}
            {failed.length > 0 && (
              <>
                <p className="text-xs font-semibold text-red-500 uppercase tracking-wide px-1 mt-4">נכשלו ({failed.length})</p>
                {failed.map(item => {
                  const meta = TYPE_META[item.type] || TYPE_META.worklog;
                  return (
                    <div
                      key={item.id}
                      className="bg-red-50 rounded-xl border border-red-200 px-4 py-3 flex items-center gap-3"
                    >
                      <div className={`flex-shrink-0 flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium ${meta.color}`}>
                        {meta.icon}
                        {meta.label}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-800 truncate">{getItemSummary(item)}</p>
                        {item.error && <p className="text-xs text-red-500 mt-0.5">{item.error}</p>}
                        <p className="text-xs text-gray-400">{formatTime(item.created_at)}</p>
                      </div>
                      <span className="flex-shrink-0 w-2 h-2 rounded-full bg-red-500" title="נכשל" />
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="flex-shrink-0 p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                        title="מחק"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  );
                })}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default PendingSync;
