// src/pages/Settings/SupplierSettings.tsx
// ניהול ספקים — 4 טאבים מאוחדים
import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowRight, Truck, Wrench, DollarSign, RotateCcw,
  Search, Plus, Eye, EyeOff, ChevronDown, ChevronRight,
  MapPin, Phone, Mail, AlertCircle, Moon, Edit2, Check, X,
  RefreshCw
} from 'lucide-react';
import api from '../../services/api';
import SupplierModal from '../../components/suppliers/SupplierModal';
import EquipmentModal from '../../components/suppliers/EquipmentModal';
import EquipmentTypeModal from '../../components/suppliers/EquipmentTypeModal';

// ─── Types ───────────────────────────────────────────────────────────────────

interface Supplier {
  id: number; code?: string; name: string; tax_id?: string;
  contact_name?: string; phone?: string; email?: string;
  address?: string; region_id?: number; area_id?: number;
  region_name?: string; area_name?: string;
  is_active: boolean; equipment_count?: number;
  active_area_ids?: number[];
}

interface EqItem {
  id: number; name: string; license_plate: string;
  equipment_type: string; supplier_id: number; supplier_name?: string;
  hourly_rate?: number; overnight_rate?: number;
  night_guard?: boolean; is_active: boolean; status?: string;
}

interface EqType {
  id: number; name: string; category_id?: number; category?: string;
  hourly_rate?: number; overnight_rate?: number; night_guard?: boolean;
  is_active: boolean; updated_at?: string;
}

interface Rotation {
  id: number; supplier_id: number; supplier_name?: string;
  area_id?: number; area_name?: string; region_name?: string;
  equipment_category_id?: number; category_name?: string;
  rotation_position: number; total_assignments: number;
  rejection_count: number; avg_response_time_hours?: number;
  is_active: boolean; is_available: boolean;
  unavailable_until?: string; priority_score?: number;
}

interface Region { id: number; name: string; }
interface Area { id: number; name: string; region_id: number; }

type TabType = 'suppliers' | 'equipment' | 'pricing' | 'rotation';

// ─── Helpers ─────────────────────────────────────────────────────────────────

const TYPE_COLORS: Record<string, string> = {
  'מחפרון': 'bg-blue-100 text-blue-700',
  'מחפר': 'bg-blue-100 text-blue-700',
  'יעה': 'bg-green-100 text-green-700',
  'טרקטור': 'bg-yellow-100 text-yellow-700',
  'מרסקת': 'bg-orange-100 text-orange-700',
  'מכבש': 'bg-purple-100 text-purple-700',
  'שופל': 'bg-red-100 text-red-700',
  'מפלסת': 'bg-pink-100 text-pink-700',
  'משאית': 'bg-cyan-100 text-cyan-700',
};
const getTypeColor = (n: string) => {
  for (const [k, c] of Object.entries(TYPE_COLORS)) if (n?.includes(k)) return c;
  return 'bg-gray-100 text-gray-600';
};

// ─── Tab 1: Suppliers ─────────────────────────────────────────────────────────

