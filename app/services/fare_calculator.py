from datetime import datetime
from typing import Tuple
from app.models.driver import VehicleType

MIN_BOOK_FARE = 5.0

VEHICLE_BASE_FARE = {
    VehicleType.BIKE: 30.0,
    VehicleType.AUTO: 29.0,
    VehicleType.CAR: 40.0,
}

VEHICLE_PER_KM = {
    VehicleType.BIKE: 9.0,
    VehicleType.AUTO: 12.0,
    VehicleType.CAR: 18.0,
}

AUTO_INCLUDED_KM = 4.0

WAITING_CHARGE_PER_MINUTE = 2.0
FREE_WAITING_MINUTES = 3
NIGHT_CHARGE_MULTIPLIER = 1.25
NIGHT_START_HOUR = 22
NIGHT_END_HOUR = 6


def _distance_fare(distance_km: float, vehicle_type: VehicleType) -> Tuple[float, float]:
    """Return (base_fare, distance_component)."""
    base = VEHICLE_BASE_FARE[vehicle_type]
    per_km = VEHICLE_PER_KM[vehicle_type]

    if vehicle_type == VehicleType.AUTO:
        if distance_km <= AUTO_INCLUDED_KM:
            return base, 0.0
        extra = distance_km - AUTO_INCLUDED_KM
        return base, extra * per_km

    return base, distance_km * per_km


def calculate_fare(
    distance_km: float,
    vehicle_type: VehicleType,
    waiting_minutes: int = 0,
    ride_time: datetime = None
) -> Tuple[float, dict]:
    """Vehicle-specific fare (Uber-style) + optional waiting / night charges."""
    if ride_time is None:
        ride_time = datetime.now()

    base_fare, distance_fare = _distance_fare(distance_km, vehicle_type)
    per_km = VEHICLE_PER_KM[vehicle_type]

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
        "fare_per_km": per_km,
        "waiting_minutes": waiting_minutes,
        "waiting_fare": round(waiting_fare, 2),
        "subtotal": round(subtotal, 2),
        "is_night": is_night,
        "night_charge": round(night_charge, 2),
        "total_fare": round(total_fare, 2),
    }

    return round(total_fare, 2), breakdown


def estimate_fare(distance_km: float, vehicle_type: VehicleType) -> float:
    """Quick fare estimate for booking (no waiting / night extras)."""
    base_fare, distance_fare = _distance_fare(distance_km, vehicle_type)
    return round(base_fare + distance_fare, 2)
