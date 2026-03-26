import React, { useEffect, useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, Search, Users as UsersIcon, Edit3, MapPin, Building2, X, PauseCircle, RefreshCw } from "lucide-react";
import api from "../../services/api";
import UnifiedLoader from "../../components/common/UnifiedLoader";

const ROLE_LABELS: Record<string, string> = {
  ADMIN: 'מנהל מערכת', REGION_MANAGER: 'מנהל מרחב', AREA_MANAGER: 'מנהל אזור',
  WORK_MANAGER: 'מנהל עבודה', ORDER_COORDINATOR: 'מתאם הזמנות', ACCOUNTANT: 'חשבונאי',
  SUPPLIER_MANAGER: 'מנהל ספקים', FIELD_WORKER: 'עובד שטח', VIEWER: 'צופה', USER: 'משתמש',
};

function formatDate(ts: string | null | undefined) {
  if (!ts) return '';
  const d = new Date(ts);
  return `${String(d.getDate()).padStart(2,'0')}/${String(d.getMonth()+1).padStart(2,'0')}/${d.getFullYear()}`;
}

// Suspend Modal 
interface SuspendModalProps {
  user: any;
  onClose: () => void;
  onDone: () => void;
}
const SuspendModal: React.FC<SuspendModalProps> = ({ user, onClose, onDone }) => {
  const [reason, setReason] = useState('');
  const [years, setYears] = useState(3);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState('');

  const handleSubmit = async () => {
    if (reason.trim().length < 3) { setErr('נדרש נימוק (לפחות 3 תווים)'); return; }
    setSaving(true); setErr('');
    try {
      await api.put(`/users/${user.id}/suspend`, { reason: reason.trim(), deletion_years: years });
      onDone();
    } catch (e: any) {
      setErr(e?.response?.data?.detail || 'שגיאה בהשהיית המשתמש');
    }
    setSaving(false);
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" dir="rtl">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 className="font-bold text-gray-900 text-lg flex items-center gap-2">
            <PauseCircle className="w-5 h-5 text-orange-500" />
            השהיית משתמש
          </h2>
          <button onClick={onClose} className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-400">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="p-5 space-y-4">
          <div className="bg-orange-50 border border-orange-200 rounded-xl px-4 py-3 text-sm text-orange-800">
            <strong>{user.full_name || user.username}</strong> יושהה ולא יוכל להתחבר למערכת.
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">סיבת ההשהיה *</label>
            <textarea
              rows={3}
              value={reason}
              onChange={e => setReason(e.target.value)}
              placeholder="הסבר מדוע המשתמש מושהה..."
              className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-orange-400 focus:border-orange-400 resize-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">מחיקה אוטומטית (שנים)</label>
            <select
              value={years}
              onChange={e => setYears(Number(e.target.value))}
              className="border border-gray-300 rounded-xl px-3 pr-3 pl-10 py-2 text-sm"
            >
              {[1,2,3,5,7].map(y => <option key={y} value={y}>{y} שנים</option>)}
            </select>
            <p className="text-xs text-gray-400 mt-1">
              המידע האישי יימחק אוטומטית אחרי {years} שנים מיום ההשהיה.
            </p>
          </div>

          {err && <p className="text-sm text-red-600">{err}</p>}
        </div>
        <div className="flex gap-2 px-5 py-4 border-t border-gray-100">
          <button
            onClick={handleSubmit}
            disabled={saving}
            className="flex-1 py-2.5 bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white font-medium rounded-xl transition-colors"
          >
{saving ? 'מבצע השהיה...' : ' השהה משתמש'}
          </button>
          <button onClick={onClose} className="px-4 py-2.5 border border-gray-200 rounded-xl text-gray-600 hover:bg-gray-50 text-sm">
            ביטול
          </button>
        </div>
      </div>
    </div>
  );
};

