
// src/pages/Settings/EquipmentCatalog.tsx
// קטלוג כלים + תעריפים — שני tabs, דף אחד
import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowRight, Wrench, Plus, Search, Edit, Trash2,
  CheckCircle, Save, X, Info, DollarSign,
  Clock, Shield, Layers, Edit2, History, AlertCircle,
} from 'lucide-react';
import api from '../../services/api';

// ─── Types ─────────────────────────────────────────────────────────────────

interface EquipmentCategory {
  id: number;
  name: string;
  code: string;
  description?: string;
  parent_category_id?: number;
  requires_license: boolean;
  license_type?: string;
  requires_certification: boolean;
  default_hourly_rate?: number;
  default_daily_rate?: number;
  maintenance_interval_hours?: number;
  maintenance_interval_days?: number;
  is_active: boolean;
}

interface EquipmentRateItem {
  id: number;
  name: string;
  hourly_rate: number | null;
  last_updated: string | null;
  updated_by: string | null;
  is_active: boolean;
}

interface RateHistoryItem {
  id: number;
  old_rate: number | null;
  new_rate: number | null;
  changed_by_name: string | null;
  reason: string | null;
  effective_date: string | null;
  created_at: string;
}

// ─── Helpers ────────────────────────────────────────────────────────────────

const fmtDate = (iso: string | null) => {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('he-IL');
};

