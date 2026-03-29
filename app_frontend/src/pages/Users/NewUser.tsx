
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, AlertCircle, User, Mail, Phone, Lock, FolderOpen, Check, ChevronDown } from 'lucide-react';
import api from '../../services/api';
import UnifiedLoader from '../../components/common/UnifiedLoader';

interface Role { id: number; code: string; name: string; }
interface Department { id: number; name: string; }
interface Region { id: number; name: string; }
interface Area { id: number; name: string; region_id: number; }
interface Project { id: number; code: string; name: string; area_id?: number; region_id?: number; }

const NewUser: React.FC = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState<1 | 2>(1);
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
    manager_id: '',
    is_active: true,
    two_factor_enabled: false,
  });
  const [selectedProjectIds, setSelectedProjectIds] = useState<number[]>([]);
  const [projectDropdownOpen, setProjectDropdownOpen] = useState(false);

  const [roles, setRoles] = useState<Role[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [regions, setRegions] = useState<Region[]>([]);
  const [areas, setAreas] = useState<Area[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { loadData(); }, []);

  useEffect(() => {
    if (formData.region_id) loadAreas(Number(formData.region_id));
    else setAreas([]);
  }, [formData.region_id]);

  const loadData = async () => {
    try {
      setLoadingData(true);
      const [rolesRes, deptsRes, regionsRes, projectsRes] = await Promise.all([
        api.get('/roles'),
        api.get('/departments'),
        api.get('/regions'),
        api.get('/projects', { params: { page_size: 200 } }),
      ]);
      setRoles(rolesRes.data.items || rolesRes.data || []);
      setDepartments(deptsRes.data.items || deptsRes.data || []);
      setRegions(regionsRes.data.items || regionsRes.data || []);
      setProjects(projectsRes.data.items || projectsRes.data || []);
    } catch (err: any) {
      setError('שגיאה בטעינת נתונים');
    } finally {
      setLoadingData(false);
    }
  };

  const loadAreas = async (regionId: number) => {
    try {
      const response = await api.get('/areas', { params: { region_id: regionId } });
      const areasData = response.data.items || response.data || [];
      setAreas(areasData.filter((a: Area) => a.region_id === regionId));
    } catch { setAreas([]); }
  };

  const toggleProject = (id: number) => {
    setSelectedProjectIds(prev =>
      prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id]
    );
  };

