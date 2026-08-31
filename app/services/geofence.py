from typing import List, Tuple
from app.core.config import settings


def point_in_polygon(point: Tuple[float, float], polygon: List[List[float]]) -> bool:
    """
    Check if a point (lat, lon) is inside a polygon using ray casting algorithm
    
    Args:
        point: (latitude, longitude)
        polygon: List of [longitude, latitude] coordinates
    
    Returns:
        True if point is inside polygon
    """
    lat, lon = point
    n = len(polygon)
    inside = False
    
    p1_lon, p1_lat = polygon[0]
    for i in range(1, n + 1):
        p2_lon, p2_lat = polygon[i % n]
        
        if lat > min(p1_lat, p2_lat):
            if lat <= max(p1_lat, p2_lat):
                if lon <= max(p1_lon, p2_lon):
                    if p1_lat != p2_lat:
                        x_intersect = (lat - p1_lat) * (p2_lon - p1_lon) / (p2_lat - p1_lat) + p1_lon
                    if p1_lon == p2_lon or lon <= x_intersect:
                        inside = not inside
        
        p1_lon, p1_lat = p2_lon, p2_lat
    
    return inside


def is_within_service_area(latitude: float, longitude: float) -> bool:
    """
    Check if coordinates are within the service area
    (Eramanthurai, Vallavilai, Nithiravilai, Marthandam surroundings)
    """
    boundary = settings.geofence_coordinates
    lons = [p[0] for p in boundary]
    lats = [p[1] for p in boundary]
    return min(lats) <= latitude <= max(lats) and min(lons) <= longitude <= max(lons)


def validate_ride_locations(
    pickup_lat: float,
    pickup_lon: float,
    dropoff_lat: float,
    dropoff_lon: float
) -> Tuple[bool, str]:
    """
    Validate that both pickup and dropoff are within the service area
    """
    if not is_within_service_area(pickup_lat, pickup_lon):
        return False, "Pickup is outside service area (Eramanthurai–Marthandam region only)"
    
    if not is_within_service_area(dropoff_lat, dropoff_lon):
        return False, "Dropoff is outside service area (Eramanthurai–Marthandam region only)"
    
    return True, ""


# Backward compatibility
is_within_kanyakumari = is_within_service_area
