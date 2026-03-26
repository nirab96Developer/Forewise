
// src/pages/Settings/WorkHours.tsx
// הגדרות זמני עבודה - שעות תקן, חריגות ומנוחה
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Clock, Save, Loader2, Sun, Shield } from 'lucide-react';
import api from '../../services/api';
import UnifiedLoader from '../../components/common/UnifiedLoader';

interface WorkHoursSettings {
  standard_hours_per_day: number;
  net_work_hours: number;
  break_hours: number;
  start_time: string;
  end_time: string;
  break_start: string;
  break_end: string;
  overnight_guard_rate: number;
}

const defaultSettings: WorkHoursSettings = {
  standard_hours_per_day: 10.5,
  net_work_hours: 9.0,
  break_hours: 1.5,
  start_time: '06:30',
  end_time: '17:00',
  break_start: '12:00',
  break_end: '13:30',
  overnight_guard_rate: 250,
};

const WorkHours: React.FC = () => {
  const navigate = useNavigate();
  const [settings, setSettings] = useState<WorkHoursSettings>(defaultSettings);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      // Try to load from API, fallback to defaults
      const response = await api.get('/settings/work-hours').catch(() => null);
      if (response?.data) {
        setSettings({ ...defaultSettings, ...response.data });
      }
    } catch (err) {
      console.error('Error loading settings:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    
    try {
      await api.put('/settings/work-hours', settings);
      setMessage({ type: 'success', text: 'ההגדרות נשמרו בהצלחה' });
    } catch (err) {
      console.error('Error saving settings:', err);
      setMessage({ type: 'error', text: 'שגיאה בשמירת ההגדרות. נסה שוב.' });
    } finally {
      setSaving(false);
      setTimeout(() => setMessage(null), 3000);
    }
  };

  const updateSetting = (key: keyof WorkHoursSettings, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  if (loading) return <UnifiedLoader size="full" />;

  return (
    <div className="min-h-screen bg-gray-50" dir="rtl">
      {/* Header */}
      <div className="sticky top-0 z-20 bg-white shadow-sm">
        <div className="px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/settings')}
              className="text-green-600 hover:text-green-800"
            >
              <ArrowRight className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-gradient-to-br from-gray-600 to-gray-700 rounded-lg flex items-center justify-center text-white">
                <Clock className="w-5 h-5" />
              </div>
              <h1 className="text-lg font-bold text-gray-900">זמני עבודה</h1>
            </div>
          </div>
          <button
            onClick={handleSave}
            disabled={saving}
            className="bg-green-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 text-sm disabled:opacity-50"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            שמור
          </button>
        </div>
      </div>

      {/* Message */}
      {message && (
        <div className={`mx-4 mt-4 px-4 py-3 rounded-lg text-sm ${
          message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'
        }`}>
          {message.text}
        </div>
      )}

      {/* Settings Form */}
      <div className="p-4 space-y-4">
        {/* Core: Net hours + Break — THIS IS WHAT worklog_service USES */}
        <div className="bg-white rounded-xl shadow-sm border border-green-200 p-4">
          <div className="flex items-center gap-2 mb-1">
            <Clock className="w-5 h-5 text-green-600" />
            <h2 className="font-semibold text-gray-900">חישוב שעות עבודה</h2>
          </div>
          <p className="text-xs text-green-700 mb-4">ערכים אלה משמשים לחישוב עלות בדיווחי שעות</p>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">שעות עבודה נטו ביום</label>
              <input
                type="number"
                value={settings.net_work_hours}
                onChange={(e) => updateSetting('net_work_hours', parseFloat(e.target.value) || 0)}
                min={1} max={16} step={0.5}
                className="w-full px-3 py-2.5 border-2 border-green-300 rounded-lg text-lg font-bold text-center focus:ring-2 focus:ring-green-500 focus:border-green-500"
              />
              <p className="text-xs text-gray-500 mt-1">דיווח תקן = ערך זה</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">שעות הפסקה</label>
              <input
                type="number"
                value={settings.break_hours}
                onChange={(e) => updateSetting('break_hours', parseFloat(e.target.value) || 0)}
                min={0} max={4} step={0.5}
                className="w-full px-3 py-2.5 border-2 border-green-300 rounded-lg text-lg font-bold text-center focus:ring-2 focus:ring-green-500 focus:border-green-500"
              />
              <p className="text-xs text-gray-500 mt-1">לא נספרות בתשלום</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">סה"כ נוכחות ביום</label>
              <div className="w-full px-3 py-2.5 border-2 border-gray-200 rounded-lg text-lg font-bold text-center bg-gray-50 text-gray-600">
                {(settings.net_work_hours + settings.break_hours).toFixed(1)}
              </div>
              <p className="text-xs text-gray-500 mt-1">נטו + הפסקה</p>
            </div>
          </div>
        </div>

        {/* Time Range */}
        <div className="bg-white rounded-xl shadow-sm border p-4">
          <div className="flex items-center gap-2 mb-4">
            <Sun className="w-5 h-5 text-yellow-500" />
            <h2 className="font-semibold text-gray-900">זמני עבודה</h2>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1.5">שעת התחלה</label>
              <input
                type="time"
                value={settings.start_time}
                onChange={(e) => updateSetting('start_time', e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1.5">שעת סיום</label>
              <input
                type="time"
                value={settings.end_time}
                onChange={(e) => updateSetting('end_time', e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1.5">תחילת הפסקה</label>
              <input
                type="time"
                value={settings.break_start}
                onChange={(e) => updateSetting('break_start', e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1.5">סיום הפסקה</label>
              <input
                type="time"
                value={settings.break_end}
                onChange={(e) => updateSetting('break_end', e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg"
              />
            </div>
          </div>
        </div>

        {/* Overnight Guard Rate */}
        <div className="bg-white rounded-xl shadow-sm border p-4">
          <div className="flex items-center gap-2 mb-4">
            <Shield className="w-5 h-5 text-indigo-600" />
            <h2 className="font-semibold text-gray-900">שמירת לילה (לינת שטח)</h2>
          </div>
          <div>
<label className="block text-sm text-gray-600 mb-1.5">מחיר שמירת לילה ( ללילה)</label>
            <div className="relative w-48">
<span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 font-medium"></span>
              <input
                type="number"
                value={settings.overnight_guard_rate ?? 0}
                onChange={(e) => updateSetting('overnight_guard_rate', parseFloat(e.target.value) || 0)}
                min={0} step={10}
                className="w-full pr-8 pl-3 py-2.5 border-2 border-indigo-300 rounded-lg text-lg font-bold text-center focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">מתווסף אוטומטית לחישוב עלות כשמסמנים "לינת שטח" בדיווח</p>
          </div>
        </div>

        {/* Info Box */}
        <div className="bg-green-50 border border-green-200 rounded-xl p-4">
          <p className="text-sm text-green-800">
            <strong>שים לב:</strong> ערכים אלה מחוברים ישירות לחישוב העלות בדיווחי שעות.
            שינוי שעות נטו / הפסקה / תעריף לינה ישפיע על כל הדיווחים החדשים שייווצרו.
          </p>
        </div>

        {/* Save Button */}
        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full bg-green-600 text-white py-3 rounded-xl flex items-center justify-center gap-2 text-sm font-medium disabled:opacity-50"
        >
          {saving ? <Loader2 className="w-5 h-5 animate-spin" /> : <Save className="w-5 h-5" />}
          שמור הגדרות
        </button>
      </div>
    </div>
  );
};

export default WorkHours;

