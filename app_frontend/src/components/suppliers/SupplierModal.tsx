// src/components/suppliers/SupplierModal.tsx 
import React, { useState, useEffect } from 'react';
import { X, ChevronLeft } from 'lucide-react';
import api from '../../services/api';

interface Region { id: number; name: string; }
interface Area { id: number; name: string; region_id: number; }
interface Props { onClose: () => void; onSaved: () => void; }

const STEPS = ['פרטי חברה', 'איש קשר', 'אזורי שירות'];

const SupplierModal: React.FC<Props> = ({ onClose, onSaved }) => {
  const [step, setStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [regions, setRegions] = useState<Region[]>([]);
  const [areas, setAreas] = useState<Area[]>([]);
  const [selectedAreas, setSelectedAreas] = useState<number[]>([]);
  const [form, setForm] = useState({ name:'', tax_id:'', address:'', notes:'', contact_name:'', phone:'', email:'', region_id:'' });

  useEffect(() => { api.get('/regions').then(r => setRegions(r.data?.items || r.data || [])).catch(()=>{}); }, []);
  useEffect(() => {
    if (form.region_id) {
      api.get('/areas', { params: { region_id: form.region_id } }).then(r => setAreas(r.data?.items || r.data || [])).catch(()=>{});
      setSelectedAreas([]);
    }
  }, [form.region_id]);

  const f = (k: string, v: string) => setForm(p => ({ ...p, [k]: v }));
  const toggleArea = (id: number) => setSelectedAreas(p => p.includes(id) ? p.filter(x => x!==id) : [...p, id]);

  const next = () => {
    if (step===0 && !form.name.trim()) { setError('שם ספק חובה'); return; }
    if (step===1 && !form.phone.trim()) { setError('טלפון חובה'); return; }
    setError(''); setStep(s => s+1);
  };

  const save = async () => {
    setSaving(true); setError('');
    try {
      const code = form.name.trim().replace(/\s+/g,'-').replace(/[^א-תa-zA-Z0-9-]/g,'').slice(0,20)+'-'+Date.now().toString().slice(-4);
      const res = await api.post('/suppliers', { code, name:form.name, tax_id:form.tax_id||undefined, address:form.address||undefined, contact_name:form.contact_name||undefined, phone:form.phone||undefined, email:form.email||undefined, region_id:form.region_id?Number(form.region_id):undefined, active_area_ids:selectedAreas });
      const sid = res.data?.id;
      if (sid && selectedAreas.length>0) {
        await Promise.allSettled(selectedAreas.map(aId => api.post('/supplier-rotations', { supplier_id:sid, area_id:aId, region_id:form.region_id?Number(form.region_id):undefined, rotation_position:99, is_active:true, is_available:true })));
      }
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
            <div className="text-white font-bold text-base">הוספת ספק חדש</div>
            <div className="text-white/75 text-xs mt-0.5">ספק חדש יצורף לסבב אוטומטית לפי אזורי השירות</div>
          </div>
          <button onClick={onClose} className="bg-white/15 text-white rounded-lg w-7 h-7 flex items-center justify-center hover:bg-white/25 border-none cursor-pointer text-sm">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Steps bar */}
        <div className="flex bg-gray-50 border-b border-gray-200">
          {STEPS.map((s, i) => (
            <button key={i} onClick={() => i<step && setStep(i)}
              className={`flex-1 py-2.5 text-xs font-medium text-center border-none bg-transparent cursor-pointer border-b-2 transition-colors ${i===step ? 'font-semibold text-kkl-green border-kkl-green' : i<step ? 'text-gray-500 border-transparent hover:text-gray-700' : 'text-gray-400 border-transparent cursor-default'}`}>
              {i+1} — {s}
            </button>
          ))}
        </div>

        {/* Body */}
        <div className="px-6 py-5 flex flex-col gap-4">
          {error && <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-xl px-3 py-2">{error}</div>}

          {step===0 && (<>
            <div><label className="block text-xs font-semibold text-gray-600 mb-1">שם חברה / ספק <span className="text-red-500">*</span></label>
              <input value={form.name} onChange={e=>f('name',e.target.value)} placeholder="שם מלא"
                className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-kkl-green focus:ring-1 focus:ring-kkl-green" /></div>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="block text-xs font-semibold text-gray-600 mb-1">ח.פ / עוסק מורשה <span className="text-red-500">*</span></label>
                <input value={form.tax_id} onChange={e=>f('tax_id',e.target.value)} placeholder="514123456"
                  className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-kkl-green focus:ring-1 focus:ring-kkl-green" /></div>
              <div><label className="block text-xs font-semibold text-gray-600 mb-1">כתובת</label>
                <input value={form.address} onChange={e=>f('address',e.target.value)} placeholder="רחוב, עיר"
                  className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-kkl-green focus:ring-1 focus:ring-kkl-green" /></div>
            </div>
            <div><label className="block text-xs font-semibold text-gray-600 mb-1">הערות</label>
              <textarea value={form.notes} onChange={e=>f('notes',e.target.value)} rows={2} placeholder="הערות (אופציונלי)"
                className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm placeholder-gray-400 resize-none focus:outline-none focus:border-kkl-green" /></div>
          </>)}

          {step===1 && (<>
            <div><label className="block text-xs font-semibold text-gray-600 mb-1">שם איש קשר</label>
              <input value={form.contact_name} onChange={e=>f('contact_name',e.target.value)} placeholder="שם מלא"
                className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-kkl-green focus:ring-1 focus:ring-kkl-green" /></div>
            <div><label className="block text-xs font-semibold text-gray-600 mb-1">טלפון <span className="text-red-500">*</span></label>
              <input value={form.phone} onChange={e=>f('phone',e.target.value)} placeholder="05X-XXXXXXX" type="tel"
                className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-kkl-green focus:ring-1 focus:ring-kkl-green" /></div>
            <div><label className="block text-xs font-semibold text-gray-600 mb-1">דוא"ל</label>
              <input value={form.email} onChange={e=>f('email',e.target.value)} placeholder="supplier@example.com" type="email"
                className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-kkl-green focus:ring-1 focus:ring-kkl-green" /></div>
          </>)}

          {step===2 && (<>
            <div><label className="block text-xs font-semibold text-gray-600 mb-1">מרחב</label>
              <select value={form.region_id} onChange={e=>f('region_id',e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-700 bg-white focus:outline-none focus:border-kkl-green cursor-pointer">
                <option value="">בחר מרחב</option>
                {regions.map(r=><option key={r.id} value={String(r.id)}>{r.name}</option>)}
              </select></div>
            {areas.length>0 && <div>
              <label className="block text-xs font-semibold text-gray-600 mb-2">אזורי שירות — סבב הוגן</label>
              <div className="flex flex-wrap gap-2">
                {areas.map(a=>(
                  <button key={a.id} onClick={()=>toggleArea(a.id)}
                    className={`px-3 py-1.5 rounded-full border text-xs font-medium cursor-pointer transition-colors ${selectedAreas.includes(a.id) ? 'border-kkl-green bg-green-50 font-semibold text-kkl-green' : 'border-gray-200 text-gray-500 hover:bg-gray-50'}`}>
                    {a.name}
                  </button>
                ))}
              </div></div>}
            {selectedAreas.length>0 && (
              <div className="bg-green-50 border border-green-200 rounded-xl px-4 py-3 text-xs font-medium text-green-700">
                ✅ הספק ייכנס לסבב הוגן ב-{selectedAreas.length} אזורים אוטומטית
              </div>
            )}
          </>)}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 bg-gray-50 border-t border-gray-100">
          <button onClick={() => step>0 ? setStep(s=>s-1) : onClose()}
            className="px-4 py-2 rounded-xl border border-gray-200 text-sm font-medium text-gray-500 hover:bg-gray-50 transition-colors">
            {step>0 ? 'חזור' : 'ביטול'}
          </button>
          {step<2
            ? <button onClick={next} className="flex items-center gap-1.5 px-5 py-2 rounded-xl bg-kkl-green text-white text-sm font-semibold hover:bg-kkl-green-dark transition-colors">
                המשך <ChevronLeft className="w-4 h-4" />
              </button>
            : <button onClick={save} disabled={saving} className="px-5 py-2 rounded-xl bg-kkl-green text-white text-sm font-semibold hover:bg-kkl-green-dark transition-colors disabled:opacity-50">
                {saving ? 'שומר...' : 'צור ספק'}
              </button>}
        </div>
      </div>
    </div>
  );
};
export default SupplierModal;
