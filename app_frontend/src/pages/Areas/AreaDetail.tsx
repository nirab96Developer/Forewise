// @ts-nocheck
// src/pages/Areas/AreaDetail.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ArrowRight, Map, TreePine, MapPin, Users, Edit, 
  Loader2, Eye, ChevronLeft, Building2, Layers
} from 'lucide-react';
import api from '../../services/api';
import LeafletMap from '../../components/Map/LeafletMap';
import TreeLoader from '../../components/common/TreeLoader';

interface Area {
  id: number;
  name: string;
  code?: string;
  region_id: number;
  region_name?: string;
  description?: string;
  manager_id?: number;
  manager_name?: string;
  total_area_hectares?: number;
}

interface Project {
  id: number;
  code: string;
  name: string;
  status: string;
  location?: { latitude?: number; longitude?: number; };
  budget?: number;
  work_type?: string;
}

const GOOGLE_MAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '';
const defaultCenter = { lat: 31.5, lng: 34.8 };

// צבעים לפי סטטוס
const statusColors: Record<string, string> = {
  active: '#10B981',
  completed: '#3B82F6',
  on_hold: '#F59E0B',
  planning: '#8B5CF6',
  cancelled: '#EF4444',
  default: '#6B7280',
};

// סוגי מפה
const mapTypes = [
  { id: 'roadmap', label: 'רגיל', icon: '🗺️' },
  { id: 'satellite', label: 'לוויין', icon: '🛰️' },
  { id: 'hybrid', label: 'היברידי', icon: '🌍' },
  { id: 'terrain', label: 'טופוגרפי', icon: '⛰️' },
];

const AreaDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [area, setArea] = useState<Area | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  useEffect(() => {
    fetchData();
  }, [id]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      const areaRes = await api.get(`/areas/${id}`);
      setArea(areaRes.data);
      
      const projectsRes = await api.get('/projects', { params: { area_id: id, per_page: 100 } });
      const projectsData = projectsRes.data.projects || projectsRes.data.items || [];
      
      // Add random locations for projects without coordinates (for demo)
      const enrichedProjects = projectsData.map((p: Project) => {
        if (!p.location?.latitude || !p.location?.longitude) {
          return {
            ...p,
            location: {
              latitude: 31.5 + (Math.random() - 0.5) * 1.5,
              longitude: 34.8 + (Math.random() - 0.5) * 1.5,
            }
          };
        }
        return p;
      });
      
      setProjects(enrichedProjects);
    } catch (err) {
      console.error('Error fetching area:', err);
      setError('שגיאה בטעינת האזור');
    }
    setLoading(false);
  };

  const onMapLoad = useCallback((map: google.maps.Map) => {
    setMapRef(map);
  }, []);

  useEffect(() => {
    if (mapRef && projects.length > 0) {
      const bounds = new google.maps.LatLngBounds();
      let hasValid = false;
      
      projects.forEach(p => {
        if (p.location?.latitude && p.location?.longitude) {
          bounds.extend({ lat: p.location.latitude, lng: p.location.longitude });
          hasValid = true;
        }
      });
      
      if (hasValid) {
        mapRef.fitBounds(bounds, 80);
      }
    }
  }, [mapRef, projects]);

  const getStatusColor = (status: string) => statusColors[status] || statusColors.default;
  
  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      active: 'פעיל', completed: 'הושלם', on_hold: 'מושהה',
      planning: 'בתכנון', cancelled: 'בוטל'
    };
    return labels[status] || status;
  };

  const projectsWithLocation = projects.filter(p => p.location?.latitude && p.location?.longitude);

  if (loading) {
    return <TreeLoader fullScreen />;
  }

  if (error || !area) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="bg-white rounded-xl shadow-lg p-6 text-center">
          <MapPin className="w-12 h-12 text-red-500 mx-auto mb-3" />
          <h2 className="text-lg font-bold mb-2">{error || 'אזור לא נמצא'}</h2>
          <button onClick={() => navigate('/areas')} className="mt-3 px-5 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
            חזור לאזורים
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
              <button onClick={() => navigate('/settings/organization/areas')} className="text-green-600 hover:text-green-800">
                <ArrowRight className="w-5 h-5" />
              </button>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center text-white shadow-lg">
                  <Building2 className="w-5 h-5" />
                </div>
                <div>
                  <h1 className="text-lg font-bold text-gray-900">{area.name}</h1>
                  <p className="text-xs text-gray-500">{area.code || area.region_name}</p>
                </div>
              </div>
            </div>
            <Link to={`/areas/${id}/edit`} className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg">
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
              <TreePine className="w-4 h-4 text-green-600" />
              <span className="font-bold">{projects.length}</span>
              <span className="text-gray-500">פרויקטים</span>
            </div>
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-blue-600" />
              <span className="font-bold">{projectsWithLocation.length}</span>
              <span className="text-gray-500">במפה</span>
            </div>
            {area.region_name && (
              <div className="flex items-center gap-2">
                <Map className="w-4 h-4 text-purple-600" />
                <span className="text-gray-600">{area.region_name}</span>
              </div>
            )}
            {area.manager_name && (
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-orange-600" />
                <span className="text-gray-600">{area.manager_name}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Status Legend */}
      <div className="bg-white border-b px-4 py-2 flex-shrink-0">
        <div className="max-w-7xl mx-auto flex items-center gap-4 overflow-x-auto text-xs">
          {Object.entries(statusColors).filter(([k]) => k !== 'default').map(([status, color]) => (
            <div key={status} className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full shadow" style={{ backgroundColor: color }} />
              <span className="text-gray-600">{getStatusLabel(status)}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Map Container - Leaflet */}
      <div className="flex-1 relative min-h-[400px]">
        <LeafletMap
          height="500px"
          mapType="satellite"
          points={projectsWithLocation.map(p => ({
            id: p.id,
            name: p.name,
            code: p.code,
            lat: p.location?.latitude || 0,
            lng: p.location?.longitude || 0,
            color: getStatusColor(p.status),
            onClick: () => setSelectedProject(p),
            popupContent: '<div style="direction:rtl;padding:6px"><b>' + p.name + '</b><br><span style="font-size:11px;color:#6b7280">' + (p.code || '') + '</span><br><a href="/projects/' + p.code + '/workspace" style="display:inline-block;margin-top:4px;padding:3px 10px;background:#16a34a;color:#fff;border-radius:5px;text-decoration:none;font-size:11px">פתח</a></div>',
          }))}
        />

        {/* Map Type Selector */}
        <div className="absolute top-3 right-3 z-10">
          <button
            onClick={() => setShowMapTypes(!showMapTypes)}
            className="bg-white shadow-lg rounded-lg px-3 py-2 flex items-center gap-2 hover:bg-gray-50 border"
          >
            <Layers className="w-4 h-4 text-gray-600" />
            <span className="text-sm font-medium">שכבות</span>
          </button>
          {showMapTypes && (
            <div className="absolute top-12 right-0 bg-white rounded-lg shadow-xl border overflow-hidden min-w-[140px]">
              {mapTypes.map((type) => (
                <button
                  key={type.id}
                  onClick={() => { setMapType(type.id); setShowMapTypes(false); }}
                  className={`w-full px-4 py-2.5 text-right flex items-center gap-2 hover:bg-gray-50 ${
                    mapType === type.id ? 'bg-green-50 text-green-700' : ''
                  }`}
                >
                  <span>{type.icon}</span>
                  <span className="text-sm">{type.label}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Selected Project Info */}
        {selectedProject && (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-white rounded-xl shadow-2xl p-4 w-[90%] max-w-sm border-2 border-blue-500">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded-full flex-shrink-0 shadow" style={{ backgroundColor: getStatusColor(selectedProject.status) }} />
                  <h3 className="font-bold text-gray-900 truncate">{selectedProject.name}</h3>
                </div>
                <p className="text-sm text-gray-500 mt-1">#{selectedProject.code}</p>
                <div className="flex items-center gap-2 mt-2 text-sm">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium`} 
                        style={{ backgroundColor: getStatusColor(selectedProject.status) + '20', color: getStatusColor(selectedProject.status) }}>
                    {getStatusLabel(selectedProject.status)}
                  </span>
                  {selectedProject.work_type && (
                    <span className="text-gray-500">{selectedProject.work_type}</span>
                  )}
                </div>
              </div>
              <button
                onClick={() => navigate(`/projects/${selectedProject.code}`)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm flex items-center gap-1 hover:bg-blue-700 shadow flex-shrink-0"
              >
                <Eye className="w-4 h-4" />
                צפייה
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Projects List */}
      <div className="bg-white border-t flex-shrink-0 max-h-[180px] overflow-y-auto">
        <div className="max-w-7xl mx-auto divide-y">
          {projects.map((project) => (
            <div
              key={project.id}
              onClick={() => navigate(`/projects/${project.code}`)}
              className="px-4 py-3 flex items-center justify-between hover:bg-blue-50 cursor-pointer transition-colors"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-4 h-4 rounded-full flex-shrink-0 shadow" style={{ backgroundColor: getStatusColor(project.status) }} />
                <div className="min-w-0">
                  <p className="font-medium text-gray-900 truncate">{project.name}</p>
                  <p className="text-xs text-gray-500">#{project.code} • {getStatusLabel(project.status)}</p>
                </div>
              </div>
              <ChevronLeft className="w-5 h-5 text-gray-400 flex-shrink-0" />
            </div>
          ))}
          {projects.length === 0 && (
            <div className="px-4 py-8 text-center text-gray-500">
              <TreePine className="w-10 h-10 mx-auto mb-2 text-gray-300" />
              <p>אין פרויקטים באזור זה</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AreaDetail;