const fmtRate = (r: number | null) =>
  r != null ? `₪${r.toLocaleString('he-IL', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—';

// ─── Toast ──────────────────────────────────────────────────────────────────

const Toast: React.FC<{ msg: string; ok: boolean; onClose: () => void }> = ({ msg, ok, onClose }) => (
  <div className={`fixed top-4 left-1/2 -translate-x-1/2 z-[2000] flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg text-white text-sm ${ok ? 'bg-green-600' : 'bg-red-600'}`}>
    {ok ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
    {msg}
    <button onClick={onClose} className="ml-2 opacity-70 hover:opacity-100"><X className="w-3 h-3" /></button>
  </div>
);

// ─── Tab: כרטיסים (Catalog) ─────────────────────────────────────────────────

const CatalogTab: React.FC = () => {
  const [categories, setCategories] = useState<EquipmentCategory[]>([]);
  // ratesByName: maps equipment type name → hourly_rate from equipment_types
  const [ratesByName, setRatesByName] = useState<Record<string, number | null>>({});
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingCategory, setEditingCategory] = useState<EquipmentCategory | null>(null);
  const [formData, setFormData] = useState({
    name: '', code: '', description: '',
    parent_category_id: null as number | null,
    requires_license: false, license_type: '',
    requires_certification: false,
    default_hourly_rate: 0, default_daily_rate: 0,
    maintenance_interval_hours: 0, maintenance_interval_days: 0,
    is_active: true,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const loadCategories = async () => {
    setLoading(true);
    try {
      const [catRes, ratesRes] = await Promise.all([
        api.get('/equipment-categories'),
        api.get('/settings/equipment-rates').catch(() => ({ data: [] })),
      ]);
      const data = catRes.data?.items || catRes.data || [];
      setCategories(Array.isArray(data) ? data : []);

      // Build name → hourly_rate lookup from equipment_types
      const lookup: Record<string, number | null> = {};
      const ratesArr: EquipmentRateItem[] = Array.isArray(ratesRes.data) ? ratesRes.data : [];
      for (const r of ratesArr) {
        lookup[r.name] = r.hourly_rate;
      }
      setRatesByName(lookup);
    } catch {
      setCategories([]);
    } finally {
      setLoading(false);
    }
  };

  // Helper: resolve the effective hourly rate for a category card.
  // First tries the exact-name match in equipment_types rates.
  // Falls back to category's own default_hourly_rate.
  const getEffectiveRate = (cat: EquipmentCategory): number | null => {
    const typeRate = ratesByName[cat.name];
    if (typeRate != null) return typeRate;
    return cat.default_hourly_rate ?? null;
  };

  useEffect(() => { loadCategories(); }, []);

  const handleOpenModal = (category?: EquipmentCategory) => {
    if (category) {
      setEditingCategory(category);
      setFormData({
        name: category.name, code: category.code,
        description: category.description || '',
        parent_category_id: category.parent_category_id || null,
        requires_license: category.requires_license,
        license_type: category.license_type || '',
        requires_certification: category.requires_certification,
        default_hourly_rate: category.default_hourly_rate || 0,
        default_daily_rate: category.default_daily_rate || 0,
        maintenance_interval_hours: category.maintenance_interval_hours || 0,
        maintenance_interval_days: category.maintenance_interval_days || 0,
        is_active: category.is_active,
      });
    } else {
      setEditingCategory(null);
      setFormData({
        name: '', code: '', description: '', parent_category_id: null,
        requires_license: false, license_type: '', requires_certification: false,
        default_hourly_rate: 0, default_daily_rate: 0,
        maintenance_interval_hours: 0, maintenance_interval_days: 0, is_active: true,
      });
    }
    setShowModal(true);
    setError('');
  };

  const handleSave = async () => {
    if (!formData.name.trim() || !formData.code.trim()) { setError('יש למלא שם וקוד'); return; }
    setSaving(true); setError('');
    try {
      if (editingCategory) {
        await api.put(`/equipment-categories/${editingCategory.id}`, formData);
      } else {
        await api.post('/equipment-categories', formData);
      }
      setShowModal(false);
      loadCategories();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'שגיאה בשמירת הקטגוריה');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('האם אתה בטוח שברצונך למחוק קטגוריה זו?')) return;
    try {
      await api.delete(`/equipment-categories/${id}`);
      loadCategories();
    } catch {
      alert('שגיאה במחיקת הקטגוריה');
    }
  };

  const toggleActive = async (category: EquipmentCategory) => {
    try {
      await api.patch(`/equipment-categories/${category.id}`, { is_active: !category.is_active });
      loadCategories();
    } catch { /* silent */ }
  };

  const getParentName = (parentId?: number) => {
    if (!parentId) return null;
    return categories.find(c => c.id === parentId)?.name;
  };

  const filteredCategories = (categories || []).filter(c =>
    c.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.code?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <>
      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-xl border border-kkl-border p-4">
          <div className="text-2xl font-bold text-kkl-green">{categories.length}</div>
          <div className="text-sm text-gray-500">סוגי כלים</div>
        </div>
        <div className="bg-white rounded-xl border border-kkl-border p-4">
          <div className="text-2xl font-bold text-green-600">{categories.filter(c => c.is_active).length}</div>
          <div className="text-sm text-gray-500">פעילים</div>
        </div>
        <div className="bg-white rounded-xl border border-kkl-border p-4">
          <div className="text-2xl font-bold text-blue-600">{categories.filter(c => c.requires_license).length}</div>
          <div className="text-sm text-gray-500">דורשים רישיון</div>
        </div>
        <div className="bg-white rounded-xl border border-kkl-border p-4">
          <div className="text-2xl font-bold text-orange-600">
            {categories.filter(c => { const r = getEffectiveRate(c); return !r || r === 0; }).length}
          </div>
          <div className="text-sm text-gray-500">ללא תעריף</div>
        </div>
      </div>

      {/* Search + New */}
      <div className="flex gap-3 mb-6">
        <div className="relative flex-1">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="חיפוש כלים..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pr-10 pl-4 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent bg-white"
          />
        </div>
        <button
          onClick={() => handleOpenModal()}
          className="px-4 py-2 bg-kkl-green text-white rounded-lg hover:bg-kkl-green-dark transition-colors flex items-center gap-2 whitespace-nowrap"
        >
          <Plus className="w-4 h-4" /> קטגוריה חדשה
        </button>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-full flex items-center justify-center py-12">
            <div className="relative">
          <div className="w-10 h-10 rounded-full border-[3px] border-emerald-200 border-t-emerald-500 animate-spin" style={{animationDuration:'0.9s'}} />
          <div className="absolute inset-0 flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 100" width="20" height="17">
                <defs>
                  <linearGradient id="ec1_t" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#1565c0"/><stop offset="100%" stopColor="#0097a7"/></linearGradient>
                  <linearGradient id="ec1_m" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#0097a7"/><stop offset="50%" stopColor="#2e7d32"/><stop offset="100%" stopColor="#66bb6a"/></linearGradient>
                  <linearGradient id="ec1_b" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#2e7d32"/><stop offset="40%" stopColor="#66bb6a"/><stop offset="100%" stopColor="#8B5e3c"/></linearGradient>
                </defs>
                <path d="M46 20 Q60 9 74 20" stroke="url(#ec1_t)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <path d="M30 47 Q42 34 60 43 Q78 34 90 47" stroke="url(#ec1_m)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <path d="M14 74 Q28 60 46 69 Q60 76 74 69 Q92 60 106 74" stroke="url(#ec1_b)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <line x1="60" y1="76" x2="60" y2="90" stroke="#8B5e3c" strokeWidth="3.5" strokeLinecap="round"/>
                <circle cx="60" cy="95" r="5" fill="#8B5e3c"/>
              </svg>
          </div>
        </div>
          </div>
        ) : filteredCategories.length === 0 ? (
          <div className="col-span-full text-center py-12 text-gray-500">
            {categories.length === 0 ? 'אין קטגוריות כלים.' : 'לא נמצאו קטגוריות'}
          </div>
        ) : (
          filteredCategories.map((category) => {
            const effectiveRate = getEffectiveRate(category);
            const hasRate = effectiveRate != null && effectiveRate > 0;
            return (
              <div
                key={category.id}
                className={`bg-white rounded-xl border ${category.is_active ? 'border-kkl-border' : 'border-gray-200 opacity-60'} p-5 hover:shadow-md transition-shadow`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${category.is_active ? 'bg-kkl-green-light' : 'bg-gray-100'}`}>
                      <Wrench className={`w-5 h-5 ${category.is_active ? 'text-kkl-green' : 'text-gray-400'}`} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-kkl-text">{category.name}</h3>
                      <span className="text-xs font-mono bg-gray-100 px-2 py-0.5 rounded">{category.code}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <button onClick={() => handleOpenModal(category)} className="p-1.5 text-gray-400 hover:text-kkl-green hover:bg-kkl-green-light rounded-lg transition-colors">
                      <Edit className="w-4 h-4" />
                    </button>
                    <button onClick={() => handleDelete(category.id)} className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {category.description && (
                  <p className="text-sm text-gray-500 mb-3">{category.description}</p>
                )}

                {getParentName(category.parent_category_id) && (
                  <div className="flex items-center gap-1 text-xs text-gray-500 mb-3">
                    <Layers className="w-3 h-3" />
                    תת-קטגוריה של: {getParentName(category.parent_category_id)}
                  </div>
                )}

                <div className="flex flex-wrap gap-2 mb-3">
                  {/* ── תעריף badge — reads from equipment_types via getEffectiveRate ── */}
                  {hasRate ? (
                    <span className="flex items-center gap-1 px-2.5 py-1 bg-green-100 text-green-700 text-xs rounded-full font-medium">
                      <DollarSign className="w-3 h-3" />
                      ₪{effectiveRate} / שעה
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 px-2.5 py-1 bg-orange-100 text-orange-600 text-xs rounded-full">
                      <DollarSign className="w-3 h-3" />
                      תעריף לא הוגדר
                    </span>
                  )}
                  {category.default_daily_rate && category.default_daily_rate > 0 ? (
                    <span className="flex items-center gap-1 px-2.5 py-1 bg-blue-50 text-blue-600 text-xs rounded-full">
                      <Clock className="w-3 h-3" />
                      ₪{category.default_daily_rate} / יום
                    </span>
                  ) : null}
                  {category.requires_license && (
                    <span className="flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                      <Shield className="w-3 h-3" />
                      רישיון {category.license_type && `(${category.license_type})`}
                    </span>
                  )}
                  {category.requires_certification && (
                    <span className="flex items-center gap-1 px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full">
                      <CheckCircle className="w-3 h-3" />
                      הסמכה
                    </span>
                  )}
                </div>

                <div className="mt-3 pt-3 border-t border-kkl-border">
                  <button
                    onClick={() => toggleActive(category)}
                    className={`text-xs px-2 py-1 rounded-full ${category.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}
                  >
                    {category.is_active ? 'פעיל' : 'מושבת'}
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Info */}
      <div className="mt-6 bg-orange-50 border border-orange-200 rounded-xl p-4 flex items-start gap-3">
        <Info className="w-5 h-5 text-orange-500 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-orange-700">
          <p className="font-medium mb-1">מה זה קטלוג כלים?</p>
          <p>קטלוג הכלים מגדיר את כל סוגי הציוד המאושרים לשימוש בפרויקטים של קק"ל. לכל סוג כלי יש תעריפי ברירת מחדל, דרישות רישיון והסמכה.</p>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl my-8">
            <div className="flex items-center justify-between p-5 border-b border-kkl-border">
              <h2 className="text-lg font-bold text-kkl-text">
                {editingCategory ? 'עריכת קטגוריית כלים' : 'קטגוריית כלים חדשה'}
              </h2>
              <button onClick={() => setShowModal(false)} className="p-2 hover:bg-gray-100 rounded-lg">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-5 space-y-4 max-h-[70vh] overflow-y-auto">
              {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">{error}</div>}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-kkl-text mb-2">שם *</label>
                  <input type="text" value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-4 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green" placeholder="דחפור" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-kkl-text mb-2">קוד *</label>
                  <input type="text" value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                    className="w-full px-4 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green font-mono" placeholder="BULLDOZER" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-kkl-text mb-2">תיאור</label>
                <textarea value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={2} className="w-full px-4 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green resize-none" />
              </div>
              <div>
                <label className="block text-sm font-medium text-kkl-text mb-2">קטגוריית אב</label>
                <select value={formData.parent_category_id || ''}
                  onChange={(e) => setFormData({ ...formData, parent_category_id: e.target.value ? parseInt(e.target.value) : null })}
                  className="w-full pr-4 pl-10 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green">
                  <option value="">ללא (קטגוריה ראשית)</option>
                  {categories.filter(c => c.id !== editingCategory?.id && !c.parent_category_id).map(c => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-kkl-text mb-2">תעריף שעתי (₪)</label>
                  <input type="number" min="0" value={formData.default_hourly_rate}
                    onChange={(e) => setFormData({ ...formData, default_hourly_rate: parseFloat(e.target.value) || 0 })}
                    className="w-full px-4 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-kkl-text mb-2">תעריף יומי (₪)</label>
                  <input type="number" min="0" value={formData.default_daily_rate}
                    onChange={(e) => setFormData({ ...formData, default_daily_rate: parseFloat(e.target.value) || 0 })}
                    className="w-full px-4 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green" />
                </div>
              </div>
              <div className="flex flex-wrap gap-4">
                {[
                  { key: 'requires_license', label: 'דורש רישיון' },
                  { key: 'requires_certification', label: 'דורש הסמכה' },
                  { key: 'is_active', label: 'פעיל' },
                ].map(({ key, label }) => (
                  <label key={key} className="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" checked={formData[key as keyof typeof formData] as boolean}
                      onChange={(e) => setFormData({ ...formData, [key]: e.target.checked })}
                      className="w-4 h-4 text-kkl-green rounded" />
                    <span className="text-sm text-kkl-text">{label}</span>
                  </label>
                ))}
              </div>
              {formData.requires_license && (
                <div>
                  <label className="block text-sm font-medium text-kkl-text mb-2">סוג רישיון</label>
                  <input type="text" value={formData.license_type}
                    onChange={(e) => setFormData({ ...formData, license_type: e.target.value })}
                    className="w-full px-4 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green" placeholder="C1, כלים כבדים..." />
                </div>
              )}
            </div>
            <div className="flex justify-end gap-3 p-5 border-t border-kkl-border">
              <button onClick={() => setShowModal(false)} className="px-4 py-2 border border-kkl-border text-kkl-text rounded-lg hover:bg-gray-50">ביטול</button>
              <button onClick={handleSave} disabled={saving}
                className="px-4 py-2 bg-kkl-green text-white rounded-lg hover:bg-kkl-green-dark flex items-center gap-2 disabled:opacity-50">
                {saving ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <Save className="w-4 h-4" />}
                {editingCategory ? 'עדכן' : 'צור'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

// ─── Tab: תעריפים (Rates) ───────────────────────────────────────────────────

const RatesTab: React.FC = () => {
  const [rates, setRates] = useState<EquipmentRateItem[]>([]);
  const [filtered, setFiltered] = useState<EquipmentRateItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [toast, setToast] = useState<{ msg: string; ok: boolean } | null>(null);

  const [editItem, setEditItem] = useState<EquipmentRateItem | null>(null);
  const [editRate, setEditRate] = useState('');
  const [editReason, setEditReason] = useState('');
  const [editSaving, setEditSaving] = useState(false);

  const [showNew, setShowNew] = useState(false);
  const [newName, setNewName] = useState('');
  const [newRate, setNewRate] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newSaving, setNewSaving] = useState(false);

  const [histItem, setHistItem] = useState<EquipmentRateItem | null>(null);
  const [history, setHistory] = useState<RateHistoryItem[]>([]);
  const [histLoading, setHistLoading] = useState(false);

  const showToast = (msg: string, ok = true) => {
    setToast({ msg, ok });
    setTimeout(() => setToast(null), 3000);
  };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/settings/equipment-rates');
      setRates(res.data);
    } catch {
      showToast('שגיאה בטעינת הנתונים', false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    const q = search.toLowerCase();
    setFiltered(q ? rates.filter(r => r.name.toLowerCase().includes(q)) : rates);
  }, [search, rates]);

  const openEdit = (item: EquipmentRateItem) => {
    setEditItem(item);
    setEditRate(item.hourly_rate != null ? String(item.hourly_rate) : '');
    setEditReason('');
  };

  const saveEdit = async () => {
    if (!editItem) return;
    if (!editReason.trim()) { showToast('חובה להזין סיבה לשינוי', false); return; }
    const rate = parseFloat(editRate);
    if (isNaN(rate) || rate < 0) { showToast('תעריף לא תקין', false); return; }
    setEditSaving(true);
    try {
      await api.patch(`/settings/equipment-rates/${editItem.id}`, { hourly_rate: rate, reason: editReason });
      showToast('התעריף עודכן בהצלחה');
      setEditItem(null);
      load();
    } catch (e: any) {
      showToast(e?.response?.data?.detail || 'שגיאה בעדכון', false);
    } finally {
      setEditSaving(false);
    }
  };

  const saveNew = async () => {
    if (!newName.trim()) { showToast('חובה להזין שם כלי', false); return; }
    setNewSaving(true);
    try {
      await api.post('/settings/equipment-rates', {
        name: newName.trim(),
        hourly_rate: newRate ? parseFloat(newRate) : null,
        description: newDesc || null,
      });
      showToast('סוג ציוד חדש נוצר בהצלחה');
      setShowNew(false);
      setNewName(''); setNewRate(''); setNewDesc('');
      load();
    } catch (e: any) {
      showToast(e?.response?.data?.detail || 'שגיאה ביצירה', false);
    } finally {
      setNewSaving(false);
    }
  };

  const openHistory = async (item: EquipmentRateItem) => {
    setHistItem(item);
    setHistLoading(true);
    setHistory([]);
    try {
      const res = await api.get(`/settings/equipment-rates/${item.id}/history`);
      setHistory(res.data);
    } catch {
      showToast('שגיאה בטעינת היסטוריה', false);
    } finally {
      setHistLoading(false);
    }
  };

  return (
    <>
      {toast && <Toast msg={toast.msg} ok={toast.ok} onClose={() => setToast(null)} />}

      <div className="flex items-center justify-between mb-4">
        <div className="relative w-72">
          <Search className="absolute right-3 top-2.5 w-4 h-4 text-gray-400" />
          <input type="text" placeholder="חיפוש סוג ציוד..."
            value={search} onChange={e => setSearch(e.target.value)}
            className="w-full pr-9 pl-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-kkl-green bg-white" />
        </div>
        <button onClick={() => setShowNew(true)}
          className="flex items-center gap-2 px-4 py-2 bg-kkl-green hover:bg-kkl-green-dark text-white rounded-xl text-sm font-medium shadow-sm">
          <Plus className="w-4 h-4" /> סוג ציוד חדש
        </button>
      </div>

      {loading ? (
        <div className="text-center py-16 text-gray-400">טוען...</div>
      ) : (
        <div className="bg-white rounded-xl border overflow-hidden shadow-sm">
          {filtered.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <Wrench className="w-10 h-10 mx-auto mb-2 opacity-30" />
              <p>אין סוגי ציוד להצגה</p>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-right px-4 py-3 font-medium text-gray-600">שם כלי</th>
                  <th className="text-right px-4 py-3 font-medium text-gray-600">תעריף לשעה</th>
                  <th className="text-right px-4 py-3 font-medium text-gray-600">עדכון אחרון</th>
                  <th className="text-right px-4 py-3 font-medium text-gray-600">עודכן ע"י</th>
                  <th className="text-right px-4 py-3 font-medium text-gray-600">פעולות</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.map(item => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Wrench className="w-4 h-4 text-gray-400 flex-shrink-0" />
                        <span className="font-medium text-gray-900">{item.name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {item.hourly_rate != null && item.hourly_rate > 0 ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                          {fmtRate(item.hourly_rate)}/שעה
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 bg-orange-100 text-orange-600 rounded-full text-xs">
                          לא הוגדר
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500">{fmtDate(item.last_updated)}</td>
                    <td className="px-4 py-3 text-gray-500">{item.updated_by || '—'}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <button onClick={() => openEdit(item)}
                          className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg" title="עריכת תעריף">
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button onClick={() => openHistory(item)}
                          className="p-1.5 text-gray-500 hover:bg-gray-100 rounded-lg" title="היסטוריה">
                          <History className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Edit Modal */}
      {editItem && (
        <div className="fixed inset-0 bg-black/40 z-[1500] flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-lg">עריכת תעריף — {editItem.name}</h3>
              <button onClick={() => setEditItem(null)} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">תעריף חדש (₪ לשעה)</label>
                <div className="relative">
                  <span className="absolute right-3 top-2.5 text-gray-400 text-sm">₪</span>
                  <input type="number" min="0" step="0.01" value={editRate} onChange={e => setEditRate(e.target.value)}
                    className="w-full pr-8 pl-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-kkl-green" placeholder="0.00" />
                </div>
                {editItem.hourly_rate != null && (
                  <p className="text-xs text-gray-400 mt-1">תעריף נוכחי: {fmtRate(editItem.hourly_rate)}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">סיבה לשינוי <span className="text-red-500">*</span></label>
                <input type="text" value={editReason} onChange={e => setEditReason(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-kkl-green" placeholder="למשל: עדכון מחירון 2026" />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={saveEdit} disabled={editSaving}
                className="flex-1 py-2 bg-kkl-green hover:bg-kkl-green-dark text-white rounded-lg text-sm font-medium disabled:opacity-50">
                {editSaving ? 'שומר...' : 'שמור שינוי'}
              </button>
              <button onClick={() => setEditItem(null)} className="flex-1 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50">ביטול</button>
            </div>
          </div>
        </div>
      )}

      {/* New Modal */}
      {showNew && (
        <div className="fixed inset-0 bg-black/40 z-[1500] flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-lg">סוג ציוד חדש</h3>
              <button onClick={() => setShowNew(false)} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">שם כלי (עברית) <span className="text-red-500">*</span></label>
                <input type="text" value={newName} onChange={e => setNewName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-kkl-green" placeholder="מחפרון בינוני" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">תעריף לשעה (₪)</label>
                <div className="relative">
                  <span className="absolute right-3 top-2.5 text-gray-400 text-sm">₪</span>
                  <input type="number" min="0" step="0.01" value={newRate} onChange={e => setNewRate(e.target.value)}
                    className="w-full pr-8 pl-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-kkl-green" placeholder="0.00" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">תיאור (אופציונלי)</label>
                <input type="text" value={newDesc} onChange={e => setNewDesc(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-kkl-green" placeholder="תיאור קצר..." />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={saveNew} disabled={newSaving}
                className="flex-1 py-2 bg-kkl-green hover:bg-kkl-green-dark text-white rounded-lg text-sm font-medium disabled:opacity-50">
                {newSaving ? 'יוצר...' : 'צור סוג ציוד'}
              </button>
              <button onClick={() => setShowNew(false)} className="flex-1 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50">ביטול</button>
            </div>
          </div>
        </div>
      )}

      {/* History Modal */}
      {histItem && (
        <div className="fixed inset-0 bg-black/40 z-[1500] flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-lg flex items-center gap-2">
                <History className="w-5 h-5 text-gray-500" />
                היסטוריית תעריפים — {histItem.name}
              </h3>
              <button onClick={() => { setHistItem(null); setHistory([]); }} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
            </div>
            {histLoading ? (
              <div className="text-center py-8 text-gray-400">טוען...</div>
            ) : history.length === 0 ? (
              <div className="text-center py-8 text-gray-400">אין שינויי תעריף עדיין</div>
            ) : (
              <div className="overflow-y-auto max-h-80">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 border-b sticky top-0">
                    <tr>
                      <th className="text-right px-3 py-2 font-medium text-gray-600">תאריך</th>
                      <th className="text-right px-3 py-2 font-medium text-gray-600">ישן</th>
                      <th className="text-right px-3 py-2 font-medium text-gray-600">חדש</th>
                      <th className="text-right px-3 py-2 font-medium text-gray-600">שונה ע"י</th>
                      <th className="text-right px-3 py-2 font-medium text-gray-600">סיבה</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {history.map(h => (
                      <tr key={h.id} className="hover:bg-gray-50">
                        <td className="px-3 py-2 text-gray-500">{fmtDate(h.effective_date || h.created_at)}</td>
                        <td className="px-3 py-2 text-red-500">{fmtRate(h.old_rate)}</td>
                        <td className="px-3 py-2 text-green-600 font-medium">{fmtRate(h.new_rate)}</td>
                        <td className="px-3 py-2 text-gray-600">{h.changed_by_name || '—'}</td>
                        <td className="px-3 py-2 text-gray-500">{h.reason || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <div className="mt-4 flex justify-end">
              <button onClick={() => { setHistItem(null); setHistory([]); }} className="px-4 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50">סגור</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

// ─── Main Page ───────────────────────────────────────────────────────────────

const EquipmentCatalog: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = (searchParams.get('tab') === 'rates') ? 'rates' : 'catalog';

  const setTab = (tab: 'catalog' | 'rates') => {
    setSearchParams(tab === 'catalog' ? {} : { tab: 'rates' });
  };

  return (
    <div className="min-h-screen bg-kkl-bg" dir="rtl">
      <div className="max-w-6xl mx-auto px-4 py-6">

        {/* Header */}
        <div className="mb-6">
          <button onClick={() => navigate('/settings')}
            className="text-kkl-green hover:text-kkl-green-dark flex items-center gap-1 mb-4 text-sm">
            <ArrowRight className="w-4 h-4" /> חזרה להגדרות
          </button>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center">
              <Wrench className="w-6 h-6 text-orange-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-kkl-text">קטלוג כלים ותעריפים</h1>
              <p className="text-gray-500 text-sm">ניהול סוגי הכלים המאושרים ותעריפי השעה שלהם</p>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-gray-100 p-1 rounded-xl mb-6 w-fit">
          {[
            { key: 'catalog', label: '📦 כרטיסי כלים' },
            { key: 'rates',   label: '₪ תעריפים' },
          ].map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setTab(key as 'catalog' | 'rates')}
              className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === key
                  ? 'bg-white text-kkl-green shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Content */}
        {activeTab === 'catalog' ? <CatalogTab /> : <RatesTab />}
      </div>
    </div>
  );
};

export default EquipmentCatalog;
