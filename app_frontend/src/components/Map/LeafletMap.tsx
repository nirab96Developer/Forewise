
// src/components/Map/LeafletMap.tsx
import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

export interface MapPoint {
  id: number;
  name: string;
  code?: string;
  lat: number;
  lng: number;
  color?: string;
  onClick?: () => void;
  popupContent?: string;
}

export interface MapPolygon {
  id: number;
  name: string;
  geometry: any;
  fillColor?: string;
  strokeColor?: string;
  fillOpacity?: number;
  strokeWeight?: number;
  onClick?: () => void;
}

export interface LeafletMapProps {
  height?: string;
  center?: [number, number];
  zoom?: number;
  points?: MapPoint[];
  polygons?: MapPolygon[];
  maskPolygon?: MapPolygon;
  fitBounds?: boolean;
  className?: string;
  mapType?: 'street' | 'satellite' | 'topo';
}

const OWM_KEY = import.meta.env.VITE_OPENWEATHER_API_KEY || '';

const BASE_TILES = {
  street:    { url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',   label: '🗺️ רגיל'   },
  satellite: { url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', label: '🛰️ לוויין' },
  hybrid:    { url: 'https://mt{s}.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', label: '🏙️ היברידי' },
  topo:      { url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',      label: '🏔️ טופו'   },
};

type BaseType   = keyof typeof BASE_TILES;
type WeatherKey = 'none' | 'clouds' | 'precipitation' | 'wind' | 'temp';

const WEATHER_LAYERS: Record<WeatherKey, { label: string; emoji: string; url: string }> = {
  none:          { label: 'כבוי',      emoji: '—',  url: '' },
  clouds:        { label: 'עננים',     emoji: '☁️', url: `https://tile.openweathermap.org/map/clouds_new/{z}/{x}/{y}.png?appid=${OWM_KEY}` },
  precipitation: { label: 'גשם',       emoji: '🌧️', url: `https://tile.openweathermap.org/map/precipitation_new/{z}/{x}/{y}.png?appid=${OWM_KEY}` },
  wind:          { label: 'רוח',       emoji: '💨', url: `https://tile.openweathermap.org/map/wind_new/{z}/{x}/{y}.png?appid=${OWM_KEY}` },
  temp:          { label: 'טמפרטורה', emoji: '🌡️', url: `https://tile.openweathermap.org/map/temp_new/{z}/{x}/{y}.png?appid=${OWM_KEY}` },
};

function geomToLatLngs(geometry: any): L.LatLngTuple[][] {
  if (!geometry?.coordinates) return [];
  const result: L.LatLngTuple[][] = [];
  if (geometry.type === 'Polygon') {
    result.push(geometry.coordinates[0].map((c: number[]) => [c[1], c[0]] as L.LatLngTuple));
  } else if (geometry.type === 'MultiPolygon') {
    geometry.coordinates.forEach((poly: number[][][]) => {
      result.push(poly[0].map((c: number[]) => [c[1], c[0]] as L.LatLngTuple));
    });
  }
  return result;
}

const LeafletMap: React.FC<LeafletMapProps> = ({
  height = '400px',
  center = [31.5, 35.0],
  zoom = 8,
  points = [],
  polygons = [],
  maskPolygon,
  fitBounds = true,
  className = '',
  mapType = 'street',
}) => {
  const containerRef   = useRef<HTMLDivElement>(null);
  const mapRef         = useRef<L.Map | null>(null);
  const tileRef        = useRef<L.TileLayer | null>(null);
  const weatherRef     = useRef<L.TileLayer | null>(null);
  const layerGroupRef  = useRef<L.LayerGroup | null>(null);
  const hasFittedRef   = useRef(false);

  const [activeBase,    setActiveBase]    = useState<BaseType>(mapType === 'satellite' ? 'satellite' : mapType === 'topo' ? 'topo' : 'street');
  const [activeWeather, setActiveWeather] = useState<WeatherKey>('none');
  const [showWeather,   setShowWeather]   = useState(false);

  // Create map once
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const ISRAEL_BOUNDS = L.latLngBounds(L.latLng(29.0, 33.8), L.latLng(33.8, 36.4));

    const map = L.map(containerRef.current, {
      center: center as L.LatLngExpression,
      zoom,
      zoomControl: true,
      attributionControl: false,
      maxBounds: ISRAEL_BOUNDS,
      maxBoundsViscosity: 1.0,
      minZoom: 7,
      bounceAtZoomLimits: false,
      worldCopyJump: false,
      tap: false,
    } as L.MapOptions & { tap: boolean });

    const subdomains = activeBase === 'hybrid' ? ['0', '1', '2', '3'] : ['a', 'b', 'c'];
    const tile = L.tileLayer(BASE_TILES[activeBase].url, { maxZoom: 20, subdomains });
    tile.addTo(map);
    tileRef.current = tile;

    map.on('drag', () => map.panInsideBounds(ISRAEL_BOUNDS, { animate: false }));

    const layerGroup = L.layerGroup().addTo(map);
    layerGroupRef.current = layerGroup;
    mapRef.current = map;

    setTimeout(() => map.invalidateSize(), 100);
    setTimeout(() => map.invalidateSize(), 500);

    return () => {
      map.remove();
      mapRef.current = null;
      tileRef.current = null;
      weatherRef.current = null;
      layerGroupRef.current = null;
    };
  }, []);

  // Switch base tile layer
  useEffect(() => {
    if (!mapRef.current || !tileRef.current) return;
    const subdomains = activeBase === 'hybrid' ? ['0', '1', '2', '3'] : ['a', 'b', 'c'];
    tileRef.current.setUrl(BASE_TILES[activeBase].url);
    (tileRef.current as any).options.subdomains = subdomains;
    tileRef.current.redraw();
  }, [activeBase]);

  // Switch weather overlay
  useEffect(() => {
    if (!mapRef.current) return;
    if (weatherRef.current) {
      mapRef.current.removeLayer(weatherRef.current);
      weatherRef.current = null;
    }
    if (activeWeather !== 'none' && WEATHER_LAYERS[activeWeather].url) {
      const wLayer = L.tileLayer(WEATHER_LAYERS[activeWeather].url, { opacity: 0.6, maxZoom: 20 });
      wLayer.addTo(mapRef.current);
      weatherRef.current = wLayer;
    }
  }, [activeWeather]);

  const prevMaskRef = useRef(maskPolygon);

  // Render points, polygons, mask
  useEffect(() => {
    if (!mapRef.current || !layerGroupRef.current) return;
    if (maskPolygon !== prevMaskRef.current) {
      hasFittedRef.current = false;
      prevMaskRef.current = maskPolygon;
    }
    const map = mapRef.current;
    const group = layerGroupRef.current;
    group.clearLayers();
    const allBounds = L.latLngBounds([]);

    if (maskPolygon?.geometry) {
      const worldOuter: L.LatLngTuple[] = [[-85, -180], [-85, 180], [85, 180], [85, -180]];
      const holes = geomToLatLngs(maskPolygon.geometry);
      holes.forEach(hole => {
        L.polygon([worldOuter, hole] as any, { fillColor: '#f0fdf4', fillOpacity: 0.7, stroke: false, interactive: false }).addTo(group);
        L.polyline(hole, { color: '#047857', weight: 3, opacity: 1, dashArray: '8, 4' }).addTo(group);
        hole.forEach(p => allBounds.extend(p));
      });
    }

    polygons.forEach(poly => {
      if (!poly.geometry) return;
      const paths = geomToLatLngs(poly.geometry);
      paths.forEach(path => {
        const lp = L.polygon(path, {
          fillColor: poly.fillColor || '#10b981',
          fillOpacity: poly.fillOpacity ?? 0.15,
          color: poly.strokeColor || '#059669',
          weight: poly.strokeWeight ?? 2,
          opacity: 0.8,
        }).addTo(group);
        lp.bindTooltip(poly.name, { permanent: false, direction: 'center' });
        if (poly.onClick) lp.on('click', poly.onClick);
        path.forEach(p => allBounds.extend(p));
      });
    });

    points.forEach(point => {
      if (!point.lat || !point.lng) return;
      const color = point.color || '#16a34a';
      const icon = L.divIcon({
        className: '',
        html: `<div style="width:16px;height:16px;border-radius:50%;background:${color};border:3px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,0.4)"></div>`,
        iconSize: [16, 16], iconAnchor: [8, 8],
      });
      const marker = L.marker([point.lat, point.lng], { icon }).addTo(group);
      const popup = point.popupContent ||
        `<div style="direction:rtl;padding:4px;min-width:100px"><b>${point.name}</b>${point.code ? `<br><span style="color:#6b7280;font-size:11px">${point.code}</span>` : ''}</div>`;
      marker.bindPopup(popup);
      if (point.onClick) marker.on('click', point.onClick);
      if (polygons.length === 0 && !maskPolygon) allBounds.extend([point.lat, point.lng]);
    });

    if (!allBounds.isValid() && points.length > 0) {
      points.forEach(p => { if (p.lat && p.lng) allBounds.extend([p.lat, p.lng]); });
    }

    const shouldFit = !hasFittedRef.current || maskPolygon;
    if (fitBounds && allBounds.isValid() && shouldFit) {
      setTimeout(() => { map.fitBounds(allBounds, { padding: [40, 40], maxZoom: 15 }); map.invalidateSize(); }, 200);
      hasFittedRef.current = true;
    }
  }, [points, polygons, maskPolygon]);

  useEffect(() => {
    const observer = new ResizeObserver(() => mapRef.current?.invalidateSize());
    if (containerRef.current) observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  const pixelHeight = height === '100%' ? 'calc(100vh - 250px)' : height;
  const btnBase = (active: boolean) => ({
    padding: '5px 10px', fontSize: 12, fontWeight: 600, borderRadius: 6,
    border: 'none', cursor: 'pointer' as const,
    background: active ? '#16a34a' : 'transparent',
    color: active ? '#fff' : '#374151',
    whiteSpace: 'nowrap' as const,
  });

  return (
    <div className={className} style={{ position: 'relative', minHeight: '300px', overflow: 'hidden', isolation: 'isolate' }}>

      {/* Base layer selector */}
      <div style={{
        position: 'absolute', top: 10, left: 10, zIndex: 1000,
        display: 'flex', gap: 2, background: 'rgba(255,255,255,0.96)',
        borderRadius: 8, padding: 3,
        boxShadow: '0 2px 12px rgba(0,0,0,0.18)', border: '1px solid #e5e7eb',
      }}>
        {(Object.keys(BASE_TILES) as BaseType[]).map(type => (
          <button key={type} onClick={() => setActiveBase(type)} style={btnBase(activeBase === type)}>
            {BASE_TILES[type].label}
          </button>
        ))}
      </div>

      {/* Weather toggle button */}
      <div style={{ position: 'absolute', top: 50, left: 10, zIndex: 1000 }}>
        <button
          onClick={() => setShowWeather(v => !v)}
          style={{
            padding: '5px 12px', fontSize: 12, fontWeight: 600, borderRadius: 8,
            border: '1px solid #e5e7eb', cursor: 'pointer',
            background: showWeather ? '#0ea5e9' : 'rgba(255,255,255,0.96)',
            color: showWeather ? '#fff' : '#374151',
            boxShadow: '0 2px 12px rgba(0,0,0,0.18)',
          }}>
          🌤️ מזג אוויר {activeWeather !== 'none' ? `· ${WEATHER_LAYERS[activeWeather].emoji}` : ''}
        </button>

        {/* Weather layer options */}
        {showWeather && (
          <div style={{
            marginTop: 4, background: 'rgba(255,255,255,0.97)', borderRadius: 8,
            boxShadow: '0 4px 16px rgba(0,0,0,0.15)', border: '1px solid #e5e7eb',
            padding: 4, display: 'flex', flexDirection: 'column', gap: 2, minWidth: 140,
          }}>
            {(Object.keys(WEATHER_LAYERS) as WeatherKey[]).map(key => (
              <button key={key} onClick={() => { setActiveWeather(key); }}
                style={{
                  padding: '5px 10px', fontSize: 12, fontWeight: 600, borderRadius: 6,
                  border: 'none', cursor: 'pointer', textAlign: 'right',
                  background: activeWeather === key ? '#0ea5e9' : 'transparent',
                  color: activeWeather === key ? '#fff' : '#374151',
                }}>
                {WEATHER_LAYERS[key].emoji} {WEATHER_LAYERS[key].label}
              </button>
            ))}
          </div>
        )}
      </div>

      <div ref={containerRef} style={{
        width: '100%', height: pixelHeight, minHeight: '300px',
        borderRadius: 12, overflow: 'hidden', background: '#e5e7eb',
      }} />
    </div>
  );
};

export default LeafletMap;
