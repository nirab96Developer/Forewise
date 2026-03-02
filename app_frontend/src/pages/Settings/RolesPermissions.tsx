
// src/pages/Settings/RolesPermissions.tsx
// ניהול תפקידים והרשאות
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight, Shield, Plus, Search, Edit, Trash2,
  CheckCircle, XCircle, Save, X, Info, Users, Lock
} from 'lucide-react';
import api from '../../services/api';

interface Role {
  id: number;
  code: string;
  name: string;
  description?: string;
  is_active: boolean;
  permissions?: Permission[];
  user_count?: number;
}

interface Permission {
  id: number;
  code: string;
  name: string;
  description?: string;
  category: string;
  is_active: boolean;
}

const permissionCategories = [
  { code: 'projects', name: 'פרויקטים', icon: '📁' },
  { code: 'work_orders', name: 'הזמנות עבודה', icon: '📝' },
  { code: 'work_logs', name: 'דיווחי שעות', icon: '⏱️' },
  { code: 'suppliers', name: 'ספקים', icon: '🚚' },
  { code: 'users', name: 'משתמשים', icon: '👥' },
  { code: 'reports', name: 'דוחות', icon: '📊' },
  { code: 'settings', name: 'הגדרות', icon: '⚙️' },
];

const RolesPermissions: React.FC = () => {
  const navigate = useNavigate();
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'roles' | 'permissions'>('roles');
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [selectedPermissions, setSelectedPermissions] = useState<number[]>([]);
  const [formData, setFormData] = useState({
    code: '',
    name: '',
    description: '',
    is_active: true,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    
    try {
      const [rolesRes, permissionsRes] = await Promise.all([
        api.get('/roles').catch(() => ({ data: [] })),
        api.get('/permissions').catch(() => ({ data: [] }))
      ]);
      
      // Handle both array and {items: [...]} response formats
      const rolesData = rolesRes?.data?.items || rolesRes?.data || [];
      const permissionsData = permissionsRes?.data?.items || permissionsRes?.data || [];
      
      setRoles(Array.isArray(rolesData) ? rolesData : []);
      setPermissions(Array.isArray(permissionsData) ? permissionsData : []);
    } catch (err) {
      console.error('Error loading data:', err);
      setRoles([]);
      setPermissions([]);
    }
    
    // Always stop loading
    setLoading(false);
  };

  const handleOpenModal = (role?: Role) => {
    if (role) {
      setEditingRole(role);
      setFormData({
        code: role.code,
        name: role.name,
        description: role.description || '',
        is_active: role.is_active,
      });
      setSelectedPermissions(role.permissions?.map(p => p.id) || []);
    } else {
      setEditingRole(null);
      setFormData({
        code: '',
        name: '',
        description: '',
        is_active: true,
      });
      setSelectedPermissions([]);
    }
    setShowModal(true);
    setError('');
  };

  const handleSave = async () => {
    if (!formData.code.trim() || !formData.name.trim()) {
      setError('יש למלא קוד ושם');
      return;
    }

    setSaving(true);
    setError('');

    try {
      const payload = {
        ...formData,
        permission_ids: selectedPermissions,
      };

      if (editingRole) {
        await api.put(`/roles/${editingRole.id}`, payload);
      } else {
        await api.post('/roles', payload);
      }
      setShowModal(false);
      loadData();
    } catch (err: any) {
      console.error('Error saving role:', err);
      setError(err.response?.data?.detail || 'שגיאה בשמירת התפקיד');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('האם אתה בטוח שברצונך למחוק תפקיד זה?')) {
      return;
    }

    try {
      await api.delete(`/roles/${id}`);
      loadData();
    } catch (err) {
      console.error('Error deleting role:', err);
      alert('שגיאה במחיקת התפקיד');
    }
  };

  const togglePermission = (permissionId: number) => {
    setSelectedPermissions(prev =>
      prev.includes(permissionId)
        ? prev.filter(id => id !== permissionId)
        : [...prev, permissionId]
    );
  };

  const getPermissionsByCategory = (categoryCode: string) => {
    return (permissions || []).filter(p => p.category === categoryCode);
  };

  const filteredRoles = (roles || []).filter(r =>
    r.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.code?.toLowerCase().includes(searchTerm.toLowerCase())
  );


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
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                <Shield className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-kkl-text">תפקידים והרשאות</h1>
                <p className="text-gray-500">ניהול תפקידים והרשאות גישה במערכת</p>
              </div>
            </div>
            {activeTab === 'roles' && (
              <button
                onClick={() => handleOpenModal()}
                className="px-3 py-1.5 bg-kkl-green text-white text-sm rounded-lg hover:bg-kkl-green-dark transition-colors flex items-center gap-1.5 whitespace-nowrap"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>תפקיד חדש</span>
              </button>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-xl shadow-sm border border-kkl-border mb-6">
          <div className="flex">
            <button
              onClick={() => setActiveTab('roles')}
              className={`flex-1 flex items-center justify-center gap-2 px-5 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'roles'
                  ? 'border-kkl-green text-kkl-green bg-kkl-green-light/30'
                  : 'border-transparent text-gray-500 hover:text-kkl-green'
              }`}
            >
              <Users className="w-4 h-4" />
              תפקידים ({roles.length})
            </button>
            <button
              onClick={() => setActiveTab('permissions')}
              className={`flex-1 flex items-center justify-center gap-2 px-5 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'permissions'
                  ? 'border-kkl-green text-kkl-green bg-kkl-green-light/30'
                  : 'border-transparent text-gray-500 hover:text-kkl-green'
              }`}
            >
              <Lock className="w-4 h-4" />
              הרשאות ({permissions.length})
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="bg-white rounded-xl shadow-sm border border-kkl-border p-4 mb-6">
          <div className="relative">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder={activeTab === 'roles' ? 'חיפוש תפקידים...' : 'חיפוש הרשאות...'}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pr-10 pl-4 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
            />
          </div>
        </div>

        {/* Content */}
        <div className="bg-white rounded-xl shadow-sm border border-kkl-border overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-2 border-kkl-green border-t-transparent rounded-full animate-spin" />
            </div>
          ) : activeTab === 'roles' ? (
            /* Roles Table */
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-kkl-border">
                  <tr>
                    <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">קוד</th>
                    <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">שם</th>
                    <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">תיאור</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">הרשאות</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">משתמשים</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">סטטוס</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">פעולות</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRoles.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center py-12 text-gray-500">
                        לא נמצאו תפקידים
                      </td>
                    </tr>
                  ) : (
                    filteredRoles.map((role) => (
                      <tr key={role.id} className="border-b border-kkl-border hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
                            {role.code}
                          </span>
                        </td>
                        <td className="px-4 py-3 font-medium text-kkl-text">{role.name}</td>
                        <td className="px-4 py-3 text-sm text-gray-500">{role.description || '-'}</td>
                        <td className="px-4 py-3 text-center">
                          <span className="px-2 py-1 bg-blue-100 text-blue-700 text-sm rounded-full">
                            {role.permissions?.length || 0}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className="px-2 py-1 bg-gray-100 text-gray-700 text-sm rounded-full">
                            {role.user_count || 0}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm ${
                            role.is_active
                              ? 'bg-green-100 text-green-700'
                              : 'bg-gray-100 text-gray-500'
                          }`}>
                            {role.is_active ? 'פעיל' : 'מושבת'}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center justify-center gap-2">
                            <button
                              onClick={() => handleOpenModal(role)}
                              className="p-2 text-gray-400 hover:text-kkl-green hover:bg-kkl-green-light rounded-lg transition-colors"
                              title="עריכה"
                            >
                              <Edit className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDelete(role.id)}
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
          ) : (
            /* Permissions Grid */
            <div className="p-6">
              {permissionCategories.map((category) => {
                const categoryPermissions = getPermissionsByCategory(category.code);
                if (categoryPermissions.length === 0) return null;

                return (
                  <div key={category.code} className="mb-6 last:mb-0">
                    <h3 className="text-lg font-semibold text-kkl-text mb-3 flex items-center gap-2">
                      <span>{category.icon}</span>
                      {category.name}
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      {categoryPermissions.map((permission) => (
                        <div
                          key={permission.id}
                          className={`p-4 rounded-lg border ${
                            permission.is_active
                              ? 'border-kkl-border bg-white'
                              : 'border-gray-200 bg-gray-50 opacity-60'
                          }`}
                        >
                          <div className="flex items-start justify-between">
                            <div>
                              <span className="font-mono text-xs bg-gray-100 px-2 py-0.5 rounded">
                                {permission.code}
                              </span>
                              <h4 className="font-medium text-kkl-text mt-1">{permission.name}</h4>
                              {permission.description && (
                                <p className="text-xs text-gray-500 mt-1">{permission.description}</p>
                              )}
                            </div>
                            {permission.is_active ? (
                              <CheckCircle className="w-5 h-5 text-green-500" />
                            ) : (
                              <XCircle className="w-5 h-5 text-gray-300" />
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Info Box */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-700">
            <p className="font-medium mb-1">על תפקידים והרשאות</p>
            <p>כל משתמש במערכת משויך לתפקיד אחד או יותר. התפקיד מגדיר אילו פעולות המשתמש יכול לבצע במערכת. הרשאות מאורגנות לפי קטגוריות לניהול קל יותר.</p>
          </div>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl my-8">
            <div className="flex items-center justify-between p-5 border-b border-kkl-border">
              <h2 className="text-lg font-bold text-kkl-text">
                {editingRole ? 'עריכת תפקיד' : 'תפקיד חדש'}
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
                  <label className="block text-sm font-medium text-kkl-text mb-2">קוד *</label>
                  <input
                    type="text"
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                    className="w-full px-4 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent font-mono"
                    placeholder="WORK_MANAGER"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-kkl-text mb-2">שם *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-4 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                    placeholder="מנהל עבודה"
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
                  placeholder="תיאור התפקיד..."
                />
              </div>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="w-4 h-4 text-kkl-green rounded focus:ring-kkl-green"
                />
                <span className="text-sm text-kkl-text">פעיל</span>
              </label>

              {/* Permissions Selection */}
              <div>
                <label className="block text-sm font-medium text-kkl-text mb-3">הרשאות</label>
                <div className="space-y-4 max-h-64 overflow-y-auto border border-kkl-border rounded-lg p-4">
                  {permissionCategories.map((category) => {
                    const categoryPermissions = getPermissionsByCategory(category.code);
                    if (categoryPermissions.length === 0) return null;

                    return (
                      <div key={category.code}>
                        <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                          <span>{category.icon}</span>
                          {category.name}
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {categoryPermissions.map((permission) => (
                            <label
                              key={permission.id}
                              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg cursor-pointer border transition-colors ${
                                selectedPermissions.includes(permission.id)
                                  ? 'bg-kkl-green-light border-kkl-green text-kkl-green'
                                  : 'bg-gray-50 border-gray-200 text-gray-600 hover:border-gray-300'
                              }`}
                            >
                              <input
                                type="checkbox"
                                checked={selectedPermissions.includes(permission.id)}
                                onChange={() => togglePermission(permission.id)}
                                className="sr-only"
                              />
                              <span className="text-sm">{permission.name}</span>
                            </label>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
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
                {editingRole ? 'עדכן' : 'צור'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RolesPermissions;

