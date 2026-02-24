// @ts-nocheck
// src/pages/Areas/Areas.tsx
import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, Search, Map, TreePine, MapPin, Building2, ChevronLeft } from 'lucide-react';
import api from '../../services/api';
import TreeLoader from '../../components/common/TreeLoader';

interface Area {
  id: number;
  name: string;
  code?: string;
  region_id: number;
  region_name?: string;
  manager_id?: number;
  manager_name?: string;
  description?: string;
  total_area_hectares?: number;
  projects_count?: number;
  is_active: boolean;
}

interface Region {
  id: number;
  name: string;
}

const Areas: React.FC = () => {
  const navigate = useNavigate();
  const [areas, setAreas] = useState<Area[]>([]);
  const [regions, setRegions] = useState<Region[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRegionId, setFilterRegionId] = useState<string>('all');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch areas and regions in parallel
      const [areasRes, regionsRes] = await Promise.all([
        api.get('/areas'),
        api.get('/regions')
      ]);
      
      const regionsData = regionsRes.data;
      setRegions(Array.isArray(regionsData) ? regionsData : (regionsData.items || regionsData.results || []));
      
      const areasData = areasRes.data;
      const areasArray = Array.isArray(areasData) ? areasData : (areasData.items || areasData.results || []);
      
      // Enrich areas with project counts
      const enrichedAreas = await Promise.all(
        areasArray.map(async (area: Area) => {
          try {
            const projectsRes = await api.get('/projects', { params: { area_id: area.id, per_page: 200 } });
            const projectsData = projectsRes.data.projects || projectsRes.data.items || [];
            
            // Find region name
            const region = regions.find(r => r.id === area.region_id);
            
            return {
              ...area,
              projects_count: projectsData.length,
              region_name: region?.name || area.region_name
            };
          } catch {
            return area;
          }
        })
      );
      
      setAreas(enrichedAreas);
    } catch (error: any) {
      console.error('Error fetching data:', error);
      setError('שגיאה בטעינת הנתונים');
    } finally {
      setLoading(false);
    }
  };

  const getRegionName = (regionId: number) => {
    const region = regions.find(r => r.id === regionId);
    return region?.name || '';
  };

  const filteredAreas = areas.filter(area => {
    const matchesSearch = !searchTerm || 
      area.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (area.code && area.code.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesRegion = filterRegionId === 'all' || area.region_id === parseInt(filterRegionId);
    
    return matchesSearch && matchesRegion;
  });

  // Group areas by region
  const areasByRegion = filteredAreas.reduce((acc, area) => {
    const regionName = area.region_name || getRegionName(area.region_id) || 'אחר';
    if (!acc[regionName]) {
      acc[regionName] = [];
    }
    acc[regionName].push(area);
    return acc;
  }, {} as Record<string, Area[]>);

  if (loading) {
    return <TreeLoader fullScreen />;
  }

  return (
    <div className="min-h-screen bg-gray-50" dir="rtl">
      {/* Header - Sticky */}
      <div className="sticky top-0 z-20 bg-white shadow-sm">
        <div className="px-4 py-3">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-xl font-bold text-gray-900">אזורים</h1>
            <Link
              to="/settings/organization/areas/new"
              className="bg-green-600 text-white px-4 py-2 rounded-lg flex items-center gap-1 text-sm"
            >
              <Plus className="w-4 h-4" />
              חדש
            </Link>
          </div>
          
          {/* Filters */}
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="חיפוש..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pr-10 pl-4 py-2 border border-gray-200 rounded-lg text-sm"
              />
            </div>
            <select
              value={filterRegionId}
              onChange={(e) => setFilterRegionId(e.target.value)}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm min-w-[100px]"
            >
              <option value="all">כל המרחבים</option>
              {regions.map(region => (
                <option key={region.id} value={region.id}>{region.name}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mx-4 mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Areas List - Grouped by Region */}
      <div className="p-4 space-y-4">
        {Object.entries(areasByRegion).map(([regionName, regionAreas]) => (
          <div key={regionName}>
            {/* Region Header */}
            <div className="flex items-center gap-2 mb-2 px-1">
              <Map className="w-4 h-4 text-green-600" />
              <h2 className="text-sm font-semibold text-gray-700">{regionName}</h2>
              <span className="text-xs text-gray-400">({regionAreas.length})</span>
            </div>
            
            {/* Areas in this region */}
            <div className="space-y-2">
              {regionAreas.map((area) => (
                <div
                  key={area.id}
                  onClick={() => navigate(`/areas/${area.id}`)}
                  className="bg-white rounded-xl shadow-sm border p-4 hover:shadow-md transition-shadow cursor-pointer"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center text-white">
                        <Building2 className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900">{area.name}</h3>
                        {area.code && (
                          <p className="text-xs text-gray-400">{area.code}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-1.5 bg-green-50 text-green-700 px-2 py-1 rounded-lg text-sm">
                        <TreePine className="w-3.5 h-3.5" />
                        <span className="font-medium">{area.projects_count || 0}</span>
                      </div>
                      <ChevronLeft className="w-5 h-5 text-gray-400" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}

        {filteredAreas.length === 0 && (
          <div className="text-center py-12">
            <MapPin className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">לא נמצאו אזורים</p>
          </div>
        )}
      </div>

      {/* Summary */}
      {filteredAreas.length > 0 && (
        <div className="p-4 bg-white border-t">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-gray-900">{filteredAreas.length}</div>
              <div className="text-xs text-gray-500">אזורים</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">
                {filteredAreas.reduce((sum, a) => sum + (a.projects_count || 0), 0)}
              </div>
              <div className="text-xs text-gray-500">פרויקטים</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-600">
                {Object.keys(areasByRegion).length}
              </div>
              <div className="text-xs text-gray-500">מרחבים</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Areas;
