
import React, { useEffect, useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, Search, Users as UsersIcon, Edit3, MapPin, Building2, X } from "lucide-react";
import api from "../../services/api";

const ROLE_LABELS: Record<string, string> = {
  ADMIN: 'מנהל מערכת', REGION_MANAGER: 'מנהל מרחב', AREA_MANAGER: 'מנהל אזור',
  WORK_MANAGER: 'מנהל עבודה', ORDER_COORDINATOR: 'מתאם הזמנות', ACCOUNTANT: 'חשבונאי',
  SUPPLIER_MANAGER: 'מנהל ספקים', FIELD_WORKER: 'עובד שטח', VIEWER: 'צופה', USER: 'משתמש',
};

const Users: React.FC = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState<any[]>([]);
  const [regions, setRegions] = useState<any[]>([]);
  const [areas, setAreas] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterRegion, setFilterRegion] = useState("");
  const [filterRole, setFilterRole] = useState("");
  const [filterActive, setFilterActive] = useState<string>("all");

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [usersRes, regionsRes, areasRes] = await Promise.all([
        api.get('/users'),
        api.get('/regions').catch(() => ({ data: [] })),
        api.get('/areas').catch(() => ({ data: [] })),
      ]);
      setUsers(usersRes.data?.items || usersRes.data || []);
      setRegions(regionsRes.data?.items || regionsRes.data || []);
      setAreas(areasRes.data?.items || areasRes.data || []);
    } catch (error) {
      console.error('Error loading users:', error);
    }
    setLoading(false);
  };

  const regionMap = useMemo(() => Object.fromEntries(regions.map((r: any) => [r.id, r.name])), [regions]);
  const areaMap = useMemo(() => Object.fromEntries(areas.map((a: any) => [a.id, a.name])), [areas]);
  const uniqueRoles = useMemo(() => {
    const roles = users.map(u => typeof u.role === 'object' ? u.role?.code : u.role).filter(Boolean);
    return [...new Set(roles)] as string[];
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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-green-200 border-t-green-600 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">טוען משתמשים...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pt-6 pb-8 px-4" dir="rtl">
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
            {/* Search */}
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

            {/* Role chip filter */}
            <select
              value={filterRole}
              onChange={e => setFilterRole(e.target.value)}
              className="pr-3 pl-10 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500 bg-white"
            >
              <option value="">כל התפקידים</option>
              {uniqueRoles.map(r => <option key={r} value={r}>{ROLE_LABELS[r] || r}</option>)}
            </select>

            {/* Region filter */}
            <select
              value={filterRegion}
              onChange={e => setFilterRegion(e.target.value)}
              className="pr-3 pl-10 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500 bg-white"
            >
              <option value="">כל המרחבים</option>
              {regions.map((r: any) => <option key={r.id} value={r.id}>{r.name}</option>)}
            </select>

            {/* Active filter chips */}
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

        {/* Results count */}
        {hasFilters && (
          <p className="text-xs text-gray-500 mb-3 px-1">מציג {filteredUsers.length} מתוך {users.length} משתמשים</p>
        )}

        {/* Users list */}
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

              return (
                <div
                  key={user.id}
                  className={`flex items-center gap-4 px-5 py-3.5 transition-colors hover:bg-gray-50 ${
                    idx !== filteredUsers.length - 1 ? 'border-b border-gray-100' : ''
                  } ${missingBinding ? 'bg-red-50/40' : ''}`}
                >
                  {/* Avatar */}
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 ${
                    user.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                  }`}>
                    {(user.full_name || user.username || '?')[0].toUpperCase()}
                  </div>

                  {/* Name + email */}
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-gray-900 text-sm">{user.full_name || user.username}</div>
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
                    {missingBinding && (
                      <span className="text-xs text-red-500">⚠ חסר שיוך</span>
                    )}
                    {!regionName && !areaName && !needsBinding && (
                      <span className="text-xs text-gray-400">כלל-ארגוני</span>
                    )}
                  </div>

                  {/* Status */}
                  <span className={`hidden sm:inline-flex px-2.5 py-1 rounded-full text-xs font-medium flex-shrink-0 ${
                    user.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                  }`}>
                    {user.is_active ? 'פעיל' : 'לא פעיל'}
                  </span>

                  {/* Edit button */}
                  <button
                    onClick={() => navigate(`/settings/admin/users/${user.id}/edit`)}
                    className="p-1.5 hover:bg-green-50 rounded-lg text-gray-400 hover:text-green-600 transition-colors flex-shrink-0"
                    title="ערוך משתמש"
                  >
                    <Edit3 className="w-4 h-4" />
                  </button>
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
