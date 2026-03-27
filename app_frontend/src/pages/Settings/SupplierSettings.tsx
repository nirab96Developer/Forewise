// src/pages/Settings/SupplierSettings.tsx 
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowRight, Truck, Wrench, DollarSign, RotateCcw,
  Search, Plus, ChevronDown, ChevronRight,
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
  category_name?: string;
  rotation_position: number; total_assignments: number;
  rejection_count: number; avg_response_time_hours?: number;
  is_active: boolean; is_available: boolean;
}
interface Region { id: number; name: string; }
interface Area { id: number; name: string; region_id: number; }
type TabType = 'suppliers' | 'equipment' | 'pricing' | 'rotation';

// badge colour per group
const gc = (g?: string) => {
  if (!g) return 'bg-gray-100 text-gray-500';
  if (g.includes('כבד')) return 'bg-green-50 text-green-700';
  if (g.includes('קל'))  return 'bg-blue-50 text-blue-700';
  if (g.includes('ציוד')) return 'bg-purple-50 text-purple-700';
  if (g.includes('שמיר')) return 'bg-amber-50 text-amber-700';
  return 'bg-gray-100 text-gray-500';
};

// Shared data 
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
      const [sR, eR, tR, rR, regR, aR] = await Promise.allSettled([
        api.get('/suppliers',           { params: { page_size: 200 } }),
        api.get('/equipment',           { params: { page_size: 200 } }),
        api.get('/equipment-types',     { params: { page_size: 50 } }),
        api.get('/supplier-rotations/', { params: { page_size: 200 } }),
        api.get('/regions'),
        api.get('/areas'),
      ]);
      if (sR.status === 'fulfilled')   setSuppliers(sR.value.data?.items || sR.value.data || []);
      if (eR.status === 'fulfilled')   setEquipment(eR.value.data?.items || []);
      if (tR.status === 'fulfilled')   setEqTypes(tR.value.data?.items || []);
      if (rR.status === 'fulfilled')   { const rots = rR.value.data?.items || rR.value.data || []; setRotations(Array.isArray(rots) ? rots : []); }
      if (regR.status === 'fulfilled') setRegions(regR.value.data?.items || regR.value.data || []);
      if (aR.status === 'fulfilled')   setAreas(aR.value.data?.items || aR.value.data || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);
  return { suppliers, setSuppliers, equipment, setEquipment, eqTypes, setEqTypes,
           rotations, regions, areas, loading, reload: load };
}

// Stats cards 
const StatsBar: React.FC<{ suppliers: Supplier[]; equipment: Equipment[]; rotations: Rotation[] }> = ({ suppliers, equipment, rotations }) => {
  const activeSuppliers = suppliers.filter(s => s.is_active).length;
  const totalEq = equipment.length;
  const inRotation = rotations.filter(r => r.is_active).length;
  const nightGuard = equipment.filter(e => e.night_guard).length;
  const noArea = suppliers.filter(s => s.is_active && !(s.active_area_ids?.length)).length;

  const cards = [
    { label: 'ספקים פעילים',     value: activeSuppliers, cls: 'text-gray-900' },
    { label: 'כלים בשטח',         value: totalEq,         cls: 'text-gray-900' },
    { label: 'בסבב הוגן',         value: inRotation,      cls: 'text-kkl-green' },
    { label: 'שמירת לילה',        value: nightGuard,      cls: 'text-blue-600' },
    { label: 'ללא אזור שירות',    value: noArea,          cls: noArea > 0 ? 'text-amber-500' : 'text-gray-900' },
  ];

  return (
    <div className="grid grid-cols-5 gap-3 mb-6">
      {cards.map(c => (
        <div key={c.label} className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="text-xs text-gray-500 font-medium mb-1">{c.label}</div>
          <div className={`text-2xl font-bold ${c.cls}`}>{c.value.toLocaleString()}</div>
        </div>
      ))}
    </div>
  );
};

