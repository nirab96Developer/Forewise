// src/components/suppliers/EquipmentModal.tsx 
import React, { useState, useEffect } from 'react';
import { X, Moon } from 'lucide-react';
import api from '../../services/api';

interface Supplier { id: number; name: string; area_name?: string; region_name?: string; contact_name?: string; }
interface EqType { id: number; name: string; hourly_rate?: number; overnight_rate?: number; category_group?: string; }
interface Props { onClose: () => void; onSaved: () => void; }

const EquipmentModal: React.FC<Props> = ({ onClose, onSaved }) => {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [eqTypes, setEqTypes] = useState<EqType[]>([]);
  const [form, setForm] = useState({ supplier_id:'', equipment_type_id:'', license_plate:'', hourly_rate:'', overnight_rate:'', night_guard:false });
  const [selSupplier, setSelSupplier] = useState<Supplier|null>(null);
  const [selType, setSelType] = useState<EqType|null>(null);

  useEffect(() => {
    Promise.all([
      api.get('/suppliers', { params: { page_size:500, is_active:true } }),
      api.get('/equipment-types', { params: { page_size:200, is_active:true } }),
    ]).then(([sR,tR]) => {
      setSuppliers(sR.data?.items||sR.data||[]);
      setEqTypes(tR.data?.items||tR.data||[]);
    }).catch(()=>{});
  }, []);

  const f = (k: string, v: string|boolean) => setForm(p=>({...p,[k]:v}));

  const onSup = (sid: string) => { f('supplier_id',sid); setSelSupplier(suppliers.find(s=>String(s.id)===sid)||null); };
  const onType = (tid: string) => {
    f('equipment_type_id',tid);
    const t = eqTypes.find(x=>String(x.id)===tid)||null;
    setSelType(t);
    if (t?.hourly_rate && !form.hourly_rate) setForm(p=>({...p,equipment_type_id:tid,hourly_rate:String(t.hourly_rate)}));
    if (t?.overnight_rate && !form.overnight_rate) setForm(p=>({...p,overnight_rate:String(t.overnight_rate)}));
  };

  const save = async () => {
    if (!form.supplier_id) { setError('יש לבחור ספק'); return; }
    if (!form.equipment_type_id) { setError('יש לבחור סוג ציוד'); return; }
    if (!form.license_plate.trim()) { setError('מספר רישוי חובה'); return; }
    setSaving(true); setError('');
    try {
      const eqType = eqTypes.find(t=>String(t.id)===form.equipment_type_id);
      await api.post('/equipment', {
        supplier_id:Number(form.supplier_id), type_id:Number(form.equipment_type_id),
        equipment_type:eqType?.name||'', name:`${eqType?.name||'כלי'} — ${form.license_plate}`,
        license_plate:form.license_plate.trim(),
        hourly_rate:form.hourly_rate?Number(form.hourly_rate):undefined,
        overnight_rate:form.overnight_rate?Number(form.overnight_rate):undefined,
        night_guard:form.night_guard, is_active:true, status:'available',
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
            <div className="text-white font-bold text-base">הוספת כלי לספק</div>
            <div className="text-white/75 text-xs mt-0.5">הכלי יצורף לסבב אוטומטית לפי אזורי השירות של הספק</div>
          </div>
          <button onClick={onClose} className="bg-white/15 text-white rounded-lg w-7 h-7 flex items-center justify-center hover:bg-white/25 border-none cursor-pointer">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 flex flex-col gap-4">
          {error && <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-xl px-3 py-2">{error}</div>}

          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">בחר ספק <span className="text-red-500">*</span></label>
            <select value={form.supplier_id} onChange={e=>onSup(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-700 bg-white focus:outline-none focus:border-kkl-green cursor-pointer">
              <option value="">— בחר ספק —</option>
              {suppliers.map(s=><option key={s.id} value={String(s.id)}>{s.name}</option>)}
            </select>
            {selSupplier && (
              <div className="flex items-center gap-3 bg-gray-50 rounded-xl border border-gray-200 px-3 py-2.5 mt-2">
                <div className="w-8 h-8 rounded-full bg-green-100 text-kkl-green text-xs font-bold flex items-center justify-center flex-shrink-0">{selSupplier.name[0]}</div>
                <div>
                  <div className="text-sm font-semibold text-gray-800">{selSupplier.name}</div>
                  <div className="text-xs text-gray-500">{[selSupplier.region_name,selSupplier.area_name,selSupplier.contact_name].filter(Boolean).join(' · ')}</div>
                </div>
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">סוג ציוד <span className="text-red-500">*</span></label>
              <select value={form.equipment_type_id} onChange={e=>onType(e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-700 bg-white focus:outline-none focus:border-kkl-green cursor-pointer">
                <option value="">— בחר סוג —</option>
                {eqTypes.map(t=><option key={t.id} value={String(t.id)}>{t.name}</option>)}
              </select>
{selType?.hourly_rate && <div className="text-xs text-kkl-green mt-1 font-medium">ברירת מחדל: {selType.hourly_rate}/שעה</div>}
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">מספר רישוי <span className="text-red-500">*</span></label>
              <input value={form.license_plate} onChange={e=>f('license_plate',e.target.value)} placeholder="12-345-67"
                className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm font-mono text-gray-800 placeholder-gray-400 focus:outline-none focus:border-kkl-green focus:ring-1 focus:ring-kkl-green" />
              <div className="text-[10px] text-gray-400 mt-1">משמש לאימות כלי בשטח</div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
<label className="block text-xs font-semibold text-gray-600 mb-1">תעריף שעתי ()</label>
              <input type="number" value={form.hourly_rate} onChange={e=>f('hourly_rate',e.target.value)} placeholder="מהקטלוג"
                className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-kkl-green" />
            </div>
            <div>
<label className="block text-xs font-semibold text-gray-600 mb-1">תעריף לינה ()</label>
              <input type="number" value={form.overnight_rate} onChange={e=>f('overnight_rate',e.target.value)} placeholder="מהקטלוג"
                className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-kkl-green" />
            </div>
          </div>
          <div className="text-xs text-gray-400">ריק = ברירת מחדל מהקטלוג</div>

          {form.supplier_id && (<>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-2">אזורי שירות — סבב הוגן <span className="text-red-500">*</span></label>
              <div className="text-xs text-gray-400 bg-gray-50 border border-gray-200 rounded-xl px-3 py-2">בחר ספק כדי לראות אזורים — ירשש מאזורי הספק אפשר לשנות</div>
            </div>
          </>)}

          <label className="flex items-center gap-3 cursor-pointer select-none">
            <input type="checkbox" checked={form.night_guard} onChange={e=>f('night_guard',e.target.checked)} className="w-4 h-4 rounded text-kkl-green focus:ring-kkl-green" />
            <Moon className="w-4 h-4 text-blue-500" />
            <span className="text-sm font-medium text-gray-700">ל תומר שמירת לילה</span>
          </label>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 bg-gray-50 border-t border-gray-100">
          <button onClick={onClose} className="px-4 py-2 rounded-xl border border-gray-200 text-sm font-medium text-gray-500 hover:bg-gray-50 transition-colors">ביטול</button>
          <button onClick={save} disabled={saving} className="px-5 py-2 rounded-xl bg-kkl-green text-white text-sm font-semibold hover:bg-kkl-green-dark transition-colors disabled:opacity-50">
{saving ? 'שומר...' : 'שמור כלי '}
          </button>
        </div>
      </div>
    </div>
  );
};
export default EquipmentModal;
