// src/pages/Settings/ProjectsManagement.tsx
// דף ניהול פרויקטים — טבלה מלאה + פילטרים + ניווט להקמה/עריכה
import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight, Plus, Search, Edit2, ExternalLink, Building2
} from 'lucide-react';
import api from '../../services/api';
import UnifiedLoader from '../../components/common/UnifiedLoader';
interface Project {
  id: number;
  code: string;
  name: string;
  description?: string;
  status: string;
  is_active: boolean;
  region_id?: number;
  region_name?: string;
  area_id?: number;
  area_name?: string;
  manager_name?: string;
  allocated_budget?: number;
  spent_budget?: number;
  start_date?: string;
  created_at?: string;
}
interface Region { id: number; name: string; }
interface Area { id: number; name: string; region_id: number; }
const ProjectsManagement: React.FC = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [regions, setRegions] = useState<Region[]>([]);
  const [areas, setAreas] = useState<Area[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterRegion, setFilterRegion] = useState('all');
  const [filterArea, setFilterArea] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  useEffect(() => { loadData(); }, []);
  const loadData = async () => {
    setLoading(true);
    try {
      const [pRes, rRes, aRes] = await Promise.all([
        api.get('/projects', { params: { page_size: 200 } }),
        api.get('/regions').catch(() => ({ data: [] })),
        api.get('/areas').catch(() => ({ data: [] })),
      ]);
      setProjects(pRes.data?.items || pRes.data || []);
      setRegions(rRes.data?.items || rRes.data || []);
      setAreas(aRes.data?.items || aRes.data || []);
    } catch (err) {
      console.error('Failed to load projects:', err);
    }
    setLoading(false);
  };
  const filteredAreas = useMemo(() =>
    areas.filter(a => filterRegion === 'all' || String(a.region_id) === filterRegion),
  [areas, filterRegion]);
  const filtered = useMemo(() => projects.filter(p => {
    const q = search.toLowerCase();
    if (q && !p.name.toLowerCase().includes(q) && !p.code.toLowerCase().includes(q) && !(p.manager_name || '').toLowerCase().includes(q)) return false;
    if (filterRegion !== 'all' && String(p.region_id) !== filterRegion) return false;
    if (filterArea !== 'all' && String(p.area_id) !== filterArea) return false;
    if (filterStatus !== 'all') {
      if (filterStatus === 'active' && !p.is_active) return false;
      if (filterStatus === 'inactive' && p.is_active) return false;
    }
    return true;
  }), [projects, search, filterRegion, filterArea, filterStatus]);
  const fmt = (n?: number) => n ? `₪${n.toLocaleString('he-IL')}` : '—';

  if (loading) return <UnifiedLoader size="full" />;
  if (loading) return <UnifiedLoader size="full" />;

  return (
    <div className="min-h-screen bg-gray-50" dir="rtl">
      {/* Header */}
      <div className="bg-white border-b shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button onClick={() => navigate('/settings')} className="text-green-600 hover:text-green-800">
                <ArrowRight className="w-5 h-5" />
              </button>
              <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
                <Building2 className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">ניהול פרויקטים</h1>
                <p className="text-sm text-gray-500">{filtered.length} מתוך {projects.length} פרויקטים</p>
              </div>
            </div>
            <button
              onClick={() => navigate('/settings/organization/projects/new')}
              className="flex items-center gap-2 px-4 py-2.5 bg-green-600 hover:bg-green-700 text-white rounded-xl text-sm font-medium"
            >
              <Plus className="w-4 h-4" />
              הקמת פרויקט
            </button>
          </div>
          {/* Filters */}
          <div className="flex flex-wrap gap-2 mt-3">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                value={search} onChange={e => setSearch(e.target.value)}
                placeholder="חיפוש לפי שם, קוד, מנהל..."
                className="w-full pr-9 pl-3 py-2 border border-gray-200 rounded-lg text-sm"
                style={{ fontSize: '16px' }}
              />
            </div>
            <select value={filterRegion} onChange={e => { setFilterRegion(e.target.value); setFilterArea('all'); }}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white">
              <option value="all">כל המרחבים</option>
              {regions.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
            </select>
            <select value={filterArea} onChange={e => setFilterArea(e.target.value)}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white">
              <option value="all">כל האזורים</option>
              {filteredAreas.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
            <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white">
              <option value="all">כל הסטטוסים</option>
              <option value="active">פעיל</option>
              <option value="inactive">לא פעיל</option>
            </select>
          </div>
        </div>
      </div>
      {/* Table */}
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[800px]">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500">קוד</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500">שם</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500">מרחב</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500">אזור</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500">מנהל</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500">תקציב</th>
                  <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500">סטטוס</th>
                  <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500">פעולות</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr><td colSpan={8} className="text-center py-12 text-gray-400">לא נמצאו פרויקטים</td></tr>
                ) : filtered.map(p => (
                  <tr key={p.id} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                    <td className="px-4 py-3 font-mono text-sm text-gray-600">{p.code}</td>
                    <td className="px-4 py-3 font-medium text-gray-900">{p.name}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{p.region_name || '—'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{p.area_name || '—'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{p.manager_name || '—'}</td>
                    <td className="px-4 py-3 text-sm">
                      {p.allocated_budget ? (
                        <div>
                          <span className="font-medium text-gray-800">{fmt(p.allocated_budget)}</span>
                          {p.spent_budget ? <span className="text-xs text-gray-400 mr-1">({fmt(p.spent_budget)} נוצל)</span> : null}
                        </div>
                      ) : <span className="text-gray-400">—</span>}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${
                        p.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                      }`}>
                        {p.is_active ? 'פעיל' : 'מושבת'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-center gap-1">
                        <button
                          onClick={() => navigate(`/projects/${p.code}/workspace`)}
                          className="p-1.5 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg"
                          title="פתח workspace"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => navigate(`/settings/organization/projects/${p.code}/edit`)}
                          className="p-1.5 text-gray-400 hover:text-orange-600 hover:bg-orange-50 rounded-lg"
                          title="ערוך"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
export default ProjectsManagement;
