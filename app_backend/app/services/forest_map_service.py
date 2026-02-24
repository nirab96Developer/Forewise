"""
Forest Map Service - שירות מפת יער
מחזיר מידע גיאוגרפי על פרויקטים ויערות
"""

import json
from typing import Optional, Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.forest_map import ForestMapResponse, ForestInfo


class ForestMapService:
    """Service for retrieving forest and project map data"""
    
    @staticmethod
    def get_project_forest_map(db: Session, project_id: int) -> ForestMapResponse:
        """
        Get forest map data for a project
        Returns the project location point and forest polygon (if available)
        """
        
        # Get project info with location
        project_query = text("""
            SELECT 
                p.id,
                p.code,
                p.name,
                p.forest_id,
                ST_X(p.location_geom) as longitude,
                ST_Y(p.location_geom) as latitude
            FROM projects p
            WHERE p.id = :project_id
        """)
        
        result = db.execute(project_query, {"project_id": project_id}).fetchone()
        
        if not result:
            return ForestMapResponse(
                project={"id": project_id, "error": "Project not found"},
                has_forest=False,
                has_location=False
            )
        
        project_data = {
            "id": result.id,
            "code": result.code,
            "name": result.name,
        }
        
        has_location = result.latitude is not None and result.longitude is not None
        
        if has_location:
            project_data["point"] = {
                "lat": float(result.latitude),
                "lng": float(result.longitude)
            }
        
        # Priority: 1) forest_polygon_id (clean, accurate) 2) forest_id (with names) 3) spatial search
        forest_info = None
        
        # First check forest_polygon_id (clean polygon table - most accurate)
        polygon_info = ForestMapService._get_polygon_for_project(db, project_id)
        if polygon_info:
            forest_info = polygon_info
        
        # If no clean polygon, try forest_id (old table with names)
        if not forest_info and result.forest_id:
            forest_info = ForestMapService._get_forest_by_id(db, result.forest_id)
        
        # If still no forest and has location, try to find polygon containing this point
        if not forest_info and has_location:
            # First try clean polygons
            forest_info = ForestMapService._find_polygon_for_point(
                db, result.longitude, result.latitude
            )
            # Then try old forests table
            if not forest_info:
                forest_info = ForestMapService._find_forest_for_point(
                    db, result.longitude, result.latitude
                )
        
        return ForestMapResponse(
            project=project_data,
            forest=forest_info,
            has_forest=forest_info is not None,
            has_location=has_location
        )
    
    @staticmethod
    def _get_forest_by_id(db: Session, forest_id: int) -> Optional[ForestInfo]:
        """Get forest info by ID with full and preview GeoJSON"""
        
        query = text("""
            SELECT 
                id,
                name,
                code,
                area_km2,
                ST_AsGeoJSON(geom) as geojson_full,
                ST_AsGeoJSON(ST_SimplifyPreserveTopology(geom, 0.0002)) as geojson_preview
            FROM forests
            WHERE id = :forest_id
        """)
        
        result = db.execute(query, {"forest_id": forest_id}).fetchone()
        
        if not result:
            return None
        
        return ForestInfo(
            id=result.id,
            name=result.name,
            code=result.code,
            area_km2=float(result.area_km2) if result.area_km2 else None,
            geojson_full=json.loads(result.geojson_full),
            geojson_preview=json.loads(result.geojson_preview)
        )
    
    @staticmethod
    def _get_polygon_for_project(db: Session, project_id: int) -> Optional[ForestInfo]:
        """Get forest polygon linked to project via forest_polygon_id"""
        
        query = text("""
            SELECT 
                fp.id,
                fp.geom,
                ST_Area(fp.geom::geography)/1000000 as area_km2,
                ST_AsGeoJSON(fp.geom) as geojson_full,
                ST_AsGeoJSON(ST_SimplifyPreserveTopology(fp.geom, 0.0002)) as geojson_preview
            FROM projects p
            JOIN forest_polygons fp ON p.forest_polygon_id = fp.id
            WHERE p.id = :project_id
        """)
        
        result = db.execute(query, {"project_id": project_id}).fetchone()
        
        if not result:
            return None
        
        return ForestInfo(
            id=result.id,
            name=f"יער #{result.id}",  # Clean polygon has no name
            code=None,
            area_km2=float(result.area_km2) if result.area_km2 else None,
            geojson_full=json.loads(result.geojson_full),
            geojson_preview=json.loads(result.geojson_preview)
        )
    
    @staticmethod
    def _find_polygon_for_point(db: Session, lng: float, lat: float) -> Optional[ForestInfo]:
        """Find clean polygon that contains the given point"""
        
        query = text("""
            SELECT 
                id,
                ST_Area(geom::geography)/1000000 as area_km2,
                ST_AsGeoJSON(geom) as geojson_full,
                ST_AsGeoJSON(ST_SimplifyPreserveTopology(geom, 0.0002)) as geojson_preview
            FROM forest_polygons
            WHERE ST_Contains(geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326))
            LIMIT 1
        """)
        
        result = db.execute(query, {"lng": lng, "lat": lat}).fetchone()
        
        if not result:
            return None
        
        return ForestInfo(
            id=result.id,
            name=f"יער #{result.id}",  # Clean polygon has no name
            code=None,
            area_km2=float(result.area_km2) if result.area_km2 else None,
            geojson_full=json.loads(result.geojson_full),
            geojson_preview=json.loads(result.geojson_preview)
        )
    
    @staticmethod
    def _find_forest_for_point(db: Session, lng: float, lat: float) -> Optional[ForestInfo]:
        """Find forest that contains the given point"""
        
        query = text("""
            SELECT 
                id,
                name,
                code,
                area_km2,
                ST_AsGeoJSON(geom) as geojson_full,
                ST_AsGeoJSON(ST_SimplifyPreserveTopology(geom, 0.0002)) as geojson_preview
            FROM forests
            WHERE ST_Contains(geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326))
            LIMIT 1
        """)
        
        result = db.execute(query, {"lng": lng, "lat": lat}).fetchone()
        
        if not result:
            return None
        
        return ForestInfo(
            id=result.id,
            name=result.name,
            code=result.code,
            area_km2=float(result.area_km2) if result.area_km2 else None,
            geojson_full=json.loads(result.geojson_full),
            geojson_preview=json.loads(result.geojson_preview)
        )
    
    @staticmethod
    def get_all_forests(db: Session) -> list:
        """Get list of all forests (for dropdown/selection)"""
        
        query = text("""
            SELECT id, name, code, area_km2
            FROM forests
            ORDER BY name
        """)
        
        results = db.execute(query).fetchall()
        
        return [
            {
                "id": r.id,
                "name": r.name,
                "code": r.code,
                "area_km2": float(r.area_km2) if r.area_km2 else None
            }
            for r in results
        ]
    
    @staticmethod
    def get_forest_geojson(db: Session, forest_id: int, simplified: bool = False) -> Optional[Dict[str, Any]]:
        """Get forest GeoJSON (full or simplified)"""
        
        if simplified:
            query = text("""
                SELECT ST_AsGeoJSON(ST_SimplifyPreserveTopology(geom, 0.0002)) as geojson
                FROM forests WHERE id = :forest_id
            """)
        else:
            query = text("""
                SELECT ST_AsGeoJSON(geom) as geojson
                FROM forests WHERE id = :forest_id
            """)
        
        result = db.execute(query, {"forest_id": forest_id}).fetchone()
        
        if not result:
            return None
        
        return json.loads(result.geojson)


# Singleton instance
forest_map_service = ForestMapService()


