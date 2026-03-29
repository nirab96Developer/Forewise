
// src/pages/Regions/RegionDetail.tsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowRight, Map, TreePine, Building2, Users, Edit,
  MapPin, Eye, ChevronLeft
} from 'lucide-react';
import api from '../../services/api';
import LeafletMap from '../../components/Map/LeafletMap';
import TreeLoader from '../../components/common/TreeLoader';
import { useRoleAccess } from '../../hooks/useRoleAccess';

interface Region {
  id: number;
  name: string;
  code: string;
  description?: string;
  manager_id?: number;
  manager_name?: string;
  total_budget?: number;
}

interface Area {
  id: number;
  name: string;
  code?: string;
  region_id: number;
  latitude?: number;
  longitude?: number;
  projects_count?: number;
}

// צבעים יפים לאזורים
const areaColors = [
  '#10B981', '#3B82F6', '#F59E0B', '#8B5CF6', 
  '#EF4444', '#EC4899', '#06B6D4', '#84CC16',
];

const RegionDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [region, setRegion] = useState<Region | null>(null);
  const [areas, setAreas] = useState<Area[]>([]);
  const [loading, setLoading] = useState(true);
  const { canManageRegions } = useRoleAccess();
  const [error, setError] = useState<string | null>(null);
  const [selectedArea, setSelectedArea] = useState<Area | null>(null);
  const [polygons, setPolygons] = useState<any[]>([]);

  useEffect(() => {
    fetchData();
  }, [id]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      const regionRes = await api.get(`/regions/${id}`);
      setRegion(regionRes.data);
      
      const areasRes = await api.get('/areas', { params: { region_id: id } });
      const areasData = Array.isArray(areasRes.data) ? areasRes.data : (areasRes.data.items || []);
      
      // קבל את כל הפרויקטים במרחב
      const projectsRes = await api.get('/projects', { params: { region_id: id, per_page: 100 } });
      const allProjects = projectsRes.data.projects || projectsRes.data.items || [];
      
      // Load region + area boundary polygons from GIS
      const allPolygons: any[] = [];
      try {
        const regionBounds = await api.get('/geo/regions/boundaries');
        const regionFeature = (regionBounds.data?.features || []).find((f: any) => f.properties?.id === Number(id));
        if (regionFeature) {
          allPolygons.push({
            id: `region-${id}`,
            name: regionRes.data.name,
            area_id: null,
            geojson: regionFeature,
            isRegion: true,
          });
        }
      } catch {}
      try {
        const areaBounds = await api.get('/geo/areas/boundaries', { params: { region_id: id } });
        for (const feat of (areaBounds.data?.features || [])) {
          allPolygons.push({
            id: `area-${feat.properties?.id}`,
            name: feat.properties?.name,
            area_id: feat.properties?.id,
            geojson: feat,
            isRegion: false,
          });
        }
      } catch {}
      setPolygons(allPolygons);
      
      const areasWithData = areasData.map((area: Area) => {
        const areaProjects = allProjects.filter((p: any) => p.area_id === area.id);
        
        // חשב ממוצע מיקום מהפרויקטים עם location אמיתי
        const validProjects = areaProjects.filter((p: any) => 
          p.location?.latitude && p.location?.longitude
        );
        
        let lat: number | undefined;
        let lng: number | undefined;
        
        if (validProjects.length > 0) {
          lat = validProjects.reduce((sum: number, p: any) => sum + (p.location.latitude || 0), 0) / validProjects.length;
          lng = validProjects.reduce((sum: number, p: any) => sum + (p.location.longitude || 0), 0) / validProjects.length;
        }
        
        return { 
          ...area, 
          latitude: lat, 
          longitude: lng, 
          projects_count: areaProjects.length 
        };
      });
      
      setAreas(areasWithData);
    } catch (err) {
      console.error('Error fetching region:', err);
      setError('שגיאה בטעינת המרחב');
    }
    setLoading(false);
  };

  // Polygon drawing is handled by LeafletMap component

  const getAreaColor = (index: number) => areaColors[index % areaColors.length];

  if (loading) {
    return <TreeLoader fullScreen />;
  }

  if (error || !region) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="bg-white rounded-xl shadow-lg p-6 text-center">
          <MapPin className="w-12 h-12 text-red-500 mx-auto mb-3" />
          <h2 className="text-lg font-bold mb-2">{error || 'מרחב לא נמצא'}</h2>
          <button onClick={() => navigate('/regions')} className="mt-3 px-5 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
            חזור למרחבים
          </button>
        </div>
      </div>
    );
  }


  return (
    <div className="min-h-screen flex flex-col" dir="rtl">
      {/* Header */}
      <div className="bg-white border-b z-20 flex-shrink-0">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button onClick={() => navigate('/settings/organization/regions')} className="text-green-600 hover:text-green-800">
                <ArrowRight className="w-5 h-5" />
              </button>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-green-600 rounded-lg flex items-center justify-center text-white shadow-lg">
                  <Map className="w-5 h-5" />
                </div>
                <div>
                  <h1 className="text-lg font-bold text-gray-900">{region.name}</h1>
                  <p className="text-xs text-gray-500">{region.code}</p>
                </div>
              </div>
            </div>
            {canManageRegions && (
              <Link to={`/regions/${id}/edit`} className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg">
                <Edit className="w-5 h-5" />
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="bg-white border-b px-4 py-2 flex-shrink-0">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center gap-6 overflow-x-auto text-sm">
            <div className="flex items-center gap-2">
              <Building2 className="w-4 h-4 text-blue-600" />
              <span className="font-bold">{areas.length}</span>
              <span className="text-gray-500">אזורים</span>
            </div>
            <div className="flex items-center gap-2">
              <TreePine className="w-4 h-4 text-green-600" />
              <span className="font-bold">{areas.reduce((sum, a) => sum + (a.projects_count || 0), 0)}</span>
              <span className="text-gray-500">פרויקטים</span>
            </div>
            {region.total_budget && region.total_budget > 0 && (
              <div className="flex items-center gap-2 px-3 py-1 bg-emerald-50 rounded-full">
                <span className="w-4 h-4 text-emerald-600 font-bold leading-none inline-flex items-center justify-center">₪</span>
<span className="font-bold text-emerald-700">{Number(region.total_budget).toLocaleString()}</span>
                <span className="text-emerald-600">תקציב</span>
              </div>
            )}
            {region.manager_name && (
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-purple-600" />
                <span className="text-gray-600">{region.manager_name}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Map Container - Leaflet */}
      <div className="relative" style={{ height: '500px' }}>
        <LeafletMap
          height="500px"
          mapType="satellite"
          points={areas.filter(a => a.latitude && a.longitude).map((area, index) => ({
            id: area.id,
            name: area.name + (area.projects_count ? ' (' + area.projects_count + ' פרויקטים)' : ''),
            lat: area.latitude!,
            lng: area.longitude!,
            color: getAreaColor(index),
            onClick: () => setSelectedArea(area),
          }))}
          fitBounds={true}
          polygons={polygons.map((poly, idx) => ({
            id: poly.id,
            name: poly.name,
            geometry: poly.geojson?.geometry || poly.geojson,
            fillColor: poly.isRegion ? '#16a34a' : getAreaColor(areas.findIndex(a => a.id === poly.area_id) >= 0 ? areas.findIndex(a => a.id === poly.area_id) : idx),
            strokeColor: poly.isRegion ? '#15803d' : getAreaColor(areas.findIndex(a => a.id === poly.area_id) >= 0 ? areas.findIndex(a => a.id === poly.area_id) : idx),
            fillOpacity: poly.isRegion ? 0.08 : 0.25,
            strokeWeight: poly.isRegion ? 3 : 2,
          }))}
          maskPolygon={undefined}
        />

        {/* Selected Area Info */}
        {selectedArea && (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-white rounded-xl shadow-2xl p-4 w-[90%] max-w-sm border-2 border-green-500">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-bold text-gray-900 text-lg">{selectedArea.name}</h3>
                <p className="text-sm text-gray-500">{selectedArea.code}</p>
                <div className="flex items-center gap-2 mt-2">
                  <TreePine className="w-4 h-4 text-green-600" />
                  <span className="text-green-700 font-medium">{selectedArea.projects_count || 0} פרויקטים</span>
                </div>
              </div>
              <button
                onClick={() => navigate(`/areas/${selectedArea.id}`)}
                className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm flex items-center gap-1 hover:bg-green-700 shadow"
              >
                <Eye className="w-4 h-4" />
                צפייה
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Areas List */}
      <div className="bg-white border-t flex-shrink-0 max-h-[180px] overflow-y-auto">
        <div className="max-w-7xl mx-auto divide-y">
          {areas.map((area, index) => (
            <div
              key={area.id}
              onClick={() => navigate(`/areas/${area.id}`)}
              className="px-4 py-3 flex items-center justify-between hover:bg-green-50 cursor-pointer transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="w-4 h-4 rounded-full shadow" style={{ backgroundColor: getAreaColor(index) }} />
                <div>
                  <p className="font-medium text-gray-900">{area.name}</p>
                  <p className="text-xs text-gray-500">{area.projects_count || 0} פרויקטים</p>
                </div>
              </div>
              <ChevronLeft className="w-5 h-5 text-gray-400" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RegionDetail;
