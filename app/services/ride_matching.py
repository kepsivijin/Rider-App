from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from math import radians, cos, sin, asin, sqrt
from app.models.driver import Driver
from app.models.user import User

EARTH_RADIUS_KM = 6371


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on earth (in kilometers)
    """
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    
    return EARTH_RADIUS_KM * c


def find_nearby_drivers(
    db: Session,
    latitude: float,
    longitude: float,
    radius_km: float = 5.0,
    limit: int = 10
) -> List[Tuple[Driver, User, float]]:
    """
    Find nearby online drivers within specified radius
    
    Returns:
        List of tuples (Driver, User, distance_km) sorted by distance
    """
    drivers = db.query(Driver, User).join(
        User, Driver.user_id == User.id
    ).filter(
        and_(
            Driver.is_online == True,
            Driver.is_approved == True,
            Driver.current_latitude.isnot(None),
            Driver.current_longitude.isnot(None),
            User.is_active == True
        )
    ).all()
    
    nearby = []
    for driver, user in drivers:
        distance = haversine_distance(
            latitude,
            longitude,
            driver.current_latitude,
            driver.current_longitude
        )
        
        if distance <= radius_km:
            nearby.append((driver, user, distance))
    
    nearby.sort(key=lambda x: x[2])
    
    return nearby[:limit]
