"""
Forest Polygon Service - שירות פוליגוני יער (נקי, ללא מידע KKL)
"""

import json
from typing import Optional, Dict, Any, List
from sqlalchemy import text
from sqlalchemy.orm import Session


class ForestPolygonService:
    """Service for managing clean forest polygons (geometry only)"""
    
    @staticmethod
    def get_project_forest_map(db: Session, project_id: int) -> Dict[str, Any]:
        """
        Get forest map data for a project
        Returns project location point and forest polygon (if linked)
        """
        
        # Get project with location and forest polygon
        query = text("""
            SELECT 
                p.id,
                p.code,
                p.name,
                p.forest_polygon_id,
                ST_X(p.location_geom) as longitude,
                ST_Y(p.location_geom) as latitude,
                CASE 
                    WHEN p.forest_polygon_id IS NOT NULL 
                    THEN ST_AsGeoJSON(fp.geom)
                    ELSE NULL 
                END as forest_geojson,
                CASE 
                    WHEN p.forest_polygon_id IS NOT NULL 
                    THEN ST_AsGeoJSON(ST_SimplifyPreserveTopology(fp.geom, 0.0002))
                    ELSE NULL 
                END as forest_geojson_simple
            FROM projects p
            LEFT JOIN forest_polygons fp ON p.forest_polygon_id = fp.id
            WHERE p.id = :project_id
        """)
        
        result = db.execute(query, {"project_id": project_id}).fetchone()
        
        if not result:
            return {
                "project": {"id": project_id, "error": "Project not found"},
                "project_point": None,
                "forest_polygon": None
            }
        
        # Build project point
        project_point = None
        if result.latitude is not None and result.longitude is not None:
            project_point = {
                "lat": float(result.latitude),
                "lng": float(result.longitude)
            }
        
        # Build forest polygon
        forest_polygon = None
        if result.forest_geojson:
            forest_polygon = {
                "id": result.forest_polygon_id,
                "geojson_full": json.loads(result.forest_geojson),
                "geojson_simple": json.loads(result.forest_geojson_simple) if result.forest_geojson_simple else None
            }
        
        return {
            "project": {
                "id": result.id,
                "code": result.code,
                "name": result.name
            },
            "project_point": project_point,
            "forest_polygon": forest_polygon
        }
    
    @staticmethod
    def import_geojson(db: Session, geojson_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Import GeoJSON features into forest_polygons table
        Accepts FeatureCollection or single Feature/Geometry
        Returns count of imported polygons
        Uses geom_hash to prevent duplicates
        """
        imported_count = 0
        skipped_duplicates = 0
        errors = []
        
        # Handle different GeoJSON structures
        features = []
        
        if geojson_data.get("type") == "FeatureCollection":
            features = geojson_data.get("features", [])
        elif geojson_data.get("type") == "Feature":
            features = [geojson_data]
        elif geojson_data.get("type") in ["Polygon", "MultiPolygon"]:
            # Direct geometry
            features = [{"type": "Feature", "geometry": geojson_data}]
        else:
            return {"success": False, "error": "Invalid GeoJSON format", "imported": 0}
        
        for i, feature in enumerate(features):
            try:
                geometry = feature.get("geometry", feature)
                geom_type = geometry.get("type")
                
                # Skip non-polygon geometries
                if geom_type not in ["Polygon", "MultiPolygon"]:
                    errors.append(f"Feature {i}: Skipped - type is {geom_type}")
                    continue
                
                # Convert Polygon to MultiPolygon for consistency
                if geom_type == "Polygon":
                    geometry = {
                        "type": "MultiPolygon",
                        "coordinates": [geometry["coordinates"]]
                    }
                
                geojson_str = json.dumps(geometry)
                
                # Insert with hash to prevent duplicates
                insert_query = text("""
                    WITH new_geom AS (
                        SELECT 
                            ST_SetSRID(ST_GeomFromGeoJSON(:geojson), 4326) as geom,
                            md5(ST_AsEWKB(ST_Multi(ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(:geojson), 4326))))) as hash
                    )
                    INSERT INTO forest_polygons (geom, geom_hash)
                    SELECT geom, hash FROM new_geom
                    ON CONFLICT (geom_hash) DO NOTHING
                    RETURNING id
                """)
                
                result = db.execute(insert_query, {"geojson": geojson_str}).fetchone()
                if result:
                    imported_count += 1
                else:
                    skipped_duplicates += 1
                
            except Exception as e:
                errors.append(f"Feature {i}: {str(e)}")
        
        db.commit()
        
        return {
            "success": True,
            "imported": imported_count,
            "skipped_duplicates": skipped_duplicates,
            "errors": errors if errors else None
        }
    
    @staticmethod
    def get_all_polygons(db: Session, simplified: bool = True) -> List[Dict[str, Any]]:
        """Get all forest polygons as GeoJSON features"""
        
        if simplified:
            query = text("""
                SELECT 
                    id,
                    ST_AsGeoJSON(ST_SimplifyPreserveTopology(geom, 0.001)) as geojson,
                    created_at
                FROM forest_polygons
                ORDER BY id
            """)
        else:
            query = text("""
                SELECT 
                    id,
                    ST_AsGeoJSON(geom) as geojson,
                    created_at
                FROM forest_polygons
                ORDER BY id
            """)
        
        results = db.execute(query).fetchall()
        
        return [
            {
                "id": r.id,
                "geometry": json.loads(r.geojson),
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in results
        ]
    
    @staticmethod
    def get_polygons_by_bbox(
        db: Session, 
        min_lng: float, 
        min_lat: float, 
        max_lng: float, 
        max_lat: float,
        limit: int = 50,
        simplified: bool = True
    ) -> List[Dict[str, Any]]:
        """Get forest polygons within a bounding box (for map viewport)"""
        
        simplify = "ST_SimplifyPreserveTopology(geom, 0.0005)" if simplified else "geom"
        
        query = text(f"""
            SELECT 
                id,
                ST_AsGeoJSON({simplify}) as geojson,
                ST_Area(geom::geography)/1000000 as area_km2
            FROM forest_polygons
            WHERE geom && ST_MakeEnvelope(:min_lng, :min_lat, :max_lng, :max_lat, 4326)
            ORDER BY ST_Area(geom) DESC
            LIMIT :limit
        """)
        
        results = db.execute(query, {
            "min_lng": min_lng,
            "min_lat": min_lat,
            "max_lng": max_lng,
            "max_lat": max_lat,
            "limit": limit
        }).fetchall()
        
        return [
            {
                "id": r.id,
                "geometry": json.loads(r.geojson),
                "area_km2": round(r.area_km2, 2) if r.area_km2 else None
            }
            for r in results
        ]
    
    @staticmethod
    def link_project_to_polygon(db: Session, project_id: int, polygon_id: int) -> bool:
        """Link a project to a forest polygon"""
        
        query = text("""
            UPDATE projects 
            SET forest_polygon_id = :polygon_id
            WHERE id = :project_id
            RETURNING id
        """)
        
        result = db.execute(query, {
            "project_id": project_id,
            "polygon_id": polygon_id
        }).fetchone()
        
        db.commit()
        return result is not None
    
    @staticmethod
    def find_polygon_containing_point(db: Session, lat: float, lng: float) -> Optional[int]:
        """Find forest polygon that contains a given point"""
        
        query = text("""
            SELECT id 
            FROM forest_polygons
            WHERE ST_Contains(geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326))
            LIMIT 1
        """)
        
        result = db.execute(query, {"lat": lat, "lng": lng}).fetchone()
        return result.id if result else None


# Singleton
forest_polygon_service = ForestPolygonService()
