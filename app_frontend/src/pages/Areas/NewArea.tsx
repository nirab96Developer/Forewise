
// src/pages/Areas/NewArea.tsx
// יצירת אזור חדש עם זיהוי מיקום אוטומטי
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowRight, MapPin, Save, Loader2, Building2, 
  Users, Map, Search, X
} from 'lucide-react';
import api from '../../services/api';
import LeafletMap from '../../components/Map/LeafletMap';

interface Region {
  id: number;
  name: string;
}

interface Manager {
  id: number;
  full_name: string;
}

interface LocationResult {
  name: string;
  geometry: {
    location: { lat: number; lng: number };
    bounds?: { 
      northeast: { lat: number; lng: number }; 
      southwest: { lat: number; lng: number };
    };
  };
  formatted_address: string;
}

const NewArea: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Form data
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [regionId, setRegionId] = useState<number | null>(null);
  const [managerId, setManagerId] = useState<number | null>(null);
  const [description, setDescription] = useState('');
  const [totalAreaHectares, setTotalAreaHectares] = useState<number | null>(null);
  
  // Options data
  const [regions, setRegions] = useState<Region[]>([]);
  const [managers, setManagers] = useState<Manager[]>([]);
  
  // Location data
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<LocationResult[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const isLoaded = true; // Leaflet always loaded

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [regionsRes, usersRes] = await Promise.all([
        api.get('/regions'),
        api.get('/users')
      ]);
      
      const regionsData = regionsRes.data;
      setRegions(Array.isArray(regionsData) ? regionsData : (regionsData.items || []));
      
      const usersData = usersRes.data;
      const usersList = Array.isArray(usersData) ? usersData : (usersData.items || []);
      // Filter for managers (users who can manage areas)
      setManagers(usersList.filter((u: any) => u.is_active !== false));
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('שגיאה בטעינת נתונים');
    } finally {
      setLoading(false);
    }
  };

  // Search for location using Nominatim (OpenStreetMap) API
  const searchLocation = async () => {
    if (!searchQuery.trim() || !isLoaded) return;

    setIsSearching(true);
    setSearchResults([]);

    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(searchQuery + ' Israel')}&format=json&limit=5&addressdetails=1`
      );
      const data = await response.json();
      const locationResults: LocationResult[] = (data || []).map((place: any) => ({
        name: place.display_name?.split(',')[0] || '',
        geometry: {
          location: {
            lat: parseFloat(place.lat),
            lng: parseFloat(place.lon)
          },
          bounds: place.boundingbox ? {
            northeast: { lat: parseFloat(place.boundingbox[1]), lng: parseFloat(place.boundingbox[3]) },
            southwest: { lat: parseFloat(place.boundingbox[0]), lng: parseFloat(place.boundingbox[2]) }
          } : undefined
        },
        formatted_address: place.display_name || ''
      }));
      setSearchResults(locationResults);
    } catch (err) {
      console.error('Search error:', err);
    }
    setIsSearching(false);
  };

  // Select a location from search results
  const selectLocation = (result: LocationResult) => {
    const location = result.geometry.location;
    setSelectedLocation(location);
    setSearchResults([]);

    // Set the name if empty
    if (!name) {
      setName(result.name);
    }

    // Calculate approximate area in hectares
    if (result.geometry.bounds) {
      const { northeast, southwest } = result.geometry.bounds;
      // Approximate area using lat/lng deltas
      const latDiff = Math.abs(northeast.lat - southwest.lat);
      const lngDiff = Math.abs(northeast.lng - southwest.lng);
      const avgLat = (northeast.lat + southwest.lat) / 2;
      const latKm = latDiff * 111.32;
      const lngKm = lngDiff * 111.32 * Math.cos(avgLat * Math.PI / 180);
      const areaKm2 = latKm * lngKm;
      setTotalAreaHectares(Math.round(areaKm2 * 100)); // km² to hectares
    } else {
      // Default 5km radius
      const radiusKm = 5;
      setTotalAreaHectares(Math.round(Math.PI * radiusKm * radiusKm * 100));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!name.trim()) {
      setError('נא להזין שם אזור');
      return;
    }
    
    if (!regionId) {
      setError('נא לבחור מרחב');
      return;
    }
    
    setSaving(true);
    setError(null);
    
    try {
      const areaData = {
        name: name.trim(),
        code: code.trim() || null,
        region_id: regionId,
        manager_id: managerId || null,
        description: description.trim() || null,
        total_area_hectares: totalAreaHectares || null,
      };
      
      await api.post('/areas', areaData);
      navigate('/areas');
    } catch (err: any) {
      console.error('Error creating area:', err);
      setError(err.response?.data?.detail || 'שגיאה ביצירת אזור');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-green-600 animate-spin mx-auto mb-3" />
          <p className="text-gray-600">טוען...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50" dir="rtl">
      {/* Header */}
      <div className="sticky top-0 z-20 bg-white shadow-sm">
        <div className="px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/areas')}
              className="text-green-600 hover:text-green-800"
            >
              <ArrowRight className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center text-white">
                <Building2 className="w-5 h-5" />
              </div>
              <h1 className="text-lg font-bold text-gray-900">אזור חדש</h1>
            </div>
          </div>
          <button
            onClick={handleSubmit}
            disabled={saving || !name || !regionId}
            className="bg-green-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 text-sm disabled:opacity-50"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            שמור
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mx-4 mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm flex items-center gap-2">
          <X className="w-4 h-4" />
          {error}
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="p-4 space-y-4">
        {/* Location Search */}
        <div className="bg-white rounded-xl shadow-sm border p-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <MapPin className="w-4 h-4 inline ml-1" />
            חיפוש מיקום (הקלד שם מקום וזה יזהה אוטומטית)
          </label>
          <div className="flex gap-2 mb-3">
            <div className="relative flex-1">
              <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), searchLocation())}
                placeholder="הקלד שם מקום, למשל: הר החרמון..."
                className="w-full pr-10 pl-4 py-2 border border-gray-200 rounded-lg text-sm"
              />
            </div>
            <button
              type="button"
              onClick={searchLocation}
              disabled={isSearching || !searchQuery.trim()}
              className="bg-blue-500 text-white px-4 py-2 rounded-lg flex items-center gap-1 text-sm disabled:opacity-50"
            >
              {isSearching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
              חפש
            </button>
          </div>
          
          {/* Search Results */}
          {searchResults.length > 0 && (
            <div className="mb-3 border rounded-lg divide-y bg-white shadow-lg max-h-48 overflow-y-auto">
              {searchResults.map((result, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => selectLocation(result)}
                  className="w-full text-right px-4 py-3 hover:bg-green-50 transition-colors"
                >
                  <p className="font-medium text-gray-900">{result.name}</p>
                  <p className="text-xs text-gray-500">{result.formatted_address}</p>
                </button>
              ))}
            </div>
          )}
          
          {/* Map */}
          <LeafletMap
            height="400px"
            center={selectedLocation ? [selectedLocation.lat, selectedLocation.lng] : [31.5, 35.0]}
            zoom={selectedLocation ? 12 : 8}
            points={selectedLocation ? [{ id: 1, name: 'מיקום נבחר', lat: selectedLocation.lat, lng: selectedLocation.lng, color: '#10B981' }] : []}
            mapType="street"
          />
          
          {selectedLocation && totalAreaHectares && (
            <p className="mt-2 text-sm text-gray-600 flex items-center gap-1">
              <Map className="w-4 h-4" />
              שטח משוער: <span className="font-medium">{totalAreaHectares.toLocaleString()}</span> הקטר
            </p>
          )}
        </div>

        {/* Basic Info */}
        <div className="bg-white rounded-xl shadow-sm border p-4 space-y-4">
          {/* Region - Required */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              <Map className="w-4 h-4 inline ml-1" />
              מרחב *
            </label>
            <select
              value={regionId || ''}
              onChange={(e) => setRegionId(e.target.value ? parseInt(e.target.value) : null)}
              className="w-full pr-4 pl-10 py-2 border border-gray-200 rounded-lg text-sm"
              required
            >
              <option value="">בחר מרחב...</option>
              {regions.map(region => (
                <option key={region.id} value={region.id}>{region.name}</option>
              ))}
            </select>
          </div>

          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              שם האזור *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="שם האזור"
              className="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm"
              required
            />
          </div>

          {/* Code */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              קוד אזור (אופציונלי)
            </label>
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="קוד ייחודי"
              className="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm"
            />
          </div>

          {/* Manager - Optional */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              <Users className="w-4 h-4 inline ml-1" />
              מנהל אזור (אופציונלי)
            </label>
            <select
              value={managerId || ''}
              onChange={(e) => setManagerId(e.target.value ? parseInt(e.target.value) : null)}
              className="w-full pr-4 pl-10 py-2 border border-gray-200 rounded-lg text-sm"
            >
              <option value="">ללא מנהל (יוקצה מאוחר יותר)</option>
              {managers.map(manager => (
                <option key={manager.id} value={manager.id}>{manager.full_name}</option>
              ))}
            </select>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              תיאור (אופציונלי)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="תיאור קצר של האזור..."
              rows={3}
              className="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm resize-none"
            />
          </div>

          {/* Total Area */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              שטח כולל (הקטר)
            </label>
            <input
              type="number"
              value={totalAreaHectares || ''}
              onChange={(e) => setTotalAreaHectares(e.target.value ? parseFloat(e.target.value) : null)}
              placeholder="יחושב אוטומטית מהמפה"
              className="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm"
            />
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={saving || !name || !regionId}
          className="w-full bg-green-600 text-white py-3 rounded-xl flex items-center justify-center gap-2 text-sm font-medium disabled:opacity-50"
        >
          {saving ? <Loader2 className="w-5 h-5 animate-spin" /> : <Save className="w-5 h-5" />}
          צור אזור חדש
        </button>
      </form>
    </div>
  );
};

export default NewArea;

