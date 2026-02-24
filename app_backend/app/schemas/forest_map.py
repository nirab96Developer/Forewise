"""
Forest Map Schemas - סכמות מפת יער
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class ForestGeoJSON(BaseModel):
    """GeoJSON representation of forest boundary"""
    type: str = "Feature"
    properties: Dict[str, Any] = {}
    geometry: Dict[str, Any]


class ProjectPoint(BaseModel):
    """Project location point"""
    lat: float
    lng: float


class ForestInfo(BaseModel):
    """Forest information with GeoJSON"""
    id: int
    name: str
    code: Optional[str] = None
    area_km2: Optional[float] = None
    geojson_preview: Dict[str, Any]
    geojson_full: Dict[str, Any]


class ForestMapResponse(BaseModel):
    """Response for forest-map endpoint"""
    project: Dict[str, Any]
    forest: Optional[ForestInfo] = None
    has_forest: bool = False
    has_location: bool = False
    
    class Config:
        from_attributes = True


class ForestListItem(BaseModel):
    """Forest item for list"""
    id: int
    name: str
    code: Optional[str] = None
    area_km2: Optional[float] = None
    
    class Config:
        from_attributes = True

