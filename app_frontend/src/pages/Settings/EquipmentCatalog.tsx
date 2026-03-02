
// src/pages/Settings/EquipmentCatalog.tsx
// קטלוג כלים - ניהול סוגי הכלים המאושרים בקק"ל
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight, Wrench, Plus, Search, Edit, Trash2,
  CheckCircle, Save, X, Info, DollarSign,
  Clock, Shield, Layers
} from 'lucide-react';
import api from '../../services/api';

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

const EquipmentCatalog: React.FC = () => {
  const navigate = useNavigate();
  const [categories, setCategories] = useState<EquipmentCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingCategory, setEditingCategory] = useState<EquipmentCategory | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    description: '',
    parent_category_id: null as number | null,
    requires_license: false,
    license_type: '',
    requires_certification: false,
    default_hourly_rate: 0,
    default_daily_rate: 0,
    maintenance_interval_hours: 0,
    maintenance_interval_days: 0,
    is_active: true,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    setLoading(true);
    try {
      const response = await api.get('/equipment-categories');
      // Handle both array and {items: [...]} response formats
      const data = response.data?.items || response.data || [];
      setCategories(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error loading equipment categories:', err);
      setCategories([]);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = (category?: EquipmentCategory) => {
    if (category) {
      setEditingCategory(category);
      setFormData({
        name: category.name,
        code: category.code,
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
        name: '',
        code: '',
        description: '',
        parent_category_id: null,
        requires_license: false,
        license_type: '',
        requires_certification: false,
        default_hourly_rate: 0,
        default_daily_rate: 0,
        maintenance_interval_hours: 0,
        maintenance_interval_days: 0,
        is_active: true,
      });
    }
    setShowModal(true);
    setError('');
  };

  const handleSave = async () => {
    if (!formData.name.trim() || !formData.code.trim()) {
      setError('יש למלא שם וקוד');
      return;
    }

    setSaving(true);
    setError('');

    try {
      if (editingCategory) {
        await api.put(`/equipment-categories/${editingCategory.id}`, formData);
      } else {
        await api.post('/equipment-categories', formData);
      }
      setShowModal(false);
      loadCategories();
    } catch (err: any) {
      console.error('Error saving equipment category:', err);
      setError(err.response?.data?.detail || 'שגיאה בשמירת הקטגוריה');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('האם אתה בטוח שברצונך למחוק קטגוריה זו?')) {
      return;
    }

    try {
      await api.delete(`/equipment-categories/${id}`);
      loadCategories();
    } catch (err) {
      console.error('Error deleting equipment category:', err);
      alert('שגיאה במחיקת הקטגוריה');
    }
  };

  const toggleActive = async (category: EquipmentCategory) => {
    try {
      await api.patch(`/equipment-categories/${category.id}`, {
        is_active: !category.is_active
      });
      loadCategories();
    } catch (err) {
      console.error('Error toggling active status:', err);
    }
  };

  const getParentName = (parentId?: number) => {
    if (!parentId) return null;
    const parent = categories.find(c => c.id === parentId);
    return parent?.name;
  };

  const filteredCategories = (categories || []).filter(c =>
    c.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.code?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Group by parent
  const rootCategories = filteredCategories.filter(c => !c.parent_category_id);

  return (
    <div className="min-h-screen bg-kkl-bg" dir="rtl">
      <div className="max-w-6xl mx-auto px-4 py-6">
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
              <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center">
                <Wrench className="w-6 h-6 text-orange-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-kkl-text">קטלוג כלים</h1>
                <p className="text-gray-500">ניהול סוגי הכלים המאושרים לשימוש בקק"ל</p>
              </div>
            </div>
            <button
              onClick={() => handleOpenModal()}
              className="px-4 py-2 bg-kkl-green text-white rounded-lg hover:bg-kkl-green-dark transition-colors flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              קטגוריה חדשה
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-xl border border-kkl-border p-4">
            <div className="text-2xl font-bold text-kkl-green">{categories.length}</div>
            <div className="text-sm text-gray-500">סוגי כלים</div>
          </div>
          <div className="bg-white rounded-xl border border-kkl-border p-4">
            <div className="text-2xl font-bold text-green-600">
              {categories.filter(c => c.is_active).length}
            </div>
            <div className="text-sm text-gray-500">פעילים</div>
          </div>
          <div className="bg-white rounded-xl border border-kkl-border p-4">
            <div className="text-2xl font-bold text-blue-600">
              {categories.filter(c => c.requires_license).length}
            </div>
            <div className="text-sm text-gray-500">דורשים רישיון</div>
          </div>
          <div className="bg-white rounded-xl border border-kkl-border p-4">
            <div className="text-2xl font-bold text-purple-600">
              {rootCategories.length}
            </div>
            <div className="text-sm text-gray-500">קטגוריות ראשיות</div>
          </div>
        </div>

        {/* Search */}
        <div className="bg-white rounded-xl shadow-sm border border-kkl-border p-4 mb-6">
          <div className="relative">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="חיפוש כלים..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pr-10 pl-4 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
            />
          </div>
        </div>

        {/* Categories Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {loading ? (
            <div className="col-span-full flex items-center justify-center py-12">
              <div className="w-8 h-8 border-2 border-kkl-green border-t-transparent rounded-full animate-spin" />
            </div>
          ) : filteredCategories.length === 0 ? (
            <div className="col-span-full text-center py-12 text-gray-500">
              {categories.length === 0 ? 'אין קטגוריות כלים. הוסף קטגוריה כדי להתחיל.' : 'לא נמצאו קטגוריות'}
            </div>
          ) : (
            filteredCategories.map((category) => (
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
                      <span className="text-xs font-mono bg-gray-100 px-2 py-0.5 rounded">
                        {category.code}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleOpenModal(category)}
                      className="p-1.5 text-gray-400 hover:text-kkl-green hover:bg-kkl-green-light rounded-lg transition-colors"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(category.id)}
                      className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                    >
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

                <div className="grid grid-cols-2 gap-2 text-sm">
                  {category.default_hourly_rate && (
                    <div className="flex items-center gap-1 text-gray-600">
                      <DollarSign className="w-4 h-4 text-kkl-green" />
                      ₪{category.default_hourly_rate}/שעה
                    </div>
                  )}
                  {category.default_daily_rate && (
                    <div className="flex items-center gap-1 text-gray-600">
                      <Clock className="w-4 h-4 text-kkl-green" />
                      ₪{category.default_daily_rate}/יום
                    </div>
                  )}
                </div>

                <div className="mt-3 pt-3 border-t border-kkl-border flex justify-between items-center">
                  <button
                    onClick={() => toggleActive(category)}
                    className={`text-xs px-2 py-1 rounded-full ${
                      category.is_active
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-500'
                    }`}
                  >
                    {category.is_active ? 'פעיל' : 'מושבת'}
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Info Box */}
        <div className="mt-6 bg-orange-50 border border-orange-200 rounded-xl p-4 flex items-start gap-3">
          <Info className="w-5 h-5 text-orange-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-orange-700">
            <p className="font-medium mb-1">מה זה קטלוג כלים?</p>
            <p>קטלוג הכלים מגדיר את כל סוגי הציוד המאושרים לשימוש בפרויקטים של קק"ל. לכל סוג כלי יש תעריפי ברירת מחדל, דרישות רישיון והסמכה, ופרמטרים לתחזוקה.</p>
          </div>
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
              <button
                onClick={() => setShowModal(false)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-5 space-y-4 max-h-[70vh] overflow-y-auto">
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-kkl-text mb-2">שם *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-4 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                    placeholder="דחפור"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-kkl-text mb-2">קוד *</label>
                  <input
                    type="text"
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                    className="w-full px-4 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent font-mono"
                    placeholder="BULLDOZER"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-kkl-text mb-2">תיאור</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={2}
                  className="w-full px-4 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent resize-none"
                  placeholder="תיאור הכלי..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-kkl-text mb-2">קטגוריית אב</label>
                <select
                  value={formData.parent_category_id || ''}
                  onChange={(e) => setFormData({ ...formData, parent_category_id: e.target.value ? parseInt(e.target.value) : null })}
                  className="w-full pr-4 pl-10 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                >
                  <option value="">ללא (קטגוריה ראשית)</option>
                  {categories
                    .filter(c => c.id !== editingCategory?.id && !c.parent_category_id)
                    .map(c => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))
                  }
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-kkl-text mb-2">תעריף שעתי (₪)</label>
                  <input
                    type="number"
                    min="0"
                    value={formData.default_hourly_rate}
                    onChange={(e) => setFormData({ ...formData, default_hourly_rate: parseFloat(e.target.value) || 0 })}
                    className="w-full px-4 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-kkl-text mb-2">תעריף יומי (₪)</label>
                  <input
                    type="number"
                    min="0"
                    value={formData.default_daily_rate}
                    onChange={(e) => setFormData({ ...formData, default_daily_rate: parseFloat(e.target.value) || 0 })}
                    className="w-full px-4 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                  />
                </div>
              </div>

              <div className="flex flex-wrap gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.requires_license}
                    onChange={(e) => setFormData({ ...formData, requires_license: e.target.checked })}
                    className="w-4 h-4 text-kkl-green rounded focus:ring-kkl-green"
                  />
                  <span className="text-sm text-kkl-text">דורש רישיון</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.requires_certification}
                    onChange={(e) => setFormData({ ...formData, requires_certification: e.target.checked })}
                    className="w-4 h-4 text-kkl-green rounded focus:ring-kkl-green"
                  />
                  <span className="text-sm text-kkl-text">דורש הסמכה</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="w-4 h-4 text-kkl-green rounded focus:ring-kkl-green"
                  />
                  <span className="text-sm text-kkl-text">פעיל</span>
                </label>
              </div>

              {formData.requires_license && (
                <div>
                  <label className="block text-sm font-medium text-kkl-text mb-2">סוג רישיון</label>
                  <input
                    type="text"
                    value={formData.license_type}
                    onChange={(e) => setFormData({ ...formData, license_type: e.target.value })}
                    className="w-full px-4 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                    placeholder="C1, כלים כבדים..."
                  />
                </div>
              )}
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
                {editingCategory ? 'עדכן' : 'צור'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EquipmentCatalog;