// Tab 1: Suppliers 
const SuppliersTab: React.FC<{
  suppliers: Supplier[]; setSuppliers: React.Dispatch<React.SetStateAction<Supplier[]>>;
  equipment: Equipment[]; regions: Region[]; areas: Area[];
  onAddEq: (supplierId?: number) => void;
}> = ({ suppliers, setSuppliers, equipment, regions, areas, onAddEq }) => {
  const [q, setQ]         = useState('');
  const [fReg, setFReg]   = useState('all');
  const [fArea, setFArea] = useState('all');
  const [fType, setFType] = useState('all');
  const [fStat, setFStat] = useState('all');
  const [expanded, setExp] = useState<number | null>(null);

  const eqTypes = useMemo(() => [...new Set(equipment.map(e => e.equipment_type).filter(Boolean))].sort() as string[], [equipment]);
  const filtAreas = useMemo(() => areas.filter(a => fReg === 'all' || String(a.region_id) === fReg), [areas, fReg]);

  const toggle = async (s: Supplier) => {
    await api.patch(`/suppliers/${s.id}/toggle-active`);
    setSuppliers(prev => prev.map(x => x.id === s.id ? { ...x, is_active: !x.is_active } : x));
  };

  const filtered = useMemo(() => suppliers.filter(s => {
    const ql = q.toLowerCase();
    if (ql && !s.name.toLowerCase().includes(ql) && !s.contact_name?.toLowerCase().includes(ql) && !s.phone?.includes(ql) && !s.tax_id?.includes(ql)) return false;
    if (fReg !== 'all' && String(s.region_id) !== fReg) return false;
    if (fArea !== 'all' && String(s.area_id) !== fArea) return false;
    if (fType !== 'all') { const ids = new Set(equipment.filter(e => e.equipment_type === fType).map(e => e.supplier_id)); if (!ids.has(s.id)) return false; }
    if (fStat === 'active' && !s.is_active) return false;
    if (fStat === 'inactive' && s.is_active) return false;
    return true;
  }), [suppliers, q, fReg, fArea, fType, fStat, equipment]);

  return (
    <div>
      {/* Filters */}
      <div className="flex gap-3 mb-4 items-center flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input value={q} onChange={e => setQ(e.target.value)} placeholder="חיפוש שם ספק, ח.פ, איש קשר..."
            className="w-full pr-10 pl-4 py-2.5 rounded-xl border border-gray-200 text-sm placeholder-gray-400 bg-white focus:outline-none focus:border-kkl-green focus:ring-1 focus:ring-kkl-green" />
        </div>
        <select value={fReg} onChange={e => { setFReg(e.target.value); setFArea('all'); }}
          className="px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-600 bg-white focus:outline-none focus:border-kkl-green cursor-pointer">
          <option value="all">כל המרחבים</option>
          {regions.map(r => <option key={r.id} value={String(r.id)}>{r.name}</option>)}
        </select>
        <select value={fArea} onChange={e => setFArea(e.target.value)}
          className="px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-600 bg-white focus:outline-none focus:border-kkl-green cursor-pointer">
          <option value="all">כל האזורים</option>
          {filtAreas.map(a => <option key={a.id} value={String(a.id)}>{a.name}</option>)}
        </select>
        <select value={fType} onChange={e => setFType(e.target.value)}
          className="px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-600 bg-white focus:outline-none focus:border-kkl-green cursor-pointer">
          <option value="all">כל סוגי הציוד</option>
          {eqTypes.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <select value={fStat} onChange={e => setFStat(e.target.value)}
          className="px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-600 bg-white focus:outline-none focus:border-kkl-green cursor-pointer">
          <option value="all">כל הסטטוסים</option>
          <option value="active">פעילים</option>
          <option value="inactive">לא פעילים</option>
        </select>
      </div>

      <div className="text-xs text-gray-400 mb-3">{filtered.length} ספקים</div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {/* Table header */}
        <div className="bg-gray-50 border-b border-gray-200 grid grid-cols-12 gap-2 px-4 py-3 hidden md:grid">
          {['שם ספק','קוד','מרחב / אזור','איש קשר','טלפון','כלים','סטטוס',''].map((h, i) => (
            <div key={i} className={`text-right text-xs font-semibold text-gray-500 uppercase tracking-wider ${i===5||i===6?'text-center':''} ${i===0?'col-span-3':i===2?'col-span-2':i===3?'col-span-2':i===4?'col-span-2':'col-span-1'}`}>{h}</div>
          ))}
        </div>

        {filtered.map(s => (
          <div key={s.id} className={!s.is_active ? 'opacity-45' : ''}>
            <div className="grid grid-cols-12 gap-2 px-4 py-3 border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors items-center"
              onClick={() => setExp(expanded === s.id ? null : s.id)}>
              <div className="col-span-3 flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-green-100 text-kkl-green text-xs font-bold flex items-center justify-center flex-shrink-0">
                  {s.name[0]}
                </div>
                <span className="font-semibold text-sm text-gray-800 truncate">{s.name}</span>
              </div>
              <div className="col-span-1 text-xs text-gray-400 font-mono">{s.code || '—'}</div>
              <div className="col-span-2 text-xs text-gray-600">
                {s.region_name && <div className="font-medium">{s.region_name}</div>}
                {s.area_name && <div className="text-gray-400">{s.area_name}</div>}
              </div>
              <div className="col-span-2 text-xs text-gray-600">{s.contact_name || '—'}</div>
              <div className="col-span-2 text-xs text-gray-500">{s.phone || '—'}</div>
              <div className="col-span-1 text-center">
                <span className="font-bold text-kkl-green">{s.equipment_count ?? 0}</span>
              </div>
              <div className="col-span-1 text-center">
                <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-bold ${s.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                  {s.is_active ? 'פעיל' : 'לא פעיל'}
                </span>
              </div>
              <div className="col-span-0 flex justify-end">
                {expanded === s.id ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
              </div>
            </div>

            {/* Expanded */}
            {expanded === s.id && (
              <div className="bg-gray-50 border-t border-gray-100 px-6 py-4">
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">פרטי חברה</div>
                    {s.tax_id && <div className="text-sm text-gray-700 font-medium mb-1">ח.פ: {s.tax_id}</div>}
                    {s.address && <div className="text-sm text-gray-700 font-medium mb-1 flex items-center gap-1"><MapPin className="w-3 h-3 text-gray-400" />{s.address}</div>}
                    {s.email && <div className="text-sm text-gray-700 font-medium mb-1 flex items-center gap-1"><Mail className="w-3 h-3 text-gray-400" /><a href={`mailto:${s.email}`} className="text-blue-600 hover:underline">{s.email}</a></div>}
                    {s.phone && <div className="text-sm text-gray-700 font-medium flex items-center gap-1"><Phone className="w-3 h-3 text-gray-400" /><a href={`tel:${s.phone}`} className="text-blue-600 hover:underline">{s.phone}</a></div>}
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">אזורי שירות — סבב הוגן</div>
                    <div className="flex flex-wrap gap-1 mb-2">
                      {(s.active_area_ids?.length ?? 0) > 0
                        ? s.active_area_ids!.slice(0, 6).map(id => {
                            return <span key={id} className="inline-block bg-green-50 text-kkl-green text-xs font-semibold px-2 py-0.5 rounded-full border border-green-200">{`אזור ${id}`}</span>;
                          })
                        : <span className="text-xs text-gray-400">לא שויך לאזורים</span>}
                    </div>
                    {(s.total_assignments ?? 0) > 0 && (
                      <div className="text-xs text-gray-500">הזמנות שהוקצו: <span className="font-semibold text-gray-700">{s.total_assignments}</span></div>
                    )}
                  </div>
                </div>
                <div className="flex gap-2 mt-4">
                  <button onClick={() => onAddEq(s.id)}
                    className="px-3 py-1.5 rounded-lg bg-kkl-green text-white text-xs font-semibold hover:bg-kkl-green-dark transition-colors">
                    + הוסף כלי
                  </button>
                  <button onClick={() => toggle(s)}
                    className={`px-3 py-1.5 rounded-lg border text-xs font-semibold transition-colors ${s.is_active ? 'border-red-200 text-red-600 hover:bg-red-50' : 'border-green-200 text-green-600 hover:bg-green-50'}`}>
                    {s.is_active ? 'השבת ספק' : 'הפעל ספק'}
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
        {filtered.length === 0 && <div className="text-center py-12 text-gray-400 text-sm">לא נמצאו ספקים</div>}
      </div>
    </div>
  );
};

// Tab 2: Equipment 
const EquipmentTab: React.FC<{
  equipment: Equipment[]; setEquipment: React.Dispatch<React.SetStateAction<Equipment[]>>;
  suppliers: Supplier[]; eqTypes: EqType[]; regions: Region[];
}> = ({ equipment, setEquipment, suppliers, eqTypes, regions }) => {
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
      <div className="flex gap-3 mb-4 items-center flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input value={q} onChange={e => setQ(e.target.value)} placeholder="חיפוש מספר רישוי..."
            className="w-full pr-10 pl-4 py-2.5 rounded-xl border border-gray-200 text-sm placeholder-gray-400 bg-white focus:outline-none focus:border-kkl-green focus:ring-1 focus:ring-kkl-green" />
        </div>
        <select value={fReg} onChange={e => setFReg(e.target.value)} className="px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-600 bg-white focus:outline-none focus:border-kkl-green cursor-pointer">
          <option value="all">כל המרחבים</option>
          {regions.map(r => <option key={r.id} value={String(r.id)}>{r.name}</option>)}
        </select>
        <select value={fType} onChange={e => setFType(e.target.value)} className="px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-600 bg-white focus:outline-none focus:border-kkl-green cursor-pointer">
          <option value="all">כל סוגי הציוד</option>
          {types.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <select value={fStat} onChange={e => setFStat(e.target.value)} className="px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-600 bg-white focus:outline-none focus:border-kkl-green cursor-pointer">
          <option value="all">כל הסטטוסים</option>
          <option value="active">פעילים</option>
          <option value="inactive">לא פעילים</option>
          <option value="no_rate">חסר תעריף</option>
          <option value="night">שמירת לילה</option>
        </select>
      </div>
      <div className="text-xs text-gray-400 mb-3">{Object.keys(bySupplier).length} ספקים · {filtered.length} כלים</div>

      <div className="space-y-3">
        {suppliers.filter(s => bySupplier[s.id]).map(s => {
          const eqList = bySupplier[s.id] || [];
          const isOpen = expanded.has(s.id);
          const nightCount = eqList.filter(e => e.night_guard).length;
          return (
            <div key={s.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50 transition-colors" onClick={() => toggleExp(s.id)}>
                <div className="w-9 h-9 rounded-full bg-green-100 text-kkl-green text-sm font-bold flex items-center justify-center flex-shrink-0">
                  {s.name[0]}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-gray-900 text-sm">{s.name}</div>
                  <div className="text-xs text-gray-400">{s.area_name || s.region_name}</div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="bg-green-100 text-green-700 text-xs font-bold px-2 py-0.5 rounded-full">{eqList.length} כלים</span>
                  {nightCount > 0 && <span className="bg-blue-50 text-blue-600 text-xs font-semibold px-2 py-0.5 rounded-full border border-blue-200">{nightCount} לילה</span>}
                  {isOpen ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
                </div>
              </div>
              {isOpen && (
                <div className="border-t border-gray-100">
                  <div className="hidden md:grid grid-cols-12 gap-2 px-5 py-2 bg-gray-50 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">
                    <div className="col-span-2">רישוי</div><div className="col-span-3">סוג ציוד</div>
                    <div className="col-span-2">קבוצה</div><div className="col-span-2 text-center">תעריף/שעה</div>
<div className="col-span-1 text-center">לינה</div><div className="col-span-1 text-center"></div>
                    <div className="col-span-1 text-center">סטטוס</div>
                  </div>
                  {eqList.map(eq => {
                    const et = eq.equipment_type ? typeMap[eq.equipment_type] : null;
                    return (
                      <div key={eq.id} className={`grid grid-cols-12 gap-2 px-5 py-2.5 border-t border-gray-50 items-center ${!eq.is_active ? 'opacity-40' : ''}`}>
                        <div className="col-span-2 font-mono font-bold text-gray-800 text-xs">{eq.license_plate || '—'}</div>
                        <div className="col-span-3 text-xs text-gray-700">{eq.equipment_type || '—'}</div>
                        <div className="col-span-2">
                          {et?.category_group && <span className={`text-xs px-2 py-0.5 rounded-md font-medium ${gc(et.category_group)}`}>{et.category_group}</span>}
                        </div>
                        <div className="col-span-2 text-center font-bold text-sm text-kkl-green">
{eq.hourly_rate ? `${Number(eq.hourly_rate).toLocaleString()}` : <span className="text-amber-500 font-semibold text-xs">לא הוגדר</span>}
                        </div>
<div className="col-span-1 text-center text-xs text-gray-500">{eq.overnight_rate ? `${eq.overnight_rate}` : '—'}</div>
                        <div className="col-span-1 text-center">{eq.night_guard ? <Moon className="w-4 h-4 text-blue-500 mx-auto" /> : <span className="text-gray-200 text-xs">—</span>}</div>
                        <div className="col-span-1 text-center">
                          <button onClick={() => toggle(eq)}>
                            <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-bold ${eq.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
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
        {Object.keys(bySupplier).length === 0 && <div className="text-center py-12 text-gray-400 text-sm">לא נמצא ציוד</div>}
      </div>
    </div>
  );
};

// Tab 3: Pricing 
const PricingTab: React.FC<{
  eqTypes: EqType[]; setEqTypes: React.Dispatch<React.SetStateAction<EqType[]>>;
}> = ({ eqTypes, setEqTypes }) => {
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
      <div className="flex gap-3 mb-4 items-center flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input value={q} onChange={e => setQ(e.target.value)} placeholder="חיפוש שם סוג ציוד..."
            className="w-full pr-10 pl-4 py-2.5 rounded-xl border border-gray-200 text-sm placeholder-gray-400 bg-white focus:outline-none focus:border-kkl-green focus:ring-1 focus:ring-kkl-green" />
        </div>
        <select value={fGrp} onChange={e => setFGrp(e.target.value)} className="px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-600 bg-white focus:outline-none focus:border-kkl-green cursor-pointer">
          <option value="all">כל הקבוצות</option>
          {groups.map(g => <option key={g} value={g}>{g}</option>)}
        </select>
        <select value={fStat} onChange={e => setFStat(e.target.value)} className="px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-600 bg-white focus:outline-none focus:border-kkl-green cursor-pointer">
          <option value="all">כל הסטטוסים</option>
          <option value="active">פעיל</option>
          <option value="no_rate">חסר תעריף</option>
        </select>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="bg-gray-50 border-b border-gray-200 hidden md:grid grid-cols-12 gap-2 px-4 py-3">
{['שם סוג ציוד','קבוצה','תעריף שעתי','תעריף לינה',' לילה','עודכן','סטטוס',''].map((h, i) => (
            <div key={i} className={`text-right text-xs font-semibold text-gray-500 uppercase tracking-wider ${i===2||i===3||i===4||i===5||i===6?'text-center':''} ${i===0?'col-span-4':i===1?'col-span-2':'col-span-1'}`}>{h}</div>
          ))}
        </div>

        {filtered.map(t => (
          <div key={t.id} className={`grid grid-cols-12 gap-2 px-4 py-3 border-b border-gray-100 items-center ${!t.hourly_rate ? 'bg-amber-50' : ''}`}>
            <div className="col-span-4 font-semibold text-gray-900 text-sm">{t.name}</div>
            <div className="col-span-2">
              {t.category_group && <span className={`text-xs px-2 py-0.5 rounded-md font-medium ${gc(t.category_group)}`}>{t.category_group}</span>}
            </div>
            <div className="col-span-1 text-center">
              {editing === t.id
                ? <input type="number" value={eRate} onChange={e => setERate(e.target.value)} placeholder={String(t.hourly_rate || '')}
                    className="w-full text-center border border-kkl-green rounded-lg px-1 py-1 text-xs focus:outline-none" />
                : t.hourly_rate
? <span className="font-bold text-kkl-green">{t.hourly_rate}</span>
                  : <button onClick={() => { setEdit(t.id); setERate(''); setENight(''); }}
                      className="px-2 py-1 rounded-lg border border-amber-300 text-xs font-semibold text-amber-600 hover:bg-amber-50">הגדר</button>}
            </div>
            <div className="col-span-1 text-center">
              {editing === t.id
                ? <input type="number" value={eNight} onChange={e => setENight(e.target.value)} placeholder={String(t.overnight_rate || '')}
                    className="w-full text-center border border-kkl-green rounded-lg px-1 py-1 text-xs focus:outline-none" />
: <span className="text-sm text-gray-600">{t.overnight_rate ? `${t.overnight_rate}` : '—'}</span>}
            </div>
            <div className="col-span-1 text-center">{t.night_guard ? <Moon className="w-4 h-4 text-blue-500 mx-auto" /> : <span className="text-gray-200 text-xs">—</span>}</div>
            <div className="col-span-1 text-center text-xs text-gray-400">{t.updated_at ? new Date(t.updated_at).toLocaleDateString('he-IL') : '—'}</div>
            <div className="col-span-1 text-center">
              <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-bold ${t.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                {t.is_active ? 'פעיל' : 'כבוי'}
              </span>
            </div>
            <div className="col-span-1 flex items-center justify-end gap-1">
              {editing === t.id
                ? <><button onClick={() => save(t)} className="p-1 text-kkl-green hover:bg-green-50 rounded-lg"><Check className="w-4 h-4" /></button>
                     <button onClick={() => setEdit(null)} className="p-1 text-gray-400 hover:bg-gray-50 rounded-lg"><X className="w-4 h-4" /></button></>
                : <button onClick={() => { setEdit(t.id); setERate(''); setENight(''); }} className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg">
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>}
            </div>
          </div>
        ))}
        {filtered.length === 0 && <div className="text-center py-10 text-gray-400 text-sm">לא נמצאו סוגי ציוד</div>}
      </div>
    </div>
  );
};

// Tab 4: Rotation 
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
    if (!r.is_available) return { label: 'לא זמין', cls: 'bg-red-50 text-red-600' };
    if (r.rotation_position === 1) return { label: 'הבא בתור', cls: 'bg-green-100 text-green-700' };
    return { label: `תור ${r.rotation_position}`, cls: 'bg-blue-50 text-blue-600' };
  };

  return (
    <div>
      {noArea.length > 0 && (
        <div className="flex items-center justify-between bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 mb-4 text-sm text-amber-700">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span><strong>{noArea.length} ספקים ללא אזור שירות</strong> — לא ייכנסו לסבב הוגן</span>
          </div>
          <button className="px-3 py-1 rounded-lg border border-amber-300 text-xs font-semibold text-amber-600 hover:bg-amber-100 transition-colors">
            תיקון
          </button>
        </div>
      )}
      <div className="flex gap-3 mb-4 items-center flex-wrap">
        <select value={fReg} onChange={e => { setFReg(e.target.value); setFA('all'); }} className="px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-600 bg-white focus:outline-none focus:border-kkl-green cursor-pointer">
          <option value="all">כל המרחבים</option>
          {regions.map(r => <option key={r.id} value={String(r.id)}>{r.name}</option>)}
        </select>
        <select value={fArea} onChange={e => setFA(e.target.value)} className="px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-600 bg-white focus:outline-none focus:border-kkl-green cursor-pointer">
          <option value="all">כל האזורים</option>
          {filtAreas.map(a => <option key={a.id} value={String(a.id)}>{a.name}</option>)}
        </select>
        <select value={fType} onChange={e => setFT(e.target.value)} className="px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-600 bg-white focus:outline-none focus:border-kkl-green cursor-pointer">
          <option value="all">כל סוגי הציוד</option>
          {types.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <button onClick={reload} className="flex items-center gap-1.5 px-3 py-2.5 border border-gray-200 rounded-xl text-sm text-gray-600 hover:bg-gray-50 transition-colors">
          <RefreshCw className="w-4 h-4" /> רענן
        </button>
      </div>

      <div className="space-y-4">
        {Object.entries(byArea).map(([aId, aRots]) => {
          const area = areas.find(a => a.id === Number(aId));
          const region = regions.find(r => r.id === area?.region_id);
          const byCat = aRots.reduce((acc, r) => { const k = r.category_name || '?'; if (!acc[k]) acc[k] = []; acc[k].push(r); return acc; }, {} as Record<string, Rotation[]>);
          return (
            <div key={aId}>
              <div className="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
                <MapPin className="w-4 h-4 text-kkl-green" />
                {area?.name}
                <span className="bg-blue-50 text-blue-600 text-xs px-2 py-0.5 rounded-full">{region?.name}</span>
                <span className="text-xs text-gray-400 font-normal mr-auto">{aRots.length} ספקים</span>
              </div>
              <div className="bg-white rounded-xl border border-gray-200 mb-3 overflow-hidden">
                {Object.entries(byCat).map(([cat, catRots]) => (
                  <div key={cat} className="border-t border-gray-50 first:border-0">
                    <div className="bg-gray-50 px-4 py-2.5 border-b border-gray-200 flex justify-between items-center">
                      <span className={`text-xs px-2 py-0.5 rounded-md font-medium ${gc(cat)}`}>{cat}</span>
                      <span className="text-xs text-gray-400">{catRots.length} ספקים</span>
                    </div>
                    <div className="hidden md:grid grid-cols-12 gap-2 px-5 py-2 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
                      <div className="col-span-1 text-center">תור</div><div className="col-span-3">ספק</div>
                      <div className="col-span-2 text-center">הזמנות</div><div className="col-span-2 text-center">דחיות</div>
                      <div className="col-span-2 text-center">תגובה ממוצעת</div><div className="col-span-2 text-center">סטטוס</div>
                    </div>
                    {catRots.sort((a, b) => (a.rotation_position||99)-(b.rotation_position||99)).map(r => {
                      const st = getSt(r);
                      return (
                        <div key={r.id} className={`grid grid-cols-12 gap-2 px-5 py-2.5 border-t border-gray-50 items-center ${r.rotation_position===1 ? 'bg-green-50' : ''}`}>
                          <div className="col-span-1 text-center font-bold text-gray-500 text-xs">{r.rotation_position||'?'}</div>
                          <div className="col-span-3 font-semibold text-gray-900 text-xs truncate">{r.supplier_name||`ספק ${r.supplier_id}`}</div>
                          <div className="col-span-2 text-center text-xs text-gray-600">{r.total_assignments||0}</div>
                          <div className="col-span-2 text-center text-xs text-gray-600">{r.rejection_count||0}</div>
                          <div className="col-span-2 text-center text-xs text-gray-400">{r.avg_response_time_hours?`${r.avg_response_time_hours.toFixed(1)} שעות`:'—'}</div>
                          <div className="col-span-2 flex justify-center">
                            <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${st.cls}`}>{st.label}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
        {Object.keys(byArea).length === 0 && <div className="text-center py-12 text-gray-400 text-sm">לא נמצאו נתוני סבב</div>}
      </div>
    </div>
  );
};

// Main 
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

  const tabs: { id: TabType; label: string; icon: React.ReactNode; count?: number }[] = [
    { id: 'suppliers', label: 'ספקים',              icon: <Truck className="w-3.5 h-3.5" />,     count: suppliers.filter(s=>s.is_active).length },
    { id: 'equipment', label: 'ציוד ספקים',         icon: <Wrench className="w-3.5 h-3.5" />,    count: equipment.length },
    { id: 'pricing',   label: 'סוגי ציוד ותעריפים', icon: <DollarSign className="w-3.5 h-3.5" />, count: eqTypes.length },
    { id: 'rotation',  label: 'סבב הוגן',            icon: <RotateCcw className="w-3.5 h-3.5" />, count: rotations.filter(r=>r.is_active).length },
  ];

  if (loading) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center" dir="rtl">
      <div className="flex flex-col items-center gap-3">
        <RefreshCw className="w-8 h-8 animate-spin text-kkl-green" />
        <span className="text-sm text-gray-500">טוען נתונים...</span>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50" dir="rtl">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Back */}
        <button onClick={() => navigate('/settings')} className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-6 transition-colors">
          <ArrowRight className="w-4 h-4" /> חזרה להגדרות
        </button>

        {/* Header + CTA */}
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">ספקים וציוד</h1>
            <p className="text-sm text-gray-500 mt-1">ספקים, ציוד, סוגי כלים, תעריפים וסבב הוגן</p>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={() => setShowSM(true)}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-gray-300 text-gray-600 text-sm font-semibold hover:bg-gray-50 transition-colors">
              <Plus className="w-4 h-4" /> ספק חדש
            </button>
            <button onClick={() => setShowEM(true)}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-kkl-green text-white text-sm font-semibold hover:bg-kkl-green-dark transition-colors">
              <Plus className="w-4 h-4" /> הוסף כלי
            </button>
          </div>
        </div>

        {/* Stats */}
        <StatsBar suppliers={suppliers} equipment={equipment} rotations={rotations} />

        {/* Tabs */}
        <div className="flex gap-1 p-1 bg-white rounded-xl border border-gray-200 mb-5">
          {tabs.map(tab => (
            <button key={tab.id} onClick={() => switchTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer border-none ${
                activeTab === tab.id
                  ? 'font-semibold bg-kkl-green text-white'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100 bg-transparent'
              }`}>
              {tab.icon}
              {tab.label}
              {tab.count !== undefined && (
                <span className={`text-xs font-bold rounded-full px-2 py-0.5 ${activeTab === tab.id ? 'bg-white/25 text-white' : 'bg-gray-100 text-gray-500'}`}>
                  {tab.count.toLocaleString()}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Tab content */}
        {activeTab === 'suppliers' && <SuppliersTab suppliers={suppliers} setSuppliers={setSuppliers} equipment={equipment} regions={regions} areas={areas} onAddEq={() => setShowEM(true)} />}
        {activeTab === 'equipment' && <EquipmentTab equipment={equipment} setEquipment={setEquipment} suppliers={suppliers} eqTypes={eqTypes} regions={regions} />}
        {activeTab === 'pricing'   && <PricingTab eqTypes={eqTypes} setEqTypes={setEqTypes} />}
        {activeTab === 'rotation'  && <RotationTab rotations={rotations} regions={regions} areas={areas} reload={reload} />}
      </div>

      {showSM && <SupplierModal onClose={() => setShowSM(false)} onSaved={() => { setShowSM(false); reload(); (window as any).showToast?.('ספק נוצר בהצלחה','success'); }} />}
      {showEM && <EquipmentModal onClose={() => setShowEM(false)} onSaved={() => { setShowEM(false); reload(); (window as any).showToast?.('כלי נוסף בהצלחה','success'); }} />}
      {showTM && <EquipmentTypeModal onClose={() => setShowTM(false)} onSaved={() => { setShowTM(false); reload(); (window as any).showToast?.('סוג ציוד נוצר','success'); }} />}
    </div>
  );
};

export default SupplierSettings;