// Change Role Modal 
interface ChangeRoleModalProps {
  user: any;
  roles: any[];
  regions: any[];
  areas: any[];
  onClose: () => void;
  onDone: () => void;
}
const ChangeRoleModal: React.FC<ChangeRoleModalProps> = ({ user, roles, regions, areas, onClose, onDone }) => {
  const currentRoleCode = typeof user.role === 'object' ? user.role?.code : user.role;
  const currentRoleObj = roles.find(r => r.code === currentRoleCode || r.name === currentRoleCode);

  const [roleId, setRoleId] = useState<number>(user.role_id || currentRoleObj?.id || 0);
  const [regionId, setRegionId] = useState<number | ''>(user.region_id || '');
  const [areaId, setAreaId] = useState<number | ''>(user.area_id || '');
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState('');

  const filteredAreas = regionId ? areas.filter((a: any) => a.region_id === regionId) : areas;

  const handleSubmit = async () => {
    if (!roleId) { setErr('בחר תפקיד'); return; }
    setSaving(true); setErr('');
    try {
      await api.put(`/users/${user.id}/role`, {
        role_id: roleId,
        region_id: regionId || null,
        area_id: areaId || null,
      });
      onDone();
    } catch (e: any) {
      setErr(e?.response?.data?.detail || 'שגיאה בשינוי תפקיד');
    }
    setSaving(false);
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" dir="rtl">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 className="font-bold text-gray-900 text-lg flex items-center gap-2">
            <RefreshCw className="w-5 h-5 text-blue-500" />
            החלפת תפקיד
          </h2>
          <button onClick={onClose} className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-400">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="p-5 space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-xl px-4 py-3 text-sm text-blue-800">
            <strong>{user.full_name || user.username}</strong> — שיוכי הפרויקטים הישנים יאופסו.
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">תפקיד חדש *</label>
            <select
              value={roleId}
              onChange={e => setRoleId(Number(e.target.value))}
              className="w-full border border-gray-300 rounded-xl px-3 pr-3 pl-10 py-2 text-sm focus:ring-2 focus:ring-blue-400"
            >
              <option value={0}>בחר תפקיד...</option>
              {roles.map((r: any) => (
                <option key={r.id} value={r.id}>{ROLE_LABELS[r.code || r.name] || r.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">מרחב</label>
            <select
              value={regionId}
              onChange={e => { setRegionId(e.target.value ? Number(e.target.value) : ''); setAreaId(''); }}
              className="w-full border border-gray-300 rounded-xl px-3 pr-3 pl-10 py-2 text-sm"
            >
              <option value="">ללא מרחב ספציפי</option>
              {regions.map((r: any) => <option key={r.id} value={r.id}>{r.name}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">אזור</label>
            <select
              value={areaId}
              onChange={e => setAreaId(e.target.value ? Number(e.target.value) : '')}
              className="w-full border border-gray-300 rounded-xl px-3 pr-3 pl-10 py-2 text-sm"
              disabled={!regionId && filteredAreas.length === 0}
            >
              <option value="">ללא אזור ספציפי</option>
              {filteredAreas.map((a: any) => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
          </div>

          {err && <p className="text-sm text-red-600">{err}</p>}
        </div>
        <div className="flex gap-2 px-5 py-4 border-t border-gray-100">
          <button
            onClick={handleSubmit}
            disabled={saving}
            className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium rounded-xl transition-colors"
          >
{saving ? 'שומר...' : ' עדכן תפקיד'}
          </button>
          <button onClick={onClose} className="px-4 py-2.5 border border-gray-200 rounded-xl text-gray-600 hover:bg-gray-50 text-sm">
            ביטול
          </button>
        </div>
      </div>
    </div>
  );
};

// Main Component 
const Users: React.FC = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState<any[]>([]);
  const [regions, setRegions] = useState<any[]>([]);
  const [areas, setAreas] = useState<any[]>([]);
  const [roles, setRoles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterRegion, setFilterRegion] = useState("");
  const [filterRole, setFilterRole] = useState("");
  const [filterActive, setFilterActive] = useState<string>("all");

  const [suspendTarget, setSuspendTarget] = useState<any | null>(null);
  const [roleTarget, setRoleTarget] = useState<any | null>(null);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [usersRes, regionsRes, areasRes, rolesRes] = await Promise.all([
        api.get('/users'),
        api.get('/regions').catch(() => ({ data: [] })),
        api.get('/areas').catch(() => ({ data: [] })),
        api.get('/roles').catch(() => ({ data: [] })),
      ]);
      setUsers(usersRes.data?.items || usersRes.data || []);
      setRegions(regionsRes.data?.items || regionsRes.data || []);
      setAreas(areasRes.data?.items || areasRes.data || []);
      const rolesData = rolesRes.data?.items || rolesRes.data || [];
      setRoles(rolesData.filter((r: any) => r.name !== 'Delete Test Role'));
    } catch (error) {
      console.error('Error loading users:', error);
    }
    setLoading(false);
  };

  const regionMap = useMemo(() => Object.fromEntries(regions.map((r: any) => [r.id, r.name])), [regions]);
  const areaMap = useMemo(() => Object.fromEntries(areas.map((a: any) => [a.id, a.name])), [areas]);
  const uniqueRoles = useMemo(() => {
    const r = users.map(u => typeof u.role === 'object' ? u.role?.code : u.role).filter(Boolean);
    return [...new Set(r)] as string[];
  }, [users]);

  const filteredUsers = useMemo(() => {
    return users.filter(u => {
      const roleCode = typeof u.role === 'object' ? u.role?.code : u.role;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        if (!(u.full_name || u.username || '').toLowerCase().includes(q) &&
            !(u.email || '').toLowerCase().includes(q)) return false;
      }
      if (filterRegion && String(u.region_id) !== filterRegion) return false;
      if (filterRole && roleCode !== filterRole) return false;
      if (filterActive === 'active' && !u.is_active) return false;
      if (filterActive === 'inactive' && u.is_active) return false;
      return true;
    });
  }, [users, searchQuery, filterRegion, filterRole, filterActive]);

  const hasFilters = searchQuery || filterRegion || filterRole || filterActive !== 'all';
  const clearFilters = () => { setSearchQuery(''); setFilterRegion(''); setFilterRole(''); setFilterActive('all'); };

  const handleModalDone = () => {
    setSuspendTarget(null);
    setRoleTarget(null);
    loadData();
  };

  if (loading) return <UnifiedLoader size="full" />;

  return (
    <div className="min-h-screen bg-gray-50 pt-6 pb-8 px-4" dir="rtl">
      {suspendTarget && (
        <SuspendModal
          user={suspendTarget}
          onClose={() => setSuspendTarget(null)}
          onDone={handleModalDone}
        />
      )}
      {roleTarget && (
        <ChangeRoleModal
          user={roleTarget}
          roles={roles}
          regions={regions}
          areas={areas}
          onClose={() => setRoleTarget(null)}
          onDone={handleModalDone}
        />
      )}

      <div className="max-w-6xl mx-auto">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">ניהול משתמשים</h1>
            <p className="text-sm text-gray-500 mt-0.5">{users.length} משתמשים במערכת</p>
          </div>
          <button
            onClick={() => navigate('/admin/users/new')}
            className="flex items-center gap-2 px-4 py-2.5 bg-green-600 text-white rounded-xl hover:bg-green-700 font-medium shadow-sm transition-colors"
          >
            <Plus className="w-4 h-4" />
            משתמש חדש
          </button>
        </div>

        {/* Search + Filters bar */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-3 mb-4">
          <div className="flex flex-wrap gap-2 items-center">
            <div className="relative flex-1 min-w-[180px]">
              <Search className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="חיפוש שם / אימייל..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full pr-9 pl-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500"
              />
            </div>

            <select
              value={filterRole}
              onChange={e => setFilterRole(e.target.value)}
              className="pr-3 pl-10 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500 bg-white"
            >
              <option value="">כל התפקידים</option>
              {uniqueRoles.map(r => <option key={r} value={r}>{ROLE_LABELS[r] || r}</option>)}
            </select>

            <select
              value={filterRegion}
              onChange={e => setFilterRegion(e.target.value)}
              className="pr-3 pl-10 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500 bg-white"
            >
              <option value="">כל המרחבים</option>
              {regions.map((r: any) => <option key={r.id} value={r.id}>{r.name}</option>)}
            </select>

            <div className="flex gap-1.5">
              {(['all', 'active', 'inactive'] as const).map(v => (
                <button
                  key={v}
                  onClick={() => setFilterActive(v)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    filterActive === v
                      ? v === 'active' ? 'bg-green-600 text-white' : v === 'inactive' ? 'bg-gray-600 text-white' : 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {v === 'all' ? 'הכל' : v === 'active' ? 'פעילים' : 'לא פעילים'}
                </button>
              ))}
            </div>

            {hasFilters && (
              <button onClick={clearFilters} className="flex items-center gap-1 text-xs text-gray-500 hover:text-red-600 px-2 py-1.5 rounded-lg hover:bg-red-50 transition-colors">
                <X className="w-3.5 h-3.5" /> נקה
              </button>
            )}
          </div>
        </div>

        {hasFilters && (
          <p className="text-xs text-gray-500 mb-3 px-1">מציג {filteredUsers.length} מתוך {users.length} משתמשים</p>
        )}

        {filteredUsers.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
            <UsersIcon className="w-14 h-14 text-gray-300 mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-gray-700 mb-1">
              {hasFilters ? 'לא נמצאו משתמשים' : 'אין משתמשים'}
            </h3>
            <p className="text-sm text-gray-500">
              {hasFilters ? 'נסה לשנות את הפילטרים' : 'התחל בהוספת משתמש חדש'}
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            {filteredUsers.map((user, idx) => {
              const roleCode = typeof user.role === 'object' ? user.role?.code : user.role;
              const roleName = ROLE_LABELS[roleCode] || (typeof user.role === 'object' ? user.role?.name : user.role) || '—';
              const regionName = user.region_id ? regionMap[user.region_id] : null;
              const areaName = user.area_id ? areaMap[user.area_id] : null;
              const needsBinding = ['REGION_MANAGER', 'AREA_MANAGER', 'WORK_MANAGER'].includes(roleCode);
              const missingBinding = needsBinding && (!user.region_id || (['AREA_MANAGER', 'WORK_MANAGER'].includes(roleCode) && !user.area_id));
              const isSuspended = user.status === 'suspended';
              const isDeleted = user.status === 'deleted';

              return (
                <div
                  key={user.id}
                  className={`flex items-center gap-4 px-5 py-3.5 transition-colors hover:bg-gray-50 ${
                    idx !== filteredUsers.length - 1 ? 'border-b border-gray-100' : ''
                  } ${missingBinding ? 'bg-red-50/40' : ''} ${isSuspended ? 'bg-orange-50/30' : ''}`}
                >
                  {/* Avatar */}
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 ${
                    isSuspended ? 'bg-orange-100 text-orange-600' :
                    isDeleted ? 'bg-red-100 text-red-500' :
                    user.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                  }`}>
                    {(user.full_name || user.username || '?')[0].toUpperCase()}
                  </div>

                  {/* Name + email + lifecycle badges */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-gray-900 text-sm">{user.full_name || user.username}</span>
                      {isSuspended && (
                        <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded-full text-xs font-medium">
                          מושהה
                        </span>
                      )}
                      {isDeleted && (
                        <span className="px-2 py-0.5 bg-gray-200 text-gray-600 rounded-full text-xs font-medium">
                          נמחק
                        </span>
                      )}
                      {isSuspended && user.scheduled_deletion_at && (
                        <span className="px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full text-xs">
                          יימחק: {formatDate(user.scheduled_deletion_at)}
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-gray-400 truncate">{user.email}</div>
                  </div>

                  {/* Role badge */}
                  <span className="hidden sm:inline-flex px-2.5 py-1 bg-blue-50 text-blue-700 rounded-lg text-xs font-medium flex-shrink-0">
                    {roleName}
                  </span>

                  {/* Region/Area */}
                  <div className="hidden md:flex flex-col gap-0.5 min-w-[120px]">
                    {regionName && (
                      <span className="flex items-center gap-1 text-xs text-gray-600">
                        <MapPin className="w-3 h-3 text-green-500" />{regionName}
                      </span>
                    )}
                    {areaName && (
                      <span className="flex items-center gap-1 text-xs text-gray-500">
                        <Building2 className="w-3 h-3 text-purple-400" />{areaName}
                      </span>
                    )}
{missingBinding && <span className="text-xs text-red-500"> חסר שיוך</span>}
                    {!regionName && !areaName && !needsBinding && (
                      <span className="text-xs text-gray-400">כלל-ארגוני</span>
                    )}
                  </div>

                  {/* Status */}
                  <span className={`hidden sm:inline-flex px-2.5 py-1 rounded-full text-xs font-medium flex-shrink-0 ${
                    isSuspended ? 'bg-orange-100 text-orange-700' :
                    isDeleted ? 'bg-gray-200 text-gray-500' :
                    user.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                  }`}>
                    {isSuspended ? 'מושהה' : isDeleted ? 'נמחק' : user.is_active ? 'פעיל' : 'לא פעיל'}
                  </span>

                  {/* Action buttons */}
                  <div className="flex items-center gap-1 flex-shrink-0">
                    {/* Suspend / Unsuspend */}
                    {!isDeleted && (
                      <button
                        onClick={() => setSuspendTarget(user)}
                        className={`p-1.5 rounded-lg transition-colors ${
                          isSuspended
                            ? 'hover:bg-green-50 text-orange-400 hover:text-green-600'
                            : 'hover:bg-orange-50 text-gray-400 hover:text-orange-500'
                        }`}
                        title={isSuspended ? 'המשתמש מושהה — לחץ לפרטים' : 'השהה משתמש'}
                      >
                        <PauseCircle className="w-4 h-4" />
                      </button>
                    )}

                    {/* Change role */}
                    {!isDeleted && (
                      <button
                        onClick={() => setRoleTarget(user)}
                        className="p-1.5 hover:bg-blue-50 rounded-lg text-gray-400 hover:text-blue-600 transition-colors"
                        title="החלף תפקיד"
                      >
                        <RefreshCw className="w-4 h-4" />
                      </button>
                    )}

                    {/* Edit */}
                    <button
                      onClick={() => navigate(`/settings/admin/users/${user.id}/edit`)}
                      className="p-1.5 hover:bg-green-50 rounded-lg text-gray-400 hover:text-green-600 transition-colors"
                      title="ערוך משתמש"
                    >
                      <Edit3 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default Users;
