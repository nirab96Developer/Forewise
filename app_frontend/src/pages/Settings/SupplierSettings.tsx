
// src/pages/Settings/SupplierSettings.tsx
// הגדרות ספקים - ניהול ספקים, ציוד ותמחור
import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  ArrowRight, Truck, Plus, Search, Edit, Trash2,
  DollarSign, Wrench, Filter, Eye,
  CheckCircle, XCircle, AlertCircle, X, Save, RotateCcw
} from 'lucide-react';
import api from '../../services/api';

// Types
interface Supplier {
  id: number;
  name: string;
  contact_name?: string;
  contact_person?: string;
  phone?: string;
  email?: string;
  is_active: boolean;
  region_id?: number;
  area_id?: number;
  region_name?: string;
  equipment_count?: number;
  code?: string;
  tax_id?: string;
  address?: string;
}

interface SupplierEquipment {
  id: number;
  supplier_id: number;
  supplier_name?: string;
  equipment_model_id?: number;
  equipment_name?: string;
  base_rate?: number;
  hourly_rate?: number;
  night_rate?: number;
  weekend_rate?: number;
  license_plate?: string;
  status?: string;
  is_active: boolean;
}

type TabType = 'suppliers' | 'equipment' | 'pricing' | 'rotation' | 'constraints';

const pathToTab: Record<string, TabType> = {
  '/settings/suppliers': 'suppliers',
  '/settings/supplier-equipment': 'equipment',
  '/settings/pricing': 'pricing',
  '/settings/fair-rotation': 'rotation',
  '/settings/constraint-reasons': 'constraints',
};

