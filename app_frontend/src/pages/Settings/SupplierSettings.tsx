// src/pages/Settings/SupplierSettings.tsx
// ניהול ספקים וציוד — 4 טאבים מאוחדים (rebuilt)
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowRight, Truck, Wrench, DollarSign, RotateCcw,
  Search, Plus, Eye, EyeOff, ChevronDown, ChevronRight,
  MapPin, Phone, Mail, AlertCircle, Moon, Edit2, Check, X, RefreshCw
} from 'lucide-react';
import api from '../../services/api';
import SupplierModal from '../../components/suppliers/SupplierModal';
import EquipmentModal from '../../components/suppliers/EquipmentModal';
import EquipmentTypeModal from '../../components/suppliers/EquipmentTypeModal';

interface Supplier {
  id: number; code?: string; name: string; tax_id?: string;
  contact_name?: string; phone?: string; email?: string; address?: string;
  region_id?: number; area_id?: number; region_name?: string; area_name?: string;
  is_active: boolean; equipment_count?: number; total_assignments?: number;
  active_area_ids?: number[];
}
interface Equipment {
  id: number; name: string; license_plate: string;
  equipment_type?: string; supplier_id: number; supplier_name?: string;
  hourly_rate?: number; overnight_rate?: number; night_guard?: boolean;
  is_active: boolean;
}
interface EqType {
  id: number; name: string; category_group?: string; category_id?: number;
  hourly_rate?: number; overnight_rate?: number; night_guard?: boolean;
  is_active: boolean; updated_at?: string;
}
interface Rotation {
  id: number; supplier_id: number; supplier_name?: string;
  area_id?: number; area_name?: string; region_name?: string;
  category_name?: string; equipment_category_id?: number;
  rotation_position: number; total_assignments: number;
  rejection_count: number; avg_response_time_hours?: number;
  is_active: boolean; is_available: boolean;
}
interface Region { id: number; name: string; }
interface Area { id: number; name: string; region_id: number; }
type TabType = 'suppliers' | 'equipment' | 'pricing' | 'rotation';

const GROUP_COLORS: Record<string, string> = {
  'כלים כבדים': 'bg-green-100 text-green-800',
  'כלים קלים':  'bg-blue-100 text-blue-800',
  'ציוד':        'bg-purple-100 text-purple-800',
  'שמירה':       'bg-orange-100 text-orange-800',
};
const gc = (g?: string) => GROUP_COLORS[g || ''] || 'bg-gray-100 text-gray-600';

// ─── Shared data ──────────────────────────────────────────────────────────────
function useAllData() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [equipment, setEquipment] = useState<Equipment[]>([]);
  const [eqTypes, setEqTypes]     = useState<EqType[]>([]);
  const [rotations, setRotations] = useState<Rotation[]>([]);
  const [regions, setRegions]     = useState<Region[]>([]);
  const [areas, setAreas]         = useState<Area[]>([]);
  const [loading, setLoading]     = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [sR, eR, tR, rR, regR, aR] = await Promise.all([
        api.get('/suppliers',          { params: { page_size: 500 } }),
        api.get('/equipment',          { params: { page_size: 500 } }),
        api.get('/equipment-types',    { params: { page_size: 50 } }),
        api.get('/supplier-rotations', { params: { page_size: 500 } }),
        api.get('/regions').catch(() => ({ data: [] })),
        api.get('/areas').catch(() => ({ data: [] })),
      ]);
      setSuppliers(sR.data?.items || sR.data || []);
      setEquipment(eR.data?.items || []);
      setEqTypes(tR.data?.items || []);
      const rots = rR.data?.items || rR.data || [];
      setRotations(Array.isArray(rots) ? rots : []);
      setRegions(regR.data?.items || regR.data || []);
      setAreas(aR.data?.items || aR.data || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);
  return { suppliers, setSuppliers, equipment, setEquipment, eqTypes, setEqTypes,
           rotations, regions, areas, loading, reload: load };
}