const SuppliersTab: React.FC<{ onAdd: () => void }> = ({ onAdd }) => {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterRegion, setFilterRegion] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [regions, setRegions] = useState<Region[]>([]);
  const [expanded, setExpanded] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [sRes, rRes] = await Promise.all([
        api.get('/suppliers', { params: { page_size: 500 } }),
        api.get('/regions').catch(() => ({ data: [] })),
      ]);
      setSuppliers(sRes.data?.items || sRes.data || []);
      setRegions(rRes.data?.items || rRes.data || []);
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const toggle = async (s: Supplier) => {
    await api.patch(`/suppliers/${s.id}/toggle-active`);
    setSuppliers(prev => prev.map(x => x.id === s.id ? { ...x, is_active: !x.is_active } : x));
  };

  const filtered = suppliers.filter(s => {
    const q = search.toLowerCase();
    if (q && !s.name.toLowerCase().includes(q) && !s.contact_name?.toLowerCase().includes(q) && !s.phone?.includes(q)) return false;
    if (filterRegion !== 'all' && String(s.region_id) !== filterRegion) return false;
    if (filterStatus === 'active' && !s.is_active) return false;
    if (filterStatus === 'inactive' && s.is_active) return false;
    return true;
  });

  return (
    <div>
      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-3 mb-4">
        <div className="relative flex-1">
          <Search className="absolute right-3 top-2.5 w-4 h-4 text-gray-400" />
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="חיפוש לפי שם, איש קשר, טלפון..."
            className="w-full pr-9 pl-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500" />
        </div>
        <select value={filterRegion} onChange={e => setFilterRegion(e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm">
          <option value="all">כל המרחבים</option>
          {regions.map(r => <option key={r.id} value={String(r.id)}>{r.name}</option>)}
        </select>
        <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm">
          <option value="all">כל הסטטוסים</option>
          <option value="active">פעילים</option>
          <option value="inactive">לא פעילים</option>
        </select>
        <button onClick={onAdd}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700">
          <Plus className="w-4 h-4" /> ספק חדש
        </button>
      </div>

      <div className="text-xs text-gray-500 mb-2">{filtered.length} ספקים</div>

      {loading ? (
        <div className="flex justify-center py-12"><RefreshCw className="w-6 h-6 animate-spin text-green-600" /></div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {/* Header */}
          <div className="hidden md:grid grid-cols-12 gap-2 px-4 py-2.5 bg-gray-50 text-xs font-medium text-gray-500 border-b">
            <div className="col-span-3">שם ספק</div>
            <div className="col-span-2">ח.פ / כתובת</div>
            <div className="col-span-2">מרחב / אזור</div>
            <div className="col-span-2">איש קשר</div>
            <div className="col-span-1 text-center">כלים</div>
            <div className="col-span-1 text-center">סטטוס</div>
            <div className="col-span-1"></div>
          </div>

          {filtered.map(s => (
            <div key={s.id} className={`border-t border-gray-50 ${!s.is_active ? 'opacity-60' : ''}`}>
              <div
                className="grid grid-cols-12 gap-2 px-4 py-3 hover:bg-gray-50 cursor-pointer items-center"
                onClick={() => setExpanded(expanded === s.id ? null : s.id)}
              >
                <div className="col-span-3 flex items-center gap-2">
                  <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <span className="text-sm font-bold text-green-700">{s.name[0]}</span>
                  </div>
                  <span className="font-medium text-gray-900 text-sm truncate">{s.name}</span>
                </div>
                <div className="col-span-2 text-xs text-gray-500">{s.tax_id || '—'}</div>
                <div className="col-span-2 text-xs text-gray-600">
                  {s.region_name && <div>{s.region_name}</div>}
                  {s.area_name && <div className="text-gray-400">{s.area_name}</div>}
                </div>
                <div className="col-span-2 text-xs">
                  {s.contact_name && <div className="text-gray-700">{s.contact_name}</div>}
                  {s.phone && <div className="text-gray-400">{s.phone}</div>}
                </div>
                <div className="col-span-1 text-center">
                  <span className="text-xs font-bold text-green-700">{s.equipment_count ?? '—'}</span>
                </div>
                <div className="col-span-1 flex justify-center">
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${s.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                    {s.is_active ? 'פעיל' : 'לא פעיל'}
                  </span>
                </div>
                <div className="col-span-1 flex justify-end">
                  {expanded === s.id ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
                </div>
              </div>

              {/* Expanded details */}
              {expanded === s.id && (
                <div className="px-4 pb-4 bg-gray-50 border-t border-gray-100">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
                    {s.email && (
                      <div className="flex items-center gap-2 text-sm">
                        <Mail className="w-4 h-4 text-gray-400" />
                        <a href={`mailto:${s.email}`} className="text-blue-600 hover:underline">{s.email}</a>
                      </div>
                    )}
                    {s.phone && (
                      <div className="flex items-center gap-2 text-sm">
                        <Phone className="w-4 h-4 text-gray-400" />
                        <a href={`tel:${s.phone}`} className="text-blue-600 hover:underline">{s.phone}</a>
                      </div>
                    )}
                    {s.address && (
                      <div className="flex items-center gap-2 text-sm">
                        <MapPin className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-600">{s.address}</span>
                      </div>
                    )}
                    {(s.active_area_ids?.length ?? 0) > 0 && (
                      <div className="text-xs text-gray-500">
                        אזורי שירות: <span className="font-medium">{s.active_area_ids?.length} אזורים</span>
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2 mt-3">
                    <button
                      onClick={() => toggle(s)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                        s.is_active
                          ? 'border-red-200 text-red-600 hover:bg-red-50'
                          : 'border-green-200 text-green-600 hover:bg-green-50'
                      }`}
                    >
                      {s.is_active ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                      {s.is_active ? 'השבת ספק' : 'הפעל ספק'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}

          {filtered.length === 0 && !loading && (
            <div className="text-center py-12 text-gray-400 text-sm">לא נמצאו ספקים</div>
          )}
        </div>
      )}
    </div>
  );
};

// ─── Tab 2: Equipment ─────────────────────────────────────────────────────────

const EquipmentTab: React.FC<{ onAdd: () => void }> = ({ onAdd }) => {
  const [equipment, setEquipment] = useState<EqItem[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [eRes, sRes] = await Promise.all([
        api.get('/equipment', { params: { limit: 500, include_supplier: true } }),
        api.get('/suppliers', { params: { page_size: 500 } }),
      ]);
      setEquipment(eRes.data?.items || []);
      setSuppliers(sRes.data?.items || sRes.data || []);
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const toggle = async (eq: EqItem) => {
    await api.patch(`/equipment/${eq.id}/toggle-active`);
    setEquipment(prev => prev.map(x => x.id === eq.id ? { ...x, is_active: !x.is_active } : x));
  };

  const types = [...new Set(equipment.map(e => e.equipment_type).filter(Boolean))].sort();

  const filtered = equipment.filter(e => {
    if (search && !e.license_plate?.toLowerCase().includes(search.toLowerCase()) &&
        !e.name?.toLowerCase().includes(search.toLowerCase())) return false;
    if (filterType !== 'all' && e.equipment_type !== filterType) return false;
    if (filterStatus === 'active' && !e.is_active) return false;
    if (filterStatus === 'inactive' && e.is_active) return false;
    if (filterStatus === 'no_rate' && e.hourly_rate) return false;
    if (filterStatus === 'night' && !e.night_guard) return false;
    return true;
  });

  const bySupplier = filtered.reduce((acc, eq) => {
    const sid = eq.supplier_id || 0;
    if (!acc[sid]) acc[sid] = [];
    acc[sid].push(eq);
    return acc;
  }, {} as Record<number, EqItem[]>);

  const supplierList = suppliers.filter(s => bySupplier[s.id]);

  const toggleExpand = (id: number) => {
    setExpanded(prev => {
      const n = new Set(prev);
      n.has(id) ? n.delete(id) : n.add(id);
      return n;
    });
  };

  return (
    <div>
      <div className="flex flex-col md:flex-row gap-3 mb-4">
        <div className="relative flex-1">
          <Search className="absolute right-3 top-2.5 w-4 h-4 text-gray-400" />
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="חיפוש לפי מספר רישוי..."
            className="w-full pr-9 pl-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500" />
        </div>
        <select value={filterType} onChange={e => setFilterType(e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm">
          <option value="all">כל סוגי הציוד</option>
          {types.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm">
          <option value="all">כל הסטטוסים</option>
          <option value="active">פעילים</option>
          <option value="inactive">לא פעילים</option>
          <option value="no_rate">חסר תעריף</option>
          <option value="night">שמירת לילה</option>
        </select>
        <button onClick={onAdd}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700">
          <Plus className="w-4 h-4" /> הוסף כלי
        </button>
      </div>

      <div className="text-xs text-gray-500 mb-2">{supplierList.length} ספקים · {filtered.length} כלים</div>

      {loading ? (
        <div className="flex justify-center py-12"><RefreshCw className="w-6 h-6 animate-spin text-green-600" /></div>
      ) : (
        <div className="space-y-2">
          {supplierList.map(s => {
            const eqList = bySupplier[s.id] || [];
            const isOpen = expanded.has(s.id);
            return (
              <div key={s.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <button
                  onClick={() => toggleExpand(s.id)}
                  className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 bg-green-100 rounded-lg flex items-center justify-center">
                      <span className="font-bold text-green-700 text-sm">{s.name[0]}</span>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-gray-900">{s.name}</div>
                      <div className="text-xs text-gray-400">{s.area_name || s.region_name}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-bold text-green-700 bg-green-50 px-2 py-0.5 rounded-full">{eqList.length} כלים</span>
                    {isOpen ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
                  </div>
                </button>

                {isOpen && (
                  <div>
                    {/* Table header */}
                    <div className="hidden md:grid grid-cols-12 gap-2 px-5 py-2 bg-gray-50 text-xs font-medium text-gray-500 border-t">
                      <div className="col-span-2">רישוי</div>
                      <div className="col-span-3">סוג ציוד</div>
                      <div className="col-span-2 text-center">תעריף/שעה</div>
                      <div className="col-span-2 text-center">תעריף לינה</div>
                      <div className="col-span-1 text-center">☽</div>
                      <div className="col-span-1 text-center">סטטוס</div>
                      <div className="col-span-1"></div>
                    </div>
                    {eqList.map(eq => (
                      <div key={eq.id}
                        className={`grid grid-cols-12 gap-2 px-5 py-2.5 border-t border-gray-50 items-center ${!eq.is_active ? 'opacity-50' : ''}`}
                      >
                        <div className="col-span-2 font-mono text-sm font-bold text-gray-800">{eq.license_plate || eq.name}</div>
                        <div className="col-span-3">
                          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${getTypeColor(eq.equipment_type || '')}`}>
                            {eq.equipment_type || '—'}
                          </span>
                        </div>
                        <div className="col-span-2 text-center text-sm font-semibold text-green-700">
                          {eq.hourly_rate ? `₪${Number(eq.hourly_rate).toLocaleString()}` : <span className="text-orange-400 text-xs">חסר</span>}
                        </div>
                        <div className="col-span-2 text-center text-sm text-gray-600">
                          {eq.overnight_rate ? `₪${Number(eq.overnight_rate).toLocaleString()}` : '—'}
                        </div>
                        <div className="col-span-1 text-center">
                          {eq.night_guard ? <Moon className="w-4 h-4 text-indigo-500 mx-auto" /> : <span className="text-gray-300 text-xs">—</span>}
                        </div>
                        <div className="col-span-1 text-center">
                          <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${eq.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-400'}`}>
                            {eq.is_active ? 'פעיל' : 'כבוי'}
                          </span>
                        </div>
                        <div className="col-span-1 text-left">
                          <button
                            onClick={() => toggle(eq)}
                            className="p-1 hover:bg-gray-100 rounded text-gray-400 hover:text-gray-600"
                            title={eq.is_active ? 'השבת' : 'הפעל'}
                          >
                            {eq.is_active ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
          {supplierList.length === 0 && !loading && (
            <div className="text-center py-12 text-gray-400 text-sm">לא נמצא ציוד</div>
          )}
        </div>
      )}
    </div>
  );
};

// ─── Tab 3: Pricing (equipment types + rates) ─────────────────────────────────

const PricingTab: React.FC<{ onAdd: () => void }> = ({ onAdd }) => {
  const [types, setTypes] = useState<EqType[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterCat, setFilterCat] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [editing, setEditing] = useState<number | null>(null);
  const [editRate, setEditRate] = useState('');
  const [editNight, setEditNight] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/equipment-types', { params: { page_size: 200 } });
      setTypes(res.data?.items || res.data || []);
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const categories = [...new Set(types.map(t => t.category).filter(Boolean))].sort() as string[];

  const filtered = types.filter(t => {
    if (filterCat !== 'all' && t.category !== filterCat) return false;
    if (filterStatus === 'active' && !t.is_active) return false;
    if (filterStatus === 'inactive' && t.is_active) return false;
    if (filterStatus === 'no_rate' && t.hourly_rate) return false;
    return true;
  });

  const saveRate = async (t: EqType) => {
    await api.put(`/equipment-types/${t.id}`, {
      hourly_rate: editRate ? Number(editRate) : t.hourly_rate,
      overnight_rate: editNight ? Number(editNight) : t.overnight_rate,
    });
    setTypes(prev => prev.map(x => x.id === t.id ? {
      ...x,
      hourly_rate: editRate ? Number(editRate) : x.hourly_rate,
      overnight_rate: editNight ? Number(editNight) : x.overnight_rate,
    } : x));
    setEditing(null);
  };

  return (
    <div>
      <div className="flex flex-col md:flex-row gap-3 mb-4">
        <select value={filterCat} onChange={e => setFilterCat(e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm">
          <option value="all">כל הקבוצות</option>
          {categories.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm">
          <option value="all">כל הסטטוסים</option>
          <option value="active">פעיל</option>
          <option value="inactive">לא פעיל</option>
          <option value="no_rate">חסר תעריף</option>
        </select>
        <button onClick={onAdd}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700">
          <Plus className="w-4 h-4" /> סוג ציוד חדש
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><RefreshCw className="w-6 h-6 animate-spin text-green-600" /></div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="hidden md:grid grid-cols-12 gap-2 px-4 py-2.5 bg-gray-50 text-xs font-medium text-gray-500 border-b">
            <div className="col-span-3">שם סוג ציוד</div>
            <div className="col-span-2">קבוצה</div>
            <div className="col-span-2 text-center">תעריף שעתי</div>
            <div className="col-span-2 text-center">תעריף לינה</div>
            <div className="col-span-1 text-center">☽</div>
            <div className="col-span-1 text-center">סטטוס</div>
            <div className="col-span-1"></div>
          </div>
          {filtered.map(t => (
            <div key={t.id}
              className={`grid grid-cols-12 gap-2 px-4 py-3 border-t border-gray-50 items-center ${!t.hourly_rate ? 'bg-orange-50/50' : ''}`}
            >
              <div className="col-span-3 font-medium text-gray-900 text-sm">{t.name}</div>
              <div className="col-span-2">
                <span className={`text-xs px-2 py-0.5 rounded-full ${getTypeColor(t.category || t.name)}`}>
                  {t.category || '—'}
                </span>
              </div>
              <div className="col-span-2 text-center">
                {editing === t.id ? (
                  <input type="number" value={editRate} onChange={e => setEditRate(e.target.value)}
                    placeholder={String(t.hourly_rate || '')}
                    className="w-full text-center border border-green-300 rounded px-2 py-1 text-sm" />
                ) : (
                  <span className={`font-bold text-sm ${t.hourly_rate ? 'text-green-700' : 'text-orange-400'}`}>
                    {t.hourly_rate ? `₪${t.hourly_rate}` : 'חסר'}
                  </span>
                )}
              </div>
              <div className="col-span-2 text-center">
                {editing === t.id ? (
                  <input type="number" value={editNight} onChange={e => setEditNight(e.target.value)}
                    placeholder={String(t.overnight_rate || '')}
                    className="w-full text-center border border-green-300 rounded px-2 py-1 text-sm" />
                ) : (
                  <span className="text-sm text-gray-600">{t.overnight_rate ? `₪${t.overnight_rate}` : '—'}</span>
                )}
              </div>
              <div className="col-span-1 text-center">
                {t.night_guard ? <Moon className="w-4 h-4 text-indigo-500 mx-auto" /> : <span className="text-gray-200">—</span>}
              </div>
              <div className="col-span-1 text-center">
                <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${t.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-400'}`}>
                  {t.is_active ? 'פעיל' : 'כבוי'}
                </span>
              </div>
              <div className="col-span-1 flex justify-end gap-1">
                {editing === t.id ? (
                  <>
                    <button onClick={() => saveRate(t)} className="p-1 text-green-600 hover:bg-green-50 rounded"><Check className="w-4 h-4" /></button>
                    <button onClick={() => setEditing(null)} className="p-1 text-gray-400 hover:bg-gray-50 rounded"><X className="w-4 h-4" /></button>
                  </>
                ) : (
                  <button onClick={() => { setEditing(t.id); setEditRate(''); setEditNight(''); }}
                    className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded">
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>
          ))}
          {filtered.length === 0 && (
            <div className="text-center py-8 text-gray-400 text-sm">לא נמצאו סוגי ציוד</div>
          )}
        </div>
      )}
    </div>
  );
};

// ─── Tab 4: Fair Rotation ─────────────────────────────────────────────────────

const RotationTab: React.FC = () => {
  const [rotations, setRotations] = useState<Rotation[]>([]);
  const [loading, setLoading] = useState(true);
  const [regions, setRegions] = useState<Region[]>([]);
  const [areas, setAreas] = useState<Area[]>([]);
  const [filterRegion, setFilterRegion] = useState('all');
  const [filterArea, setFilterArea] = useState('all');
  const [filterType, setFilterType] = useState('all');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [rRes, aRes, rotRes] = await Promise.all([
        api.get('/regions').catch(() => ({ data: [] })),
        api.get('/areas').catch(() => ({ data: [] })),
        api.get('/supplier-rotations', { params: { page_size: 500 } }),
      ]);
      setRegions(rRes.data?.items || rRes.data || []);
      setAreas(aRes.data?.items || aRes.data || []);
      const rots = rotRes.data?.items || rotRes.data || [];
      setRotations(Array.isArray(rots) ? rots : []);
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const noAreaSuppliers = rotations.filter(r => !r.area_id && r.is_active);

  const filteredAreas = areas.filter(a =>
    filterRegion === 'all' || regions.find(r => r.id === a.region_id && String(r.id) === filterRegion)
  );

  const types = [...new Set(rotations.map(r => r.category_name).filter(Boolean))].sort() as string[];

  const filtered = rotations.filter(r => {
    if (filterArea !== 'all' && String(r.area_id) !== filterArea) return false;
    if (filterType !== 'all' && r.category_name !== filterType) return false;
    return r.is_active && r.area_id;
  });

  const byArea = filtered.reduce((acc, r) => {
    const k = r.area_id!;
    if (!acc[k]) acc[k] = [];
    acc[k].push(r);
    return acc;
  }, {} as Record<number, Rotation[]>);

  const getRotStatus = (r: Rotation) => {
    if (!r.is_available) return { label: 'לא זמין', cls: 'bg-red-100 text-red-700' };
    if (r.rotation_position === 1) return { label: 'הבא בתור', cls: 'bg-green-100 text-green-700' };
    return { label: `תור ${r.rotation_position}`, cls: 'bg-blue-100 text-blue-700' };
  };

  return (
    <div>
      {noAreaSuppliers.length > 0 && (
        <div className="flex items-start gap-3 bg-orange-50 border border-orange-200 rounded-xl p-4 mb-4">
          <AlertCircle className="w-5 h-5 text-orange-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-orange-800">
            <span className="font-semibold">{noAreaSuppliers.length} ספקים ללא אזור שירות</span> — לא ייכנסו לסבב הוגן.
            יש לשייך אותם לאזורים בטאב "ספקים".
          </div>
        </div>
      )}

      <div className="flex flex-col md:flex-row gap-3 mb-4">
        <select value={filterRegion} onChange={e => { setFilterRegion(e.target.value); setFilterArea('all'); }}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm">
          <option value="all">כל המרחבים</option>
          {regions.map(r => <option key={r.id} value={String(r.id)}>{r.name}</option>)}
        </select>
        <select value={filterArea} onChange={e => setFilterArea(e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm">
          <option value="all">כל האזורים</option>
          {filteredAreas.map(a => <option key={a.id} value={String(a.id)}>{a.name}</option>)}
        </select>
        <select value={filterType} onChange={e => setFilterType(e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm">
          <option value="all">כל סוגי הציוד</option>
          {types.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <button onClick={load} className="flex items-center gap-1.5 px-3 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50">
          <RefreshCw className="w-4 h-4" /> רענן
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><RefreshCw className="w-6 h-6 animate-spin text-green-600" /></div>
      ) : (
        <div className="space-y-4">
          {Object.entries(byArea).map(([areaId, areaRots]) => {
            const area = areas.find(a => a.id === Number(areaId));
            const region = regions.find(r => r.id === area?.region_id);
            const byCategory = areaRots.reduce((acc, r) => {
              const k = r.category_name || '?';
              if (!acc[k]) acc[k] = [];
              acc[k].push(r);
              return acc;
            }, {} as Record<string, Rotation[]>);

            return (
              <div key={areaId} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <div className="px-4 py-3 bg-gray-50 border-b flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-green-600" />
                  <span className="font-semibold text-gray-900">{area?.name || `אזור ${areaId}`}</span>
                  <span className="text-xs text-gray-400">/ {region?.name}</span>
                  <span className="mr-auto text-xs text-gray-500">{areaRots.length} ספקים בסבב</span>
                </div>
                {Object.entries(byCategory).map(([cat, catRots]) => (
                  <div key={cat} className="border-t border-gray-50">
                    <div className="px-4 py-2 bg-gray-50/50">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${getTypeColor(cat)}`}>{cat}</span>
                    </div>
                    <div className="hidden md:grid grid-cols-12 gap-2 px-5 py-1.5 text-[10px] font-medium text-gray-400 border-t border-gray-50">
                      <div className="col-span-1 text-center">תור</div>
                      <div className="col-span-3">ספק</div>
                      <div className="col-span-2 text-center">הזמנות</div>
                      <div className="col-span-2 text-center">דחיות</div>
                      <div className="col-span-2 text-center">מענה ממוצע</div>
                      <div className="col-span-2 text-center">סטטוס</div>
                    </div>
                    {catRots
                      .sort((a, b) => (a.rotation_position || 99) - (b.rotation_position || 99))
                      .map(r => {
                        const st = getRotStatus(r);
                        return (
                          <div key={r.id} className="grid grid-cols-12 gap-2 px-5 py-2.5 border-t border-gray-50 items-center text-sm">
                            <div className="col-span-1 text-center font-bold text-gray-500">{r.rotation_position || '?'}</div>
                            <div className="col-span-3 font-medium text-gray-900 truncate">{r.supplier_name || `ספק ${r.supplier_id}`}</div>
                            <div className="col-span-2 text-center text-gray-600">{r.total_assignments || 0}</div>
                            <div className="col-span-2 text-center text-gray-600">{r.rejection_count || 0}</div>
                            <div className="col-span-2 text-center text-gray-500 text-xs">
                              {r.avg_response_time_hours ? `${r.avg_response_time_hours.toFixed(1)} שעות` : '—'}
                            </div>
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
          {Object.keys(byArea).length === 0 && (
            <div className="text-center py-12 text-gray-400 text-sm">לא נמצאו נתוני סבב</div>
          )}
        </div>
      )}
    </div>
  );
};

// ─── Main Component ───────────────────────────────────────────────────────────

const SupplierSettings: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const getInitialTab = (): TabType => {
    const t = searchParams.get('tab') as TabType;
    if (['suppliers', 'equipment', 'pricing', 'rotation'].includes(t)) return t;
    return 'suppliers';
  };
  const [activeTab, setActiveTab] = useState<TabType>(getInitialTab());

  const switchTab = (tab: TabType) => {
    setActiveTab(tab);
    setSearchParams({ tab });
  };

  // Modal state (passed to child tabs)
  const [showSupplierModal, setShowSupplierModal] = useState(false);
  const [showEquipmentModal, setShowEquipmentModal] = useState(false);
  const [showTypeModal, setShowTypeModal] = useState(false);

  const tabs: { id: TabType; label: string; icon: React.ReactNode }[] = [
    { id: 'suppliers', label: 'ספקים', icon: <Truck className="w-4 h-4" /> },
    { id: 'equipment', label: 'ציוד ספקים', icon: <Wrench className="w-4 h-4" /> },
    { id: 'pricing', label: 'סוגי ציוד ותעריפים', icon: <DollarSign className="w-4 h-4" /> },
    { id: 'rotation', label: 'סבב הוגן', icon: <RotateCcw className="w-4 h-4" /> },
  ];

  return (
    <div className="min-h-screen bg-gray-50" dir="rtl">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto">
          <button onClick={() => navigate('/settings')} className="flex items-center gap-1.5 text-sm text-green-600 hover:text-green-800 mb-3">
            <ArrowRight className="w-4 h-4" /> חזרה להגדרות
          </button>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">ספקים וציוד</h1>
              <p className="text-sm text-gray-500 mt-1">ניהול ספקים, ציוד, תמחור וסבב הוגן</p>
            </div>
          </div>
          {/* Tabs */}
          <div className="flex gap-1 mt-4 overflow-x-auto">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => switchTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                  activeTab === tab.id
                    ? 'bg-green-600 text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {tab.icon} {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        {activeTab === 'suppliers' && (
          <SuppliersTab onAdd={() => setShowSupplierModal(true)} />
        )}
        {activeTab === 'equipment' && (
          <EquipmentTab onAdd={() => setShowEquipmentModal(true)} />
        )}
        {activeTab === 'pricing' && (
          <PricingTab onAdd={() => setShowTypeModal(true)} />
        )}
        {activeTab === 'rotation' && <RotationTab />}
      </div>

      {/* Modals will be imported from /components/suppliers/ */}
      {showSupplierModal && (
        <SupplierModal
          onClose={() => setShowSupplierModal(false)}
          onSaved={() => { setShowSupplierModal(false); (window as any).showToast?.('ספק נוצר בהצלחה', 'success'); }}
        />
      )}
      {showEquipmentModal && (
        <EquipmentModal
          onClose={() => setShowEquipmentModal(false)}
          onSaved={() => { setShowEquipmentModal(false); (window as any).showToast?.('כלי נוסף בהצלחה', 'success'); }}
        />
      )}
      {showTypeModal && (
        <EquipmentTypeModal
          onClose={() => setShowTypeModal(false)}
          onSaved={() => { setShowTypeModal(false); (window as any).showToast?.('סוג ציוד נוצר בהצלחה', 'success'); }}
        />
      )}
    </div>
  );
};

export default SupplierSettings;
