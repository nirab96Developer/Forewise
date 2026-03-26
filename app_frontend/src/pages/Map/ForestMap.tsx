
// src/pages/Map/ForestMap.tsx
// Map Intelligence - responsive: mobile overlay sidebar, desktop side panel
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layers, Eye, EyeOff, Home, Building2, ChevronLeft, Map as MapIcon, X } from 'lucide-react';
import UnifiedLoader from '../../components/common/UnifiedLoader';
import LeafletMap from '../../components/Map/LeafletMap';
import api from '../../services/api';
// permissions utils available if needed

const REGION_COLORS: Record<number, { fill: string; stroke: string; name: string }> = {
  1: { fill: '#059669', stroke: '#047857', name: 'צפון' },
  2: { fill: '#2563eb', stroke: '#1d4ed8', name: 'מרכז' },
  3: { fill: '#d97706', stroke: '#b45309', name: 'דרום' },
};
const AREA_COLORS = ['#10b981','#3b82f6','#f59e0b','#ef4444','#8b5cf6','#ec4899','#14b8a6','#f97316','#6366f1','#84cc16'];

const ForestMap = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [layerData, setLayerData] = useState<any>(null);
  const [selectedRegion, setSelectedRegion] = useState<number | null>(null);
  const [selectedProject, setSelectedProject] = useState<any>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [myProjectIds, setMyProjectIds] = useState(new Set());
  let userData: any = {};
  try { userData = JSON.parse(localStorage.getItem('user') || '{}'); } catch { /* corrupted storage */ }
  const userAreaId = userData.area_id;
  const userRole = userData.role || userData.role_code || '';
  const isWorkManager = userRole === 'WORK_MANAGER' || userRole === 'FIELD_WORKER';

  // WORK_MANAGER sees only their projects — hide region/area layers
  const [layerVis, setLayerVis] = useState<Record<string, boolean>>({
    regions: !isWorkManager,
    areas: !isWorkManager,
    forests: true,
    projects: true,
    myProjects: isWorkManager,
  });

  useEffect(() => {
    (async () => {
      try {
        const [lr, mr] = await Promise.all([
          api.get('/geo/layers/all'),
          api.get('/project-assignments/my-assignments').catch(() => ({ data: { projects: [] } })),
        ]);
        setLayerData(lr.data);
        setMyProjectIds(new Set((mr.data.projects || []).map((p: any) => p.project_id || p.id)));
      } catch (e) { console.error(e); }
      setLoading(false);
    })();
  }, []);

  if (loading) return <UnifiedLoader size="full" />;

  // Build layers
  const mapPolygons: any[] = [];
  let maskPoly;

  if (selectedRegion && layerData?.regions?.features) {
    const feat = layerData.regions.features.find((f: any) => f.properties.id === selectedRegion);
    if (feat) maskPoly = { id: -1, name: '', geometry: feat.geometry, strokeColor: REGION_COLORS[selectedRegion]?.stroke || '#047857', strokeWeight: 3 };
  }

  if (layerVis.regions && !selectedRegion && layerData?.regions?.features) {
    layerData.regions.features.forEach((f: any) => {
      const rid = f.properties.id;
      const c = REGION_COLORS[rid] || { fill: '#6b7280', stroke: '#4b5563' };
      mapPolygons.push({ id: rid, name: c.name, geometry: f.geometry, fillColor: c.fill, strokeColor: c.stroke, fillOpacity: 0.12, strokeWeight: 2, onClick: () => { setSelectedRegion(rid); setSidebarOpen(false); } });
    });
  }

  if (layerVis.areas && layerData?.areas?.features) {
    layerData.areas.features.forEach((f: any, idx: any) => {
      if (selectedRegion && f.properties.region_id !== selectedRegion) return;
      const color = AREA_COLORS[idx % AREA_COLORS.length];
      mapPolygons.push({ id: f.properties.id, name: f.properties.name, geometry: f.geometry, fillColor: color, strokeColor: color, fillOpacity: f.properties.id === userAreaId ? 0.20 : 0.06, strokeWeight: f.properties.id === userAreaId ? 3 : 1.5 });
    });
  }

  // Forest polygons — dark green fill
  if (layerVis.forests && layerData?.forests?.features) {
    layerData.forests.features.forEach((f: any) => {
      mapPolygons.push({
        id: `forest-${f.properties.id}`,
        name: `יער (${f.properties.area_km2} km²)`,
        geometry: f.geometry,
        fillColor: '#166534',
        strokeColor: '#14532d',
        fillOpacity: 0.35,
        strokeWeight: 1.5,
      });
    });
  }

  let mapPoints: any[] = [];
  if (layerVis.projects && layerData?.projects) {
    let projs = layerData.projects;
    if (layerVis.myProjects && myProjectIds.size > 0) projs = projs.filter((p: any) => myProjectIds.has(p.id));
    if (selectedRegion) projs = projs.filter((p: any) => p.region_id === selectedRegion);
    mapPoints = projs.filter((p: any) => p.lat && p.lng).map((p: any) => ({
      id: p.id, name: p.name, code: p.code, lat: p.lat, lng: p.lng,
      color: myProjectIds.has(p.id) ? '#f59e0b' : '#16a34a',
      popupContent:
        '<div style="direction:rtl;padding:6px;min-width:170px">' +
        '<b>' + p.name + '</b><br>' +
        '<span style="color:#6b7280;font-size:11px">' + p.code + ' | ' + (REGION_COLORS[p.region_id]?.name || '') + '</span><br>' +
        '<span style="display:inline-block;margin-top:3px;color:#374151;font-size:11px">מיקום פרויקט</span>' +
        (p.geo_validation_status === 'NEAR'
? '<br><span style="display:inline-block;margin-top:3px;color:#b45309;font-size:11px;font-weight:600"> נקודה קרובה לגבול (NEAR 3km)' +
            (p.distance_to_area_meters != null ? ' (' + p.distance_to_area_meters + 'm)' : '') +
            '</span>'
          : '') +
        '<br><a href="/projects/' + p.code + '/workspace" style="display:inline-block;margin-top:6px;padding:4px 10px;background:#16a34a;color:#fff;border-radius:5px;text-decoration:none;font-size:11px">פתח</a>' +
        '</div>',
      onClick: () => setSelectedProject(p),
    }));
  }

  const stats = { regions: layerData?.regions?.features?.length || 0, areas: layerData?.areas?.features?.length || 0, projects: layerData?.projects?.length || 0 };
  const toggleLayer = (key: string) => setLayerVis((prev: any) => ({ ...prev, [key]: !prev[key] }));
  const goBackToMenu = () => navigate('/');

  // Auto-center on user's projects (WORK_MANAGER) or region selection
  let mapCenter: [number, number] = [31.5, 35.0];
  let mapZoom = 8;

  const myPoints = mapPoints.filter(p => myProjectIds.has(p.id));
  const focusPoints = isWorkManager && myPoints.length > 0 ? myPoints : mapPoints;

  if (focusPoints.length > 0) {
    const lats = focusPoints.map(p => p.lat);
    const lngs = focusPoints.map(p => p.lng);
    const minLat = Math.min(...lats), maxLat = Math.max(...lats);
    const minLng = Math.min(...lngs), maxLng = Math.max(...lngs);
    mapCenter = [(minLat + maxLat) / 2, (minLng + maxLng) / 2];
    // Calculate zoom based on spread
    const latSpread = maxLat - minLat;
    const lngSpread = maxLng - minLng;
    const spread = Math.max(latSpread, lngSpread);
    mapZoom = spread < 0.05 ? 13 : spread < 0.15 ? 12 : spread < 0.4 ? 11 : spread < 1.0 ? 10 : spread < 2.0 ? 9 : 8;
  } else if (selectedRegion) {
    // Center on selected region
    const regionProjects = (layerData?.projects || []).filter((p: any) => p.region_id === selectedRegion && p.lat && p.lng);
    if (regionProjects.length > 0) {
      const lats = regionProjects.map((p: any) => p.lat);
      const lngs = regionProjects.map((p: any) => p.lng);
      mapCenter = [(Math.min(...lats) + Math.max(...lats)) / 2, (Math.min(...lngs) + Math.max(...lngs)) / 2];
      mapZoom = 10;
    }
  }

  return (
    <div className="h-[calc(100vh-64px)] relative" dir="rtl">
      {/* Mobile overlay backdrop */}
      {sidebarOpen && <div className="fixed inset-0 bg-black/40 z-[1001] md:hidden" onClick={() => setSidebarOpen(false)} />}

      {/* Sidebar - overlay on mobile, absolute on desktop */}
      <div className={`
        fixed md:absolute top-16 md:top-0 right-0 bottom-0 z-[1002]
        bg-white shadow-xl md:shadow-lg border-l border-gray-200
        flex flex-col overflow-y-auto overflow-x-visible box-border
        w-[92vw] max-w-[26rem] min-w-[16rem] md:w-72 md:max-w-[85vw]
        transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : 'translate-x-full'}
      `}
      dir="rtl">
        <div className="p-4 border-b bg-gradient-to-l from-green-50 to-white flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2"><MapIcon className="w-5 h-5 text-green-600" /><h2 className="font-bold text-gray-900 text-sm">מפת יערות</h2></div>
            <p className="text-xs text-gray-500 mt-0.5">{stats.projects} פרויקטים | {stats.areas} אזורים</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={goBackToMenu}
              className="px-2.5 py-1.5 rounded-lg border border-gray-200 hover:bg-gray-100 text-gray-700 text-xs font-medium touch-manipulation"
              title="חזרה לתפריט הראשי"
            >
              <span className="inline-flex items-center gap-1">
                <ChevronLeft className="w-3.5 h-3.5" />
                חזרה
              </span>
            </button>
            <button onClick={() => setSidebarOpen(false)} className="p-2 rounded-lg hover:bg-gray-100 touch-manipulation"><X className="w-5 h-5 text-gray-400" /></button>
          </div>
        </div>

        <div className="p-4 border-b">
          <h3 className="text-xs font-bold text-gray-500 mb-2">שכבות</h3>
          <div className="space-y-1.5">
            {[
{key:'forests',label:'גבולות יערות',icon:''},
{key:'regions',label:'מרחבים',icon:''},
{key:'areas',label:'אזורים',icon:''},
{key:'projects',label:'נקודות פרויקטים',icon:''},
{key:'myProjects',label:'שלי בלבד',icon:''},
            ]
              .filter(l => isWorkManager ? !['regions','areas'].includes(l.key) : true)
              .map(l => (
              <button key={l.key} onClick={() => toggleLayer(l.key)}
                className={`w-full flex items-center gap-3 px-4.5 py-2.5 rounded-lg text-sm touch-manipulation ${layerVis[l.key] ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-gray-50 text-gray-400 border border-gray-200'}`}>
                <span>{l.icon}</span><span className="flex-1 text-right font-medium">{l.label}</span>
                {layerVis[l.key] ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
              </button>
            ))}
          </div>
        </div>

        {!isWorkManager && (
          <div className="p-4 border-b">
            <h3 className="text-xs font-bold text-gray-500 mb-2">מרחבים</h3>
            <button onClick={() => { setSelectedRegion(null); setSidebarOpen(false); }}
              className={`w-full flex items-center gap-3 px-4.5 py-2.5 rounded-lg text-sm mb-1 touch-manipulation ${!selectedRegion ? 'bg-gray-100 font-bold' : 'hover:bg-gray-50'}`}>
              <Home className="w-4 h-4 text-gray-500" /><span>כל הארץ</span>
            </button>
            {Object.entries(REGION_COLORS).map(([id, cfg]) => (
              <button key={id} onClick={() => { setSelectedRegion(Number(id)); setSidebarOpen(false); }}
                className={`w-full flex items-center gap-3 px-4.5 py-2.5 rounded-lg text-sm mb-0.5 touch-manipulation ${selectedRegion === Number(id) ? 'bg-green-100 font-bold text-green-800' : 'hover:bg-gray-50'}`}>
                <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: cfg.fill }} />
                <span>{cfg.name}</span>
                <span className="mr-auto text-xs text-gray-400">{layerData?.projects?.filter((p: any) => p.region_id === Number(id)).length || 0}</span>
              </button>
            ))}
          </div>
        )}

        {selectedProject && (
          <div className="p-3 bg-green-50 border-b">
            <div className="bg-white rounded-lg p-3 border border-green-200">
              <h4 className="font-bold text-gray-900 text-sm">{selectedProject.name}</h4>
              <p className="text-xs text-gray-500">{selectedProject.code}</p>
              <button onClick={() => navigate('/projects/' + selectedProject.code + '/workspace')}
                className="mt-2 w-full flex items-center justify-center gap-2 px-3 py-2 bg-green-600 text-white text-sm rounded-lg touch-manipulation">
                <Building2 className="w-4 h-4" />פתח
              </button>
            </div>
          </div>
        )}

        <div className="p-3">
          <div className="grid grid-cols-2 gap-1 text-xs">
            <div className="flex items-center gap-1"><div className="w-3 h-3 bg-green-600 rounded-full border-2 border-white shadow" /><span className="text-gray-500">פרויקט</span></div>
            <div className="flex items-center gap-1"><div className="w-3 h-3 bg-amber-500 rounded-full border-2 border-white shadow" /><span className="text-gray-500">שלי</span></div>
            <div className="flex items-center gap-1"><div className="w-3 h-2 bg-green-500/20 border border-green-600 rounded" /><span className="text-gray-500">מרחב</span></div>
            <div className="flex items-center gap-1"><div className="w-3 h-2 bg-blue-500/20 border border-blue-500 rounded" /><span className="text-gray-500">אזור</span></div>
          </div>
        </div>
      </div>

      {/* Sidebar toggle - always visible */}
      <button onClick={() => setSidebarOpen(true)}
        className={`absolute top-3 right-3 z-[999] bg-white shadow-lg rounded-xl p-3 border touch-manipulation min-w-[48px] min-h-[48px] flex items-center justify-center hover:bg-gray-50 active:bg-gray-100 ${sidebarOpen ? 'md:opacity-0 pointer-events-none md:pointer-events-auto' : ''}`}>
        <Layers className="w-5 h-5 text-green-700" />
      </button>

      {/* Quick back to regular app menu */}
      <button
        onClick={goBackToMenu}
        className="absolute top-3 right-[72px] z-[999] bg-white shadow-lg rounded-xl px-3 py-2 border touch-manipulation hover:bg-gray-50 active:bg-gray-100 text-xs font-medium text-gray-700"
        title="חזרה לתפריט"
      >
        <span className="inline-flex items-center gap-1">
          <ChevronLeft className="w-4 h-4" />
          תפריט
        </span>
      </button>

      {/* Map - always full width; sidebar overlays */}
      <div className="h-full">
        <LeafletMap
          height="calc(100vh - 64px)"
          points={mapPoints}
          polygons={mapPolygons}
          maskPolygon={maskPoly}
          mapType="satellite"
          center={mapCenter}
          zoom={mapZoom}
          fitBounds={true}
        />
      </div>
    </div>
  );
};

export default ForestMap;
