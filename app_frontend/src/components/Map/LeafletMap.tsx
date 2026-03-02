
// src/components/Map/LeafletMap.tsx
// Universal Leaflet map - robust, mobile-friendly, no API key
import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix default marker icons
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

const TILES = {
  street: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  satellite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
  topo: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
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
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const tileRef = useRef<L.TileLayer | null>(null);
  const layerGroupRef = useRef<L.LayerGroup | null>(null);
  const [activeType, setActiveType] = useState(mapType);

  // Create map once
  useEffect(() => {
    if (!containerRef.current) return;
    if (mapRef.current) return;

    const map = L.map(containerRef.current, {
      center: center as L.LatLngExpression,
      zoom,
      zoomControl: true,
      attributionControl: false,
    });

    const tile = L.tileLayer(TILES[activeType], { maxZoom: 19 });
    tile.addTo(map);
    tileRef.current = tile;

    const layerGroup = L.layerGroup().addTo(map);
    layerGroupRef.current = layerGroup;

    mapRef.current = map;

    // Fix size after render
    setTimeout(() => { map.invalidateSize(); }, 100);
    setTimeout(() => { map.invalidateSize(); }, 500);

    return () => {
      map.remove();
      mapRef.current = null;
      tileRef.current = null;
      layerGroupRef.current = null;
    };
  }, []);

  // Switch tile layer
  useEffect(() => {
    if (!mapRef.current || !tileRef.current) return;
    tileRef.current.setUrl(TILES[activeType]);
  }, [activeType]);

  // Render content (points, polygons, mask)
  useEffect(() => {
    if (!mapRef.current || !layerGroupRef.current) return;
    const map = mapRef.current;
    const group = layerGroupRef.current;
    group.clearLayers();

    const allBounds = L.latLngBounds([]);

    // Mask - dim outside, highlight inside
    if (maskPolygon?.geometry) {
      const worldOuter: L.LatLngTuple[] = [[-85, -180], [-85, 180], [85, 180], [85, -180]];
      const holes = geomToLatLngs(maskPolygon.geometry);
      holes.forEach(hole => {
        L.polygon([worldOuter, hole] as any, {
          fillColor: '#f0fdf4', fillOpacity: 0.7, stroke: false, interactive: false,
        }).addTo(group);
        L.polyline(hole, {
          color: '#047857', weight: 3, opacity: 1, dashArray: '8, 4',
        }).addTo(group);
        hole.forEach(p => allBounds.extend(p));
      });
    }

    // Polygons
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

    // Points
    points.forEach(point => {
      if (!point.lat || !point.lng) return;
      const color = point.color || '#16a34a';
      const icon = L.divIcon({
        className: '',
        html: '<div style="width:16px;height:16px;border-radius:50%;background:' + color +
          ';border:3px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,0.4)"></div>',
        iconSize: [16, 16], iconAnchor: [8, 8],
      });
      const marker = L.marker([point.lat, point.lng], { icon }).addTo(group);
      const popup = point.popupContent ||
        '<div style="direction:rtl;padding:4px;min-width:100px"><b>' + point.name + '</b>' +
        (point.code ? '<br><span style="color:#6b7280;font-size:11px">' + point.code + '</span>' : '') + '</div>';
      marker.bindPopup(popup);
      if (point.onClick) marker.on('click', point.onClick);
      // Only include points in bounds if there are no polygons (otherwise zoom to polygons)
      if (polygons.length === 0 && !maskPolygon) {
        allBounds.extend([point.lat, point.lng]);
      }
    });

    // If no polygon bounds set, fallback to points
    if (!allBounds.isValid() && points.length > 0) {
      points.forEach(p => { if (p.lat && p.lng) allBounds.extend([p.lat, p.lng]); });
    }

    // Fit bounds
    if (fitBounds && allBounds.isValid()) {
      setTimeout(() => {
        map.fitBounds(allBounds, { padding: [40, 40], maxZoom: 15 });
        map.invalidateSize();
      }, 200);
    }
  }, [points, polygons, maskPolygon]);

  // Fix size when tab becomes visible
  useEffect(() => {
    const observer = new ResizeObserver(() => {
      mapRef.current?.invalidateSize();
    });
    if (containerRef.current) observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  const pixelHeight = height === '100%' ? 'calc(100vh - 250px)' : height;

  return (
    <div className={className} style={{ position: 'relative', minHeight: '300px', overflow: 'hidden', isolation: 'isolate' }}>
      {/* Map type buttons */}
      <div style={{
        position: 'absolute', top: 10, left: 10, zIndex: 1000,
        display: 'flex', gap: 2, background: '#fff', borderRadius: 8, padding: 3,
        boxShadow: '0 2px 8px rgba(0,0,0,0.2)', border: '1px solid #e5e7eb'
      }}>
        {(['street', 'satellite', 'topo'] as const).map(type => (
          <button key={type} onClick={() => setActiveType(type)}
            style={{
              padding: '5px 12px', fontSize: 12, fontWeight: 600, borderRadius: 6, border: 'none', cursor: 'pointer',
              background: activeType === type ? '#16a34a' : 'transparent',
              color: activeType === type ? '#fff' : '#374151',
            }}>
            {type === 'street' ? 'רגיל' : type === 'satellite' ? 'לוויין' : 'טופו'}
          </button>
        ))}
      </div>

      <div ref={containerRef} style={{
        width: '100%',
        height: pixelHeight,
        minHeight: '300px',
        borderRadius: 12,
        overflow: 'hidden',
        background: '#e5e7eb',
      }} />
    </div>
  );
};

export default LeafletMap;
