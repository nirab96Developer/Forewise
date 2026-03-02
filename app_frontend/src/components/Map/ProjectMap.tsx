
// src/components/Map/ProjectMap.tsx
// Project map using Leaflet - shows project point + forest polygon
import React from 'react';
import { MapPin, ExternalLink } from 'lucide-react';
import LeafletMap from './LeafletMap';

interface ProjectMapProps {
  projectCode: string;
  projectName: string;
  latitude?: number;
  longitude?: number;
  geoJson?: any;
}

const ProjectMap: React.FC<ProjectMapProps> = ({
  projectCode, projectName,
  latitude = 31.7683, longitude = 35.2137,
  geoJson
}) => {
  const points = [{
    id: 1, name: projectName, code: projectCode,
    lat: latitude, lng: longitude, color: '#16a34a',
  }];

  const polygons = [];
  const geometry = geoJson?.geometry || geoJson;
  if (geometry && (geometry.type === 'Polygon' || geometry.type === 'MultiPolygon')) {
    polygons.push({
      id: 1, name: projectName, geometry,
      fillColor: '#10b981', strokeColor: '#059669',
      fillOpacity: 0.20, strokeWeight: 3,
    });
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-xl p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-600 rounded-lg flex items-center justify-center shadow">
              <MapPin className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-gray-900">{projectName}</h3>
              <p className="text-sm text-gray-600">{"נ\"צ: " + latitude.toFixed(6) + ", " + longitude.toFixed(6)}</p>
            </div>
          </div>
          <a href={"https://www.google.com/maps?q=" + latitude + "," + longitude}
            target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800 p-2">
            <ExternalLink className="w-5 h-5" />
          </a>
        </div>
      </div>

      {/* Map */}
      <LeafletMap
        height="500px"
        center={[latitude, longitude]}
        zoom={14}
        points={points}
        polygons={polygons}
        mapType="satellite"
        className="rounded-xl overflow-hidden shadow-xl border-2 border-gray-200"
      />
    </div>
  );
};

export default ProjectMap;
