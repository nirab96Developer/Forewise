// src/components/suppliers/SupplierModal.tsx
import React, { useState, useEffect } from 'react';
import { X, ChevronRight, ChevronLeft, Check, Truck } from 'lucide-react';
import api from '../../services/api';

interface Region { id: number; name: string; }
interface Area { id: number; name: string; region_id: number; }
interface Props { onClose: () => void; onSaved: () => void; }

const SupplierModal: React.FC<Props> = ({ onClose, onSaved }) => {
  const [step, setStep] = useState(1);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [regions, setRegions] = useState<Region[]>([]);
  const [areas, setAreas] = useState<Area[]>([]);
  const [selectedAreas, setSelectedAreas] = useState<number[]>([]);
  const [form, setForm] = useState({ name:'', tax_id:'', address:'', contact_name:'', phone:'', email:'', region_id:'' });

  useEffect(() => { api.get('/regions').then(r => setRegions(r.data?.items || r.data || [])).catch(() => {}); }, []);
  useEffect(() => {
    if (form.region_id) {
      api.get('/areas', { params: { region_id: form.region_id } }).then(r => setAreas(r.data?.items || r.data || [])).catch(() => {});
      setSelectedAreas([]);
    }
  }, [form.region_id]);

  const f = (k: string, v: string) => setForm(p => ({ ...p, [k]: v }));
  const toggleArea = (id: number) => setSelectedAreas(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);

  const next = () => {
    if (step === 1 && !form.name.trim()) { setError('שם ספק חובה'); return; }
    if (step === 2 && !form.phone.trim()) { setError('טלפון חובה'); return; }
    setError(''); setStep(s => s + 1);
  };

  const save = async () => {
    setSaving(true); setError('');
    try {
      // Auto-generate code from name (slug)
      const autoCode = form.name.trim().replace(/\s+/g, '-').replace(/[^a-zA-Z0-9\u0590-\u05FF-]/g, '').slice(0, 20) + '-' + Date.now().toString().slice(-4);
      const res = await api.post('/suppliers', {
        code: autoCode,
        name: form.name,
        tax_id: form.tax_id || undefined,
        address: form.address || undefined,
        contact_name: form.contact_name || undefined,
        phone: form.phone || undefined,
        email: form.email || undefined,
        region_id: form.region_id ? Number(form.region_id) : undefined,
        active_area_ids: selectedAreas,
      });
      const sid = res.data?.id;
      if (sid && selectedAreas.length > 0) {
        await Promise.allSettled(selectedAreas.map(areaId => api.post('/supplier-rotations', {
          supplier_id: sid, area_id: areaId, region_id: form.region_id ? Number(form.region_id) : undefined,
          rotation_position: 99, is_active: true, is_available: true,
        })));
      }
      onSaved(); onClose();
    } catch (e: any) { setError(e?.response?.data?.detail || 'שגיאה בשמירה'); }
    setSaving(false);
  };

  const steps = ['פרטי חברה', 'איש קשר', 'אזורי שירות'];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-5 border-b">
          <div className="flex items-center gap-2"><Truck className="w-5 h-5 text-green-600" /><h2 className="text-lg font-bold">ספק חדש</h2></div>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded-lg"><X className="w-5 h-5 text-gray-400" /></button>
        </div>
        <div className="flex px-5 pt-4 gap-2">
          {steps.map((s, i) => (
            <div key={i} className="flex-1 text-center">
              <div className={`w-7 h-7 rounded-full flex items-center justify-center mx-auto text-xs font-bold mb-1 ${step > i+1 ? 'bg-green-500 text-white' : step === i+1 ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-400'}`}>
                {step > i+1 ? <Check className="w-4 h-4" /> : i+1}
              </div>
              <span className={`text-[10px] ${step === i+1 ? 'text-green-700 font-medium' : 'text-gray-400'}`}>{s}</span>
            </div>
          ))}
        </div>
        <div className="p-5 space-y-4">
          {error && <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{error}</p>}
          {step === 1 && (<>
            <div><label className="block text-sm font-medium text-gray-700 mb-1">שם הספק *</label>
              <input value={form.name} onChange={e => f('name', e.target.value)} placeholder="שם החברה" className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500" /></div>
            <div><label className="block text-sm font-medium text-gray-700 mb-1">מספר ח.פ</label>
              <input value={form.tax_id} onChange={e => f('tax_id', e.target.value)} placeholder="000000000" className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500" /></div>
            <div><label className="block text-sm font-medium text-gray-700 mb-1">כתובת</label>
              <input value={form.address} onChange={e => f('address', e.target.value)} placeholder="רחוב ומספר, עיר" className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500" /></div>
          </>)}
          {step === 2 && (<>
            <div><label className="block text-sm font-medium text-gray-700 mb-1">שם איש קשר</label>
              <input value={form.contact_name} onChange={e => f('contact_name', e.target.value)} placeholder="שם מלא" className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500" /></div>
            <div><label className="block text-sm font-medium text-gray-700 mb-1">טלפון *</label>
              <input value={form.phone} onChange={e => f('phone', e.target.value)} placeholder="05X-XXXXXXX" type="tel" className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500" /></div>
            <div><label className="block text-sm font-medium text-gray-700 mb-1">דוא"ל</label>
              <input value={form.email} onChange={e => f('email', e.target.value)} placeholder="supplier@example.com" type="email" className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500" /></div>
          </>)}
          {step === 3 && (<>
            <div><label className="block text-sm font-medium text-gray-700 mb-1">מרחב</label>
              <select value={form.region_id} onChange={e => f('region_id', e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500">
                <option value="">בחר מרחב</option>
                {regions.map(r => <option key={r.id} value={String(r.id)}>{r.name}</option>)}
              </select></div>
            {areas.length > 0 && <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">אזורי שירות</label>
              <div className="flex flex-wrap gap-2">
                {areas.map(a => (
                  <button key={a.id} onClick={() => toggleArea(a.id)}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${selectedAreas.includes(a.id) ? 'bg-green-600 text-white border-green-600' : 'bg-white text-gray-600 border-gray-200 hover:border-green-400'}`}>
                    {a.name}
                  </button>
                ))}
              </div></div>}
            {selectedAreas.length > 0 && <div className="bg-green-50 border border-green-200 rounded-lg px-4 py-3 text-sm text-green-800">
              ✅ הספק ייכנס לסבב הוגן ב-<strong>{selectedAreas.length} אזורים</strong>
            </div>}
          </>)}
        </div>
        <div className="flex justify-between items-center px-5 pb-5">
          <button onClick={() => step > 1 ? setStep(s => s-1) : onClose()} className="flex items-center gap-1.5 px-4 py-2 border border-gray-200 text-gray-600 rounded-lg text-sm hover:bg-gray-50">
            <ChevronRight className="w-4 h-4" />{step > 1 ? 'חזרה' : 'ביטול'}
          </button>
          {step < 3
            ? <button onClick={next} className="flex items-center gap-1.5 px-5 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700">המשך <ChevronLeft className="w-4 h-4" /></button>
            : <button onClick={save} disabled={saving} className="flex items-center gap-1.5 px-5 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 disabled:opacity-50">
                {saving ? 'שומר...' : <><Check className="w-4 h-4" /> צור ספק</>}
              </button>}
        </div>
      </div>
    </div>
  );
};

export default SupplierModal;
