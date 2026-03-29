
// src/pages/Regions/Regions.tsx
import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, Search, Map, TreePine, MapPin, Building2, ChevronLeft } from 'lucide-react';
import api from '../../services/api';
import TreeLoader from '../../components/common/TreeLoader';

interface Region {
  id: number;
  name: string;
  code: string;
  manager_id?: number;
  manager_name?: string;
  description?: string;
  areas_count?: number;
  projects_count?: number;
  total_budget?: number;
  is_active?: boolean;
}

const Regions: React.FC = () => {
  const navigate = useNavigate();
  const [regions, setRegions] = useState<Region[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch regions
      const response = await api.get('/regions');
      const data = response.data;
      const regionsData = Array.isArray(data) ? data : (data.items || data.results || []);
      
      // Enrich regions with counts
      const enrichedRegions = await Promise.all(
        regionsData.map(async (region: Region) => {
          try {
            // Fetch areas for this region
            const areasRes = await api.get('/areas', { params: { region_id: region.id } });
            const areasData = Array.isArray(areasRes.data) ? areasRes.data : (areasRes.data.items || []);
            
            // Fetch projects for this region
            const projectsRes = await api.get('/projects', { params: { region_id: region.id, per_page: 200 } });
            const projectsData = projectsRes.data.projects || projectsRes.data.items || [];
            
            return {
              ...region,
              areas_count: areasData.length,
              projects_count: projectsData.length
            };
          } catch {
            return region;
          }
        })
      );
      
      setRegions(enrichedRegions);
    } catch (error: any) {
      console.error('Error fetching regions:', error);
      setError('שגיאה בטעינת המרחבים');
    } finally {
      setLoading(false);
    }
  };

  const filteredRegions = regions.filter(region => {
    if (!searchTerm) return true;
    return region.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
           region.code.toLowerCase().includes(searchTerm.toLowerCase());
  });

  if (loading) {
    return <TreeLoader fullScreen />;
  }

  // Mobile-friendly card layout
  return (
    <div className="min-h-screen bg-gray-50" dir="rtl">
      {/* Header - Sticky */}
      <div className="sticky top-0 z-20 bg-white shadow-sm">
        <div className="px-4 py-3">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-xl font-bold text-gray-900">מרחבים</h1>
            <Link
              to="/settings/organization/regions/new"
              className="bg-green-600 text-white px-4 py-2 rounded-lg flex items-center gap-1 text-sm"
            >
              <Plus className="w-4 h-4" />
              חדש
            </Link>
          </div>
          
          {/* Search */}
          <div className="relative">
            <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="חיפוש..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pr-10 pl-4 py-2 border border-gray-200 rounded-lg text-sm"
            />
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mx-4 mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Regions List */}
      <div className="p-4 space-y-3">
        {filteredRegions.map((region) => (
          <div
            key={region.id}
            onClick={() => navigate(`/regions/${region.id}`)}
            className="bg-white rounded-xl shadow-sm border p-4 hover:shadow-md transition-shadow cursor-pointer"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-green-600 rounded-xl flex items-center justify-center text-white shadow-lg">
                  <Map className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900 text-lg">{region.name}</h3>
                  <p className="text-sm text-gray-500">{region.code}</p>
                </div>
              </div>
              <ChevronLeft className="w-5 h-5 text-gray-400" />
            </div>
            
            {/* Stats */}
            <div className="mt-4 flex flex-wrap items-center gap-2 text-sm">
              <div className="flex items-center gap-1.5 bg-blue-50 text-blue-700 px-3 py-1.5 rounded-lg">
                <Building2 className="w-4 h-4" />
                <span className="font-medium">{region.areas_count || 0}</span>
                <span>אזורים</span>
              </div>
              <div className="flex items-center gap-1.5 bg-green-50 text-green-700 px-3 py-1.5 rounded-lg">
                <TreePine className="w-4 h-4" />
                <span className="font-medium">{region.projects_count || 0}</span>
                <span>פרויקטים</span>
              </div>
              {region.total_budget && region.total_budget > 0 && (
                <div className="flex items-center gap-1.5 bg-emerald-100 text-emerald-700 px-3 py-1.5 rounded-lg font-bold">
                  <span className="w-4 h-4 font-bold leading-none inline-flex items-center justify-center">₪</span>
<span>{Number(region.total_budget).toLocaleString()}</span>
                </div>
              )}
            </div>
          </div>
        ))}

        {filteredRegions.length === 0 && (
          <div className="text-center py-12">
            <MapPin className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">לא נמצאו מרחבים</p>
          </div>
        )}
      </div>

      {/* Summary */}
      {filteredRegions.length > 0 && (
        <div className="p-4 bg-white border-t">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-gray-900">{filteredRegions.length}</div>
              <div className="text-xs text-gray-500">מרחבים</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-600">
                {filteredRegions.reduce((sum, r) => sum + (r.areas_count || 0), 0)}
              </div>
              <div className="text-xs text-gray-500">אזורים</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">
                {filteredRegions.reduce((sum, r) => sum + (r.projects_count || 0), 0)}
              </div>
              <div className="text-xs text-gray-500">פרויקטים</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Regions;
