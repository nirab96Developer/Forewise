
// src/pages/Projects/NewProject.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Loader2 } from 'lucide-react';
import projectService, { ProjectCreate } from '../../services/projectService';
import api from '../../services/api';

interface User {
  id: number;
  full_name: string;
  username: string;
  email: string;
  role?: {
    code: string;
    name: string;
  };
}

interface Region {
  id: number;
  name: string;
  name_he?: string;
  code: string;
}

interface Area {
  id: number;
  name: string;
  name_he?: string;
  code: string;
  region_id: number;
}

const NewProject: React.FC = () => {
  const navigate = useNavigate();

  let userData: any = {};
  try { userData = JSON.parse(localStorage.getItem('user') || '{}'); } catch {}
  const userRole = (userData.role || userData.role_code || '').toUpperCase();
  const userRegionId = userData.region_id;
  const userAreaId = userData.area_id;
  const isAreaManager = userRole === 'AREA_MANAGER';
  const isRegionManager = userRole === 'REGION_MANAGER';

  const [formData, setFormData] = useState<ProjectCreate>({
    name: '',
    code: '',
    description: '',
    planned_start_date: '',
    planned_end_date: '',
    allocated_budget: undefined,
    region_id: isAreaManager || isRegionManager ? userRegionId : undefined,
    area_id: isAreaManager ? userAreaId : undefined,
    manager_id: undefined
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [regions, setRegions] = useState<Region[]>([]);
  const [loadingRegions, setLoadingRegions] = useState(true);
  const [filteredAreas, setFilteredAreas] = useState<Area[]>([]);
  const [loadingAreas, setLoadingAreas] = useState(false);

  useEffect(() => {
    loadUsers();
    loadRegions();
    // For Area/Region Manager — load their areas immediately
    if ((isAreaManager || isRegionManager) && userRegionId) {
      loadAreas(userRegionId);
    }
  }, []);

  // Load areas when region changes (only for non-locked users)
  useEffect(() => {
    if (isAreaManager || isRegionManager) return; // already loaded above
    if (formData.region_id) {
      loadAreas(formData.region_id);
    } else {
      setFilteredAreas([]);
      if (formData.area_id) {
        setFormData(prev => ({ ...prev, area_id: undefined }));
      }
    }
  }, [formData.region_id]);

  const loadUsers = async () => {
    try {
      setLoadingUsers(true);
      const response = await api.get('/users', {
        params: {
          page: 1,
          per_page: 100,
          status: 'active'
        }
      });
      
      const usersData = Array.isArray(response.data) ? response.data : (response.data?.items || []);
      
      // Filter users who can be managers
      const managers = usersData.filter((user: User) => {
        const roleCode = user.role?.code || '';
        return ['ADMIN', 'REGION_MANAGER', 'AREA_MANAGER', 'WORK_MANAGER'].includes(roleCode);
      });
      
      setUsers(managers);
    } catch (error) {
      console.error('Error loading users:', error);
    } finally {
      setLoadingUsers(false);
    }
  };

  const loadRegions = async () => {
    try {
      setLoadingRegions(true);
      const response = await api.get('/regions');
      const regionsData = Array.isArray(response.data) ? response.data : (response.data?.items || []);
      setRegions(regionsData);
    } catch (error) {
      console.error('Error loading regions:', error);
    } finally {
      setLoadingRegions(false);
    }
  };

  const loadAreas = async (regionId: number) => {
    try {
      setLoadingAreas(true);
      const response = await api.get('/areas', {
        params: {
          region_id: regionId
        }
      });
      const areasData = Array.isArray(response.data) ? response.data : (response.data?.items || []);
      setFilteredAreas(areasData);
    } catch (error) {
      console.error('Error loading areas:', error);
      setFilteredAreas([]);
    } finally {
      setLoadingAreas(false);
    }
  };

  // Fix 7: client-side validation before submit
  const getValidationErrors = () => {
    const errs: string[] = [];
    if (!formData.region_id) errs.push('מרחב');
    if (!formData.area_id) errs.push('אזור');
    if (!formData.manager_id) errs.push('מנהל עבודה');
    return errs;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const missing = getValidationErrors();
    if (missing.length > 0) {
      const msg = `שדות חובה חסרים: ${missing.join(', ')}`;
      setError(msg);
      if ((window as any).showToast) (window as any).showToast(msg, 'error');
      return;
    }
    setLoading(true);
    setError(null);

    try {
      const newProject = await projectService.createProject(formData);
      
      if ((window as any).showToast) {
        (window as any).showToast('הפרויקט נוצר בהצלחה!', 'success');
      } else {
        alert('הפרויקט נוצר בהצלחה!');
      }
      
      navigate(`/projects/${newProject.code || newProject.id}`);
    } catch (error: any) {
      console.error('Error creating project:', error);
      const errorMessage = error.response?.data?.detail || error.response?.data?.message || 'שגיאה ביצירת הפרויקט';
      setError(errorMessage);
      
      if ((window as any).showToast) {
        (window as any).showToast(errorMessage, 'error');
      } else {
        alert(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'allocated_budget' || name === 'progress_percentage'
        ? (value ? parseFloat(value) : undefined)
        : name === 'manager_id' || name === 'region_id' || name === 'area_id'
        ? (value ? parseInt(value) : undefined)
        : value
    }));
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6" dir="rtl">
      <div className="w-full max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center mb-4">
            <button 
              onClick={() => navigate('/projects')}
              className="text-fw-green hover:text-fw-green-hover flex items-center"
            >
              <ArrowRight className="w-4 h-4 ml-1" />
              חזרה לרשימת פרויקטים
            </button>
          </div>
          <h1 className="text-3xl font-bold text-primary">מלא את הפרטים ליצירת פרויקט חדש</h1>
        </div>

        {/* Form */}
        <div className="card">
          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Project Name */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-primary mb-2">
                שם הפרויקט *
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name || ''}
                onChange={handleChange}
                required
                placeholder="הכנס שם הפרויקט"
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-fw-green focus:border-fw-green transition-all"
              />
            </div>

            {/* Project Code */}
            <div>
              <label htmlFor="code" className="block text-sm font-medium text-primary mb-2">
                קוד הפרויקט (אופציונלי)
              </label>
              <input
                type="text"
                id="code"
                name="code"
                value={formData.code || ''}
                onChange={handleChange}
                placeholder="ייווצר אוטומטית אם לא מוגדר"
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-fw-green focus:border-fw-green transition-all"
              />
            </div>

            {/* Description */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-primary mb-2">
                תיאור הפרויקט *
              </label>
              <textarea
                id="description"
                name="description"
                value={formData.description || ''}
                onChange={handleChange}
                required
                rows={4}
                placeholder="תאר את הפרויקט..."
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-fw-green focus:border-fw-green transition-all"
              />
            </div>

            {/* Date Range */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="planned_start_date" className="block text-sm font-medium text-primary mb-2">
                  תאריך התחלה מתוכנן *
                </label>
                <input
                  type="date"
                  id="planned_start_date"
                  name="planned_start_date"
                  value={formData.planned_start_date || ''}
                  onChange={handleChange}
                  required
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-fw-green focus:border-fw-green transition-all"
                />
              </div>
              <div>
                <label htmlFor="planned_end_date" className="block text-sm font-medium text-primary mb-2">
                  תאריך סיום מתוכנן *
                </label>
                <input
                  type="date"
                  id="planned_end_date"
                  name="planned_end_date"
                  value={formData.planned_end_date || ''}
                  onChange={handleChange}
                  required
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-fw-green focus:border-fw-green transition-all"
                />
              </div>
            </div>

            {/* Region and Area - Cascade */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="region_id" className="block text-sm font-medium text-primary mb-2">
                  מרחב
                </label>
                <select
                  id="region_id"
                  name="region_id"
                  value={formData.region_id || ''}
                  onChange={handleChange}
                  disabled={loadingRegions || isAreaManager || isRegionManager}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-fw-green focus:border-fw-green transition-all disabled:bg-gray-100 disabled:cursor-not-allowed"
                >
                  <option value="">{loadingRegions ? 'טוען מרחבים...' : 'בחר מרחב'}</option>
                  {regions.map((region) => (
                    <option key={region.id} value={region.id}>
                      {region.name_he || region.name || region.code}
                    </option>
                  ))}
                </select>
                {!loadingRegions && regions.length === 0 && (
                  <p className="text-xs text-secondary mt-1">אין מרחבים זמינים במערכת</p>
                )}
              </div>
              <div>
                <label htmlFor="area_id" className="block text-sm font-medium text-primary mb-2">
                  אזור
                </label>
                <select
                  id="area_id"
                  name="area_id"
                  value={formData.area_id || ''}
                  onChange={handleChange}
                  disabled={!formData.region_id || loadingAreas || isAreaManager}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-fw-green focus:border-fw-green transition-all disabled:bg-gray-100 disabled:cursor-not-allowed"
                >
                  <option value="">
                    {!formData.region_id 
                      ? 'בחר מרחב תחילה' 
                      : loadingAreas 
                      ? 'טוען אזורים...' 
                      : 'בחר אזור'}
                  </option>
                  {filteredAreas.map((area) => (
                    <option key={area.id} value={area.id}>
                      {area.name_he || area.name || area.code}
                    </option>
                  ))}
                </select>
                {formData.region_id && !loadingAreas && filteredAreas.length === 0 && (
                  <p className="text-xs text-secondary mt-1">אין אזורים זמינים במרחב זה</p>
                )}
              </div>
            </div>

            {/* Manager */}
            <div>
              <label htmlFor="manager_id" className="block text-sm font-medium text-primary mb-2">
                מנהל הפרויקט
              </label>
              <select
                id="manager_id"
                name="manager_id"
                value={formData.manager_id || ''}
                onChange={handleChange}
                disabled={loadingUsers}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-fw-green focus:border-fw-green transition-all disabled:bg-gray-100 disabled:cursor-not-allowed"
              >
                <option value="">{loadingUsers ? 'טוען מנהלים...' : 'בחר מנהל'}</option>
                {users.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.full_name || user.username}
                  </option>
                ))}
              </select>
              {!loadingUsers && users.length === 0 && (
                <p className="text-xs text-error-red mt-1">אין מנהלים זמינים במערכת</p>
              )}
            </div>

            {/* Budget */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="allocated_budget" className="block text-sm font-medium text-primary mb-2">
                  תקציב מוקצה (ש"ח)
                </label>
                <input
                  type="number"
                  id="allocated_budget"
                  name="allocated_budget"
                  value={formData.allocated_budget || ''}
                  onChange={handleChange}
                  placeholder="הכנס תקציב"
                  min="0"
                  step="0.01"
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-fw-green focus:border-fw-green transition-all"
                />
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                <p className="text-error-red text-sm">{error}</p>
              </div>
            )}

            {/* Submit Button */}
            <div className="flex gap-4 pt-4">
              <button
                type="button"
                onClick={() => navigate('/projects')}
                className="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-xl font-medium transition-colors"
              >
                ביטול
              </button>
              <button
                type="submit"
                disabled={loading || getValidationErrors().length > 0}
                title={getValidationErrors().length > 0 ? `חסרים: ${getValidationErrors().join(', ')}` : undefined}
                className="flex-1 bg-fw-green hover:bg-fw-green-hover text-white px-6 py-3 rounded-xl font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    יוצר...
                  </>
                ) : (
                  'צור פרויקט'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default NewProject;