// ──────────────────────────────────────────────────────────────────────────────
// Add/Edit Supplier Modal
// ──────────────────────────────────────────────────────────────────────────────
const SupplierModal: React.FC<{
  supplier: Supplier | null;
  onClose: () => void;
  onSaved: () => void;
}> = ({ supplier, onClose, onSaved }) => {
  const isEdit = !!supplier;
  const [form, setForm] = useState({
    name: supplier?.name || '',
    contact_name: supplier?.contact_name || supplier?.contact_person || '',
    phone: supplier?.phone || '',
    email: supplier?.email || '',
    address: supplier?.address || '',
    tax_id: supplier?.tax_id || '',
  });
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState('');

  const handleSave = async () => {
    if (!form.name.trim()) { setErr('שם ספק הוא שדה חובה'); return; }
    setSaving(true);
    setErr('');
    try {
      if (isEdit) {
        await api.put(`/suppliers/${supplier.id}`, form);
      } else {
        // Generate code from name
        const code = 'SUP-' + Date.now().toString().slice(-6);
        await api.post('/suppliers', { ...form, code });
      }
      onSaved();
      onClose();
    } catch (e: any) {
      const msg = e?.response?.data?.detail || 'שגיאה בשמירה';
      setErr(typeof msg === 'string' ? msg : JSON.stringify(msg));
      if ((window as any).showToast) (window as any).showToast(msg, 'error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-5 border-b border-kkl-border">
          <h2 className="text-lg font-bold text-kkl-text">{isEdit ? 'עריכת ספק' : 'הוספת ספק חדש'}</h2>
          <button onClick={onClose} className="p-1.5 hover:bg-gray-100 rounded-lg"><X className="w-5 h-5" /></button>
        </div>
        <div className="p-5 space-y-4">
          {err && <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">{err}</div>}
          {[
            { key: 'name', label: 'שם ספק *', placeholder: 'שם מלא של הספק' },
            { key: 'contact_name', label: 'איש קשר', placeholder: 'שם איש הקשר' },
            { key: 'phone', label: 'טלפון', placeholder: '050-0000000' },
            { key: 'email', label: 'אימייל', placeholder: 'example@supplier.com' },
            { key: 'tax_id', label: 'ח.פ / עוסק מורשה', placeholder: '000000000' },
            { key: 'address', label: 'כתובת', placeholder: 'כתובת הספק' },
          ].map(f => (
            <div key={f.key}>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">{f.label}</label>
              <input
                value={(form as any)[f.key]}
                onChange={e => setForm(prev => ({ ...prev, [f.key]: e.target.value }))}
                placeholder={f.placeholder}
                className="w-full px-3 py-2 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent text-sm"
              />
            </div>
          ))}
        </div>
        <div className="flex gap-3 p-5 border-t border-kkl-border">
          <button onClick={onClose} className="flex-1 px-4 py-2 border border-kkl-border rounded-lg text-gray-600 hover:bg-gray-50 text-sm">ביטול</button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex-1 px-4 py-2 bg-kkl-green text-white rounded-lg hover:bg-kkl-green-dark text-sm flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {saving ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <Save className="w-4 h-4" />}
            {isEdit ? 'שמור שינויים' : 'הוסף ספק'}
          </button>
        </div>
      </div>
    </div>
  );
};

// ──────────────────────────────────────────────────────────────────────────────
// Main Component
// ──────────────────────────────────────────────────────────────────────────────
const SupplierSettings: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const getInitialTab = (): TabType => pathToTab[location.pathname] || 'suppliers';

  const [activeTab, setActiveTab] = useState<TabType>(getInitialTab());
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [supplierEquipment, setSupplierEquipment] = useState<SupplierEquipment[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState<Supplier | null>(null);

  useEffect(() => {
    const newTab = pathToTab[location.pathname];
    if (newTab && newTab !== activeTab) setActiveTab(newTab);
  }, [location.pathname]);

  useEffect(() => { loadData(); }, [activeTab]);

  const showToast = (msg: string, type = 'error') => {
    if ((window as any).showToast) (window as any).showToast(msg, type);
  };

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'suppliers') {
        const response = await api.get('/suppliers');
        const data = response.data?.items || response.data || [];
        setSuppliers(Array.isArray(data) ? data : []);
      } else if (activeTab === 'equipment') {
        // Use the new global endpoint
        const response = await api.get('/suppliers-equipment');
        const data = response.data?.items || response.data || [];
        setSupplierEquipment(Array.isArray(data) ? data : []);
      }
    } catch (error: any) {
      console.error('Error loading data:', error);
      showToast('שגיאה בטעינת הנתונים', 'error');
      setSuppliers([]);
      setSupplierEquipment([]);
    } finally {
      setLoading(false);
    }
  };

  const toggleSupplierStatus = async (supplier: Supplier) => {
    try {
      await api.patch(`/suppliers/${supplier.id}`, { is_active: !supplier.is_active });
      showToast(supplier.is_active ? 'הספק הושבת' : 'הספק הופעל', 'success');
      loadData();
    } catch (error: any) {
      showToast(error?.response?.data?.detail || 'שגיאה בעדכון סטטוס', 'error');
    }
  };

  const deleteSupplier = async (supplier: Supplier) => {
    if (!window.confirm(`למחוק את הספק "${supplier.name}"?`)) return;
    try {
      await api.delete(`/suppliers/${supplier.id}`);
      showToast('הספק נמחק בהצלחה', 'success');
      loadData();
    } catch (error: any) {
      showToast(error?.response?.data?.detail || 'שגיאה במחיקת הספק', 'error');
    }
  };

  const filteredSuppliers = (suppliers || []).filter(s =>
    s.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (s.contact_name || s.contact_person || '')?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredEquipment = (supplierEquipment || []).filter(eq =>
    eq.supplier_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    eq.equipment_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    eq.license_plate?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const tabs = [
    { id: 'suppliers' as TabType, label: 'רשימת ספקים', icon: <Truck className="w-4 h-4" /> },
    { id: 'equipment' as TabType, label: 'ציוד ספקים', icon: <Wrench className="w-4 h-4" /> },
    { id: 'pricing' as TabType, label: 'תמחור כלים', icon: <DollarSign className="w-4 h-4" /> },
    { id: 'rotation' as TabType, label: 'סבב הוגן', icon: <RotateCcw className="w-4 h-4" /> },
    { id: 'constraints' as TabType, label: 'סיבות אילוץ', icon: <AlertCircle className="w-4 h-4" /> },
  ];

  return (
    <div className="min-h-screen bg-kkl-bg" dir="rtl">
      {/* Modals */}
      {(showAddModal || editingSupplier) && (
        <SupplierModal
          supplier={editingSupplier}
          onClose={() => { setShowAddModal(false); setEditingSupplier(null); }}
          onSaved={loadData}
        />
      )}

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/settings')}
            className="text-kkl-green hover:text-kkl-green-dark flex items-center gap-1 mb-4 text-sm"
          >
            <ArrowRight className="w-4 h-4" />
            חזרה להגדרות
          </button>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-kkl-green rounded-xl flex items-center justify-center">
                <Truck className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-kkl-text">הגדרות ספקים</h1>
                <p className="text-gray-500">ניהול ספקים, ציוד ותמחור</p>
              </div>
            </div>
            {(activeTab === 'suppliers') && (
              <button
                onClick={() => { setEditingSupplier(null); setShowAddModal(true); }}
                className="px-4 py-2 bg-kkl-green text-white rounded-lg hover:bg-kkl-green-dark transition-colors flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                הוסף ספק
              </button>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-xl shadow-sm border border-kkl-border mb-6">
          <div className="flex overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-5 py-4 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-kkl-green text-kkl-green bg-kkl-green-light/30'
                    : 'border-transparent text-gray-500 hover:text-kkl-green hover:bg-gray-50'
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Search (only for data tabs) */}
        {(activeTab === 'suppliers' || activeTab === 'equipment') && (
          <div className="bg-white rounded-xl shadow-sm border border-kkl-border p-4 mb-6">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder={`חיפוש ${activeTab === 'suppliers' ? 'ספקים' : 'ציוד'}...`}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pr-10 pl-4 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                />
              </div>
              <button className="px-4 py-2.5 border border-kkl-border rounded-lg hover:bg-gray-50 flex items-center gap-2 text-gray-600">
                <Filter className="w-4 h-4" />
                סינון
              </button>
            </div>
          </div>
        )}

        {/* Content */}
        <div className="bg-white rounded-xl shadow-sm border border-kkl-border overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="relative">
          <div className="w-10 h-10 rounded-full border-[3px] border-emerald-200 border-t-emerald-500 animate-spin" style={{animationDuration:'0.9s'}} />
          <div className="absolute inset-0 flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 100" width="20" height="17">
                <defs>
                  <linearGradient id="ss1_t" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#1565c0"/><stop offset="100%" stopColor="#0097a7"/></linearGradient>
                  <linearGradient id="ss1_m" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#0097a7"/><stop offset="50%" stopColor="#2e7d32"/><stop offset="100%" stopColor="#66bb6a"/></linearGradient>
                  <linearGradient id="ss1_b" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#2e7d32"/><stop offset="40%" stopColor="#66bb6a"/><stop offset="100%" stopColor="#8B5e3c"/></linearGradient>
                </defs>
                <path d="M46 20 Q60 9 74 20" stroke="url(#ss1_t)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <path d="M30 47 Q42 34 60 43 Q78 34 90 47" stroke="url(#ss1_m)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <path d="M14 74 Q28 60 46 69 Q60 76 74 69 Q92 60 106 74" stroke="url(#ss1_b)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <line x1="60" y1="76" x2="60" y2="90" stroke="#8B5e3c" strokeWidth="3.5" strokeLinecap="round"/>
                <circle cx="60" cy="95" r="5" fill="#8B5e3c"/>
              </svg>
          </div>
        </div>
            </div>
          ) : activeTab === 'suppliers' ? (
            /* ── Suppliers Table ── */
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-kkl-border">
                  <tr>
                    <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">שם ספק</th>
                    <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">איש קשר</th>
                    <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">טלפון</th>
                    <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">מרחב</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">סטטוס</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">פעולות</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredSuppliers.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="text-center py-12 text-gray-500">לא נמצאו ספקים</td>
                    </tr>
                  ) : (
                    filteredSuppliers.map((supplier) => (
                      <tr key={supplier.id} className="border-b border-kkl-border hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-kkl-green-light rounded-lg flex items-center justify-center">
                              <Truck className="w-5 h-5 text-kkl-green" />
                            </div>
                            <div>
                              <span className="font-medium text-kkl-text">{supplier.name}</span>
                              {supplier.code && <p className="text-xs text-gray-400">{supplier.code}</p>}
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-gray-600">{supplier.contact_name || supplier.contact_person || '-'}</td>
                        <td className="px-4 py-3 text-gray-600 direction-ltr">{supplier.phone || '-'}</td>
                        <td className="px-4 py-3 text-gray-600">{supplier.region_name || '-'}</td>
                        <td className="px-4 py-3 text-center">
                          <button
                            onClick={() => toggleSupplierStatus(supplier)}
                            className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm transition-colors ${
                              supplier.is_active ? 'bg-green-100 text-green-700 hover:bg-green-200' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                            }`}
                          >
                            {supplier.is_active ? <><CheckCircle className="w-4 h-4" />פעיל</> : <><XCircle className="w-4 h-4" />מושבת</>}
                          </button>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center justify-center gap-2">
                            <button
                              onClick={() => navigate(`/suppliers/${supplier.id}`)}
                              className="p-2 text-gray-400 hover:text-kkl-green hover:bg-kkl-green-light rounded-lg transition-colors"
                              title="צפייה מלאה"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => setEditingSupplier(supplier)}
                              className="p-2 text-gray-400 hover:text-kkl-green hover:bg-kkl-green-light rounded-lg transition-colors"
                              title="עריכה"
                            >
                              <Edit className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => deleteSupplier(supplier)}
                              className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                              title="מחיקה"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          ) : activeTab === 'equipment' ? (
            /* ── Supplier Equipment Table ── */
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-kkl-border">
                  <tr>
                    <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">ספק</th>
                    <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">סוג כלי</th>
                    <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">לוחית רישוי</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">תעריף שעתי</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">סטטוס</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">פעולות</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEquipment.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="text-center py-12 text-gray-500">לא נמצא ציוד ספקים</td>
                    </tr>
                  ) : (
                    filteredEquipment.map((eq) => (
                      <tr key={eq.id} className="border-b border-kkl-border hover:bg-gray-50">
                        <td className="px-4 py-3 font-medium text-kkl-text">{eq.supplier_name || '-'}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <Wrench className="w-4 h-4 text-kkl-green" />
                            {eq.equipment_name || '-'}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-gray-600 font-mono">{eq.license_plate || '-'}</td>
                        <td className="px-4 py-3 text-center font-medium">
                          {(eq.hourly_rate || eq.base_rate) ? `₪${eq.hourly_rate || eq.base_rate}` : '-'}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm ${
                            eq.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                          }`}>
                            {eq.is_active ? 'פעיל' : 'מושבת'}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center justify-center gap-2">
                            <button
                              onClick={() => navigate(`/suppliers/${eq.supplier_id}`)}
                              className="p-2 text-gray-400 hover:text-kkl-green hover:bg-kkl-green-light rounded-lg transition-colors"
                              title="עבור לספק"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          ) : activeTab === 'pricing' ? (
            /* ── Pricing Tab — redirect ── */
            <div className="p-8 text-center">
              <DollarSign className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-kkl-text mb-2">תמחור כלים</h3>
              <p className="text-gray-500 mb-4">ניהול תעריפי שעה לכל סוגי הכלים</p>
              <button
                onClick={() => navigate('/settings/equipment-catalog?tab=rates')}
                className="px-4 py-2 bg-kkl-green text-white rounded-lg hover:bg-kkl-green-dark transition-colors"
              >
                עבור לניהול תעריפים
              </button>
            </div>
          ) : activeTab === 'rotation' ? (
            /* ── Fair Rotation Tab — redirect ── */
            <div className="p-8 text-center">
              <RotateCcw className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-kkl-text mb-2">סבב הוגן</h3>
              <p className="text-gray-500 mb-4">הגדרת כללי הקצאת ספקים בסבב הוגן</p>
              <button
                onClick={() => navigate('/settings/fair-rotation')}
                className="px-4 py-2 bg-kkl-green text-white rounded-lg hover:bg-kkl-green-dark transition-colors"
              >
                עבור להגדרות סבב הוגן
              </button>
            </div>
          ) : (
            /* ── Constraint Reasons Tab — redirect ── */
            <div className="p-8 text-center">
              <AlertCircle className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-kkl-text mb-2">סיבות אילוץ ספק</h3>
              <p className="text-gray-500 mb-4">ניהול סיבות לבחירת ספק ידנית מחוץ לסבב</p>
              <button
                onClick={() => navigate('/settings/constraint-reasons')}
                className="px-4 py-2 bg-kkl-green text-white rounded-lg hover:bg-kkl-green-dark transition-colors"
              >
                נהל סיבות אילוץ
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SupplierSettings;
