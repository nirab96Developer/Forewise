// src/components/suppliers/EquipmentModal.tsx
import React, { useState, useEffect } from 'react';
import { X, Check, Moon } from 'lucide-react';
import api from '../../services/api';

interface Supplier { id: number; name: string; area_name?: string; region_name?: string; contact_name?: string; }
interface EqType { id: number; name: string; hourly_rate?: number; overnight_rate?: number; }
interface Props { onClose: () => void; onSaved: () => void; }

const EquipmentModal: React.FC<Props> = ({ onClose, onSaved }) => {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [eqTypes, setEqTypes] = useState<EqType[]>([]);
  const [form, setForm] = useState({
    supplier_id: '', equipment_type_id: '', license_plate: '',
    hourly_rate: '', overnight_rate: '', night_guard: false,
  });
  const [selectedSupplier, setSelectedSupplier] = useState<Supplier | null>(null);
  const [selectedType, setSelectedType] = useState<EqType | null>(null);

  useEffect(() => {
    Promise.all([
      api.get('/suppliers', { params: { page_size: 500, is_active: true } }),
      api.get('/equipment-types', { params: { page_size: 200, is_active: true } }),
    ]).then(([sRes, tRes]) => {
      setSuppliers(sRes.data?.items || sRes.data || []);
      setEqTypes(tRes.data?.items || tRes.data || []);
    }).catch(() => {});
  }, []);

  const f = (k: string, v: string | boolean) => setForm(p => ({ ...p, [k]: v }));

  const onSupplierChange = (sid: string) => {
    f('supplier_id', sid);
    setSelectedSupplier(suppliers.find(s => String(s.id) === sid) || null);
  };
  const onTypeChange = (tid: string) => {
    f('equipment_type_id', tid);
    const t = eqTypes.find(x => String(x.id) === tid) || null;
    setSelectedType(t);
    if (t?.hourly_rate && !form.hourly_rate) f('hourly_rate', String(t.hourly_rate));
    if (t?.overnight_rate && !form.overnight_rate) f('overnight_rate', String(t.overnight_rate));
  };

  const save = async () => {
    if (!form.supplier_id) { setError('יש לבחור ספק'); return; }
    if (!form.equipment_type_id) { setError('יש לבחור סוג ציוד'); return; }
    if (!form.license_plate.trim()) { setError('מספר רישוי חובה'); return; }
    setSaving(true); setError('');
    try {
      const eqType = eqTypes.find(t => String(t.id) === form.equipment_type_id);
      await api.post('/equipment', {
        supplier_id: Number(form.supplier_id),
        type_id: Number(form.equipment_type_id),
        equipment_type: eqType?.name || '',
        name: `${eqType?.name || 'כלי'} — ${form.license_plate}`,
        license_plate: form.license_plate.trim(),
        hourly_rate: form.hourly_rate ? Number(form.hourly_rate) : undefined,
        overnight_rate: form.overnight_rate ? Number(form.overnight_rate) : undefined,
        night_guard: form.night_guard,
        is_active: true, status: 'available',
      });
      onSaved(); onClose();
    } catch (e: any) { setError(e?.response?.data?.detail || 'שגיאה בשמירה'); }
    setSaving(false);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-5 border-b">
          <h2 className="text-lg font-bold text-gray-900">הוספת כלי לספק</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded-lg"><X className="w-5 h-5 text-gray-400" /></button>
        </div>
        <div className="p-5 space-y-4">
          {error && <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{error}</p>}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">ספק *</label>
            <select value={form.supplier_id} onChange={e => onSupplierChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500">
              <option value="">בחר ספק</option>
              {suppliers.map(s => <option key={s.id} value={String(s.id)}>{s.name}</option>)}
            </select>
            {selectedSupplier && (
              <p className="text-xs text-gray-500 mt-1">
                {selectedSupplier.region_name && <>{selectedSupplier.region_name} · </>}
                {selectedSupplier.area_name && <>{selectedSupplier.area_name} · </>}
                {selectedSupplier.contact_name}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">סוג ציוד *</label>
            <select value={form.equipment_type_id} onChange={e => onTypeChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500">
              <option value="">בחר סוג ציוד</option>
              {eqTypes.map(t => <option key={t.id} value={String(t.id)}>{t.name}</option>)}
            </select>
            {selectedType?.hourly_rate && (
              <p className="text-xs text-green-600 mt-1">תעריף ברירת מחדל: ₪{selectedType.hourly_rate}/שעה</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">מספר רישוי *</label>
            <input value={form.license_plate} onChange={e => f('license_plate', e.target.value)}
              placeholder="00-000-00"
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm font-mono focus:ring-2 focus:ring-green-500" />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">תעריף שעתי (₪)</label>
              <input type="number" value={form.hourly_rate} onChange={e => f('hourly_rate', e.target.value)}
                placeholder={selectedType?.hourly_rate ? String(selectedType.hourly_rate) : 'מקטלוג'}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">תעריף לינה (₪)</label>
              <input type="number" value={form.overnight_rate} onChange={e => f('overnight_rate', e.target.value)}
                placeholder={selectedType?.overnight_rate ? String(selectedType.overnight_rate) : 'אופציונלי'}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500" />
            </div>
          </div>

          <label className="flex items-center gap-3 cursor-pointer select-none">
            <input type="checkbox" checked={form.night_guard} onChange={e => f('night_guard', e.target.checked)}
              className="w-4 h-4 rounded text-green-600 focus:ring-green-500" />
            <Moon className="w-4 h-4 text-indigo-500" />
            <span className="text-sm font-medium text-gray-700">שמירת לילה — הכלי מתאים לעבודות לילה</span>
          </label>

          {form.supplier_id && form.equipment_type_id && form.license_plate && (
            <div className="bg-green-50 border border-green-200 rounded-lg px-4 py-3 text-sm text-green-800">
              ✅ הכלי יצורף לסבב הוגן לפי אזורי השירות של הספק
            </div>
          )}
        </div>
        <div className="flex justify-end gap-3 px-5 pb-5">
          <button onClick={onClose} className="px-4 py-2 border border-gray-200 text-gray-600 rounded-lg text-sm hover:bg-gray-50">ביטול</button>
          <button onClick={save} disabled={saving}
            className="flex items-center gap-1.5 px-5 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 disabled:opacity-50">
            {saving ? 'שומר...' : <><Check className="w-4 h-4" /> הוסף כלי</>}
          </button>
        </div>
      </div>
    </div>
  );
};

export default EquipmentModal;
