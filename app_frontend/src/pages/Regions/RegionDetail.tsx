// @ts-nocheck
// src/pages/Regions/RegionDetail.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ArrowRight, Map, TreePine, Building2, Users, Edit, 
  Loader2, MapPin, Eye, ChevronLeft, Layers, DollarSign
} from 'lucide-react';
import api from '../../services/api';
import LeafletMap from '../../components/Map/LeafletMap';
import type { MapPoint, MapPolygon } from '../../components/Map/LeafletMap';
import TreeLoader from '../../components/common/TreeLoader';

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

// API key loaded via index.html script tag - no need for useLoadScript
const defaultCenter = { lat: 31.5, lng: 34.8 };

// צבעים יפים לאזורים
const areaColors = [
  '#10B981', '#3B82F6', '#F59E0B', '#8B5CF6', 
  '#EF4444', '#EC4899', '#06B6D4', '#84CC16',
];

// סוגי מפה
const mapTypes = [
  { id: 'roadmap', label: 'רגיל', icon: '🗺️' },
  { id: 'satellite', label: 'לוויין', icon: '🛰️' },
  { id: 'hybrid', label: 'היברידי', icon: '🌍' },
  { id: 'terrain', label: 'טופוגרפי', icon: '⛰️' },
];

const RegionDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [region, setRegion] = useState<Region | null>(null);
  const [areas, setAreas] = useState<Area[]>([]);
  const [loading, setLoading] = useState(true);
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
      
      // שלוף את הפוליגונים של כל פרויקט
      const polygonPromises = allProjects.map(async (project: any) => {
        try {
          const mapData = await api.get(`/projects/${project.id}/forest-map`);
          if (mapData.data.has_forest && mapData.data.forest) {
            return {
              id: project.id,
              name: project.name,
              area_id: project.area_id,
              geojson: mapData.data.forest.geojson_preview || mapData.data.forest.geojson_full
            };
          }
        } catch (err) {
          console.log(`No forest polygon for project ${project.id}`);
        }
        return null;
      });
      
      const fetchedPolygons = (await Promise.all(polygonPromises)).filter(p => p !== null);
      setPolygons(fetchedPolygons);
      
      const areasWithData = areasData.map((area: Area) => {
        const areaProjects = allProjects.filter((p: any) => p.area_id === area.id);
        
        // חשב ממוצע מיקום מהפרויקטים עם location אמיתי
        const validProjects = areaProjects.filter((p: any) => 
          p.location?.latitude && p.location?.longitude
        );
        
        let lat = 31.5; // ברירת מחדל - מרכז ישראל
        let lng = 35.0;
        
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
    <div className="h-screen flex flex-col overflow-hidden" dir="rtl">
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
            <Link to={`/regions/${id}/edit`} className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg">
              <Edit className="w-5 h-5" />
            </Link>
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
                <DollarSign className="w-4 h-4 text-emerald-600" />
                <span className="font-bold text-emerald-700">₪{Number(region.total_budget).toLocaleString()}</span>
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
      <div className="flex-1 relative min-h-[400px]">
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
          polygons={polygons.map((poly, idx) => ({
            id: poly.id,
            name: poly.name,
            geometry: poly.geojson?.geometry || poly.geojson,
            fillColor: getAreaColor(areas.findIndex(a => a.id === poly.area_id) || idx),
            strokeColor: getAreaColor(areas.findIndex(a => a.id === poly.area_id) || idx),
            fillOpacity: 0.25,
            strokeWeight: 2,
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
