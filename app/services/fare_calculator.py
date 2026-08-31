from datetime import datetime
from typing import Tuple
from app.models.driver import VehicleType

VEHICLE_BASE_FARE = {
    VehicleType.BIKE: 20.0,
    VehicleType.AUTO: 40.0,
    VehicleType.CAR: 60.0
}

VEHICLE_PER_KM = {
    VehicleType.BIKE: 8.0,
    VehicleType.AUTO: 12.0,
    VehicleType.CAR: 15.0
}

WAITING_CHARGE_PER_MINUTE = 2.0
FREE_WAITING_MINUTES = 3
NIGHT_CHARGE_MULTIPLIER = 1.25
NIGHT_START_HOUR = 22
NIGHT_END_HOUR = 6


def calculate_fare(
    distance_km: float,
    vehicle_type: VehicleType,
    waiting_minutes: int = 0,
    ride_time: datetime = None
) -> Tuple[float, dict]:
    """
    Calculate ride fare based on distance, vehicle type, waiting time, and time of day
    
    Returns:
        Tuple of (total_fare, breakdown_dict)
    """
    if ride_time is None:
        ride_time = datetime.now()
    
    base_fare = VEHICLE_BASE_FARE[vehicle_type]
    per_km_rate = VEHICLE_PER_KM[vehicle_type]
    
    distance_fare = distance_km * per_km_rate
    
    waiting_fare = 0.0
    if waiting_minutes > FREE_WAITING_MINUTES:
        waiting_fare = (waiting_minutes - FREE_WAITING_MINUTES) * WAITING_CHARGE_PER_MINUTE
    
    subtotal = base_fare + distance_fare + waiting_fare
    
    is_night = ride_time.hour >= NIGHT_START_HOUR or ride_time.hour < NIGHT_END_HOUR
    night_charge = 0.0
    if is_night:
        night_charge = subtotal * (NIGHT_CHARGE_MULTIPLIER - 1)
    
    total_fare = subtotal + night_charge
    
    breakdown = {
        "base_fare": round(base_fare, 2),
        "distance_km": round(distance_km, 2),
        "distance_fare": round(distance_fare, 2),
        "waiting_minutes": waiting_minutes,
        "waiting_fare": round(waiting_fare, 2),
        "subtotal": round(subtotal, 2),
        "is_night": is_night,
        "night_charge": round(night_charge, 2),
        "total_fare": round(total_fare, 2)
    }
    
    return round(total_fare, 2), breakdown


def estimate_fare(distance_km: float, vehicle_type: VehicleType) -> float:
    """Quick fare estimate without waiting time and night charges"""
    fare, _ = calculate_fare(distance_km, vehicle_type, 0)
    return fare