// ─── Tab 1: Suppliers ─────────────────────────────────────────────────────────
const SuppliersTab: React.FC<{
  suppliers: Supplier[]; setSuppliers: React.Dispatch<React.SetStateAction<Supplier[]>>;
  equipment: Equipment[]; regions: Region[]; areas: Area[]; onAdd: () => void;
}> = ({ suppliers, setSuppliers, equipment, regions, areas, onAdd }) => {
  const [q, setQ]             = useState('');
  const [fReg, setFReg]       = useState('all');
  const [fArea, setFArea]     = useState('all');
  const [fType, setFType]     = useState('all');
  const [fStat, setFStat]     = useState('all');
  const [expanded, setExp]    = useState<number | null>(null);

  const eqTypes = useMemo(() => [...new Set(equipment.map(e => e.equipment_type).filter(Boolean))].sort() as string[], [equipment]);
  const filtAreas = useMemo(() => areas.filter(a => fReg === 'all' || String(a.region_id) === fReg), [areas, fReg]);

  const toggle = async (s: Supplier) => {
    await api.patch(`/suppliers/${s.id}/toggle-active`);
    setSuppliers(prev => prev.map(x => x.id === s.id ? { ...x, is_active: !x.is_active } : x));
  };

  const filtered = useMemo(() => suppliers.filter(s => {
    const ql = q.toLowerCase();
    if (ql && !s.name.toLowerCase().includes(ql) && !s.contact_name?.toLowerCase().includes(ql) && !s.phone?.includes(ql)) return false;
    if (fReg !== 'all' && String(s.region_id) !== fReg) return false;
    if (fArea !== 'all' && String(s.area_id) !== fArea) return false;
    if (fType !== 'all') {
      const ids = new Set(equipment.filter(e => e.equipment_type === fType).map(e => e.supplier_id));
      if (!ids.has(s.id)) return false;
    }
    if (fStat === 'active' && !s.is_active) return false;
    if (fStat === 'inactive' && s.is_active) return false;
    return true;
  }), [suppliers, q, fReg, fArea, fType, fStat, equipment]);

  return (
    <div>
      <div className="flex flex-wrap gap-2 mb-4">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute right-3 top-2.5 w-4 h-4 text-gray-400" />
          <input value={q} onChange={e => setQ(e.target.value)} placeholder="חיפוש שם, איש קשר, טלפון..."
            className="w-full pr-9 pl-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500" />
        </div>
        <select value={fReg} onChange={e => { setFReg(e.target.value); setFArea('all'); }} className="px-3 py-2 border border-gray-200 rounded-lg text-sm">
          <option value="all">כל המרחבים</option>
          {regions.map(r => <option key={r.id} value={String(r.id)}>{r.name}</option>)}
        </select>
        <select value={fArea} onChange={e => setFArea(e.target.value)} className="px-3 py-2 border border-gray-200 rounded-lg text-sm">
          <option value="all">כל האזורים</option>
          {filtAreas.map(a => <option key={a.id} value={String(a.id)}>{a.name}</option>)}
        </select>
        <select value={fType} onChange={e => setFType(e.target.value)} className="px-3 py-2 border border-gray-200 rounded-lg text-sm">
          <option value="all">כל סוגי הציוד</option>
          {eqTypes.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <select value={fStat} onChange={e => setFStat(e.target.value)} className="px-3 py-2 border border-gray-200 rounded-lg text-sm">
          <option value="all">כל הסטטוסים</option>
          <option value="active">פעילים</option>
          <option value="inactive">לא פעילים</option>
        </select>
        <button onClick={onAdd} className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700">
          <Plus className="w-4 h-4" /> ספק חדש
        </button>
      </div>
      <div className="text-xs text-gray-400 mb-2">{filtered.length} ספקים</div>
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="hidden md:grid grid-cols-12 gap-2 px-4 py-2.5 bg-gray-50 text-xs font-semibold text-gray-500 border-b">
          <div className="col-span-3">שם ספק</div><div className="col-span-1">קוד</div>
          <div className="col-span-2">מרחב / אזור</div><div className="col-span-2">איש קשר</div>
          <div className="col-span-1 text-center">כלים</div><div className="col-span-2 text-center">סטטוס</div><div className="col-span-1"/>
        </div>
        {filtered.map(s => (
          <div key={s.id} className={`border-t border-gray-50 ${!s.is_active ? 'opacity-60' : ''}`}>
            <div className="grid grid-cols-12 gap-2 px-4 py-3 hover:bg-gray-50 cursor-pointer items-center"
              onClick={() => setExp(expanded === s.id ? null : s.id)}>
              <div className="col-span-3 flex items-center gap-2">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${s.is_active ? 'bg-green-100' : 'bg-gray-100'}`}>
                  <span className={`text-sm font-bold ${s.is_active ? 'text-green-700' : 'text-gray-400'}`}>{s.name[0]}</span>
                </div>
                <span className="font-medium text-sm text-gray-900 truncate">{s.name}</span>
              </div>
              <div className="col-span-1 text-xs text-gray-400 font-mono">{s.code || '—'}</div>
              <div className="col-span-2 text-xs text-gray-600">
                {s.region_name && <div>{s.region_name}</div>}
                {s.area_name && <div className="text-gray-400">{s.area_name}</div>}
              </div>
              <div className="col-span-2 text-xs">
                {s.contact_name && <div className="text-gray-700">{s.contact_name}</div>}
                {s.phone && <div className="text-gray-400">{s.phone}</div>}
              </div>
              <div className="col-span-1 text-center text-sm font-bold text-green-700">{s.equipment_count ?? '—'}</div>
              <div className="col-span-2 flex justify-center">
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${s.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-400'}`}>
                  {s.is_active ? 'פעיל' : 'לא פעיל'}
                </span>
              </div>
              <div className="col-span-1 flex justify-end">
                {expanded === s.id ? <ChevronDown className="w-4 h-4 text-gray-300" /> : <ChevronRight className="w-4 h-4 text-gray-300" />}
              </div>
            </div>
            {expanded === s.id && (
              <div className="px-4 pb-4 bg-blue-50/20 border-t border-gray-100">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3 text-sm">
                  {s.tax_id && <div className="text-gray-600 text-xs"><span className="text-gray-400">ח.פ: </span>{s.tax_id}</div>}
                  {s.address && <div className="flex items-start gap-1 text-xs text-gray-600"><MapPin className="w-3 h-3 mt-0.5 text-gray-400 flex-shrink-0" />{s.address}</div>}
                  {s.email && <div className="flex items-center gap-1"><Mail className="w-3 h-3 text-gray-400" /><a href={`mailto:${s.email}`} className="text-blue-600 hover:underline text-xs">{s.email}</a></div>}
                  {s.phone && <div className="flex items-center gap-1"><Phone className="w-3 h-3 text-gray-400" /><a href={`tel:${s.phone}`} className="text-blue-600 hover:underline text-xs">{s.phone}</a></div>}
                  {(s.active_area_ids?.length ?? 0) > 0 && <div className="col-span-2 text-xs text-gray-500">סבב הוגן: <span className="font-medium text-green-700">{s.active_area_ids?.length} אזורים</span></div>}
                  {(s.total_assignments ?? 0) > 0 && <div className="text-xs text-gray-500">הזמנות: <span className="font-medium">{s.total_assignments}</span></div>}
                </div>
                <div className="mt-3">
                  <button onClick={() => toggle(s)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border ${s.is_active ? 'border-red-200 text-red-600 hover:bg-red-50' : 'border-green-200 text-green-600 hover:bg-green-50'}`}>
                    {s.is_active ? <><EyeOff className="w-3 h-3" /> השבת ספק</> : <><Eye className="w-3 h-3" /> הפעל ספק</>}
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
        {filtered.length === 0 && <div className="text-center py-10 text-gray-400 text-sm">לא נמצאו ספקים</div>}
      </div>
    </div>
  );
};

// ─── Tab 2: Equipment ─────────────────────────────────────────────────────────
const EquipmentTab: React.FC<{
  equipment: Equipment[]; setEquipment: React.Dispatch<React.SetStateAction<Equipment[]>>;
  suppliers: Supplier[]; eqTypes: EqType[]; regions: Region[]; onAdd: () => void;
}> = ({ equipment, setEquipment, suppliers, eqTypes, regions, onAdd }) => {
  const [q, setQ]           = useState('');
  const [fType, setFType]   = useState('all');
  const [fStat, setFStat]   = useState('all');
  const [fReg, setFReg]     = useState('all');
  const [expanded, setExp]  = useState<Set<number>>(new Set());

  const types = useMemo(() => [...new Set(equipment.map(e => e.equipment_type).filter(Boolean))].sort() as string[], [equipment]);
  const supMap = useMemo(() => { const m: Record<number, Supplier> = {}; suppliers.forEach(s => { m[s.id] = s; }); return m; }, [suppliers]);
  const typeMap = useMemo(() => { const m: Record<string, EqType> = {}; eqTypes.forEach(t => { m[t.name] = t; }); return m; }, [eqTypes]);

  const toggle = async (eq: Equipment) => {
    await api.patch(`/equipment/${eq.id}/toggle-active`);
    setEquipment(prev => prev.map(x => x.id === eq.id ? { ...x, is_active: !x.is_active } : x));
  };

  const filtered = useMemo(() => equipment.filter(e => {
    if (q && !e.license_plate?.toLowerCase().includes(q.toLowerCase()) && !e.name?.toLowerCase().includes(q.toLowerCase())) return false;
    if (fType !== 'all' && e.equipment_type !== fType) return false;
    if (fStat === 'active' && !e.is_active) return false;
    if (fStat === 'inactive' && e.is_active) return false;
    if (fStat === 'no_rate' && e.hourly_rate) return false;
    if (fStat === 'night' && !e.night_guard) return false;
    if (fReg !== 'all') { const s = supMap[e.supplier_id]; if (!s || String(s.region_id) !== fReg) return false; }
    return true;
  }), [equipment, q, fType, fStat, fReg, supMap]);

  const bySupplier = useMemo(() => filtered.reduce((acc, eq) => {
    const sid = eq.supplier_id || 0; if (!acc[sid]) acc[sid] = []; acc[sid].push(eq); return acc;
  }, {} as Record<number, Equipment[]>), [filtered]);

  const toggleExp = (id: number) => setExp(prev => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n; });

  return (
    <div>
      <div className="flex flex-wrap gap-2 mb-4">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute right-3 top-2.5 w-4 h-4 text-gray-400" />
          <input value={q} onChange={e => setQ(e.target.value)} placeholder="חיפוש מספר רישוי..."
            className="w-full pr-9 pl-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500" />
        </div>
        <select value={fReg} onChange={e => setFReg(e.target.value)} className="px-3 py-2 border border-gray-200 rounded-lg text-sm">
          <option value="all">כל המרחבים</option>
          {regions.map(r => <option key={r.id} value={String(r.id)}>{r.name}</option>)}
        </select>
        <select value={fType} onChange={e => setFType(e.target.value)} className="px-3 py-2 border border-gray-200 rounded-lg text-sm">
          <option value="all">כל סוגי הציוד</option>
          {types.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <select value={fStat} onChange={e => setFStat(e.target.value)} className="px-3 py-2 border border-gray-200 rounded-lg text-sm">
          <option value="all">כל הסטטוסים</option>
          <option value="active">פעילים</option>
          <option value="inactive">לא פעילים</option>
          <option value="no_rate">חסר תעריף</option>
          <option value="night">שמירת לילה</option>
        </select>
        <button onClick={onAdd} className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700">
          <Plus className="w-4 h-4" /> הוסף כלי
        </button>
      </div>
      <div className="text-xs text-gray-400 mb-2">{Object.keys(bySupplier).length} ספקים · {filtered.length} כלים</div>
      <div className="space-y-2">
        {suppliers.filter(s => bySupplier[s.id]).map(s => {
          const eqList = bySupplier[s.id] || [];
          const isOpen = expanded.has(s.id);
          return (
            <div key={s.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <button onClick={() => toggleExp(s.id)} className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 bg-green-100 rounded-lg flex items-center justify-center">
                    <span className="font-bold text-green-700 text-sm">{s.name[0]}</span>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold text-gray-900 text-sm">{s.name}</div>
                    <div className="text-xs text-gray-400">{s.area_name || s.region_name}</div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs font-bold text-green-700 bg-green-50 px-2 py-0.5 rounded-full">{eqList.length} כלים</span>
                  {isOpen ? <ChevronDown className="w-4 h-4 text-gray-300" /> : <ChevronRight className="w-4 h-4 text-gray-300" />}
                </div>
              </button>
              {isOpen && (
                <div>
                  <div className="hidden md:grid grid-cols-12 gap-2 px-5 py-2 bg-gray-50 text-[10px] font-semibold text-gray-400 border-t">
                    <div className="col-span-2">רישוי</div><div className="col-span-3">סוג ציוד</div>
                    <div className="col-span-2">קבוצה</div><div className="col-span-2 text-center">תעריף/שעה</div>
                    <div className="col-span-1 text-center">לינה</div><div className="col-span-1 text-center">☽</div>
                    <div className="col-span-1 text-center">סטטוס</div>
                  </div>
                  {eqList.map(eq => {
                    const et = eq.equipment_type ? typeMap[eq.equipment_type] : null;
                    return (
                      <div key={eq.id} className={`grid grid-cols-12 gap-2 px-5 py-2.5 border-t border-gray-50 items-center ${!eq.is_active ? 'opacity-40' : ''}`}>
                        <div className="col-span-2 font-mono font-bold text-gray-800 text-xs">{eq.license_plate || eq.name}</div>
                        <div className="col-span-3 text-xs text-gray-700">{eq.equipment_type || '—'}</div>
                        <div className="col-span-2">
                          {et?.category_group && <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${gc(et.category_group)}`}>{et.category_group}</span>}
                        </div>
                        <div className="col-span-2 text-center font-bold text-xs text-green-700">
                          {eq.hourly_rate ? `₪${Number(eq.hourly_rate).toLocaleString()}` : <span className="text-orange-400">חסר</span>}
                        </div>
                        <div className="col-span-1 text-center text-xs text-gray-500">{eq.overnight_rate ? `₪${eq.overnight_rate}` : '—'}</div>
                        <div className="col-span-1 text-center">{eq.night_guard ? <Moon className="w-4 h-4 text-indigo-500 mx-auto" /> : <span className="text-gray-200 text-xs">—</span>}</div>
                        <div className="col-span-1 text-center">
                          <button onClick={() => toggle(eq)}>
                            <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${eq.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-400'}`}>
                              {eq.is_active ? 'פעיל' : 'כבוי'}
                            </span>
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
        {Object.keys(bySupplier).length === 0 && <div className="text-center py-10 text-gray-400 text-sm">לא נמצא ציוד</div>}
      </div>
    </div>
  );
};

// ─── Tab 3: Pricing ───────────────────────────────────────────────────────────
const PricingTab: React.FC<{
  eqTypes: EqType[]; setEqTypes: React.Dispatch<React.SetStateAction<EqType[]>>; onAdd: () => void;
}> = ({ eqTypes, setEqTypes, onAdd }) => {
  const [q, setQ]           = useState('');
  const [fGrp, setFGrp]     = useState('all');
  const [fStat, setFStat]   = useState('all');
  const [editing, setEdit]  = useState<number | null>(null);
  const [eRate, setERate]   = useState('');
  const [eNight, setENight] = useState('');

  const groups = useMemo(() => [...new Set(eqTypes.map(t => t.category_group).filter(Boolean))].sort() as string[], [eqTypes]);

  const filtered = useMemo(() => eqTypes.filter(t => {
    if (q && !t.name.toLowerCase().includes(q.toLowerCase())) return false;
    if (fGrp !== 'all' && t.category_group !== fGrp) return false;
    if (fStat === 'active' && !t.is_active) return false;
    if (fStat === 'inactive' && t.is_active) return false;
    if (fStat === 'no_rate' && t.hourly_rate) return false;
    return true;
  }), [eqTypes, q, fGrp, fStat]);

  const save = async (t: EqType) => {
    const body: Record<string, unknown> = {};
    if (eRate) body.hourly_rate = Number(eRate);
    if (eNight) body.overnight_rate = Number(eNight);
    if (!Object.keys(body).length) { setEdit(null); return; }
    await api.put(`/equipment-types/${t.id}`, body);
    setEqTypes(prev => prev.map(x => x.id === t.id ? {
      ...x, hourly_rate: eRate ? Number(eRate) : x.hourly_rate, overnight_rate: eNight ? Number(eNight) : x.overnight_rate,
    } : x));
    setEdit(null);
  };

  return (
    <div>
      <div className="flex flex-wrap gap-2 mb-4">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute right-3 top-2.5 w-4 h-4 text-gray-400" />
          <input value={q} onChange={e => setQ(e.target.value)} placeholder="חיפוש שם סוג ציוד..."
            className="w-full pr-9 pl-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500" />
        </div>
        <select value={fGrp} onChange={e => setFGrp(e.target.value)} className="px-3 py-2 border border-gray-200 rounded-lg text-sm">
          <option value="all">כל הקבוצות</option>
          {groups.map(g => <option key={g} value={g}>{g}</option>)}
        </select>
        <select value={fStat} onChange={e => setFStat(e.target.value)} className="px-3 py-2 border border-gray-200 rounded-lg text-sm">
          <option value="all">כל הסטטוסים</option>
          <option value="active">פעיל</option>
          <option value="inactive">לא פעיל</option>
          <option value="no_rate">חסר תעריף</option>
        </select>
        <button onClick={onAdd} className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700">
          <Plus className="w-4 h-4" /> סוג ציוד חדש
        </button>
      </div>
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="hidden md:grid grid-cols-12 gap-2 px-4 py-2.5 bg-gray-50 text-xs font-semibold text-gray-500 border-b">
          <div className="col-span-4">שם סוג ציוד</div><div className="col-span-2">קבוצה</div>
          <div className="col-span-2 text-center">תעריף שעתי</div><div className="col-span-2 text-center">תעריף לינה</div>
          <div className="col-span-1 text-center">☽</div><div className="col-span-1 text-center">סטטוס</div>
        </div>
        {filtered.map(t => (
          <div key={t.id} className={`grid grid-cols-12 gap-2 px-4 py-3 border-t border-gray-50 items-center ${!t.hourly_rate ? 'bg-orange-50/20' : ''}`}>
            <div className="col-span-4 font-medium text-gray-900 text-sm">{t.name}</div>
            <div className="col-span-2">{t.category_group && <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${gc(t.category_group)}`}>{t.category_group}</span>}</div>
            <div className="col-span-2 text-center">
              {editing === t.id
                ? <input type="number" value={eRate} onChange={e => setERate(e.target.value)} placeholder={String(t.hourly_rate || '')}
                    className="w-full text-center border border-green-300 rounded px-2 py-1 text-xs" />
                : <span className={`font-bold text-sm ${t.hourly_rate ? 'text-green-700' : 'text-orange-400'}`}>{t.hourly_rate ? `₪${t.hourly_rate}` : 'חסר'}</span>}
            </div>
            <div className="col-span-2 text-center">
              {editing === t.id
                ? <input type="number" value={eNight} onChange={e => setENight(e.target.value)} placeholder={String(t.overnight_rate || '')}
                    className="w-full text-center border border-green-300 rounded px-2 py-1 text-xs" />
                : <span className="text-sm text-gray-600">{t.overnight_rate ? `₪${t.overnight_rate}` : '—'}</span>}
            </div>
            <div className="col-span-1 text-center">{t.night_guard ? <Moon className="w-4 h-4 text-indigo-500 mx-auto" /> : <span className="text-gray-200 text-xs">—</span>}</div>
            <div className="col-span-1 flex items-center justify-center gap-1">
              {editing === t.id
                ? <><button onClick={() => save(t)} className="p-1 text-green-600 hover:bg-green-50 rounded"><Check className="w-4 h-4" /></button>
                     <button onClick={() => setEdit(null)} className="p-1 text-gray-400 hover:bg-gray-50 rounded"><X className="w-4 h-4" /></button></>
                : <button onClick={() => { setEdit(t.id); setERate(''); setENight(''); }} className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded">
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>}
            </div>
          </div>
        ))}
        {filtered.length === 0 && <div className="text-center py-8 text-gray-400 text-sm">לא נמצאו סוגי ציוד</div>}
      </div>
    </div>
  );
};

// ─── Tab 4: Rotation ──────────────────────────────────────────────────────────
const RotationTab: React.FC<{
  rotations: Rotation[]; regions: Region[]; areas: Area[]; reload: () => void;
}> = ({ rotations, regions, areas, reload }) => {
  const [fReg, setFReg] = useState('all');
  const [fArea, setFA]  = useState('all');
  const [fType, setFT]  = useState('all');

  const noArea = useMemo(() => rotations.filter(r => !r.area_id && r.is_active), [rotations]);
  const filtAreas = useMemo(() => areas.filter(a => fReg === 'all' || regions.find(r => r.id === a.region_id && String(r.id) === fReg)), [areas, regions, fReg]);
  const types = useMemo(() => [...new Set(rotations.map(r => r.category_name).filter(Boolean))].sort() as string[], [rotations]);

  const filtered = useMemo(() => rotations.filter(r => {
    if (!r.is_active || !r.area_id) return false;
    if (fArea !== 'all' && String(r.area_id) !== fArea) return false;
    if (fType !== 'all' && r.category_name !== fType) return false;
    if (fReg !== 'all') { const a = areas.find(x => x.id === r.area_id); if (!a || String(a.region_id) !== fReg) return false; }
    return true;
  }), [rotations, fArea, fType, fReg, areas]);

  const byArea = useMemo(() => filtered.reduce((acc, r) => {
    const k = r.area_id!; if (!acc[k]) acc[k] = []; acc[k].push(r); return acc;
  }, {} as Record<number, Rotation[]>), [filtered]);

  const getSt = (r: Rotation) => {
    if (!r.is_available) return { label: 'לא זמין', cls: 'bg-red-100 text-red-700' };
    if (r.rotation_position === 1) return { label: 'הבא בתור', cls: 'bg-green-100 text-green-700' };
    return { label: `תור ${r.rotation_position}`, cls: 'bg-blue-100 text-blue-700' };
  };

  return (
    <div>
      {noArea.length > 0 && (
        <div className="flex items-start gap-3 bg-orange-50 border border-orange-200 rounded-xl p-4 mb-4">
          <AlertCircle className="w-5 h-5 text-orange-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-orange-800">
            <strong>{noArea.length} ספקים ללא אזור שירות</strong> — לא ייכנסו לסבב הוגן. שייך אותם בטאב "ספקים".
          </div>
        </div>
      )}
      <div className="flex flex-wrap gap-2 mb-4">
        <select value={fReg} onChange={e => { setFReg(e.target.value); setFA('all'); }} className="px-3 py-2 border border-gray-200 rounded-lg text-sm">
          <option value="all">כל המרחבים</option>
          {regions.map(r => <option key={r.id} value={String(r.id)}>{r.name}</option>)}
        </select>
        <select value={fArea} onChange={e => setFA(e.target.value)} className="px-3 py-2 border border-gray-200 rounded-lg text-sm">
          <option value="all">כל האזורים</option>
          {filtAreas.map(a => <option key={a.id} value={String(a.id)}>{a.name}</option>)}
        </select>
        <select value={fType} onChange={e => setFT(e.target.value)} className="px-3 py-2 border border-gray-200 rounded-lg text-sm">
          <option value="all">כל סוגי הציוד</option>
          {types.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <button onClick={reload} className="flex items-center gap-1.5 px-3 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50">
          <RefreshCw className="w-4 h-4" /> רענן
        </button>
      </div>
      <div className="space-y-4">
        {Object.entries(byArea).map(([aId, aRots]) => {
          const area = areas.find(a => a.id === Number(aId));
          const region = regions.find(r => r.id === area?.region_id);
          const byCat = aRots.reduce((acc, r) => { const k = r.category_name || '?'; if (!acc[k]) acc[k] = []; acc[k].push(r); return acc; }, {} as Record<string, Rotation[]>);
          return (
            <div key={aId} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="px-4 py-3 bg-gray-50 border-b flex items-center gap-2">
                <MapPin className="w-4 h-4 text-green-600" />
                <span className="font-semibold text-gray-900">{area?.name || `אזור ${aId}`}</span>
                <span className="text-xs text-gray-400">/ {region?.name}</span>
                <span className="mr-auto text-xs text-gray-400">{aRots.length} ספקים</span>
              </div>
              {Object.entries(byCat).map(([cat, catRots]) => (
                <div key={cat} className="border-t border-gray-50">
                  <div className="px-4 py-2 bg-gray-50/50">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${gc(cat)}`}>{cat}</span>
                  </div>
                  <div className="hidden md:grid grid-cols-12 gap-2 px-5 py-1.5 text-[10px] font-semibold text-gray-400 border-t border-gray-50">
                    <div className="col-span-1 text-center">תור</div><div className="col-span-3">ספק</div>
                    <div className="col-span-2 text-center">הזמנות</div><div className="col-span-2 text-center">דחיות</div>
                    <div className="col-span-2 text-center">תגובה ממוצעת</div><div className="col-span-2 text-center">סטטוס</div>
                  </div>
                  {catRots.sort((a, b) => (a.rotation_position||99)-(b.rotation_position||99)).map(r => {
                    const st = getSt(r);
                    return (
                      <div key={r.id} className="grid grid-cols-12 gap-2 px-5 py-2.5 border-t border-gray-50 items-center">
                        <div className="col-span-1 text-center font-bold text-gray-400 text-xs">{r.rotation_position||'?'}</div>
                        <div className="col-span-3 font-medium text-gray-900 text-xs truncate">{r.supplier_name||`ספק ${r.supplier_id}`}</div>
                        <div className="col-span-2 text-center text-xs text-gray-600">{r.total_assignments||0}</div>
                        <div className="col-span-2 text-center text-xs text-gray-600">{r.rejection_count||0}</div>
                        <div className="col-span-2 text-center text-xs text-gray-400">{r.avg_response_time_hours?`${r.avg_response_time_hours.toFixed(1)} שעות`:'—'}</div>
                        <div className="col-span-2 flex justify-center">
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${st.cls}`}>{st.label}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          );
        })}
        {Object.keys(byArea).length === 0 && <div className="text-center py-10 text-gray-400 text-sm">לא נמצאו נתוני סבב</div>}
      </div>
    </div>
  );
};

// ─── Main ─────────────────────────────────────────────────────────────────────
const SupplierSettings: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const getTab = (): TabType => {
    const t = searchParams.get('tab') as TabType;
    return ['suppliers','equipment','pricing','rotation'].includes(t) ? t : 'suppliers';
  };
  const [activeTab, setActiveTab] = useState<TabType>(getTab);
  const switchTab = (tab: TabType) => { setActiveTab(tab); setSearchParams({ tab }); };

  const { suppliers, setSuppliers, equipment, setEquipment, eqTypes, setEqTypes,
          rotations, regions, areas, loading, reload } = useAllData();

  const [showSM, setShowSM] = useState(false);
  const [showEM, setShowEM] = useState(false);
  const [showTM, setShowTM] = useState(false);

  const tabs = [
    { id: 'suppliers' as TabType, label: 'ספקים',              icon: <Truck className="w-4 h-4" /> },
    { id: 'equipment' as TabType, label: 'ציוד ספקים',         icon: <Wrench className="w-4 h-4" /> },
    { id: 'pricing'   as TabType, label: 'סוגי ציוד ותעריפים', icon: <DollarSign className="w-4 h-4" /> },
    { id: 'rotation'  as TabType, label: 'סבב הוגן',           icon: <RotateCcw className="w-4 h-4" /> },
  ];

  if (loading) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center" dir="rtl">
      <div className="flex flex-col items-center gap-3 text-gray-500">
        <RefreshCw className="w-8 h-8 animate-spin text-green-600" />
        <span className="text-sm">טוען נתונים...</span>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50" dir="rtl">
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto">
          <button onClick={() => navigate('/settings')} className="flex items-center gap-1.5 text-sm text-green-600 hover:text-green-800 mb-3">
            <ArrowRight className="w-4 h-4" /> חזרה להגדרות
          </button>
          <h1 className="text-2xl font-bold text-gray-900">ספקים וציוד</h1>
          <p className="text-sm text-gray-500 mt-0.5">ניהול ספקים, ציוד, תמחור וסבב הוגן</p>
          <div className="flex gap-1 mt-4 overflow-x-auto pb-1">
            {tabs.map(tab => (
              <button key={tab.id} onClick={() => switchTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${activeTab === tab.id ? 'bg-green-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}>
                {tab.icon} {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>
      <div className="max-w-7xl mx-auto px-6 py-6">
        {activeTab === 'suppliers' && <SuppliersTab suppliers={suppliers} setSuppliers={setSuppliers} equipment={equipment} regions={regions} areas={areas} onAdd={() => setShowSM(true)} />}
        {activeTab === 'equipment' && <EquipmentTab equipment={equipment} setEquipment={setEquipment} suppliers={suppliers} eqTypes={eqTypes} regions={regions} onAdd={() => setShowEM(true)} />}
        {activeTab === 'pricing'   && <PricingTab eqTypes={eqTypes} setEqTypes={setEqTypes} onAdd={() => setShowTM(true)} />}
        {activeTab === 'rotation'  && <RotationTab rotations={rotations} regions={regions} areas={areas} reload={reload} />}
      </div>
      {showSM && <SupplierModal onClose={() => setShowSM(false)} onSaved={() => { setShowSM(false); reload(); (window as any).showToast?.('ספק נוצר בהצלחה','success'); }} />}
      {showEM && <EquipmentModal onClose={() => setShowEM(false)} onSaved={() => { setShowEM(false); reload(); (window as any).showToast?.('כלי נוסף בהצלחה','success'); }} />}
      {showTM && <EquipmentTypeModal onClose={() => setShowTM(false)} onSaved={() => { setShowTM(false); reload(); (window as any).showToast?.('סוג ציוד נוצר','success'); }} />}
    </div>
  );
};

export default SupplierSettings;
