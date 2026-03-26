// src/components/map/PolygonDrawer.tsx
// Leaflet polygon drawing component for forest boundaries
import React, { useEffect, useRef, useState } from 'react';
import { MapPin, Save, X } from 'lucide-react';
import api from '../../services/api';
import { showToast } from '../common/Toast';

interface PolygonDrawerProps {
  projectId?: number;
  projectName?: string;
  existingGeoJSON?: any;
  onSave?: (polygonId: number, areaHectares: number) => void;
  onClose?: () => void;
}

const PolygonDrawer: React.FC<PolygonDrawerProps> = ({
  projectId, projectName, existingGeoJSON, onSave, onClose
}) => {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const drawnItemsRef = useRef<any>(null);
  const [area, setArea] = useState<{ hectares: number; dunam: number } | null>(null);
  const [saving, setSaving] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    const initMap = async () => {
      const L = (await import('leaflet')).default;
      await import('leaflet-draw');
      await import('leaflet/dist/leaflet.css');
      await import('leaflet-draw/dist/leaflet.draw.css');

      const map = L.map(mapRef.current!, {
        center: [31.5, 34.8],
        zoom: 8,
        zoomControl: true,
      });

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19,
      }).addTo(map);

      const drawnItems = new L.FeatureGroup();
      map.addLayer(drawnItems);
      drawnItemsRef.current = drawnItems;

      // Load existing polygon
      if (existingGeoJSON) {
        try {
          const layer = L.geoJSON(existingGeoJSON);
          layer.eachLayer((l: any) => drawnItems.addLayer(l));
          map.fitBounds(drawnItems.getBounds(), { padding: [50, 50] });
          updateArea(drawnItems);
        } catch {}
      }

      // Draw controls
      const drawControl = new (L.Control as any).Draw({
        position: 'topright',
        draw: {
          polygon: {
            allowIntersection: false,
            showArea: true,
            shapeOptions: { color: '#2d6a2d', weight: 3, fillOpacity: 0.15 },
          },
          polyline: false,
          rectangle: false,
          circle: false,
          marker: false,
          circlemarker: false,
        },
        edit: { featureGroup: drawnItems, remove: true },
      });
      map.addControl(drawControl);

      map.on('draw:created', (e: any) => {
        drawnItems.addLayer(e.layer);
        updateArea(drawnItems);
      });
      map.on('draw:edited', () => updateArea(drawnItems));
      map.on('draw:deleted', () => updateArea(drawnItems));

      mapInstanceRef.current = map;
      setReady(true);

      setTimeout(() => map.invalidateSize(), 200);
    };

    initMap();

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  const updateArea = (featureGroup: any) => {
    let totalArea = 0;
    featureGroup.eachLayer((layer: any) => {
      if (layer.getLatLngs) {
        const L = (window as any).L;
        if (L?.GeometryUtil?.geodesicArea) {
          totalArea += L.GeometryUtil.geodesicArea(layer.getLatLngs()[0]);
        }
      }
    });
    const hectares = Math.round(totalArea / 10000 * 100) / 100;
    setArea({ hectares, dunam: Math.round(hectares * 10 * 10) / 10 });
  };

  const handleSave = async () => {
    if (!drawnItemsRef.current) return;
    const layers: any[] = [];
    drawnItemsRef.current.eachLayer((l: any) => {
      if (l.toGeoJSON) layers.push(l.toGeoJSON());
    });
    if (layers.length === 0) {
      showToast('יש לצייר פוליגון לפני שמירה', 'error');
      return;
    }

    const geometry = layers.length === 1
      ? layers[0].geometry
      : { type: 'MultiPolygon', coordinates: layers.map(l => l.geometry.coordinates) };

    setSaving(true);
    try {
      const res = await api.post('/geo/forest-polygons', {
        project_id: projectId,
        name: projectName || '',
        geometry,
      });
      showToast(`פוליגון נשמר — ${res.data.area_hectares} הקטר (${res.data.area_dunam} דונם)`, 'success');
      onSave?.(res.data.id, res.data.area_hectares);
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'שגיאה בשמירת פוליגון', 'error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex flex-col h-full" dir="rtl">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-3 bg-white border-b">
        <div className="flex items-center gap-2">
          <MapPin className="w-5 h-5 text-green-600" />
          <h3 className="font-bold text-gray-900">סרטוט גבולות יער</h3>
          {projectName && <span className="text-sm text-gray-500">— {projectName}</span>}
        </div>
        <div className="flex items-center gap-2">
          {area && (
            <span className="text-sm bg-green-50 text-green-700 px-3 py-1 rounded-full font-medium">
              {area.hectares} הקטר | {area.dunam} דונם
            </span>
          )}
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-1.5 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium disabled:opacity-50"
          >
            {saving ? <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <Save className="w-4 h-4" />}
            שמור פוליגון
          </button>
          {onClose && (
            <button onClick={onClose} className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg">
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      {/* Instructions */}
      {ready && !area && (
        <div className="bg-blue-50 border-b border-blue-200 px-4 py-2 text-sm text-blue-700">
          לחץ על כפתור הפוליגון בפינה הימנית העליונה של המפה, ואז לחץ על המפה להוספת נקודות. לחץ פעמיים לסגירת הפוליגון.
        </div>
      )}

      {/* Map */}
      <div ref={mapRef} className="flex-1 min-h-[400px]" style={{ direction: 'ltr' }} />
    </div>
  );
};

export default PolygonDrawer;
