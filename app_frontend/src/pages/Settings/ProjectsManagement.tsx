// src/pages/Settings/ProjectsManagement.tsx
// ניהול פרויקטים — טבלה + מפה + פילטרים + הקמה/עריכה/השבתה
import React, { useState, useEffect, useMemo, lazy, Suspense } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight, Plus, Search, Edit2, ExternalLink, Building2,
  Map as MapIcon, List, Archive, Power
} from 'lucide-react';
import api from '../../services/api';
import UnifiedLoader from '../../components/common/UnifiedLoader';

const LeafletMap = lazy(() => import('../../components/Map/LeafletMap'));

interface Project {
  id: number; code: string; name: string; description?: string;
  status: string; is_active: boolean;
  region_id?: number; region_name?: string;
  area_id?: number; area_name?: string;
  manager_name?: string; manager_id?: number;
  allocated_budget?: number; spent_budget?: number;
  start_date?: string; created_at?: string;
  lat?: number; lng?: number;
}
interface Region { id: number; name: string; }
interface Area { id: number; name: string; region_id: number; }

const REGION_COLORS: Record<number, string> = { 1: '#059669', 2: '#2563eb', 3: '#d97706' };
const AREA_COLORS = ['#10b981','#3b82f6','#f59e0b','#ef4444','#8b5cf6','#ec4899','#14b8a6'];

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
  const [viewMode, setViewMode] = useState<'table' | 'map'>('table');
  const [geoLayers, setGeoLayers] = useState<any>(null);
  const [deactivateId, setDeactivateId] = useState<number | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  let userData: any = {};
  try { userData = JSON.parse(localStorage.getItem('user') || '{}'); } catch {}
  const userRole = (userData.role || userData.role_code || '').toUpperCase();
  const userRegionId = userData.region_id;
  const userAreaId = userData.area_id;

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [pRes, rRes, aRes] = await Promise.all([
        api.get('/projects', { params: { page_size: 500 } }),
        api.get('/regions').catch(() => ({ data: [] })),
        api.get('/areas').catch(() => ({ data: [] })),
      ]);
      const allProjects = pRes.data?.items || pRes.data || [];
      setProjects(allProjects);
      setRegions(rRes.data?.items || rRes.data || []);
      setAreas(aRes.data?.items || aRes.data || []);

      // Load geo layers for map view
      try {
        const lr = await api.get('/geo/layers/all');
        setGeoLayers(lr.data);
      } catch {}
    } catch (err) {
      console.error('Failed to load projects:', err);
    }
    setLoading(false);
  };

  const filteredAreas = useMemo(() =>
    areas.filter(a => filterRegion === 'all' || String(a.region_id) === filterRegion),
  [areas, filterRegion]);

  const filtered = useMemo(() => {
    let list = projects;
    // Role scoping
    if (userRole === 'AREA_MANAGER' && userAreaId) list = list.filter(p => p.area_id === userAreaId);
    else if (userRole === 'REGION_MANAGER' && userRegionId) list = list.filter(p => p.region_id === userRegionId);

    return list.filter(p => {
      const q = search.toLowerCase();
      if (q && !p.name.toLowerCase().includes(q) && !p.code.toLowerCase().includes(q) && !(p.manager_name || '').toLowerCase().includes(q)) return false;
      if (filterRegion !== 'all' && String(p.region_id) !== filterRegion) return false;
      if (filterArea !== 'all' && String(p.area_id) !== filterArea) return false;
      if (filterStatus !== 'all') {
        if (filterStatus === 'active' && !p.is_active) return false;
        if (filterStatus === 'inactive' && p.is_active) return false;
      }
      return true;
    });
  }, [projects, search, filterRegion, filterArea, filterStatus, userRole, userAreaId, userRegionId]);

  const handleDeactivate = async () => {
    if (!deactivateId) return;
    setActionLoading(true);
    try {
      await api.delete(`/projects/${deactivateId}`);
      setProjects(prev => prev.map(p => p.id === deactivateId ? { ...p, is_active: false, status: 'inactive' } : p));
      setDeactivateId(null);
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'שגיאה בהשבתת פרויקט');
    }
    setActionLoading(false);
  };

  const fmt = (n?: number) => n ? `${n.toLocaleString('he-IL')}` : '—';
  if (loading) return <UnifiedLoader size="full" />;

  // Map data
  const mapPolygons: any[] = [];
  const mapPoints: any[] = [];

  if (viewMode === 'map' && geoLayers) {
    if (geoLayers.regions?.features) {
      geoLayers.regions.features.forEach((f: any) => {
        const rid = f.properties.id;
        mapPolygons.push({
          id: rid, name: f.properties.name, geometry: f.geometry,
          fillColor: REGION_COLORS[rid] || '#6b7280',
          strokeColor: REGION_COLORS[rid] || '#4b5563',
          fillOpacity: 0.08, strokeWeight: 2,
        });
      });
    }
    if (geoLayers.areas?.features) {
      geoLayers.areas.features.forEach((f: any, idx: number) => {
        const color = AREA_COLORS[idx % AREA_COLORS.length];
        mapPolygons.push({
          id: `area-${f.properties.id}`, name: f.properties.name, geometry: f.geometry,
          fillColor: color, strokeColor: color, fillOpacity: 0.12, strokeWeight: 1.5,
        });
      });
    }
  }

  // Enrich project lat/lng from geo layers data
  const geoProjects = geoLayers?.projects || [];
  const geoMap = new Map<number, { lat: number; lng: number }>();
  geoProjects.forEach((gp: any) => {
    if (gp.lat && gp.lng) geoMap.set(gp.id, { lat: gp.lat, lng: gp.lng });
  });

  filtered.forEach(p => {
    const geo = geoMap.get(p.id);
    const lat = p.lat || geo?.lat;
    const lng = p.lng || geo?.lng;
    if (lat && lng) {
      mapPoints.push({
        id: p.id, name: p.name, code: p.code, lat, lng,
        color: p.is_active ? '#16a34a' : '#9ca3af',
        popupContent:
          '<div style="direction:rtl;padding:6px;min-width:170px">' +
          '<b>' + p.name + '</b><br>' +
          '<span style="color:#6b7280;font-size:11px">' + p.code + '</span><br>' +
          '<span style="font-size:11px;color:#374151">' + (p.area_name || '') + ' | ' + (p.region_name || '') + '</span><br>' +
          '<span style="display:inline-block;margin-top:2px;padding:1px 6px;border-radius:8px;font-size:10px;font-weight:600;' +
          (p.is_active ? 'background:#dcfce7;color:#166534' : 'background:#f3f4f6;color:#6b7280') + '">' +
          (p.is_active ? 'פעיל' : 'מושבת') + '</span><br>' +
          '<a href="/projects/' + p.code + '/workspace" style="display:inline-block;margin-top:6px;padding:4px 10px;background:#16a34a;color:#fff;border-radius:5px;text-decoration:none;font-size:11px">פתח</a>' +
          '</div>',
      });
    }
  });

  return (
    <div className="min-h-screen bg-gray-50" dir="rtl">
      {/* Header */}
      <div className="bg-white border-b shadow-sm sticky top-16 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button onClick={() => navigate('/settings')} className="text-green-600 hover:text-green-800">
                <ArrowRight className="w-5 h-5" />
              </button>
              <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
                <Building2 className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">ניהול פרויקטים</h1>
                <p className="text-sm text-gray-500">{filtered.length} מתוך {projects.length} פרויקטים</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {/* View Toggle */}
              <div className="flex bg-gray-100 rounded-lg p-0.5">
                <button
                  onClick={() => setViewMode('table')}
                  className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${viewMode === 'table' ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'}`}
                >
                  <List className="w-3.5 h-3.5" /> טבלה
                </button>
                <button
                  onClick={() => setViewMode('map')}
                  className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${viewMode === 'map' ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'}`}
                >
                  <MapIcon className="w-3.5 h-3.5" /> מפה
                </button>
              </div>
              <button
                onClick={() => navigate('/settings/organization/projects/new')}
                className="flex items-center gap-2 px-4 py-2.5 bg-green-600 hover:bg-green-700 text-white rounded-xl text-sm font-medium"
              >
                <Plus className="w-4 h-4" /> הקמת פרויקט
              </button>
            </div>
          </div>
          {/* Filters */}
          <div className="flex flex-wrap gap-2 mt-3">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                value={search} onChange={e => setSearch(e.target.value)}
                placeholder="חיפוש לפי שם, קוד, מנהל..."
                className="w-full pr-9 pl-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-300 focus:border-green-400"
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

      <div className="max-w-7xl mx-auto px-4 py-4">
        {viewMode === 'table' ? (
          /* ── TABLE VIEW ── */
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
                    <tr key={p.id} className={`border-b border-gray-50 hover:bg-gray-50/50 transition-colors ${!p.is_active ? 'opacity-60' : ''}`}>
                      <td className="px-4 py-3 font-mono text-sm text-gray-600">{p.code}</td>
                      <td className="px-4 py-3 font-medium text-gray-900">{p.name}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{p.region_name || '—'}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{p.area_name || '—'}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{p.manager_name || '—'}</td>
                      <td className="px-4 py-3 text-sm">
                        {p.allocated_budget ? (
                          <div>
                            <span className="font-medium text-gray-800">{fmt(p.allocated_budget)} ₪</span>
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
                          <button onClick={() => navigate(`/projects/${p.code}/workspace`)}
                            className="p-1.5 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg" title="פתח workspace">
                            <ExternalLink className="w-4 h-4" />
                          </button>
                          <button onClick={() => navigate(`/settings/organization/projects/${p.code}/edit`)}
                            className="p-1.5 text-gray-400 hover:text-orange-600 hover:bg-orange-50 rounded-lg" title="ערוך">
                            <Edit2 className="w-4 h-4" />
                          </button>
                          {p.is_active && (
                            <button onClick={() => setDeactivateId(p.id)}
                              className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg" title="השבת">
                              <Power className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          /* ── MAP VIEW ── */
          <div className="bg-white rounded-xl shadow-sm border overflow-hidden" style={{ height: 'calc(100vh - 250px)' }}>
            <Suspense fallback={<UnifiedLoader size="md" />}>
              <LeafletMap
                height="100%"
                points={mapPoints}
                polygons={mapPolygons}
                mapType="street"
                fitBounds={true}
              />
            </Suspense>
          </div>
        )}
      </div>

      {/* Deactivate Modal */}
      {deactivateId && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setDeactivateId(null)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm" onClick={e => e.stopPropagation()}>
            <div className="p-6 text-center">
              <div className="w-14 h-14 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Archive className="w-7 h-7 text-amber-600" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">השבתת פרויקט</h3>
              <p className="text-sm text-gray-600 mb-1">
                האם להשבית את <strong>{projects.find(p => p.id === deactivateId)?.name}</strong>?
              </p>
              <p className="text-xs text-gray-400 mb-5">הפרויקט יסומן כלא פעיל. ניתן לשחזר בעתיד.</p>
              <div className="flex gap-3">
                <button onClick={() => setDeactivateId(null)}
                  className="flex-1 px-4 py-2.5 border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50 text-sm font-medium">
                  ביטול
                </button>
                <button onClick={handleDeactivate} disabled={actionLoading}
                  className="flex-1 px-4 py-2.5 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-sm font-medium disabled:opacity-50">
                  {actionLoading ? 'משבית...' : 'השבת פרויקט'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default ProjectsManagement;
