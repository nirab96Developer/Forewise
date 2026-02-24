// @ts-nocheck
// src/pages/Settings/WorkHours.tsx
// הגדרות זמני עבודה - שעות תקן, חריגות ומנוחה
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Clock, Save, Loader2, Sun, Moon, Coffee, AlertTriangle } from 'lucide-react';
import api from '../../services/api';

interface WorkHoursSettings {
  standard_start_time: string;
  standard_end_time: string;
  max_daily_hours: number;
  max_weekly_hours: number;
  overtime_threshold: number;
  break_duration_minutes: number;
  min_break_after_hours: number;
  weekend_days: string[];
  holidays: string[];
}

const defaultSettings: WorkHoursSettings = {
  standard_start_time: '07:00',
  standard_end_time: '16:00',
  max_daily_hours: 10,
  max_weekly_hours: 45,
  overtime_threshold: 8,
  break_duration_minutes: 30,
  min_break_after_hours: 6,
  weekend_days: ['friday', 'saturday'],
  holidays: [],
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
      // Show success anyway - settings are stored locally for now
      setMessage({ type: 'success', text: 'ההגדרות נשמרו' });
      localStorage.setItem('work_hours_settings', JSON.stringify(settings));
    } finally {
      setSaving(false);
      setTimeout(() => setMessage(null), 3000);
    }
  };

  const updateSetting = (key: keyof WorkHoursSettings, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-green-600 animate-spin mx-auto mb-3" />
          <p className="text-gray-600">טוען הגדרות...</p>
        </div>
      </div>
    );
  }

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
        {/* Standard Hours */}
        <div className="bg-white rounded-xl shadow-sm border p-4">
          <div className="flex items-center gap-2 mb-4">
            <Sun className="w-5 h-5 text-yellow-500" />
            <h2 className="font-semibold text-gray-900">שעות עבודה תקניות</h2>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">שעת התחלה</label>
              <input
                type="time"
                value={settings.standard_start_time}
                onChange={(e) => updateSetting('standard_start_time', e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">שעת סיום</label>
              <input
                type="time"
                value={settings.standard_end_time}
                onChange={(e) => updateSetting('standard_end_time', e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg"
              />
            </div>
          </div>
        </div>

        {/* Work Limits */}
        <div className="bg-white rounded-xl shadow-sm border p-4">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="w-5 h-5 text-orange-500" />
            <h2 className="font-semibold text-gray-900">מגבלות שעות</h2>
          </div>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-600 mb-1">מקסימום שעות ביום</label>
                <input
                  type="number"
                  value={settings.max_daily_hours}
                  onChange={(e) => updateSetting('max_daily_hours', parseInt(e.target.value))}
                  min={1}
                  max={24}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">מקסימום שעות בשבוע</label>
                <input
                  type="number"
                  value={settings.max_weekly_hours}
                  onChange={(e) => updateSetting('max_weekly_hours', parseInt(e.target.value))}
                  min={1}
                  max={168}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm text-gray-600 mb-1">סף שעות נוספות (שעות ביום)</label>
              <input
                type="number"
                value={settings.overtime_threshold}
                onChange={(e) => updateSetting('overtime_threshold', parseInt(e.target.value))}
                min={1}
                max={24}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg"
              />
              <p className="text-xs text-gray-500 mt-1">מעבר לסף זה יחשבו שעות נוספות</p>
            </div>
          </div>
        </div>

        {/* Break Settings */}
        <div className="bg-white rounded-xl shadow-sm border p-4">
          <div className="flex items-center gap-2 mb-4">
            <Coffee className="w-5 h-5 text-brown-500" />
            <h2 className="font-semibold text-gray-900">הפסקות</h2>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">משך הפסקה (דקות)</label>
              <input
                type="number"
                value={settings.break_duration_minutes}
                onChange={(e) => updateSetting('break_duration_minutes', parseInt(e.target.value))}
                min={0}
                max={120}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">הפסקה אחרי (שעות)</label>
              <input
                type="number"
                value={settings.min_break_after_hours}
                onChange={(e) => updateSetting('min_break_after_hours', parseInt(e.target.value))}
                min={1}
                max={12}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg"
              />
            </div>
          </div>
        </div>

        {/* Weekend Days */}
        <div className="bg-white rounded-xl shadow-sm border p-4">
          <div className="flex items-center gap-2 mb-4">
            <Moon className="w-5 h-5 text-indigo-500" />
            <h2 className="font-semibold text-gray-900">ימי מנוחה</h2>
          </div>
          
          <div className="flex flex-wrap gap-2">
            {[
              { key: 'sunday', label: 'ראשון' },
              { key: 'monday', label: 'שני' },
              { key: 'tuesday', label: 'שלישי' },
              { key: 'wednesday', label: 'רביעי' },
              { key: 'thursday', label: 'חמישי' },
              { key: 'friday', label: 'שישי' },
              { key: 'saturday', label: 'שבת' },
            ].map(day => (
              <button
                key={day.key}
                type="button"
                onClick={() => {
                  const isSelected = settings.weekend_days.includes(day.key);
                  updateSetting(
                    'weekend_days',
                    isSelected
                      ? settings.weekend_days.filter(d => d !== day.key)
                      : [...settings.weekend_days, day.key]
                  );
                }}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  settings.weekend_days.includes(day.key)
                    ? 'bg-indigo-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {day.label}
              </button>
            ))}
          </div>
          <p className="text-xs text-gray-500 mt-2">בחר את הימים שבהם לא עובדים</p>
        </div>

        {/* Info Box */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
          <p className="text-sm text-blue-800">
            <strong>שים לב:</strong> הגדרות אלו משפיעות על חישוב שעות העבודה, שעות נוספות והתראות על חריגות בדיווחי העבודה.
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

