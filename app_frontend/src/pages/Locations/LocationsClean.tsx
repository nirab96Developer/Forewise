
// src/pages/Locations/LocationsClean.tsx
// דף מיקומים עם עיצוב נקי לבן וירוק

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Plus,
  Search,
  Eye,
  Edit,
  MapPin,
  Loader2,
  Navigation,
  Map,
  Home,
  Filter,
  ChevronRight,
  Globe,
  Target,
} from 'lucide-react';
import api from '../../services/api';

interface Location {
  id: number;
  code: string;
  name: string;
  description?: string;
  area_id?: number;
  area_name?: string;
  region_name?: string;
  latitude?: number;
  longitude?: number;
  address?: string;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

const LocationsClean: React.FC = () => {
  const navigate = useNavigate();
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('grid');

  useEffect(() => {
    fetchLocations();
  }, []);

  const fetchLocations = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params: any = {};
      if (searchTerm) params.search = searchTerm;
      
      const response = await api.get('/locations', { params });
      const data = response.data;
      setLocations(Array.isArray(data) ? data : (data?.items || data?.results || []));
    } catch (error: any) {
      console.error('Error fetching locations:', error);
      setError('שגיאה בטעינת המיקומים');
      setLocations([]);
    }
    
    // Always stop loading
    setLoading(false);
  };

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      fetchLocations();
    }, 500);
    return () => clearTimeout(timeoutId);
  }, [searchTerm]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-green-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">טוען מיקומים...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">מיקומים</h1>
          <p className="text-gray-600 mt-2">ניהול מיקומים פיזיים ואתרי עבודה</p>
        </div>

        {/* Actions Bar */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-8">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="חיפוש לפי שם, קוד או כתובת..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pr-10 pl-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
                />
              </div>
            </div>
            
            <div className="flex gap-3">
              {/* View Mode Toggle */}
              <div className="flex bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`px-3 py-1 rounded transition-colors ${
                    viewMode === 'grid' 
                      ? 'bg-white text-gray-900 shadow-sm' 
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <Map className="w-5 h-5" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`px-3 py-1 rounded transition-colors ${
                    viewMode === 'list' 
                      ? 'bg-white text-gray-900 shadow-sm' 
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <Filter className="w-5 h-5" />
                </button>
              </div>
              
              {/* Add Button */}
              <Link
                to="/locations/new"
                className="flex items-center gap-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
              >
                <Plus className="w-5 h-5" />
                מיקום חדש
              </Link>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Locations Grid/List */}
        {locations.length === 0 ? (
          <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
            <MapPin className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              {searchTerm ? 'לא נמצאו מיקומים' : 'אין מיקומים'}
            </h2>
            <p className="text-gray-600 mb-6">
              {searchTerm 
                ? 'נסה לחפש במונחים אחרים'
                : 'התחל ביצירת מיקום חדש'}
            </p>
            {!searchTerm && (
              <Link
                to="/locations/new"
                className="inline-flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
              >
                <Plus className="w-5 h-5" />
                צור מיקום ראשון
              </Link>
            )}
          </div>
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {locations.map((location) => (
              <div 
                key={location.id} 
                className="bg-white rounded-lg border border-gray-200 hover:shadow-lg transition-all duration-300 cursor-pointer group"
                onClick={() => navigate(`/locations/${location.id}`)}
              >
                {/* Card Header */}
                <div className="p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex items-start gap-3">
                      <div className="p-2 bg-green-100 rounded-lg">
                        <MapPin className="w-5 h-5 text-green-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900 group-hover:text-green-600 transition-colors">
                          {location.name}
                        </h3>
                        <span className="text-sm text-gray-500">#{location.code}</span>
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      location.is_active !== false
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {location.is_active !== false ? 'פעיל' : 'לא פעיל'}
                    </span>
                  </div>
                  
                  {location.description && (
                    <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                      {location.description}
                    </p>
                  )}
                  
                  <div className="space-y-2 text-sm">
                    {location.address && (
                      <div className="flex items-center text-gray-600">
                        <Home className="w-4 h-4 text-gray-400 ml-2" />
                        <span className="truncate">{location.address}</span>
                      </div>
                    )}
                    
                    {(location.area_name || location.region_name) && (
                      <div className="flex items-center text-gray-600">
                        <Globe className="w-4 h-4 text-gray-400 ml-2" />
                        {location.area_name || location.region_name}
                      </div>
                    )}
                    
                    {location.latitude && location.longitude && (
                      <div className="flex items-center text-gray-600">
                        <Navigation className="w-4 h-4 text-gray-400 ml-2" />
                        {location.latitude.toFixed(4)}, {location.longitude.toFixed(4)}
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Card Footer */}
                <div className="px-6 py-3 border-t border-gray-100 bg-gray-50 rounded-b-lg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/locations/${location.id}`);
                        }}
                        className="text-green-600 hover:text-green-700 transition-colors"
                        title="צפה במיקום"
                      >
                        <Eye className="w-5 h-5" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/locations/${location.id}/edit`);
                        }}
                        className="text-gray-600 hover:text-gray-700 transition-colors"
                        title="ערוך מיקום"
                      >
                        <Edit className="w-5 h-5" />
                      </button>
                      {location.latitude && location.longitude && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            window.open(`https://maps.google.com/?q=${location.latitude},${location.longitude}`, '_blank');
                          }}
                          className="text-blue-600 hover:text-blue-700 transition-colors"
                          title="פתח במפות"
                        >
                          <Target className="w-5 h-5" />
                        </button>
                      )}
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-green-600 transition-colors" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-gray-200">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">מיקום</th>
                  <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">כתובת</th>
                  <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">אזור</th>
                  <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">סטטוס</th>
                  <th className="text-center px-6 py-3 text-xs font-medium text-gray-500 uppercase">פעולות</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {locations.map((location) => (
                  <tr 
                    key={location.id} 
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/locations/${location.id}`)}
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-green-100 rounded-lg">
                          <MapPin className="w-4 h-4 text-green-600" />
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">{location.name}</div>
                          <div className="text-sm text-gray-500">#{location.code}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {location.address || '-'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {location.area_name || location.region_name || '-'}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        location.is_active !== false
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {location.is_active !== false ? 'פעיל' : 'לא פעיל'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/locations/${location.id}`);
                          }}
                          className="text-green-600 hover:text-green-700 transition-colors"
                        >
                          <Eye className="w-5 h-5" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/locations/${location.id}/edit`);
                          }}
                          className="text-gray-600 hover:text-gray-700 transition-colors"
                        >
                          <Edit className="w-5 h-5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Summary */}
        {locations.length > 0 && (
          <div className="mt-8 bg-white rounded-lg border border-gray-200 p-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="text-center">
                <p className="text-2xl font-bold text-gray-900">{locations.length}</p>
                <p className="text-sm text-gray-600 mt-1">סה"כ מיקומים</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">
                  {locations.filter(l => l.is_active !== false).length}
                </p>
                <p className="text-sm text-gray-600 mt-1">מיקומים פעילים</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">
                  {locations.filter(l => l.latitude && l.longitude).length}
                </p>
                <p className="text-sm text-gray-600 mt-1">עם קואורדינטות</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-orange-600">
                  {locations.filter(l => l.address).length}
                </p>
                <p className="text-sm text-gray-600 mt-1">עם כתובת</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LocationsClean;
