"""
Forest Polygon Schemas - סכמות פוליגוני יער (נקי, ללא שם)
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel


class ForestPolygonBase(BaseModel):
    """Base forest polygon - just geometry"""
    pass


class ForestPolygonCreate(BaseModel):
    """Create forest polygon from GeoJSON"""
    geojson: Dict[str, Any]  # GeoJSON geometry (MultiPolygon or Polygon)


class ForestPolygonResponse(BaseModel):
    """Response with polygon data"""
    id: int
    geojson: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ForestPolygonImportRequest(BaseModel):
    """Request to import multiple polygons from GeoJSON FeatureCollection"""
    geojson: Dict[str, Any]  # Full GeoJSON FeatureCollection or single Feature


class ForestPolygonImportResponse(BaseModel):
    """Response after import"""
    imported_count: int
    polygon_ids: List[int]
    message: str


class ProjectForestMapResponse(BaseModel):
    """Response for project forest-map endpoint"""
    project_id: int
    project_code: str
    project_name: str
    project_point: Optional[Dict[str, float]] = None  # {lat, lng}
    forest_polygon: Optional[Dict[str, Any]] = None  # GeoJSON
    has_location: bool = False
    has_polygon: bool = False

