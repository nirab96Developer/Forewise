"""
Geo Router - API endpoints for forest polygons, region/area boundaries
"""

from typing import Annotated, Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
import json

from app.core.database import get_db
from app.models import User
from app.models.region import Region
from app.models.area import Area
from app.core.dependencies import get_current_active_user, require_permission
from app.services.forest_polygon_service import forest_polygon_service

router = APIRouter(prefix="/geo", tags=["Geo"])


# ===== Public Endpoints =====

@router.get("/forest-polygons", response_model=List[Dict[str, Any]])
def list_forest_polygons(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    simplified: bool = True
):
    """
    List all forest polygons
    - simplified: True = simplified geometry for faster loading
    """
    require_permission(current_user, "projects.read")
    return forest_polygon_service.get_all_polygons(db, simplified=simplified)


@router.get("/forest-polygons/bbox")
def get_forest_polygons_by_bbox(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    min_lng: float = 34.0,
    min_lat: float = 29.0,
    max_lng: float = 36.0,
    max_lat: float = 34.0,
    limit: int = 50,
    simplified: bool = True
):
    """
    Get forest polygons within a bounding box (for map viewport)
    Returns only polygons that intersect the given bbox
    """
    require_permission(current_user, "projects.read")
    return forest_polygon_service.get_polygons_by_bbox(
        db, min_lng, min_lat, max_lng, max_lat, limit, simplified
    )


@router.get("/forest-polygons/{polygon_id}")
def get_forest_polygon(
    polygon_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    simplified: bool = False
):
    """Get a single forest polygon by ID"""
    require_permission(current_user, "projects.read")
    
    polygons = forest_polygon_service.get_all_polygons(db, simplified=simplified)
    polygon = next((p for p in polygons if p["id"] == polygon_id), None)
    
    if not polygon:
        raise HTTPException(status_code=404, detail="Forest polygon not found")
    
    return polygon