// Filter projects by selected area region all
  // Dynamic form rules based on selected role
  const selectedRole = roles.find(r => r.id === Number(formData.role_id));
  const roleCode = selectedRole?.code || '';
  const GLOBAL_ROLES = ['ADMIN', 'REGION_MANAGER'];
  const isGlobalRole = GLOBAL_ROLES.includes(roleCode);
  const needsRegion = !isGlobalRole && !!roleCode;
  const needsArea = ['AREA_MANAGER', 'WORK_MANAGER'].includes(roleCode);
  const needsManager = roleCode === 'WORK_MANAGER';

  // Auto-assign department by role
  const ROLE_DEPT_MAP: Record<string, string> = {
    ADMIN: 'מחלקת הנהלה',
    ORDER_COORDINATOR: 'מחלקת הנהלה',
    REGION_MANAGER: 'מחלקת הנהלה',
    AREA_MANAGER: 'מחלקת הנהלה',
    WORK_MANAGER: 'מחלקת מנהלי עבודה',
    ACCOUNTANT: 'מחלקת חשבונות',
    SUPPLIER_MANAGER: 'מחלקת הנהלה',
    FIELD_WORKER: 'מחלקת מנהלי עבודה',
    VIEWER: 'מחלקת הנהלה',
    USER: 'מחלקת מנהלי עבודה',
  };
  useEffect(() => {
    if (roleCode && departments.length > 0) {
      const deptName = ROLE_DEPT_MAP[roleCode];
      if (deptName) {
        const dept = departments.find(d => d.name === deptName);
        if (dept) setFormData(prev => ({ ...prev, department_id: String(dept.id) }));
      }
    }
  }, [roleCode, departments.length]);

  // Load managers for dropdown
  const [managers, setManagers] = useState<{id: number; full_name: string}[]>([]);
  useEffect(() => {
    if (needsManager) {
      api.get('/users', { params: { page_size: 100 } }).then(r => {
        const items = r.data?.items || r.data || [];
        setManagers(items.filter((u: any) => u.is_active));
      }).catch(() => {});
    }
  }, [needsManager]);

  const filteredProjects = projects.filter(p => {
    if (formData.area_id) return p.area_id === Number(formData.area_id);
    if (formData.region_id) return p.region_id === Number(formData.region_id);
    return true;
  });

  const validateStep1 = (): boolean => {
    if (!formData.username || !formData.email || !formData.full_name || !formData.password) {
      setError('נא למלא את כל השדות החובה');
      return false;
    }
    if (formData.password !== formData.confirm_password) {
      setError('הסיסמאות לא תואמות');
      return false;
    }
    if (formData.password.length < 8) {
      setError('הסיסמה חייבת להכיל לפחות 8 תווים');
      return false;
    }
    setError(null);
    return true;
  };

  const handleNext = () => {
    if (validateStep1()) setStep(2);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const userData = {
        username: formData.username,
        email: formData.email,
        full_name: formData.full_name,
        phone: formData.phone || undefined,
        password: formData.password,
        role_id: formData.role_id ? Number(formData.role_id) : undefined,
        department_id: formData.department_id ? Number(formData.department_id) : undefined,
        region_id: formData.region_id ? Number(formData.region_id) : undefined,
        area_id: formData.area_id ? Number(formData.area_id) : undefined,
        manager_id: formData.manager_id ? Number(formData.manager_id) : undefined,
        is_active: formData.is_active,
        two_factor_enabled: formData.two_factor_enabled,
        project_ids: selectedProjectIds,
      };

      await api.post('/users', userData);
      if ((window as any).showToast) {
        (window as any).showToast(
          `משתמש נוצר בהצלחה${selectedProjectIds.length > 0 ? ` ושויך ל-${selectedProjectIds.length} פרויקטים` : ''}!`,
          'success'
        );
      }
      navigate('/settings/admin/users');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'שגיאה ביצירת משתמש');
    } finally {
      setLoading(false);
    }
  };

  if (loadingData) return <UnifiedLoader size="full" />;

  const inputCls = "w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent text-base";
  const labelCls = "block text-sm font-medium text-gray-700 mb-1.5";

  return (
    <div className="min-h-screen bg-gray-50 pt-6 pb-10 px-4" dir="rtl">
      <div className="max-w-2xl mx-auto">

        {/* Step indicator */}
        <div className="flex items-center gap-3 mb-6">
          <button onClick={() => navigate('/settings/admin/users')} className="text-gray-500 hover:text-gray-700">
            <ArrowRight className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <div className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${step >= 1 ? 'bg-green-600 text-white' : 'bg-gray-200 text-gray-500'}`}>1</div>
            <span className="text-sm text-gray-500">פרטי משתמש</span>
            <div className="w-8 h-0.5 bg-gray-300" />
            <div className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${step >= 2 ? 'bg-green-600 text-white' : 'bg-gray-200 text-gray-500'}`}>2</div>
            <span className="text-sm text-gray-500">שיוך לפרויקטים</span>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-1">הוספת משתמש חדש</h1>
          <p className="text-gray-500 text-sm mb-6">
            {step === 1 ? 'שלב 1: פרטים אישיים ואבטחה' : 'שלב 2: שיוך לפרויקטים (אופציונלי)'}
          </p>

          {error && (
            <div className="mb-5 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
              <span className="text-red-800 text-sm">{error}</span>
            </div>
          )}

          {/* ===== STEP 1: User details ===== */}
          {step === 1 && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className={labelCls}>שם משתמש *</label>
                  <input type="text" value={formData.username}
                    onChange={e => setFormData({ ...formData, username: e.target.value })}
                    className={inputCls} required />
                </div>
                <div>
                  <label className={labelCls}><Mail className="inline w-3.5 h-3.5 ml-1" />אימייל *</label>
                  <input type="email" value={formData.email}
                    onChange={e => setFormData({ ...formData, email: e.target.value })}
                    className={inputCls} required />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className={labelCls}><User className="inline w-3.5 h-3.5 ml-1" />שם מלא *</label>
                  <input type="text" value={formData.full_name}
                    onChange={e => setFormData({ ...formData, full_name: e.target.value })}
                    className={inputCls} required />
                </div>
                <div>
                  <label className={labelCls}><Phone className="inline w-3.5 h-3.5 ml-1" />טלפון</label>
                  <input type="tel" value={formData.phone}
                    onChange={e => setFormData({ ...formData, phone: e.target.value })}
                    className={inputCls} />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className={labelCls}><Lock className="inline w-3.5 h-3.5 ml-1" />סיסמה *</label>
                  <input type="password" value={formData.password}
                    onChange={e => setFormData({ ...formData, password: e.target.value })}
                    className={inputCls} required minLength={8} />
                </div>
                <div>
                  <label className={labelCls}><Lock className="inline w-3.5 h-3.5 ml-1" />אימות סיסמה *</label>
                  <input type="password" value={formData.confirm_password}
                    onChange={e => setFormData({ ...formData, confirm_password: e.target.value })}
                    className={inputCls} required minLength={8} />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className={labelCls}>תפקיד</label>
                  <select value={formData.role_id}
                    onChange={e => setFormData({ ...formData, role_id: e.target.value })}
                    className={inputCls}>
                    <option value="">בחר תפקיד</option>
                    {roles.filter(r => r.code !== 'SUPPLIER').map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className={labelCls}>מחלקה</label>
                  <input type="text" readOnly
                    value={departments.find(d => d.id === Number(formData.department_id))?.name || 'ייקבע אוטומטית לפי תפקיד'}
                    className={`${inputCls} bg-gray-50 text-gray-500`} />
                </div>
              </div>

              {/* Region + Area — dynamic by role */}
              {!isGlobalRole && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className={labelCls}>מרחב {needsRegion ? '*' : ''}</label>
                    <select value={formData.region_id}
                      onChange={e => setFormData({ ...formData, region_id: e.target.value, area_id: '' })}
                      className={inputCls}>
                      <option value="">בחר מרחב</option>
                      {regions.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
                    </select>
                  </div>
                  {needsArea && (
                    <div>
                      <label className={labelCls}>אזור *</label>
                      <select value={formData.area_id}
                        onChange={e => setFormData({ ...formData, area_id: e.target.value })}
                        className={inputCls} disabled={!formData.region_id}>
                        <option value="">בחר אזור</option>
                        {areas.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                      </select>
                    </div>
                  )}
                </div>
              )}

              {/* Manager — only for Work Manager */}
              {needsManager && (
                <div>
                  <label className={labelCls}>מנהל ישיר</label>
                  <select value={formData.manager_id}
                    onChange={e => setFormData({ ...formData, manager_id: e.target.value })}
                    className={inputCls}>
                    <option value="">בחר מנהל ישיר</option>
                    {managers.map(m => <option key={m.id} value={m.id}>{m.full_name}</option>)}
                  </select>
                </div>
              )}

              <div className="space-y-2 pt-1">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={formData.is_active}
                    onChange={e => setFormData({ ...formData, is_active: e.target.checked })}
                    className="w-4 h-4 text-green-600 rounded border-gray-300 focus:ring-green-500" />
                  <span className="text-sm text-gray-700">משתמש פעיל</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={formData.two_factor_enabled}
                    onChange={e => setFormData({ ...formData, two_factor_enabled: e.target.checked })}
                    className="w-4 h-4 text-green-600 rounded border-gray-300 focus:ring-green-500" />
                  <span className="text-sm text-gray-700">הפעל אימות דו-שלבי (2FA)</span>
                </label>
              </div>

              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => navigate('/settings/admin/users')}
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-xl text-gray-700 hover:bg-gray-50 font-medium">
                  ביטול
                </button>
                <button type="button" onClick={handleNext}
                  className="flex-1 px-4 py-3 bg-green-600 text-white rounded-xl hover:bg-green-700 font-medium flex items-center justify-center gap-2">
                  הבא: שיוך לפרויקטים
                  <ChevronDown className="w-4 h-4 rotate-[-90deg]" />
                </button>
              </div>
            </div>
          )}

          {/* ===== STEP 2: Project assignment ===== */}
          {step === 2 && (
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className={labelCls}>
                  <FolderOpen className="inline w-4 h-4 ml-1" />
                  בחר פרויקטים לשיוך המשתמש
                </label>
                <p className="text-xs text-gray-500 mb-3">
                  ניתן לבחור מספר פרויקטים. המשתמש יתווסף כ-"חבר צוות" לכל פרויקט שנבחר.
                </p>

                {/* Selected count badge */}
                {selectedProjectIds.length > 0 && (
                  <div className="mb-2 flex items-center gap-2">
                    <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">
                      {selectedProjectIds.length} פרויקטים נבחרו
                    </span>
                    <button type="button" onClick={() => setSelectedProjectIds([])}
                      className="text-xs text-red-500 hover:text-red-700 underline">
                      נקה הכל
                    </button>
                  </div>
                )}

                {/* Projects dropdown/list */}
                <div className="border border-gray-200 rounded-xl overflow-hidden">
                  <button type="button" onClick={() => setProjectDropdownOpen(!projectDropdownOpen)}
                    className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors text-sm font-medium text-gray-700">
                    <span>
                      {projectDropdownOpen ? 'סגור רשימה' : `לחץ לבחירת פרויקטים (${filteredProjects.length} זמינים)`}
                    </span>
                    <ChevronDown className={`w-4 h-4 transition-transform ${projectDropdownOpen ? 'rotate-180' : ''}`} />
                  </button>

                  {projectDropdownOpen && (
                    <div className="max-h-64 overflow-y-auto divide-y divide-gray-100">
                      {filteredProjects.length === 0 ? (
                        <div className="p-4 text-center text-sm text-gray-500">
                          {formData.area_id || formData.region_id ? 'אין פרויקטים באזור/מרחב שנבחר' : 'אין פרויקטים זמינים'}
                        </div>
                      ) : (
                        filteredProjects.map(project => {
                          const selected = selectedProjectIds.includes(project.id);
                          return (
                            <button key={project.id} type="button"
                              onClick={() => toggleProject(project.id)}
                              className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm text-right transition-colors hover:bg-gray-50 ${selected ? 'bg-green-50' : ''}`}>
                              <div className={`flex-shrink-0 w-5 h-5 rounded border flex items-center justify-center ${selected ? 'bg-green-600 border-green-600' : 'border-gray-300'}`}>
                                {selected && <Check className="w-3 h-3 text-white" />}
                              </div>
                              <div className="flex-1 text-right">
                                <span className="font-medium text-gray-900">{project.name}</span>
                                <span className="text-gray-400 text-xs mr-2">{project.code}</span>
                              </div>
                            </button>
                          );
                        })
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Selected projects summary */}
              {selectedProjectIds.length > 0 && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-xl">
                  <p className="text-xs font-medium text-green-800 mb-1.5">פרויקטים שנבחרו:</p>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedProjectIds.map(id => {
                      const p = projects.find(pr => pr.id === id);
                      return p ? (
                        <span key={id} className="flex items-center gap-1 px-2 py-0.5 bg-white border border-green-300 text-green-800 rounded-full text-xs">
                          {p.name}
                          <button type="button" onClick={() => toggleProject(id)} className="text-green-600 hover:text-red-500">×</button>
                        </span>
                      ) : null;
                    })}
                  </div>
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setStep(1)}
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-xl text-gray-700 hover:bg-gray-50 font-medium">
                  חזור
                </button>
                <button type="submit" disabled={loading}
                  className="flex-1 px-4 py-3 bg-green-600 text-white rounded-xl hover:bg-green-700 font-semibold disabled:opacity-50 flex items-center justify-center gap-2">
                  {loading ? (
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <Check className="w-4 h-4" />
                  )}
                  {loading ? 'יוצר משתמש...' : 'צור משתמש'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default NewUser;
