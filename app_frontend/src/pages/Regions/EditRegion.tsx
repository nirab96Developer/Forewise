
// src/pages/Regions/EditRegion.tsx
// עריכת מרחב עם תקציב
import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowRight, Map, Save, User, Trash2 } from 'lucide-react';
import api from '../../services/api';
import TreeLoader from '../../components/common/TreeLoader';

interface User {
  id: number;
  full_name: string;
  username: string;
}

const EditRegion: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    description: '',
    manager_id: '',
    total_budget: '',
    version: 1,
  });
  const [managers, setManagers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [loadingManagers, setLoadingManagers] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
    loadManagers();
  }, [id]);

  const loadData = async () => {
    try {
      const response = await api.get(`/regions/${id}`);
      const region = response.data;
      setFormData({
        name: region.name || '',
        code: region.code || '',
        description: region.description || '',
        manager_id: region.manager_id?.toString() || '',
        total_budget: region.total_budget?.toString() || '',
        version: region.version || 1,
      });
    } catch (err) {
      setError('שגיאה בטעינת המרחב');
    } finally {
      setLoadingData(false);
    }
  };

  const loadManagers = async () => {
    try {
      const response = await api.get('/users', { params: { status: 'active', per_page: 100 } });
      const users = response.data?.items || response.data || [];
      const filtered = users.filter((u: any) => 
        ['ADMIN', 'REGION_MANAGER'].includes(u.role?.code)
      );
      setManagers(filtered);
    } catch (err) {
      console.error('Error loading managers:', err);
    } finally {
      setLoadingManagers(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const payload = {
        name: formData.name,
        code: formData.code || undefined,
        description: formData.description || undefined,
        manager_id: formData.manager_id ? parseInt(formData.manager_id) : null,
        total_budget: formData.total_budget ? parseFloat(formData.total_budget) : null,
        version: formData.version,
      };

      await api.put(`/regions/${id}`, payload);
      navigate('/settings/organization/regions');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'שגיאה בעדכון המרחב');
    } finally {
      setLoading(false);
    }
  };

  if (loadingData) {
    return <TreeLoader fullScreen />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-emerald-50/30" dir="rtl">
      <div className="max-w-2xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-6">
          <button 
            onClick={() => navigate('/settings/organization/regions')}
            className="text-emerald-600 hover:text-emerald-700 flex items-center gap-1 mb-4 text-sm font-medium"
          >
            <ArrowRight className="w-4 h-4" />
            חזרה למרחבים
          </button>
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-200">
              <Map className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">עריכת מרחב</h1>
              <p className="text-gray-500">{formData.name}</p>
            </div>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
          <div className="p-6 space-y-6">
            {/* Name */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                שם המרחב *
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              />
            </div>

            {/* Code */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                קוד מרחב
              </label>
              <input
                type="text"
                name="code"
                value={formData.code}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent font-mono"
              />
            </div>

            {/* Budget - Highlighted */}
            <div className="bg-emerald-50 rounded-xl p-4 border border-emerald-200">
              <label className="flex items-center gap-2 text-sm font-semibold text-emerald-700 mb-2">
                <span className="w-4 h-4 font-bold leading-none inline-flex items-center justify-center">₪</span>
תקציב כולל למרחב ()
              </label>
              <input
                type="number"
                name="total_budget"
                value={formData.total_budget}
                onChange={handleChange}
                min="0"
                step="0.01"
                placeholder="לדוגמה: 10000000"
                className="w-full px-4 py-3 border border-emerald-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white text-lg font-bold"
              />
              <p className="text-xs text-emerald-600 mt-2">
                התקציב הכולל שמוקצה למרחב זה.
              </p>
            </div>

            {/* Manager */}
            <div>
              <label className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-2">
                <User className="w-4 h-4" />
                מנהל מרחב
              </label>
              <select
                name="manager_id"
                value={formData.manager_id}
                onChange={handleChange}
                disabled={loadingManagers}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              >
                <option value="">{loadingManagers ? 'טוען...' : 'בחר מנהל'}</option>
                {managers.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.full_name || m.username}
                  </option>
                ))}
              </select>
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                תיאור
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows={3}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent resize-none"
              />
            </div>

            {/* Error */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl">
                {error}
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="bg-gray-50 px-6 py-4 flex justify-between">
            <button
              type="button"
              onClick={() => navigate(`/regions/${id}`)}
              className="px-5 py-2.5 text-red-600 hover:bg-red-50 rounded-xl font-medium flex items-center gap-2"
            >
              <Trash2 className="w-4 h-4" />
              מחיקה
            </button>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => navigate('/settings/organization/regions')}
                className="px-5 py-2.5 border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-100 font-medium"
              >
                ביטול
              </button>
              <button
                type="submit"
                disabled={loading || !formData.name}
                className="px-5 py-2.5 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 font-medium flex items-center gap-2 disabled:opacity-50"
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Save className="w-5 h-5" />
                )}
                שמור שינויים
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditRegion;

