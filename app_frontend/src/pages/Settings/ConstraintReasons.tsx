
// src/pages/Settings/ConstraintReasons.tsx
// ניהול סיבות אילוץ ספק
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight, AlertTriangle, Plus, Search, Edit, Trash2,
  CheckCircle, XCircle, Save, X, Info
} from 'lucide-react';
import api from '../../services/api';
import { useRoleAccess } from '../../hooks/useRoleAccess';

interface ConstraintReason {
  id: number;
  code: string;
  name_he: string;
  name_en?: string;
  description?: string;
  category: string;
  requires_additional_text: boolean;
  requires_approval: boolean;
  is_active: boolean;
  display_order: number;
}

const categoryLabels: Record<string, string> = {
  technical: 'טכני',
  availability: 'זמינות',
  geographical: 'גיאוגרפי',
  capacity: 'קיבולת',
  other: 'אחר',
};

const ConstraintReasons: React.FC = () => {
  const navigate = useNavigate();
  const [reasons, setReasons] = useState<ConstraintReason[]>([]);
  const [loading, setLoading] = useState(true);
  const { canManageSystem } = useRoleAccess();
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingReason, setEditingReason] = useState<ConstraintReason | null>(null);
  const [formData, setFormData] = useState({
    code: '',
    name_he: '',
    name_en: '',
    description: '',
    category: 'other',
    requires_additional_text: false,
    requires_approval: false,
    is_active: true,
    display_order: 0,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadReasons();
  }, []);

  const loadReasons = async () => {
    setLoading(true);
    try {
      const response = await api.get('/supplier-constraint-reasons', {
        params: { is_active: null } // Get all, including inactive
      });
      // Handle both array and {items: [...]} response formats
      const data = response.data?.items || response.data || [];
      setReasons(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error loading constraint reasons:', err);
      setReasons([]);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = (reason?: ConstraintReason) => {
    if (reason) {
      setEditingReason(reason);
      setFormData({
        code: reason.code,
        name_he: reason.name_he,
        name_en: reason.name_en || '',
        description: reason.description || '',
        category: reason.category,
        requires_additional_text: reason.requires_additional_text,
        requires_approval: reason.requires_approval,
        is_active: reason.is_active,
        display_order: reason.display_order,
      });
    } else {
      setEditingReason(null);
      setFormData({
        code: '',
        name_he: '',
        name_en: '',
        description: '',
        category: 'other',
        requires_additional_text: false,
        requires_approval: false,
        is_active: true,
        display_order: reasons.length + 1,
      });
    }
    setShowModal(true);
    setError('');
  };

  const handleSave = async () => {
    if (!formData.code.trim() || !formData.name_he.trim()) {
      setError('יש למלא קוד ושם בעברית');
      return;
    }

    setSaving(true);
    setError('');

    try {
      if (editingReason) {
        await api.put(`/supplier-constraint-reasons/${editingReason.id}`, formData);
      } else {
        await api.post('/supplier-constraint-reasons', formData);
      }
      setShowModal(false);
      loadReasons();
    } catch (err: any) {
      console.error('Error saving constraint reason:', err);
      setError(err.response?.data?.detail || 'שגיאה בשמירת סיבת האילוץ');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('האם אתה בטוח שברצונך למחוק סיבת אילוץ זו?')) {
      return;
    }

    try {
      await api.delete(`/supplier-constraint-reasons/${id}`);
      loadReasons();
    } catch (err) {
      console.error('Error deleting constraint reason:', err);
      alert('שגיאה במחיקת סיבת האילוץ');
    }
  };

  const toggleActive = async (reason: ConstraintReason) => {
    try {
      await api.patch(`/supplier-constraint-reasons/${reason.id}`, {
        is_active: !reason.is_active
      });
      loadReasons();
    } catch (err) {
      console.error('Error toggling active status:', err);
    }
  };

  const filteredReasons = reasons.filter(r =>
    r.name_he.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.code.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-fw-bg" dir="rtl">
      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/settings/suppliers')}
            className="text-fw-green hover:text-fw-green-dark flex items-center gap-1 mb-4 text-sm"
          >
            <ArrowRight className="w-4 h-4" />
            חזרה להגדרות ספקים
          </button>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-orange-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-fw-text">סיבות אילוץ ספק</h1>
                <p className="text-gray-500">ניהול סיבות לבחירת ספק ידנית במקום סבב הוגן</p>
              </div>
            </div>
            {canManageSystem && (
              <button
                onClick={() => handleOpenModal()}
                className="px-3 py-1.5 bg-fw-green text-white text-sm rounded-lg hover:bg-fw-green-dark transition-colors flex items-center gap-1.5 whitespace-nowrap"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>סיבה חדשה</span>
              </button>
            )}
          </div>
        </div>

        {/* Search */}
        <div className="bg-white rounded-xl shadow-sm border border-fw-border p-4 mb-6">
          <div className="relative">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="חיפוש סיבות אילוץ..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pr-10 pl-4 py-2.5 border border-fw-border rounded-lg focus:ring-2 focus:ring-fw-green focus:border-transparent"
            />
          </div>
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl shadow-sm border border-fw-border overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="relative overflow-visible" style={{ padding: 4 }}>
          <div className="w-10 h-10 rounded-full border-[3px] border-emerald-200 border-t-emerald-500 animate-spin" style={{animationDuration:'0.9s'}} />
          <div className="absolute inset-0 flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 100" width="20" height="17">
                <defs>
                  <linearGradient id="cr1_t" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#1565c0"/><stop offset="100%" stopColor="#0097a7"/></linearGradient>
                  <linearGradient id="cr1_m" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#0097a7"/><stop offset="50%" stopColor="#2e7d32"/><stop offset="100%" stopColor="#66bb6a"/></linearGradient>
                  <linearGradient id="cr1_b" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#2e7d32"/><stop offset="40%" stopColor="#66bb6a"/><stop offset="100%" stopColor="#8B5e3c"/></linearGradient>
                </defs>
                <path d="M46 20 Q60 9 74 20" stroke="url(#cr1_t)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <path d="M30 47 Q42 34 60 43 Q78 34 90 47" stroke="url(#cr1_m)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <path d="M14 74 Q28 60 46 69 Q60 76 74 69 Q92 60 106 74" stroke="url(#cr1_b)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <line x1="60" y1="76" x2="60" y2="90" stroke="#8B5e3c" strokeWidth="3.5" strokeLinecap="round"/>
                <circle cx="60" cy="95" r="5" fill="#8B5e3c"/>
              </svg>
          </div>
        </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-fw-border">
                  <tr>
                    <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">קוד</th>
                    <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">שם</th>
                    <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">קטגוריה</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">דורש הסבר</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">דורש אישור</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">סטטוס</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">פעולות</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredReasons.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center py-12 text-gray-500">
                        לא נמצאו סיבות אילוץ
                      </td>
                    </tr>
                  ) : (
                    filteredReasons.map((reason) => (
                      <tr key={reason.id} className="border-b border-fw-border hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
                            {reason.code}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div>
                            <span className="font-medium text-fw-text">{reason.name_he}</span>
                            {reason.description && (
                              <p className="text-xs text-gray-500 mt-1">{reason.description}</p>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className="px-2 py-1 bg-blue-100 text-blue-700 text-sm rounded-full">
                            {categoryLabels[reason.category] || reason.category}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          {reason.requires_additional_text ? (
                            <CheckCircle className="w-5 h-5 text-green-500 mx-auto" />
                          ) : (
                            <XCircle className="w-5 h-5 text-gray-300 mx-auto" />
                          )}
                        </td>
                        <td className="px-4 py-3 text-center">
                          {reason.requires_approval ? (
                            <CheckCircle className="w-5 h-5 text-green-500 mx-auto" />
                          ) : (
                            <XCircle className="w-5 h-5 text-gray-300 mx-auto" />
                          )}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <button
                            onClick={() => toggleActive(reason)}
                            className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm ${
                              reason.is_active
                                ? 'bg-green-100 text-green-700'
                                : 'bg-gray-100 text-gray-500'
                            }`}
                          >
                            {reason.is_active ? 'פעיל' : 'מושבת'}
                          </button>
                        </td>
                        <td className="px-4 py-3">
                          {canManageSystem && (
                            <div className="flex items-center justify-center gap-2">
                              <button
                                onClick={() => handleOpenModal(reason)}
                                className="p-2 text-gray-400 hover:text-fw-green hover:bg-fw-green-light rounded-lg transition-colors"
                                title="עריכה"
                              >
                                <Edit className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleDelete(reason.id)}
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
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-700">
            <p className="font-medium mb-1">מתי משתמשים בסיבות אילוץ?</p>
            <p>כאשר מנהל עבודה בוחר ספק ידנית במקום לתת למערכת לבחור לפי סבב הוגן, הוא חייב לציין סיבה. סיבות אלו מתועדות ומאפשרות מעקב ובקרה על חריגות מהסבב.</p>
          </div>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg">
            <div className="flex items-center justify-between p-5 border-b border-fw-border">
              <h2 className="text-lg font-bold text-fw-text">
                {editingReason ? 'עריכת סיבת אילוץ' : 'סיבת אילוץ חדשה'}
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

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-fw-text mb-2">קוד *</label>
                  <input
                    type="text"
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                    className="w-full px-4 py-2.5 border border-fw-border rounded-lg focus:ring-2 focus:ring-fw-green focus:border-transparent"
                    placeholder="TECH_01"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-fw-text mb-2">קטגוריה</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full pr-4 pl-10 py-2.5 border border-fw-border rounded-lg focus:ring-2 focus:ring-fw-green focus:border-transparent"
                  >
                    <option value="technical">טכני</option>
                    <option value="availability">זמינות</option>
                    <option value="geographical">גיאוגרפי</option>
                    <option value="capacity">קיבולת</option>
                    <option value="other">אחר</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-fw-text mb-2">שם בעברית *</label>
                <input
                  type="text"
                  value={formData.name_he}
                  onChange={(e) => setFormData({ ...formData, name_he: e.target.value })}
                  className="w-full px-4 py-2.5 border border-fw-border rounded-lg focus:ring-2 focus:ring-fw-green focus:border-transparent"
                  placeholder="ספק יחיד באזור"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-fw-text mb-2">שם באנגלית</label>
                <input
                  type="text"
                  value={formData.name_en}
                  onChange={(e) => setFormData({ ...formData, name_en: e.target.value })}
                  className="w-full px-4 py-2.5 border border-fw-border rounded-lg focus:ring-2 focus:ring-fw-green focus:border-transparent"
                  placeholder="Single supplier in area"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-fw-text mb-2">תיאור</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={2}
                  className="w-full px-4 py-2.5 border border-fw-border rounded-lg focus:ring-2 focus:ring-fw-green focus:border-transparent resize-none"
                  placeholder="תיאור מפורט של סיבת האילוץ..."
                />
              </div>

              <div className="flex flex-wrap gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.requires_additional_text}
                    onChange={(e) => setFormData({ ...formData, requires_additional_text: e.target.checked })}
                    className="w-4 h-4 text-fw-green rounded focus:ring-fw-green"
                  />
                  <span className="text-sm text-fw-text">דורש הסבר נוסף</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.requires_approval}
                    onChange={(e) => setFormData({ ...formData, requires_approval: e.target.checked })}
                    className="w-4 h-4 text-fw-green rounded focus:ring-fw-green"
                  />
                  <span className="text-sm text-fw-text">דורש אישור מנהל</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="w-4 h-4 text-fw-green rounded focus:ring-fw-green"
                  />
                  <span className="text-sm text-fw-text">פעיל</span>
                </label>
              </div>
            </div>

            <div className="flex justify-end gap-3 p-5 border-t border-fw-border">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 border border-fw-border text-fw-text rounded-lg hover:bg-gray-50 transition-colors"
              >
                ביטול
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-4 py-2 bg-fw-green text-white rounded-lg hover:bg-fw-green-dark transition-colors flex items-center gap-2 disabled:opacity-50"
              >
                {saving ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                {editingReason ? 'עדכן' : 'צור'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConstraintReasons;

