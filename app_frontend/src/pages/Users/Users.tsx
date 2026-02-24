// @ts-nocheck
import React, { useEffect, useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, Search, Users as UsersIcon, Edit3, MapPin, Building2, Filter } from "lucide-react";
import api from "../../services/api";

const Users: React.FC = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState<any[]>([]);
  const [regions, setRegions] = useState<any[]>([]);
  const [areas, setAreas] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterRegion, setFilterRegion] = useState("");
  const [filterRole, setFilterRole] = useState("");
  const [filterUnassigned, setFilterUnassigned] = useState(false);
  
  useEffect(() => {
    loadData();
  }, []);
  
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
      setUsers([]);
    }
    setLoading(false);
  };

  // Region/Area lookup maps
  const regionMap = useMemo(() => Object.fromEntries(regions.map((r: any) => [r.id, r.name])), [regions]);
  const areaMap = useMemo(() => Object.fromEntries(areas.map((a: any) => [a.id, a.name])), [areas]);

  // Get unique roles
  const uniqueRoles = useMemo(() => {
    const roles = users.map(u => typeof u.role === 'object' ? u.role?.code : u.role).filter(Boolean);
    return [...new Set(roles)];
  }, [users]);

  // Filtered users
  const filteredUsers = useMemo(() => {
    return users.filter(u => {
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const name = (u.full_name || u.username || '').toLowerCase();
        const email = (u.email || '').toLowerCase();
        if (!name.includes(q) && !email.includes(q)) return false;
      }
      if (filterRegion && u.region_id != filterRegion) return false;
      if (filterRole) {
        const code = typeof u.role === 'object' ? u.role?.code : u.role;
        if (code !== filterRole) return false;
      }
      if (filterUnassigned) {
        const code = typeof u.role === 'object' ? u.role?.code : u.role;
        const needsRegion = ['REGION_MANAGER'].includes(code);
        const needsArea = ['AREA_MANAGER', 'WORK_MANAGER'].includes(code);
        if (needsRegion && !u.region_id) return true;
        if (needsArea && !u.area_id) return true;
        if (!needsRegion && !needsArea) return false;
        return false;
      }
      return true;
    });
  }, [users, searchQuery, filterRegion, filterRole, filterUnassigned]);
  
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
    <div className="min-h-screen bg-gray-50 pt-20 pb-8 px-4 md:pr-72" dir="rtl">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900">ניהול משתמשים</h1>
          <button 
            onClick={() => navigate('/admin/users/new')}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            משתמש חדש
          </button>
        </div>
        
        {users.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm p-12 text-center">
            <UsersIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">אין משתמשים</h3>
            <p className="text-gray-500">התחל על ידי הוספת משתמש ראשון</p>
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            {/* Search + Filters */}
            <div className="p-4 border-b space-y-3">
              <div className="relative">
                <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="חיפוש לפי שם או אימייל..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pr-10 pl-4 py-2 border rounded-lg"
                />
              </div>
              <div className="flex gap-3 flex-wrap items-center">
                <div className="flex items-center gap-1 text-sm text-gray-500">
                  <Filter className="w-4 h-4" />
                  <span>סינון:</span>
                </div>
                <select value={filterRegion} onChange={(e) => setFilterRegion(e.target.value)} className="px-3 py-1.5 border rounded-lg text-sm">
                  <option value="">כל המרחבים</option>
                  {regions.map((r: any) => <option key={r.id} value={r.id}>{r.name}</option>)}
                </select>
                <select value={filterRole} onChange={(e) => setFilterRole(e.target.value)} className="px-3 py-1.5 border rounded-lg text-sm">
                  <option value="">כל התפקידים</option>
                  {uniqueRoles.map((r: string) => <option key={r} value={r}>{r}</option>)}
                </select>
                <label className="flex items-center gap-1.5 text-sm cursor-pointer">
                  <input type="checkbox" checked={filterUnassigned} onChange={(e) => setFilterUnassigned(e.target.checked)} className="rounded" />
                  <span className="text-red-600">ללא שיוך</span>
                </label>
                {(searchQuery || filterRegion || filterRole || filterUnassigned) && (
                  <button onClick={() => { setSearchQuery(''); setFilterRegion(''); setFilterRole(''); setFilterUnassigned(false); }} className="text-xs text-blue-600 hover:underline">נקה הכל</button>
                )}
              </div>
            </div>
            
            {/* Table with Region/Area columns */}
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">משתמש</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">תפקיד</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">מרחב</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">אזור</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">סטטוס</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">פעולות</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredUsers.map((user) => {
                  const roleCode = typeof user.role === 'object' ? user.role?.code : user.role;
                  const roleName = typeof user.role === 'object' ? user.role?.name : user.role;
                  const regionName = user.region_id ? regionMap[user.region_id] : null;
                  const areaName = user.area_id ? areaMap[user.area_id] : null;
                  const needsBinding = ['REGION_MANAGER','AREA_MANAGER','WORK_MANAGER'].includes(roleCode);
                  const missingBinding = needsBinding && (!user.region_id || (['AREA_MANAGER','WORK_MANAGER'].includes(roleCode) && !user.area_id));
                  
                  return (
                    <tr key={user.id} className={`hover:bg-gray-50 ${missingBinding ? 'bg-red-50/50' : ''}`}>
                      <td className="px-4 py-3">
                        <div className="text-sm font-medium text-gray-900">{user.full_name || user.username}</div>
                        <div className="text-xs text-gray-500">{user.email}</div>
                      </td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs font-medium">{roleName || roleCode || '—'}</span>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {regionName ? (
                          <span className="flex items-center gap-1 text-gray-700">
                            <MapPin className="w-3 h-3 text-green-600" />{regionName}
                          </span>
                        ) : (
                          <span className="text-gray-400 text-xs">{needsBinding ? '❌ חסר' : 'כלל-ארגוני'}</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {areaName ? (
                          <span className="flex items-center gap-1 text-gray-700">
                            <Building2 className="w-3 h-3 text-purple-600" />{areaName}
                          </span>
                        ) : (
                          <span className="text-gray-400 text-xs">{['AREA_MANAGER','WORK_MANAGER'].includes(roleCode) ? '❌ חסר' : '—'}</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded-full text-xs ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                          {user.is_active ? 'פעיל' : 'לא פעיל'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <button onClick={() => navigate(`/settings/admin/users/${user.id}/edit`)} className="p-1.5 hover:bg-gray-100 rounded text-gray-500 hover:text-green-600 transition-colors" title="ערוך">
                          <Edit3 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <div className="p-4 bg-gray-50 text-center text-sm text-gray-500">
              מציג {filteredUsers.length} מתוך {users.length} משתמשים
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Users;
