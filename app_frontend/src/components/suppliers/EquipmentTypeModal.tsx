// src/components/suppliers/EquipmentTypeModal.tsx
import React, { useState, useEffect } from 'react';
import { X, Check, Moon, Plus } from 'lucide-react';
import api from '../../services/api';

interface Category { id: number; name: string; default_hourly_rate?: number; }
interface Props { onClose: () => void; onSaved: () => void; }
const GROUPS = ['כלים כבדים', 'כלים קלים', 'ציוד', 'שמירה'];

const EquipmentTypeModal: React.FC<Props> = ({ onClose, onSaved }) => {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [categories, setCategories] = useState<Category[]>([]);
  const [showNewCat, setShowNewCat] = useState(false);
  const [newCatName, setNewCatName] = useState('');
  const [form, setForm] = useState({
    category_id: '', name: '', hourly_rate: '', overnight_rate: '', night_guard: false, notes: '', category_group: '',
  });
  const [catDefaultRate, setCatDefaultRate] = useState<number | null>(null);
  const [rateChanged, setRateChanged] = useState(false);
  const [showRateConfirm, setShowRateConfirm] = useState(false);

  useEffect(() => {
    api.get('/equipment-categories', { params: { page_size: 200 } })
      .then(r => setCategories(r.data?.items || r.data || [])).catch(() => {});
  }, []);

  const f = (k: string, v: string | boolean) => {
    if (k === 'hourly_rate') setRateChanged(true);
    setForm(p => ({ ...p, [k]: v }));
  };

  const onCatChange = (cid: string) => {
    f('category_id', cid);
    const cat = categories.find(c => String(c.id) === cid);
    if (cat?.default_hourly_rate && !form.hourly_rate) {
      setForm(p => ({ ...p, category_id: cid, hourly_rate: String(cat.default_hourly_rate) }));
      setCatDefaultRate(cat.default_hourly_rate);
    } else {
      setCatDefaultRate(cat?.default_hourly_rate || null);
    }
  };

  const createCategory = async () => {
    if (!newCatName.trim()) return;
    try {
      const res = await api.post('/equipment-categories', { name: newCatName.trim() });
      const newCat = res.data;
      setCategories(prev => [...prev, newCat]);
      setForm(p => ({ ...p, category_id: String(newCat.id) }));
      setNewCatName(''); setShowNewCat(false);
    } catch (e: any) { setError('שגיאה ביצירת קבוצה'); }
  };

  const save = async () => {
    if (!form.category_id) { setError('יש לבחור קבוצה'); return; }
    if (!form.name.trim()) { setError('שם סוג ציוד חובה'); return; }
    if (!form.hourly_rate) { setError('תעריף שעתי חובה'); return; }
    if (rateChanged && catDefaultRate && Number(form.hourly_rate) !== catDefaultRate && !showRateConfirm) {
      setShowRateConfirm(true); return;
    }
    setSaving(true); setError('');
    try {
      const autoCode = form.name.trim().replace(/[^a-zA-Z0-9\u0590-\u05FF]/g, '_').slice(0, 30) + '_' + Date.now().toString().slice(-4);
      await api.post('/equipment-types', {
        code: autoCode,
        name: form.name.trim(),
        category_id: Number(form.category_id),
        category_group: form.category_group || undefined,
        hourly_rate: Number(form.hourly_rate),
        overnight_rate: form.overnight_rate ? Number(form.overnight_rate) : undefined,
        night_guard: form.night_guard,
        description: form.notes || undefined,
        is_active: true,
      });
      onSaved(); onClose();
    } catch (e: any) { setError(e?.response?.data?.detail || 'שגיאה בשמירה'); }
    setSaving(false);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-5 border-b">
          <h2 className="text-lg font-bold text-gray-900">סוג ציוד חדש</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded-lg"><X className="w-5 h-5 text-gray-400" /></button>
        </div>
        <div className="p-5 space-y-4">
          {error && <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{error}</p>}
          {showRateConfirm && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
              <p className="text-sm text-amber-800 font-medium mb-2">התעריף שונה מברירת המחדל של הקבוצה (₪{catDefaultRate}). להמשיך?</p>
              <div className="flex gap-2">
                <button onClick={() => { setShowRateConfirm(false); save(); }} className="px-3 py-1.5 bg-amber-500 text-white rounded text-xs">כן, שמור</button>
                <button onClick={() => setShowRateConfirm(false)} className="px-3 py-1.5 border border-amber-300 text-amber-700 rounded text-xs">ביטול</button>
              </div>
            </div>
          )}

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm font-medium text-gray-700">קבוצה *</label>
              <button onClick={() => setShowNewCat(!showNewCat)} className="text-xs text-green-600 hover:underline flex items-center gap-0.5">
                <Plus className="w-3 h-3" /> קבוצה חדשה
              </button>
            </div>
            {showNewCat && (
              <div className="flex gap-2 mb-2">
                <input value={newCatName} onChange={e => setNewCatName(e.target.value)}
                  placeholder="שם הקבוצה החדשה"
                  className="flex-1 px-3 py-2 border border-green-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500" />
                <button onClick={createCategory} className="px-3 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700">צור</button>
              </div>
            )}
            <select value={form.category_id} onChange={e => onCatChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500">
              <option value="">בחר קבוצה</option>
              {categories.map(c => <option key={c.id} value={String(c.id)}>{c.name}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">שם סוג הציוד *</label>
            <input value={form.name} onChange={e => f('name', e.target.value)}
              placeholder="לדוגמה: מחפרון זרוע טלסקופי"
              disabled={!form.category_id}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500 disabled:bg-gray-50" />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">תעריף שעתי (₪) *</label>
              <input type="number" value={form.hourly_rate} onChange={e => f('hourly_rate', e.target.value)}
                placeholder="150"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">תעריף לינה (₪)</label>
              <input type="number" value={form.overnight_rate} onChange={e => f('overnight_rate', e.target.value)}
                placeholder="375"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500" />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">קבוצת ציוד</label>
            <select value={form.category_group} onChange={e => f('category_group', e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500">
              <option value="">בחר קבוצה (אופציונלי)</option>
              {GROUPS.map(g => <option key={g} value={g}>{g}</option>)}
            </select>
          </div>

          <label className="flex items-center gap-3 cursor-pointer select-none">
            <input type="checkbox" checked={form.night_guard} onChange={e => f('night_guard', e.target.checked)}
              className="w-4 h-4 rounded text-green-600 focus:ring-green-500" />
            <Moon className="w-4 h-4 text-indigo-500" />
            <span className="text-sm font-medium text-gray-700">סוג ציוד מתאים לשמירת לילה</span>
          </label>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">הערות</label>
            <textarea value={form.notes} onChange={e => f('notes', e.target.value)} rows={2}
              placeholder="הערות נוספות..."
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500 resize-none" />
          </div>
        </div>
        <div className="flex justify-end gap-3 px-5 pb-5">
          <button onClick={onClose} className="px-4 py-2 border border-gray-200 text-gray-600 rounded-lg text-sm hover:bg-gray-50">ביטול</button>
          <button onClick={save} disabled={saving}
            className="flex items-center gap-1.5 px-5 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 disabled:opacity-50">
            {saving ? 'שומר...' : <><Check className="w-4 h-4" /> צור סוג ציוד</>}
          </button>
        </div>
      </div>
    </div>
  );
};

export default EquipmentTypeModal;
