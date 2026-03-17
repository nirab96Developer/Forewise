
// src/pages/Equipment/EquipmentInventory.tsx
// מלאי כלים — כרטיסי ספקים עם פירוט כלים
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight, Search, Truck, DollarSign, Eye, MapPin,
  Package, Building2, ChevronDown, ChevronUp, Phone, User, Wrench
} from 'lucide-react';
import api from '../../services/api';
import UnifiedLoader from '../../components/common/UnifiedLoader';

interface Equipment {
  id: number;
  code: string;
  name: string;
  license_plate: string;
  equipment_type: string;
  equipment_type_id?: number;
  supplier_id: number;
  supplier_name?: string;
  hourly_rate?: number;
  daily_rate?: number;
  status?: string;
  is_active: boolean;
}

interface Supplier {
  id: number;
  name: string;
  contact_name?: string;
  phone?: string;
  contact_phone?: string;
  email?: string;
  region_id?: number;
  area_id?: number;
  region_name?: string;
  area_name?: string;
  rating?: number;
  is_active: boolean;
}

type ViewMode = 'suppliers' | 'grid';

const TYPE_COLORS: Record<string, string> = {
  'מחפרון': 'bg-blue-100 text-blue-700',
  'טרקטור': 'bg-green-100 text-green-700',
  'מרסקת': 'bg-orange-100 text-orange-700',
  'שופל': 'bg-purple-100 text-purple-700',
  'מפלסת': 'bg-cyan-100 text-cyan-700',
  'מכבש': 'bg-red-100 text-red-700',
  'יעה': 'bg-amber-100 text-amber-700',
  'מחפר': 'bg-indigo-100 text-indigo-700',
};

function getTypeColor(name: string): string {
  for (const [key, cls] of Object.entries(TYPE_COLORS)) {
    if (name?.includes(key)) return cls;
  }
  return 'bg-gray-100 text-gray-700';
}

