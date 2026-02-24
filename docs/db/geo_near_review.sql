-- Geo NEAR Review List (3km rule)
-- Returns projects whose point is outside their area's polygon,
-- but within 3,000 meters of that polygon (near-border cases).

SELECT
  p.id   AS project_id,
  p.name AS project_name,
  p.area_id,
  a.name AS area_name,
  a.region_id,
  ROUND(ST_Distance(p.location_geom::geography, a.geom::geography))::int AS distance_meters,
  ST_AsText(p.location_geom) AS project_point_wkt
FROM projects p
JOIN areas a ON a.id = p.area_id
WHERE p.location_geom IS NOT NULL
  AND a.geom IS NOT NULL
  AND NOT ST_Covers(a.geom, p.location_geom)
  AND ST_Distance(p.location_geom::geography, a.geom::geography) <= 3000
ORDER BY distance_meters DESC, p.id;

