// src/components/suppliers/EquipmentTypeModal.tsx 
import React, { useState, useEffect } from 'react';
import { X, Plus, Moon } from 'lucide-react';
import api from '../../services/api';

interface Category { id: number; name: string; default_hourly_rate?: number; }
interface Props { onClose: () => void; onSaved: () => void; }
const GROUPS = ['כלים כבדים','כלים קלים','ציוד','שמירה'];

const EquipmentTypeModal: React.FC<Props> = ({ onClose, onSaved }) => {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [categories, setCategories] = useState<Category[]>([]);
  const [showNewCat, setShowNewCat] = useState(false);
  const [newCatName, setNewCatName] = useState('');
  const [form, setForm] = useState({ category_id:'', name:'', hourly_rate:'', overnight_rate:'', night_guard:false, notes:'', category_group:'' });
  const [catDefaultRate, setCatDefaultRate] = useState<number|null>(null);
  const [rateChanged, setRateChanged] = useState(false);
  const [showRateConfirm, setShowRateConfirm] = useState(false);

  useEffect(() => { api.get('/equipment-categories', { params: { page_size:200 } }).then(r => setCategories(r.data?.items||r.data||[])).catch(()=>{}); }, []);

  const f = (k: string, v: string|boolean) => { if (k==='hourly_rate') setRateChanged(true); setForm(p=>({...p,[k]:v})); };

  const onCat = (cid: string) => {
    const cat = categories.find(c=>String(c.id)===cid);
    if (cat?.default_hourly_rate && !form.hourly_rate) {
      setForm(p=>({...p,category_id:cid,hourly_rate:String(cat.default_hourly_rate)}));
      setCatDefaultRate(cat.default_hourly_rate);
    } else { f('category_id',cid); setCatDefaultRate(cat?.default_hourly_rate||null); }
  };

  const createCat = async () => {
    if (!newCatName.trim()) return;
    try {
      const res = await api.post('/equipment-categories', { name:newCatName.trim() });
      setCategories(p=>[...p, res.data]);
      setForm(p=>({...p,category_id:String(res.data.id)}));
      setNewCatName(''); setShowNewCat(false);
    } catch { setError('שגיאה ביצירת קבוצה'); }
  };

  const save = async () => {
    if (!form.category_id) { setError('יש לבחור קבוצה'); return; }
    if (!form.name.trim()) { setError('שם סוג ציוד חובה'); return; }
    if (!form.hourly_rate) { setError('תעריף שעתי חובה'); return; }
    if (rateChanged && catDefaultRate && Number(form.hourly_rate)!==catDefaultRate && !showRateConfirm) { setShowRateConfirm(true); return; }
    setSaving(true); setError('');
    try {
      const code = form.name.trim().replace(/[^א-תa-zA-Z0-9]/g,'_').slice(0,30)+'_'+Date.now().toString().slice(-4);
      await api.post('/equipment-types', {
        code, name:form.name.trim(), category_id:Number(form.category_id), category_group:form.category_group||undefined,
        hourly_rate:Number(form.hourly_rate), overnight_rate:form.overnight_rate?Number(form.overnight_rate):undefined,
        night_guard:form.night_guard, description:form.notes||undefined, is_active:true,
      });
      onSaved(); onClose();
    } catch (e:any) { setError(e?.response?.data?.detail||'שגיאה בשמירה'); }
    setSaving(false);
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl w-full max-w-lg overflow-hidden border border-gray-200 shadow-lg" onClick={e=>e.stopPropagation()}>
        {/* Header */}
        <div className="bg-kkl-green px-6 py-4 flex items-start justify-between">
          <div>
            <div className="text-white font-bold text-base">סוג ציוד חדש</div>
            <div className="text-white/75 text-xs mt-0.5">יתווסף לקטלוג ויהיה זמין לשיוך לספקים</div>
          </div>
          <button onClick={onClose} className="bg-white/15 text-white rounded-lg w-7 h-7 flex items-center justify-center hover:bg-white/25 border-none cursor-pointer">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 flex flex-col gap-4">
          {error && <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-xl px-3 py-2">{error}</div>}

          {showRateConfirm && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-xs text-amber-700">
<div className="font-medium mb-2">התעריף שונה מברירת המחדל של הקבוצה ({catDefaultRate}). להמשיך?</div>
              <div className="flex gap-2">
                <button onClick={()=>{setShowRateConfirm(false);save();}} className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-kkl-green text-white hover:bg-kkl-green-dark border-none cursor-pointer">כן, שמור</button>
                <button onClick={()=>setShowRateConfirm(false)} className="px-3 py-1.5 rounded-lg border border-gray-300 text-gray-600 text-xs font-semibold hover:bg-gray-50 cursor-pointer">לא</button>
              </div>
            </div>
          )}

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-semibold text-gray-600">קבוצה <span className="text-red-500">*</span></label>
              <button onClick={()=>setShowNewCat(!showNewCat)} className="flex items-center gap-0.5 text-xs text-kkl-green hover:underline border-none bg-transparent cursor-pointer">
                <Plus className="w-3 h-3" /> קבוצה חדשה
              </button>
            </div>
            {showNewCat && (
              <div className="flex gap-2 mb-2">
                <input value={newCatName} onChange={e=>setNewCatName(e.target.value)} placeholder="שם הקבוצה החדשה"
                  className="flex-1 px-3 py-2 rounded-xl border border-kkl-green text-sm focus:outline-none" />
                <button onClick={createCat} className="px-3 py-2 bg-kkl-green text-white rounded-xl text-sm font-semibold hover:bg-kkl-green-dark border-none cursor-pointer">צור</button>
              </div>
            )}
            <select value={form.category_id} onChange={e=>onCat(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-700 bg-white focus:outline-none focus:border-kkl-green cursor-pointer">
              <option value="">— בחר קבוצה תחילה —</option>
              {categories.map(c=><option key={c.id} value={String(c.id)}>{c.name}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">שם סוג ציוד <span className="text-red-500">*</span></label>
            <input value={form.name} onChange={e=>f('name',e.target.value)} placeholder="בחר קבוצה תחילה" disabled={!form.category_id}
              className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-kkl-green disabled:bg-gray-50 disabled:text-gray-400" />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">קבוצת ציוד</label>
            <select value={form.category_group} onChange={e=>f('category_group',e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-700 bg-white focus:outline-none focus:border-kkl-green cursor-pointer">
              <option value="">בחר קבוצה (אופציונלי)</option>
              {GROUPS.map(g=><option key={g} value={g}>{g}</option>)}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
<label className="block text-xs font-semibold text-gray-600 mb-1">תעריף שעתי () <span className="text-red-500">*</span></label>
              <input type="number" value={form.hourly_rate} onChange={e=>f('hourly_rate',e.target.value)} placeholder="—"
                className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-kkl-green" />
            </div>
            <div>
<label className="block text-xs font-semibold text-gray-600 mb-1">תעריף לינה ()</label>
              <input type="number" value={form.overnight_rate} onChange={e=>f('overnight_rate',e.target.value)} placeholder="—"
                className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-kkl-green" />
            </div>
          </div>

          <label className="flex items-center gap-3 cursor-pointer select-none">
            <input type="checkbox" checked={form.night_guard} onChange={e=>f('night_guard',e.target.checked)} className="w-4 h-4 rounded text-kkl-green focus:ring-kkl-green" />
            <Moon className="w-4 h-4 text-blue-500" />
            <span className="text-sm font-medium text-gray-700">ל תומר שמירת לילה</span>
          </label>

          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">הערות</label>
            <textarea value={form.notes} onChange={e=>f('notes',e.target.value)} rows={2} placeholder="בחר קבוצה תחילה"
              className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm placeholder-gray-400 resize-none focus:outline-none focus:border-kkl-green" />
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 bg-gray-50 border-t border-gray-100">
          <button onClick={onClose} className="px-4 py-2 rounded-xl border border-gray-200 text-sm font-medium text-gray-500 hover:bg-gray-50 transition-colors">ביטול</button>
          <button onClick={save} disabled={saving||!form.category_id||!form.name.trim()} className="px-5 py-2 rounded-xl bg-kkl-green text-white text-sm font-semibold hover:bg-kkl-green-dark transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
{saving ? 'שומר...' : 'שמור סוג ציוד '}
          </button>
        </div>
      </div>
    </div>
  );
};
export default EquipmentTypeModal;