const EquipmentInventory: React.FC = () => {
  const navigate = useNavigate();
  const [equipment, setEquipment] = useState<Equipment[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState<ViewMode>('suppliers');
  const [expandedSuppliers, setExpandedSuppliers] = useState<Set<number>>(new Set());
  const [selectedRegion, setSelectedRegion] = useState<string>('all');

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [eqRes, supRes] = await Promise.all([
        api.get('/equipment', { params: { page_size: 500 } }),
        api.get('/suppliers', { params: { page_size: 200 } })
      ]);
      const eqData = eqRes.data?.items || eqRes.data || [];
      const supData = supRes.data?.items || supRes.data || [];
      setEquipment(Array.isArray(eqData) ? eqData : []);
      setSuppliers(Array.isArray(supData) ? supData : []);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleSupplier = (id: number) => {
    setExpandedSuppliers(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const expandAll = () => {
    setExpandedSuppliers(new Set(suppliers.map(s => s.id)));
  };

  // Group equipment by supplier
  const bySupplier = equipment.reduce((acc, eq) => {
    const sid = eq.supplier_id || 0;
    if (!acc[sid]) acc[sid] = [];
    acc[sid].push(eq);
    return acc;
  }, {} as Record<number, Equipment[]>);

  // Get unique regions from suppliers
  const regions = [...new Set(suppliers.map(s => s.region_name).filter(Boolean))] as string[];

  // Filter
  const filteredSuppliers = suppliers
    .filter(s => {
      if (selectedRegion !== 'all' && s.region_name !== selectedRegion) return false;
      if (!searchTerm) return true;
      const term = searchTerm.toLowerCase();
      const supplierMatch = s.name?.toLowerCase().includes(term);
      const eqMatch = (bySupplier[s.id] || []).some(eq =>
        eq.license_plate?.toLowerCase().includes(term) ||
        eq.name?.toLowerCase().includes(term) ||
        eq.equipment_type?.toLowerCase().includes(term)
      );
      return supplierMatch || eqMatch;
    })
    .sort((a, b) => (bySupplier[b.id]?.length || 0) - (bySupplier[a.id]?.length || 0));

  const filteredEquipment = equipment.filter(eq => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return eq.name?.toLowerCase().includes(term) ||
      eq.license_plate?.toLowerCase().includes(term) ||
      eq.supplier_name?.toLowerCase().includes(term) ||
      eq.equipment_type?.toLowerCase().includes(term);
  });

  // Stats
  const activeCount = equipment.filter(e => e.is_active).length;
  const supplierCount = Object.keys(bySupplier).length;
  const typesSet = new Set(equipment.map(e => e.equipment_type).filter(Boolean));

  if (loading) return <UnifiedLoader size="full" />;

  return (
    <div className="min-h-screen bg-gray-50" dir="rtl">
      <div className="max-w-7xl mx-auto px-4 py-6">

        {/* Header */}
        <div className="mb-6">
          <button onClick={() => navigate(-1)} className="text-emerald-600 hover:text-emerald-700 flex items-center gap-1 mb-3 text-sm font-medium">
            <ArrowRight className="w-4 h-4" /> חזרה
          </button>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-green-600 rounded-2xl flex items-center justify-center shadow-lg shadow-emerald-200">
                <Package className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">מלאי כלים</h1>
                <p className="text-gray-500 text-sm">כלים לפי ספקים, מרחבים וסוגי ציוד</p>
              </div>
            </div>
          </div>
        </div>

        {/* KPI Row */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="text-xs text-gray-500 mb-1">סה"כ כלים</div>
            <div className="text-2xl font-bold text-gray-900">{equipment.length}</div>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="text-xs text-gray-500 mb-1">כלים פעילים</div>
            <div className="text-2xl font-bold text-emerald-600">{activeCount}</div>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="text-xs text-gray-500 mb-1">ספקים</div>
            <div className="text-2xl font-bold text-blue-600">{supplierCount}</div>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="text-xs text-gray-500 mb-1">סוגי ציוד</div>
            <div className="text-2xl font-bold text-purple-600">{typesSet.size || '—'}</div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1 relative">
              <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="חיפוש לפי שם ספק, מספר רישוי, סוג כלי..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pr-10 pl-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              />
            </div>
            <select
              value={selectedRegion}
              onChange={(e) => setSelectedRegion(e.target.value)}
              className="px-3 py-2.5 border border-gray-200 rounded-lg text-sm bg-white min-w-[140px]"
            >
              <option value="all">כל המרחבים</option>
              {regions.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
            <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('suppliers')}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${viewMode === 'suppliers' ? 'bg-white shadow-sm text-emerald-700' : 'text-gray-500'}`}
              >
                לפי ספק
              </button>
              <button
                onClick={() => setViewMode('grid')}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${viewMode === 'grid' ? 'bg-white shadow-sm text-emerald-700' : 'text-gray-500'}`}
              >
                כרטיסים
              </button>
            </div>
          </div>
        </div>

        {/* ═══════ SUPPLIER VIEW ═══════ */}
        {viewMode === 'suppliers' && (
          <div>
            <div className="flex justify-between items-center mb-3">
              <span className="text-sm text-gray-500">{filteredSuppliers.length} ספקים</span>
              <button onClick={expandAll} className="text-xs text-emerald-600 hover:underline">פתח הכל</button>
            </div>
            <div className="space-y-3">
              {filteredSuppliers.map(supplier => {
                const eqList = bySupplier[supplier.id] || [];
                const isExpanded = expandedSuppliers.has(supplier.id);
                if (eqList.length === 0) return null;

                const eqTypes = [...new Set(eqList.map(e => e.equipment_type || e.name).filter(Boolean))];

                return (
                  <div key={supplier.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                    {/* Supplier Header */}
                    <button
                      onClick={() => toggleSupplier(supplier.id)}
                      className="w-full px-5 py-4 flex items-center gap-4 hover:bg-gray-50 transition-colors"
                    >
                      {/* Avatar */}
                      <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center flex-shrink-0">
                        <span className="text-lg font-bold text-emerald-700">
                          {supplier.name?.charAt(0)}
                        </span>
                      </div>

                      {/* Info */}
                      <div className="flex-1 text-right min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-bold text-gray-900 truncate">{supplier.name}</span>
                          <span className="bg-emerald-100 text-emerald-700 text-xs font-bold px-2 py-0.5 rounded-full flex-shrink-0">
                            {eqList.length} כלים
                          </span>
                        </div>
                        <div className="flex items-center gap-3 text-xs text-gray-500 flex-wrap">
                          {(supplier.region_name || supplier.area_name) && (
                            <span className="flex items-center gap-1">
                              <MapPin className="w-3 h-3" />
                              {supplier.region_name}{supplier.area_name ? ` · ${supplier.area_name}` : ''}
                            </span>
                          )}
                          {supplier.contact_name && (
                            <span className="flex items-center gap-1">
                              <User className="w-3 h-3" />
                              {supplier.contact_name}
                            </span>
                          )}
                          {(supplier.phone || supplier.contact_phone) && (
                            <span className="flex items-center gap-1">
                              <Phone className="w-3 h-3" />
                              {supplier.phone || supplier.contact_phone}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Equipment type tags */}
                      <div className="hidden md:flex gap-1.5 flex-shrink-0 flex-wrap max-w-[250px] justify-end">
                        {eqTypes.slice(0, 3).map((t, i) => (
                          <span key={i} className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${getTypeColor(t)}`}>
                            {t}
                          </span>
                        ))}
                        {eqTypes.length > 3 && (
                          <span className="text-[10px] text-gray-400">+{eqTypes.length - 3}</span>
                        )}
                      </div>

                      {/* Chevron */}
                      <div className="flex-shrink-0">
                        {isExpanded ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
                      </div>
                    </button>

                    {/* Equipment List (expanded) */}
                    {isExpanded && (
                      <div className="border-t border-gray-100">
                        {/* Mobile: equipment type tags */}
                        <div className="md:hidden flex gap-1.5 flex-wrap px-5 pt-3">
                          {eqTypes.map((t, i) => (
                            <span key={i} className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${getTypeColor(t)}`}>
                              {t}
                            </span>
                          ))}
                        </div>

                        {/* Table header */}
                        <div className="hidden md:grid grid-cols-12 gap-2 px-5 py-2 bg-gray-50 text-xs font-medium text-gray-500">
                          <div className="col-span-2">מספר רישוי</div>
                          <div className="col-span-3">שם / סוג כלי</div>
                          <div className="col-span-2">סוג ציוד</div>
                          <div className="col-span-2">תעריף שעתי</div>
                          <div className="col-span-2">סטטוס</div>
                          <div className="col-span-1"></div>
                        </div>

                        {eqList.map(eq => (
                          <div
                            key={eq.id}
                            className="grid grid-cols-1 md:grid-cols-12 gap-2 px-5 py-3 border-t border-gray-50 hover:bg-gray-50/50 transition-colors items-center"
                          >
                            {/* Mobile layout */}
                            <div className="md:hidden flex items-center justify-between">
                              <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-slate-800 rounded-lg flex items-center justify-center">
                                  <Truck className="w-4 h-4 text-white" />
                                </div>
                                <div>
                                  <div className="font-bold text-gray-900">{eq.license_plate || eq.code}</div>
                                  <div className="text-xs text-gray-500">{eq.name || eq.equipment_type}</div>
                                </div>
                              </div>
                              <div className="text-left">
                                <div className="text-sm font-bold text-emerald-600">
                                  {eq.hourly_rate ? `₪${eq.hourly_rate}` : '—'}
                                </div>
                                <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${eq.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                                  {eq.is_active ? 'פעיל' : 'לא פעיל'}
                                </span>
                              </div>
                            </div>

                            {/* Desktop layout */}
                            <div className="hidden md:contents">
                              <div className="col-span-2 flex items-center gap-2">
                                <div className="w-8 h-8 bg-slate-800 rounded-lg flex items-center justify-center flex-shrink-0">
                                  <Truck className="w-3.5 h-3.5 text-white" />
                                </div>
                                <span className="font-mono font-bold text-gray-900 text-sm">{eq.license_plate || eq.code}</span>
                              </div>
                              <div className="col-span-3 text-sm text-gray-700 truncate">{eq.name || eq.equipment_type || '—'}</div>
                              <div className="col-span-2">
                                <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${getTypeColor(eq.equipment_type || eq.name || '')}`}>
                                  {eq.equipment_type || eq.name || '—'}
                                </span>
                              </div>
                              <div className="col-span-2 font-bold text-emerald-600 text-sm">
                                {eq.hourly_rate ? `₪${eq.hourly_rate.toLocaleString()}` : '—'}
                                {eq.daily_rate ? <span className="text-xs text-gray-400 font-normal mr-1">/ ₪{eq.daily_rate} יומי</span> : ''}
                              </div>
                              <div className="col-span-2">
                                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${eq.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                                  {eq.is_active ? 'פעיל' : 'לא פעיל'}
                                </span>
                              </div>
                              <div className="col-span-1 text-left">
                                <button
                                  onClick={(e) => { e.stopPropagation(); if (eq.id) navigate(`/equipment/${eq.id}`); }}
                                  className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-400 hover:text-emerald-600"
                                >
                                  <Eye className="w-4 h-4" />
                                </button>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ═══════ GRID VIEW ═══════ */}
        {viewMode === 'grid' && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredEquipment.length === 0 ? (
              <div className="col-span-full text-center py-12 text-gray-500">לא נמצאו כלים</div>
            ) : (
              filteredEquipment.map(eq => (
                <div key={eq.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
                  <div className="bg-slate-800 px-4 py-3 text-white flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Truck className="w-4 h-4 text-slate-300" />
                      <span className="font-bold tracking-wider">{eq.license_plate || eq.code}</span>
                    </div>
                    <button onClick={() => { if (eq.id) navigate(`/equipment/${eq.id}`); }} className="p-1.5 hover:bg-white/10 rounded-lg">
                      <Eye className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  <div className="p-4">
                    <div className="font-bold text-gray-900 mb-2">{eq.name || eq.equipment_type}</div>
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center gap-2 text-gray-600">
                        <Building2 className="w-3.5 h-3.5 text-gray-400" />
                        <span>{eq.supplier_name || '—'}</span>
                      </div>
                      <div className="flex items-center gap-2 text-gray-600">
                        <Wrench className="w-3.5 h-3.5 text-gray-400" />
                        <span className={`text-xs px-2 py-0.5 rounded-full ${getTypeColor(eq.equipment_type || eq.name || '')}`}>
                          {eq.equipment_type || eq.name || '—'}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <DollarSign className="w-3.5 h-3.5 text-emerald-500" />
                        <span className="font-bold text-emerald-600">{eq.hourly_rate ? `₪${eq.hourly_rate}/שעה` : '—'}</span>
                      </div>
                    </div>
                    <div className="mt-3 flex justify-between items-center">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${eq.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                        {eq.is_active ? 'פעיל' : 'לא פעיל'}
                      </span>
                      <span className="text-xs text-gray-400">#{eq.id}</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Summary Bar */}
        <div className="mt-8 bg-gradient-to-r from-emerald-500 to-green-600 rounded-xl p-5 text-white">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h3 className="font-bold mb-0.5">סיכום מלאי</h3>
              <p className="text-sm text-emerald-100">כל הכלים הרשומים במערכת</p>
            </div>
            <div className="flex gap-6 sm:gap-8">
              <div className="text-center">
                <div className="text-2xl font-bold">{equipment.length}</div>
                <div className="text-xs text-emerald-100">סה"כ כלים</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">{supplierCount}</div>
                <div className="text-xs text-emerald-100">ספקים</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">{activeCount}</div>
                <div className="text-xs text-emerald-100">פעילים</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">{typesSet.size || '—'}</div>
                <div className="text-xs text-emerald-100">סוגי ציוד</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EquipmentInventory;