@router.get("/projects/{project_id}/forest-polygon")
def get_project_forest_polygon(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Get forest polygon linked to a project
    Returns project location and polygon geometry (if linked)
    """
    require_permission(current_user, "projects.read")
    return forest_polygon_service.get_project_forest_map(db, project_id)


# ===== Admin Import Endpoints =====

@router.post("/forest-polygons/import")
async def import_forest_polygons_json(
    geojson: Dict[str, Any],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Import forest polygons from GeoJSON (JSON body)
    Admin only - requires settings.manage permission
    
    Accepts:
    - FeatureCollection
    - Single Feature
    - Direct Polygon/MultiPolygon geometry
    """
    require_permission(current_user, "settings.manage")
    
    result = forest_polygon_service.import_geojson(db, geojson)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Import failed"))
    
    return result


@router.post("/forest-polygons/import-file")
async def import_forest_polygons_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Import forest polygons from GeoJSON file upload
    Admin only - requires settings.manage permission
    """
    require_permission(current_user, "settings.manage")
    
    # Validate file type
    if not file.filename.endswith(('.json', '.geojson')):
        raise HTTPException(
            status_code=400, 
            detail="Only .json or .geojson files are allowed"
        )
    
    try:
        content = await file.read()
        geojson = json.loads(content.decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    result = forest_polygon_service.import_geojson(db, geojson)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Import failed"))
    
    return result


# ===== Link Project to Polygon =====

@router.post("/projects/{project_id}/link-polygon/{polygon_id}")
def link_project_to_polygon(
    project_id: int,
    polygon_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Link a project to a forest polygon
    Admin only
    """
    require_permission(current_user, "projects.update")
    
    success = forest_polygon_service.link_project_to_polygon(db, project_id, polygon_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {"success": True, "project_id": project_id, "polygon_id": polygon_id}


@router.post("/projects/{project_id}/find-polygon")
def find_and_link_polygon_for_project(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Find forest polygon that contains the project's location and link it
    Uses spatial query ST_Contains
    """
    require_permission(current_user, "projects.update")
    
    # Get project location
    map_data = forest_polygon_service.get_project_forest_map(db, project_id)
    
    if not map_data.get("project_point"):
        raise HTTPException(
            status_code=400, 
            detail="Project has no location coordinates"
        )
    
    point = map_data["project_point"]
    polygon_id = forest_polygon_service.find_polygon_containing_point(
        db, 
        point["lat"], 
        point["lng"]
    )
    
    if not polygon_id:
        return {
            "success": False, 
            "message": "No forest polygon contains this project's location"
        }
    
    forest_polygon_service.link_project_to_polygon(db, project_id, polygon_id)
    
    return {
        "success": True,
        "project_id": project_id,
        "polygon_id": polygon_id,
        "message": f"Project linked to polygon {polygon_id}"
    }


# ===== Region & Area Boundaries =====

@router.get("/regions/boundaries")
def get_region_boundaries(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Get region boundary polygons for map display.
    Returns GeoJSON features for regions that have geometry.
    """
    rows = db.execute(text("""
        SELECT r.id, r.name, r.code,
               ST_AsGeoJSON(r.geom)::json as geometry
        FROM regions r
        WHERE r.geom IS NOT NULL AND r.is_active = true
        ORDER BY r.name
    """)).fetchall()
    
    features = []
    for row in rows:
        features.append({
            "type": "Feature",
            "properties": {
                "id": row.id,
                "name": row.name,
                "code": row.code,
                "layer_type": "region",
            },
            "geometry": row.geometry,
        })
    
    return {
        "type": "FeatureCollection",
        "features": features,
    }


@router.get("/areas/boundaries")
def get_area_boundaries(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    region_id: Optional[int] = None,
):
    """
    Get area boundary polygons for map display.
    Optionally filter by region_id.
    """
    sql = """
        SELECT a.id, a.name, a.code, a.region_id,
               r.name as region_name,
               ST_AsGeoJSON(a.geom)::json as geometry
        FROM areas a
        LEFT JOIN regions r ON r.id = a.region_id
        WHERE a.geom IS NOT NULL AND a.is_active = true
    """
    params = {}
    if region_id:
        sql += " AND a.region_id = :region_id"
        params["region_id"] = region_id
    sql += " ORDER BY a.name"
    
    rows = db.execute(text(sql), params).fetchall()
    
    features = []
    for row in rows:
        features.append({
            "type": "Feature",
            "properties": {
                "id": row.id,
                "name": row.name,
                "code": row.code,
                "region_id": row.region_id,
                "region_name": row.region_name,
                "layer_type": "area",
            },
            "geometry": row.geometry,
        })
    
    return {
        "type": "FeatureCollection",
        "features": features,
    }


@router.get("/layers/all")
def get_all_map_layers(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Get all GIS layers in one call: regions, areas, project points.
    Optimized for initial map load.
    """
    # Region boundaries
    regions = db.execute(text("""
        SELECT r.id, r.name, r.code, ST_AsGeoJSON(r.geom)::json as geometry
        FROM regions r WHERE r.geom IS NOT NULL AND r.is_active = true
    """)).fetchall()
    
    # Area boundaries
    areas = db.execute(text("""
        SELECT a.id, a.name, a.code, a.region_id, ST_AsGeoJSON(a.geom)::json as geometry
        FROM areas a WHERE a.geom IS NOT NULL AND a.is_active = true
    """)).fetchall()
    
    # Project points
    projects = db.execute(text("""
        SELECT p.id, p.code, p.name, p.region_id, p.area_id,
               ST_Y(p.location_geom::geometry) as lat,
               ST_X(p.location_geom::geometry) as lng,
               'projects.location_geom' AS point_source,
               CASE
                 WHEN a.geom IS NULL THEN 'FAR'
                 WHEN ST_Covers(a.geom, p.location_geom) THEN 'INSIDE'
                 WHEN ST_Distance(p.location_geom::geography, a.geom::geography) <= 3000 THEN 'NEAR'
                 ELSE 'FAR'
               END AS geo_validation_status,
               CASE
                 WHEN a.geom IS NULL THEN NULL
                 ELSE ROUND(ST_Distance(p.location_geom::geography, a.geom::geography))::int
               END AS distance_to_area_meters
        FROM projects p
        LEFT JOIN areas a ON a.id = p.area_id
        WHERE p.location_geom IS NOT NULL AND p.is_active = true
    """)).fetchall()
    
    # Forest polygons — limit to reasonable size for map rendering
    forest_polys = db.execute(text("""
        SELECT id,
               ST_AsGeoJSON(
                   ST_Simplify(geom::geometry, 0.0003)
               )::json as geometry,
               ST_Area(geom::geography) / 1000000 as area_km2
        FROM forest_polygons
        WHERE geom IS NOT NULL
        ORDER BY area_km2 DESC
        LIMIT 273
    """)).fetchall()

    return {
        "regions": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"id": r.id, "name": r.name, "code": r.code, "layer_type": "region"},
                    "geometry": r.geometry,
                }
                for r in regions
            ],
        },
        "areas": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"id": a.id, "name": a.name, "code": a.code, "region_id": a.region_id, "layer_type": "area"},
                    "geometry": a.geometry,
                }
                for a in areas
            ],
        },
        "forests": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"id": fp.id, "area_km2": round(float(fp.area_km2), 2), "layer_type": "forest"},
                    "geometry": fp.geometry,
                }
                for fp in forest_polys
            ],
        },
        "projects": [
            {
                "id": p.id,
                "code": p.code,
                "name": p.name,
                "region_id": p.region_id,
                "area_id": p.area_id,
                "lat": float(p.lat) if p.lat else None,
                "lng": float(p.lng) if p.lng else None,
                "point_source": p.point_source,
                "geo_validation_status": p.geo_validation_status,
                "distance_to_area_meters": int(p.distance_to_area_meters) if p.distance_to_area_meters is not None else None,
            }
            for p in projects
        ],
    }


@router.get("/projects/{project_id}/navigation-point")
def get_navigation_point(
    project_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Get GPS point for Waze/Google Maps navigation."""
    from sqlalchemy import text
    
    # Try project geo data
    row = db.execute(text("""
        SELECT 
            COALESCE(l.center_lat, l.latitude) as lat,
            COALESCE(l.center_lng, l.longitude) as lng
        FROM projects p
        LEFT JOIN locations l ON l.id = p.location_id
        WHERE p.id = :pid
    """), {"pid": project_id}).first()
    
    if row and row[0] and row[1]:
        return {"lat": float(row[0]), "lng": float(row[1])}
    
    # Try forest polygon centroid
    row2 = db.execute(text("""
        SELECT ST_Y(ST_Centroid(f.geom)) as lat, ST_X(ST_Centroid(f.geom)) as lng
        FROM projects p
        JOIN forests f ON f.id = p.forest_id
        WHERE p.id = :pid AND f.geom IS NOT NULL
    """), {"pid": project_id}).first()
    
    if row2 and row2[0]:
        return {"lat": float(row2[0]), "lng": float(row2[1])}
    
    raise HTTPException(status_code=404, detail="אין נתוני מיקום לפרויקט זה")

