
import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowRight, AlertCircle, User, Mail, Phone, Lock, Trash2 } from 'lucide-react';
import api from '../../services/api';
import UnifiedLoader from '../../components/common/UnifiedLoader';

interface Role {
  id: number;
  code: string;
  name: string;
}

interface Department {
  id: number;
  name: string;
}

interface Region {
  id: number;
  name: string;
}

interface Area {
  id: number;
  name: string;
  region_id: number;
}

const EditUser: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    full_name: '',
    phone: '',
    password: '',
    confirm_password: '',
    role_id: '',
    department_id: '',
    region_id: '',
    area_id: '',
    is_active: true,
    two_factor_enabled: false,
  });
  const [roles, setRoles] = useState<Role[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [regions, setRegions] = useState<Region[]>([]);
  const [areas, setAreas] = useState<Area[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  useEffect(() => {
    if (id) {
      loadData();
      
      // Safety timeout
      const timeout = setTimeout(() => {
        setLoadingData(false);
      }, 10000);
      
      return () => clearTimeout(timeout);
    }
  }, [id]);

  useEffect(() => {
    if (formData.region_id) {
      loadAreas(Number(formData.region_id));
    }
  }, [formData.region_id]);

  const loadData = async () => {
    try {
      setLoadingData(true);
      const [userRes, rolesRes, deptsRes, regionsRes] = await Promise.all([
        api.get(`/users/${id}`),
        api.get('/roles'),
        api.get('/departments'),
        api.get('/regions'),
      ]);
      
      const user = userRes.data;
      setFormData({
        username: user.username || '',
        email: user.email || '',
        full_name: user.full_name || '',
        phone: user.phone || '',
        password: '',
        confirm_password: '',
        role_id: user.role_id || '',
        department_id: user.department_id || '',
        region_id: user.region_id || '',
        area_id: user.area_id || '',
        is_active: user.is_active !== false,
        two_factor_enabled: user.two_factor_enabled || false,
      });
      
      setRoles(rolesRes.data.items || rolesRes.data || []);
      setDepartments(deptsRes.data.items || deptsRes.data || []);
      setRegions(regionsRes.data.items || regionsRes.data || []);
      
      if (user.region_id) {
        loadAreas(user.region_id);
      }
    } catch (err: any) {
      setError('שגיאה בטעינת נתונים');
      console.error(err);
    } finally {
      setLoadingData(false);
    }
  };

  const loadAreas = async (regionId: number) => {
    try {
      const response = await api.get('/areas', { params: { region_id: regionId } });
      const areasData = response.data.items || response.data || [];
      setAreas(areasData.filter((a: Area) => a.region_id === regionId));
    } catch (err: any) {
      console.error('Error loading areas:', err);
      setAreas([]);
    }
  };

  const handleDeactivateUser = async () => {
    setDeleteLoading(true);
    try {
      await api.patch(`/users/${id}`, { is_active: false });
      setShowDeleteConfirm(false);
      navigate('/settings/admin/users', { replace: true });
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'שגיאה בהסרת משתמש');
      setShowDeleteConfirm(false);
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (formData.password && formData.password !== formData.confirm_password) {
      setError('הסיסמאות לא תואמות');
      return;
    }

    if (formData.password && formData.password.length < 8) {
      setError('הסיסמה חייבת להכיל לפחות 8 תווים');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const userData: any = {
        username: formData.username,
        email: formData.email,
        full_name: formData.full_name,
        phone: formData.phone || undefined,
        role_id: formData.role_id ? Number(formData.role_id) : undefined,
        department_id: formData.department_id ? Number(formData.department_id) : undefined,
        region_id: formData.region_id ? Number(formData.region_id) : undefined,
        area_id: formData.area_id ? Number(formData.area_id) : undefined,
        is_active: formData.is_active,
        two_factor_enabled: formData.two_factor_enabled,
      };

      if (formData.password) {
        userData.password = formData.password;
      }

      await api.put(`/users/${id}`, userData);
      alert('משתמש עודכן בהצלחה!');
      navigate('/admin');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'שגיאה בעדכון משתמש');
    } finally {
      setLoading(false);
    }
  };

  if (loadingData) return <UnifiedLoader size="full" />;

  return (
    <div className="min-h-screen bg-gray-50 p-6" dir="rtl">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-xl shadow-lg p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">עריכת משתמש</h1>
            <p className="text-gray-600">עדכון פרטי משתמש</p>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-red-600" />
              <span className="text-red-800">{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  שם משתמש *
                </label>
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Mail className="inline w-4 h-4 ml-1" />
                  אימייל *
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <User className="inline w-4 h-4 ml-1" />
                שם מלא *
              </label>
              <input
                type="text"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Phone className="inline w-4 h-4 ml-1" />
                טלפון
              </label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                placeholder="050-0000000"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
              />
            </div>

            <div className="border-t pt-4">
              <p className="text-sm text-gray-600 mb-4">שינוי סיסמה (השאר ריק אם לא רוצה לשנות)</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <Lock className="inline w-4 h-4 ml-1" />
                    סיסמה חדשה
                  </label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                    minLength={8}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <Lock className="inline w-4 h-4 ml-1" />
                    אימות סיסמה
                  </label>
                  <input
                    type="password"
                    value={formData.confirm_password}
                    onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                    minLength={8}
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  תפקיד
                </label>
                <select
                  value={formData.role_id}
                  onChange={(e) => setFormData({ ...formData, role_id: e.target.value })}
                  className="w-full pr-4 pl-10 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                  disabled={loadingData}
                >
                  <option value="">בחר תפקיד</option>
                  {roles.map((role) => (
                    <option key={role.id} value={role.id}>
                      {role.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  מחלקה
                </label>
                <select
                  value={formData.department_id}
                  onChange={(e) => setFormData({ ...formData, department_id: e.target.value })}
                  className="w-full pr-4 pl-10 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                  disabled={loadingData}
                >
                  <option value="">בחר מחלקה</option>
                  {departments.map((dept) => (
                    <option key={dept.id} value={dept.id}>
                      {dept.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  מרחב
                </label>
                <select
                  value={formData.region_id}
                  onChange={(e) => setFormData({ ...formData, region_id: e.target.value, area_id: '' })}
                  className="w-full pr-4 pl-10 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                  disabled={loadingData}
                >
                  <option value="">בחר מרחב</option>
                  {regions.map((region) => (
                    <option key={region.id} value={region.id}>
                      {region.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  אזור
                </label>
                <select
                  value={formData.area_id}
                  onChange={(e) => setFormData({ ...formData, area_id: e.target.value })}
                  className="w-full pr-4 pl-10 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                  disabled={loadingData || !formData.region_id}
                >
                  <option value="">בחר אזור</option>
                  {areas.map((area) => (
                    <option key={area.id} value={area.id}>
                      {area.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="h-4 w-4 text-kkl-green focus:ring-kkl-green border-gray-300 rounded"
                />
                <label htmlFor="is_active" className="mr-2 text-sm text-gray-700">
                  משתמש פעיל
                </label>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="two_factor_enabled"
                  checked={formData.two_factor_enabled}
                  onChange={(e) => setFormData({ ...formData, two_factor_enabled: e.target.checked })}
                  className="h-4 w-4 text-kkl-green focus:ring-kkl-green border-gray-300 rounded"
                />
                <label htmlFor="two_factor_enabled" className="mr-2 text-sm text-gray-700">
                  הפעל אימות דו-שלבי (2FA)
                </label>
              </div>
            </div>

            <div className="flex gap-4">
              <button
                type="button"
                onClick={() => navigate('/admin')}
                className="flex-1 px-6 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
              >
                ביטול
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 px-6 py-3 bg-kkl-green text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? 'שומר...' : 'שמור שינויים'}
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>

            {/* Delete / Deactivate */}
            <div className="mt-6 pt-6 border-t border-red-100">
              <button
                type="button"
                onClick={() => setShowDeleteConfirm(true)}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 border-2 border-red-200 text-red-600 rounded-lg hover:bg-red-50 hover:border-red-300 transition-colors text-sm font-medium"
              >
                <Trash2 className="w-4 h-4" />
                הסרת משתמש מהמערכת
              </button>
            </div>
          </form>

          {/* Delete Confirmation Modal */}
          {showDeleteConfirm && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setShowDeleteConfirm(false)}>
              <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm" onClick={e => e.stopPropagation()}>
                <div className="p-6 text-center">
                  <div className="w-14 h-14 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Trash2 className="w-7 h-7 text-red-600" />
                  </div>
                  <h3 className="text-lg font-bold text-gray-900 mb-2">הסרת משתמש</h3>
                  <p className="text-sm text-gray-600 mb-1">
                    האם להסיר את <strong>{formData.full_name || formData.username}</strong> מהמערכת?
                  </p>
                  <p className="text-xs text-gray-400 mb-5">
                    המשתמש יושבת ולא יוכל להתחבר. ניתן לשחזר בעתיד.
                  </p>
                  <div className="flex gap-3">
                    <button
                      onClick={() => setShowDeleteConfirm(false)}
                      className="flex-1 px-4 py-2.5 border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50 text-sm font-medium"
                    >
                      ביטול
                    </button>
                    <button
                      onClick={handleDeactivateUser}
                      disabled={deleteLoading}
                      className="flex-1 px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium disabled:opacity-50 flex items-center justify-center gap-1.5"
                    >
                      {deleteLoading ? 'מסיר...' : 'כן, הסר משתמש'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EditUser;








