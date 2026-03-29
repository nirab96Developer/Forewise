
// src/pages/Settings/FairRotation.tsx
// ניהול סבב הוגן של ספקים
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight, RotateCcw, Plus, Search, Edit, Trash2,
  ChevronUp, ChevronDown,
  Info, Save, X, Truck
} from 'lucide-react';
import api from '../../services/api';
import { useRoleAccess } from '../../hooks/useRoleAccess';

interface SupplierRotation {
  id: number;
  supplier_id: number;
  supplier_name?: string;
  rotation_date: string;
  priority: number;
  sequence_number: number;
  status: string;
  is_active: boolean;
  last_used_date?: string;
  usage_count: number;
  skip_count: number;
  equipment_type?: string;
  notes?: string;
}

interface Supplier {
  id: number;
  name: string;
  is_active: boolean;
}

const FairRotation: React.FC = () => {
  const navigate = useNavigate();
  const [rotations, setRotations] = useState<SupplierRotation[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const { canManageRotation } = useRoleAccess();
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingRotation, setEditingRotation] = useState<SupplierRotation | null>(null);
  const [formData, setFormData] = useState({
    supplier_id: 0,
    priority: 1,
    sequence_number: 1,
    status: 'active',
    is_active: true,
    equipment_type: '',
    notes: '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [rotationsRes, suppliersRes] = await Promise.all([
        api.get('/supplier-rotations/'),
        api.get('/suppliers')
      ]);
      // Handle both array and {items: [...]} response formats
      const rotationsData = rotationsRes.data?.items || rotationsRes.data || [];
      const suppliersData = suppliersRes.data?.items || suppliersRes.data || [];
      setRotations(Array.isArray(rotationsData) ? rotationsData : []);
      setSuppliers(Array.isArray(suppliersData) ? suppliersData : []);
    } catch (err) {
      console.error('Error loading data:', err);
      // Set empty arrays on error
      setRotations([]);
      setSuppliers([]);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = (rotation?: SupplierRotation) => {
    if (rotation) {
      setEditingRotation(rotation);
      setFormData({
        supplier_id: rotation.supplier_id,
        priority: rotation.priority,
        sequence_number: rotation.sequence_number,
        status: rotation.status,
        is_active: rotation.is_active,
        equipment_type: rotation.equipment_type || '',
        notes: rotation.notes || '',
      });
    } else {
      setEditingRotation(null);
      setFormData({
        supplier_id: suppliers[0]?.id || 0,
        priority: rotations.length + 1,
        sequence_number: rotations.length + 1,
        status: 'active',
        is_active: true,
        equipment_type: '',
        notes: '',
      });
    }
    setShowModal(true);
    setError('');
  };

  const handleSave = async () => {
    if (!formData.supplier_id) {
      setError('יש לבחור ספק');
      return;
    }

    setSaving(true);
    setError('');

    try {
      const payload = {
        ...formData,
        rotation_date: new Date().toISOString().split('T')[0],
        usage_count: editingRotation?.usage_count || 0,
        skip_count: editingRotation?.skip_count || 0,
      };

      if (editingRotation) {
        await api.put(`/supplier-rotations/${editingRotation.id}`, payload);
      } else {
        await api.post('/supplier-rotations/', payload);
      }
      setShowModal(false);
      loadData();
    } catch (err: any) {
      console.error('Error saving rotation:', err);
      setError(err.response?.data?.detail || 'שגיאה בשמירת הסבב');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('האם אתה בטוח שברצונך למחוק ספק זה מהסבב?')) {
      return;
    }

    try {
      await api.delete(`/supplier-rotations/${id}`);
      loadData();
    } catch (err) {
      console.error('Error deleting rotation:', err);
      alert('שגיאה במחיקת הספק מהסבב');
    }
  };

  const movePriority = async (rotation: SupplierRotation, direction: 'up' | 'down') => {
    const newPriority = direction === 'up' ? rotation.priority - 1 : rotation.priority + 1;
    if (newPriority < 1) return;

    try {
      await api.patch(`/supplier-rotations/${rotation.id}`, {
        priority: newPriority
      });
      loadData();
    } catch (err) {
      console.error('Error updating priority:', err);
    }
  };

  const toggleActive = async (rotation: SupplierRotation) => {
    try {
      await api.patch(`/supplier-rotations/${rotation.id}`, {
        is_active: !rotation.is_active
      });
      loadData();
    } catch (err) {
      console.error('Error toggling active status:', err);
    }
  };

  const getSupplierName = (supplierId: number) => {
    const supplier = (suppliers || []).find(s => s.id === supplierId);
    return supplier?.name || `ספק #${supplierId}`;
  };

  const filteredRotations = (rotations || [])
    .filter(r => {
      const supplierName = getSupplierName(r.supplier_id).toLowerCase();
      return supplierName.includes(searchTerm.toLowerCase());
    })
    .sort((a, b) => (a.priority || 0) - (b.priority || 0));

  return (
    <div className="min-h-screen bg-kkl-bg" dir="rtl">
      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/settings/suppliers')}
            className="text-kkl-green hover:text-kkl-green-dark flex items-center gap-1 mb-4 text-sm"
          >
            <ArrowRight className="w-4 h-4" />
            חזרה להגדרות ספקים
          </button>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                <RotateCcw className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-kkl-text">סבב הוגן</h1>
                <p className="text-gray-500">ניהול סדר ועדיפות ספקים בהקצאות</p>
              </div>
            </div>
            {canManageRotation && (
              <button
                onClick={() => handleOpenModal()}
                className="px-4 py-2 bg-kkl-green text-white rounded-lg hover:bg-kkl-green-dark transition-colors flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                הוסף ספק לסבב
              </button>
            )}
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-xl border border-kkl-border p-4">
            <div className="text-2xl font-bold text-kkl-green">{rotations.length}</div>
            <div className="text-sm text-gray-500">ספקים בסבב</div>
          </div>
          <div className="bg-white rounded-xl border border-kkl-border p-4">
            <div className="text-2xl font-bold text-green-600">
              {rotations.filter(r => r.is_active).length}
            </div>
            <div className="text-sm text-gray-500">ספקים פעילים</div>
          </div>
          <div className="bg-white rounded-xl border border-kkl-border p-4">
            <div className="text-2xl font-bold text-blue-600">
              {rotations.reduce((sum, r) => sum + (r.usage_count || 0), 0)}
            </div>
            <div className="text-sm text-gray-500">סה"כ הקצאות</div>
          </div>
          <div className="bg-white rounded-xl border border-kkl-border p-4">
            <div className="text-2xl font-bold text-orange-600">
              {rotations.reduce((sum, r) => sum + (r.skip_count || 0), 0)}
            </div>
            <div className="text-sm text-gray-500">דילוגים</div>
          </div>
        </div>

        {/* Search */}
        <div className="bg-white rounded-xl shadow-sm border border-kkl-border p-4 mb-6">
          <div className="relative">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="חיפוש ספקים..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pr-10 pl-4 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
            />
          </div>
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl shadow-sm border border-kkl-border overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="relative overflow-visible" style={{ padding: 4 }}>
          <div className="w-10 h-10 rounded-full border-[3px] border-emerald-200 border-t-emerald-500 animate-spin" style={{animationDuration:'0.9s'}} />
          <div className="absolute inset-0 flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 100" width="20" height="17">
                <defs>
                  <linearGradient id="fr1_t" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#1565c0"/><stop offset="100%" stopColor="#0097a7"/></linearGradient>
                  <linearGradient id="fr1_m" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#0097a7"/><stop offset="50%" stopColor="#2e7d32"/><stop offset="100%" stopColor="#66bb6a"/></linearGradient>
                  <linearGradient id="fr1_b" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#2e7d32"/><stop offset="40%" stopColor="#66bb6a"/><stop offset="100%" stopColor="#8B5e3c"/></linearGradient>
                </defs>
                <path d="M46 20 Q60 9 74 20" stroke="url(#fr1_t)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <path d="M30 47 Q42 34 60 43 Q78 34 90 47" stroke="url(#fr1_m)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <path d="M14 74 Q28 60 46 69 Q60 76 74 69 Q92 60 106 74" stroke="url(#fr1_b)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <line x1="60" y1="76" x2="60" y2="90" stroke="#8B5e3c" strokeWidth="3.5" strokeLinecap="round"/>
                <circle cx="60" cy="95" r="5" fill="#8B5e3c"/>
              </svg>
          </div>
        </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-kkl-border">
                  <tr>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600 w-16">עדיפות</th>
                    <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">ספק</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">סוג ציוד</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">אזור</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">מרחב</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">הקצאות</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">דילוגים</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">שימוש אחרון</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">סטטוס</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">פעולות</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRotations.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="text-center py-12 text-gray-500">
                        {rotations.length === 0 ? 'אין ספקים בסבב. הוסף ספקים כדי להתחיל.' : 'לא נמצאו ספקים'}
                      </td>
                    </tr>
                  ) : (
                    filteredRotations.map((rotation, index) => (
                      <tr key={rotation.id} className="border-b border-kkl-border hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <div className="flex items-center justify-center gap-1">
                            <button
                              onClick={() => movePriority(rotation, 'up')}
                              disabled={index === 0}
                              className="p-1 hover:bg-gray-200 rounded disabled:opacity-30"
                            >
                              <ChevronUp className="w-4 h-4" />
                            </button>
                            <span className="w-8 h-8 bg-kkl-green text-white rounded-full flex items-center justify-center font-bold text-sm">
                              {rotation.priority}
                            </span>
                            <button
                              onClick={() => movePriority(rotation, 'down')}
                              disabled={index === filteredRotations.length - 1}
                              className="p-1 hover:bg-gray-200 rounded disabled:opacity-30"
                            >
                              <ChevronDown className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-kkl-green-light rounded-lg flex items-center justify-center">
                              <Truck className="w-5 h-5 text-kkl-green" />
                            </div>
                            <span className="font-medium text-kkl-text">
                              {getSupplierName(rotation.supplier_id)}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-center">
                          {rotation.equipment_type ? (
                            <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                              {rotation.equipment_type}
                            </span>
                          ) : (
                            <span className="text-gray-400 text-xs">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-center text-xs text-gray-600">
                          {(rotation as any).area_name || '—'}
                        </td>
                        <td className="px-4 py-3 text-center text-xs text-gray-600">
                          {(rotation as any).region_name || '—'}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className="font-medium text-kkl-green">{rotation.usage_count || (rotation as any).total_assignments || 0}</span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className={(rotation.skip_count || (rotation as any).rejection_count) > 0 ? 'text-orange-600' : 'text-gray-400'}>
                            {rotation.skip_count || (rotation as any).rejection_count || 0}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center text-sm text-gray-500">
                          {(rotation.last_used_date || (rotation as any).last_assignment_date)
                            ? new Date(rotation.last_used_date || (rotation as any).last_assignment_date).toLocaleDateString('he-IL')
                            : '-'
                          }
                        </td>
                        <td className="px-4 py-3 text-center">
                          <button
                            onClick={() => toggleActive(rotation)}
                            className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm ${
                              rotation.is_active
                                ? 'bg-green-100 text-green-700'
                                : 'bg-gray-100 text-gray-500'
                            }`}
                          >
                            {rotation.is_active ? 'פעיל' : 'מושבת'}
                          </button>
                        </td>
                        <td className="px-4 py-3">
                          {canManageRotation && (
                            <div className="flex items-center justify-center gap-2">
                              <button
                                onClick={() => handleOpenModal(rotation)}
                                className="p-2 text-gray-400 hover:text-kkl-green hover:bg-kkl-green-light rounded-lg transition-colors"
                                title="עריכה"
                              >
                                <Edit className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleDelete(rotation.id)}
                                className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                                title="מחיקה"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Info Box */}
        <div className="mt-6 bg-purple-50 border border-purple-200 rounded-xl p-4 flex items-start gap-3">
          <Info className="w-5 h-5 text-purple-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-purple-700">
            <p className="font-medium mb-1">איך עובד הסבב ההוגן?</p>
            <p>המערכת מקצה ספקים לפי סדר העדיפות. כאשר ספק מקבל הקצאה, הוא עובר לסוף התור. ספקים שדולגו (לא זמינים או נבחר ספק אחר) נספרים בנפרד לצורך מעקב.</p>
          </div>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg">
            <div className="flex items-center justify-between p-5 border-b border-kkl-border">
              <h2 className="text-lg font-bold text-kkl-text">
                {editingRotation ? 'עריכת ספק בסבב' : 'הוספת ספק לסבב'}
              </h2>
              <button
                onClick={() => setShowModal(false)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-5 space-y-4">
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-kkl-text mb-2">ספק *</label>
                <select
                  value={formData.supplier_id}
                  onChange={(e) => setFormData({ ...formData, supplier_id: parseInt(e.target.value) })}
                  className="w-full pr-4 pl-10 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                >
                  <option value={0}>בחר ספק...</option>
                  {suppliers.filter(s => s.is_active).map(supplier => (
                    <option key={supplier.id} value={supplier.id}>
                      {supplier.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-kkl-text mb-2">עדיפות</label>
                  <input
                    type="number"
                    min="1"
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) || 1 })}
                    className="w-full px-4 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-kkl-text mb-2">סוג ציוד</label>
                  <input
                    type="text"
                    value={formData.equipment_type}
                    onChange={(e) => setFormData({ ...formData, equipment_type: e.target.value })}
                    className="w-full px-4 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                    placeholder="השאר ריק לכל הסוגים"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-kkl-text mb-2">הערות</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  rows={2}
                  className="w-full px-4 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent resize-none"
                  placeholder="הערות נוספות..."
                />
              </div>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="w-4 h-4 text-kkl-green rounded focus:ring-kkl-green"
                />
                <span className="text-sm text-kkl-text">פעיל בסבב</span>
              </label>
            </div>

            <div className="flex justify-end gap-3 p-5 border-t border-kkl-border">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 border border-kkl-border text-kkl-text rounded-lg hover:bg-gray-50 transition-colors"
              >
                ביטול
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-4 py-2 bg-kkl-green text-white rounded-lg hover:bg-kkl-green-dark transition-colors flex items-center gap-2 disabled:opacity-50"
              >
                {saving ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                {editingRotation ? 'עדכן' : 'הוסף'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FairRotation;

