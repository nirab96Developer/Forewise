
// src/pages/Projects/EditProject.tsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowRight, Loader2 } from 'lucide-react';
import projectService, { Project, ProjectUpdate } from '../../services/projectService';
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

const EditProject: React.FC = () => {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [formData, setFormData] = useState<ProjectUpdate>({});
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [regions, setRegions] = useState<Region[]>([]);
  const [loadingRegions, setLoadingRegions] = useState(true);
  const [filteredAreas, setFilteredAreas] = useState<Area[]>([]);
  const [loadingAreas, setLoadingAreas] = useState(false);

  useEffect(() => {
    if (code) {
      loadData();
      loadUsers();
      loadRegions();
      
      // Safety timeout - force stop loading after 10 seconds
      const timeout = setTimeout(() => {
        console.log('[EditProject] Safety timeout - forcing loading to stop');
        setLoadingData(false);
      }, 10000);
      
      return () => clearTimeout(timeout);
    }
  }, [code]);

  // Load areas and managers when region changes
  useEffect(() => {
    if (formData.region_id) {
      loadAreas(formData.region_id);
      loadUsers(formData.region_id);
    } else {
      setFilteredAreas([]);
      // Reset area_id if region is cleared
      if (formData.area_id) {
        setFormData(prev => ({ ...prev, area_id: undefined }));
      }
      // Load all managers if no region selected
      loadUsers();
    }
  }, [formData.region_id]);
  
  useEffect(() => {
    // Focus on manager field if focus=manager in URL
    if (searchParams.get('focus') === 'manager' && !loadingUsers && users.length > 0) {
      const managerSelect = document.getElementById('manager_id');
      if (managerSelect) {
        setTimeout(() => {
          managerSelect.scrollIntoView({ behavior: 'smooth', block: 'center' });
          managerSelect.focus();
        }, 300);
      }
    }
  }, [searchParams, loadingUsers, users]);

  const loadUsers = async (regionId?: number) => {
    try {
      setLoadingUsers(true);
      // Get users who can be project managers (ADMIN, REGION_MANAGER, AREA_MANAGER, WORK_MANAGER)
      const params: any = {
        page: 1,
        per_page: 100,
        status: 'active'
      };
      
      // Add region_id filter if provided
      if (regionId) {
        params.region_id = regionId;
      }
      
      const response = await api.get('/users', { params });
      
      const usersData = Array.isArray(response.data) ? response.data : (response.data?.items || []);
      
      // Filter users who can be managers (ADMIN, REGION_MANAGER, AREA_MANAGER, WORK_MANAGER)
      const managers = usersData.filter((user: User) => {
        const roleCode = user.role?.code || '';
        return ['ADMIN', 'REGION_MANAGER', 'AREA_MANAGER', 'WORK_MANAGER'].includes(roleCode);
      });
      
      setUsers(managers);
    } catch (error) {
      console.error('Error loading users:', error);
      // Fallback to empty list if API fails
      setUsers([]);
    } finally {
      setLoadingUsers(false);
    }
  };

  const loadRegions = async () => {
    try {
      setLoadingRegions(true);
      const response = await api.get('/regions', {
        params: {
          page: 1,
          per_page: 100
        }
      });
      
      const regionsData = Array.isArray(response.data) ? response.data : (response.data?.items || []);
      setRegions(regionsData);
    } catch (error) {
      console.error('Error loading regions:', error);
      setRegions([]);
    } finally {
      setLoadingRegions(false);
    }
  };

  const loadAreas = async (regionId: number) => {
    try {
      setLoadingAreas(true);
      const response = await api.get('/areas', {
        params: {
          region_id: regionId,
          page: 1,
          per_page: 100
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

  const loadData = async () => {
    console.log('[EditProject] Starting loadData...');
    setLoadingData(true);
    
    try {
      console.log('[EditProject] Fetching project:', code);
      const projectData = await projectService.getProjectByCode(code!);
      console.log('[EditProject] Project loaded:', projectData);
      setProject(projectData);
      
      // Set form data
      setFormData({
        name: projectData.name,
        code: projectData.code,
        description: projectData.description,
        status: projectData.status,
        priority: projectData.priority,
        planned_start_date: projectData.planned_start_date,
        planned_end_date: projectData.planned_end_date,
        allocated_budget: projectData.allocated_budget,
        // progress_percentage removed - not used
        manager_id: projectData.manager_id,
        region_id: projectData.region_id,
        area_id: projectData.area_id,
      });

      console.log('[EditProject] Loading related data...');
      // Load areas and managers if region_id exists
      if (projectData.region_id) {
        await Promise.all([
          loadAreas(projectData.region_id),
          loadUsers(projectData.region_id)
        ]);
      } else {
        // Load all managers if no region
        await loadUsers();
      }
      
      console.log('[EditProject] All data loaded successfully');
    } catch (error: any) {
      console.error('[EditProject] Error loading project:', error);
      setError('שגיאה בטעינת פרטי הפרויקט');
    }
    
    // Always stop loading
    console.log('[EditProject] Stopping loading...');
    setLoadingData(false);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    
    // If region changes, reset area_id
    if (name === 'region_id') {
      setFormData(prev => ({
        ...prev,
        region_id: value ? parseInt(value) : undefined,
        area_id: undefined // Reset area when region changes
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: name === 'allocated_budget' || name === 'progress_percentage'
          ? (value ? parseFloat(value) : undefined)
          : name === 'manager_id' || name === 'area_id'
          ? (value ? parseInt(value) : undefined)
          : value
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (!project?.id) {
        setError('פרויקט לא נמצא');
        setLoading(false);
        return;
      }

      await projectService.updateProject(project.id, formData);
      
      if ((window as any).showToast) {
        (window as any).showToast('הפרויקט עודכן בהצלחה!', 'success');
      } else {
        alert('הפרויקט עודכן בהצלחה!');
      }
      
      navigate(`/projects/${code}`);
    } catch (error: any) {
      console.error('Error updating project:', error);
      const errorMessage = error.response?.data?.detail || error.response?.data?.message || 'שגיאה בעדכון הפרויקט';
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

  if (loadingData) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex items-center gap-2">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span>טוען...</span>
        </div>
      </div>
    );
  }

  if (error && !project) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl text-red-600 mb-4">{error}</div>
          <button 
            onClick={() => loadData()}
            className="bg-kkl-green text-white px-4 py-2 rounded-lg hover:bg-green-700"
          >
            נסה שוב
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-page p-6 pr-72" dir="rtl">
      <div className="w-full max-w-3xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center mb-4">
            <button 
              onClick={() => navigate(`/projects/${code}`)}
              className="text-kkl-green hover:text-kkl-green-hover flex items-center"
            >
              <ArrowRight className="w-4 h-4 ml-1" />
              חזרה לפרויקט
            </button>
          </div>
          <h1 className="text-3xl font-bold text-primary">{project?.name || 'עריכת פרויקט'}</h1>
        </div>

        {/* Form */}
        <div className="card">
          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Name */}
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
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-kkl-green focus:border-kkl-green transition-all"
              />
            </div>

            {/* Code */}
            <div>
              <label htmlFor="code" className="block text-sm font-medium text-primary mb-2">
                קוד הפרויקט *
              </label>
              <input
                type="text"
                id="code"
                name="code"
                value={formData.code || ''}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-kkl-green focus:border-kkl-green transition-all"
              />
            </div>

            {/* Description */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-primary mb-2">
                תיאור
              </label>
              <textarea
                id="description"
                name="description"
                value={formData.description || ''}
                onChange={handleChange}
                rows={4}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-kkl-green focus:border-kkl-green transition-all"
              />
            </div>

            {/* Status */}
            <div>
              <label htmlFor="status" className="block text-sm font-medium text-primary mb-2">
                סטטוס
              </label>
              <select
                id="status"
                name="status"
                value={formData.status || ''}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-kkl-green focus:border-kkl-green transition-all"
              >
                <option value="ACTIVE">פעיל</option>
                <option value="COMPLETED">הושלם</option>
                <option value="SUSPENDED">מושהה</option>
                <option value="CANCELLED">בוטל</option>
              </select>
            </div>

            {/* Date Range */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="planned_start_date" className="block text-sm font-medium text-primary mb-2">
                  תאריך התחלה מתוכנן
                </label>
                <input
                  type="date"
                  id="planned_start_date"
                  name="planned_start_date"
                  value={formData.planned_start_date || ''}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-kkl-green focus:border-kkl-green transition-all"
                />
              </div>
              <div>
                <label htmlFor="planned_end_date" className="block text-sm font-medium text-primary mb-2">
                  תאריך סיום מתוכנן
                </label>
                <input
                  type="date"
                  id="planned_end_date"
                  name="planned_end_date"
                  value={formData.planned_end_date || ''}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-kkl-green focus:border-kkl-green transition-all"
                />
              </div>
            </div>

            {/* Budget */}
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
                min="0"
                step="0.01"
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-kkl-green focus:border-kkl-green transition-all"
              />
            </div>

            {/* Progress */}
            <div>
              <label htmlFor="progress_percentage" className="block text-sm font-medium text-primary mb-2">
                אחוז התקדמות (%)
              </label>
              <input
                type="number"
                id="progress_percentage"
                name="progress_percentage"
                value={formData.progress_percentage || ''}
                onChange={handleChange}
                min="0"
                max="100"
                step="0.1"
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-kkl-green focus:border-kkl-green transition-all"
              />
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
                  disabled={loadingRegions}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-kkl-green focus:border-kkl-green transition-all disabled:bg-gray-100 disabled:cursor-not-allowed"
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
                  disabled={!formData.region_id || loadingAreas}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-kkl-green focus:border-kkl-green transition-all disabled:bg-gray-100 disabled:cursor-not-allowed"
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
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-kkl-green focus:border-kkl-green transition-all disabled:bg-gray-100 disabled:cursor-not-allowed"
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
                onClick={() => navigate(`/projects/${code}`)}
                className="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-xl font-medium transition-colors"
              >
                ביטול
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 bg-kkl-green hover:bg-kkl-green-hover text-white px-6 py-3 rounded-xl font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    מעדכן...
                  </>
                ) : (
                  'עדכן'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default EditProject;
