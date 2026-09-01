from datetime import datetime
from typing import Tuple
from app.models.driver import VehicleType

FARE_PER_KM = 5.0

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
    Calculate ride fare: ₹5 per km (+ optional waiting / night charges).
    """
    if ride_time is None:
        ride_time = datetime.now()

    distance_fare = distance_km * FARE_PER_KM

    waiting_fare = 0.0
    if waiting_minutes > FREE_WAITING_MINUTES:
        waiting_fare = (waiting_minutes - FREE_WAITING_MINUTES) * WAITING_CHARGE_PER_MINUTE

    subtotal = distance_fare + waiting_fare

    is_night = ride_time.hour >= NIGHT_START_HOUR or ride_time.hour < NIGHT_END_HOUR
    night_charge = 0.0
    if is_night:
        night_charge = subtotal * (NIGHT_CHARGE_MULTIPLIER - 1)

    total_fare = subtotal + night_charge

    breakdown = {
        "base_fare": 0.0,
        "distance_km": round(distance_km, 2),
        "distance_fare": round(distance_fare, 2),
        "fare_per_km": FARE_PER_KM,
        "waiting_minutes": waiting_minutes,
        "waiting_fare": round(waiting_fare, 2),
        "subtotal": round(subtotal, 2),
        "is_night": is_night,
        "night_charge": round(night_charge, 2),
        "total_fare": round(total_fare, 2)
    }

    return round(total_fare, 2), breakdown


def estimate_fare(distance_km: float, vehicle_type: VehicleType) -> float:
    """Quick fare estimate: ₹5 per km."""
    return round(distance_km * FARE_PER_KM, 2)
