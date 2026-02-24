-- Geo FAR Review List (3km rule)
-- Returns projects whose point is more than 3,000 meters
-- from their assigned area's polygon (true geo integrity issue)

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
  AND ST_Distance(p.location_geom::geography, a.geom::geography) > 3000
ORDER BY distance_meters DESC;

