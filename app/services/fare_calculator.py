from datetime import datetime
from typing import Tuple
from app.models.driver import VehicleType

MIN_BOOK_FARE = 5.0

BIKE_PER_KM = 10.0
AUTO_PER_PERSON_KM = 8.0
CAR_PER_PERSON_KM = 10.0

WAITING_CHARGE_PER_MINUTE = 2.0
FREE_WAITING_MINUTES = 3
NIGHT_CHARGE_MULTIPLIER = 1.25
NIGHT_START_HOUR = 22
NIGHT_END_HOUR = 6


def _trip_fare(distance_km: float, vehicle_type: VehicleType, passenger_count: int = 1) -> float:
    """Rural pricing: bike ₹10/km; auto & car per person per km."""
    if vehicle_type == VehicleType.BIKE:
        return distance_km * BIKE_PER_KM
    if vehicle_type == VehicleType.AUTO:
        return distance_km * AUTO_PER_PERSON_KM * max(1, passenger_count)
    return distance_km * CAR_PER_PERSON_KM * max(1, passenger_count)


def calculate_fare(
    distance_km: float,
    vehicle_type: VehicleType,
    waiting_minutes: int = 0,
    ride_time: datetime = None,
    passenger_count: int = 1,
) -> Tuple[float, dict]:
    if ride_time is None:
        ride_time = datetime.now()

    distance_fare = _trip_fare(distance_km, vehicle_type, passenger_count)

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
        "passenger_count": max(1, passenger_count),
        "waiting_minutes": waiting_minutes,
        "waiting_fare": round(waiting_fare, 2),
        "subtotal": round(subtotal, 2),
        "is_night": is_night,
        "night_charge": round(night_charge, 2),
        "total_fare": round(total_fare, 2),
    }

    return round(total_fare, 2), breakdown


def estimate_fare(
    distance_km: float,
    vehicle_type: VehicleType,
    passenger_count: int = 1,
) -> float:
    return round(_trip_fare(distance_km, vehicle_type, passenger_count), 2)
