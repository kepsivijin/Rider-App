from typing import Optional
from sqlalchemy.orm import Session

from app.models.ride import Ride, RideStatus
from app.models.driver import Driver
from app.models.user import User
from app.schemas.ride import RideResponse
from app.services.geocoding import resolve_address
from app.core.redis_client import redis_client
import json


def serialize_ride(ride: Ride, db: Session, viewer: Optional[User] = None) -> RideResponse:
    driver_name = None
    driver_vehicle = None
    driver_user_id = None
    driver_vehicle_type = None
    driver_passenger_capacity = None
    customer_name = None
    customer_phone = None

    if ride.driver_id:
        driver = db.query(Driver).filter(Driver.id == ride.driver_id).first()
        if driver:
            driver_user_id = driver.user_id
            driver_user = db.query(User).filter(User.id == driver.user_id).first()
            if driver_user:
                driver_name = driver_user.full_name
            driver_vehicle = driver.vehicle_number
            driver_vehicle_type = (
                driver.vehicle_type.value if hasattr(driver.vehicle_type, "value") else str(driver.vehicle_type)
            )
            driver_passenger_capacity = getattr(driver, "passenger_capacity", 1)

    customer = db.query(User).filter(User.id == ride.customer_id).first()
    if customer:
        customer_name = customer.full_name
        customer_phone = customer.phone_number

    pickup_address = resolve_address(ride.pickup_address, ride.pickup_latitude, ride.pickup_longitude)
    dropoff_address = resolve_address(ride.dropoff_address, ride.dropoff_latitude, ride.dropoff_longitude)

    pickup_otp = None
    notification_message = None
    is_customer = viewer and viewer.id == ride.customer_id
    is_driver = False
    if viewer:
        driver_profile = db.query(Driver).filter(Driver.user_id == viewer.id).first()
        is_driver = driver_profile and ride.driver_id == driver_profile.id

    if is_customer and ride.pickup_otp and ride.status in (RideStatus.ACCEPTED, RideStatus.STARTED):
        pickup_otp = ride.pickup_otp
        if ride.status == RideStatus.ACCEPTED and not ride.pickup_verified:
            notification_message = (
                f"Driver {driver_name or 'accepted'}! Tell the driver your pickup OTP: {ride.pickup_otp}"
            )

    data = RideResponse.model_validate(ride).model_dump()
    data["pickup_address"] = pickup_address
    data["dropoff_address"] = dropoff_address
    data["driver_name"] = driver_name
    data["driver_vehicle"] = driver_vehicle
    data["driver_user_id"] = driver_user_id
    data["customer_name"] = customer_name
    data["customer_phone"] = customer_phone
    data["vehicle_type"] = getattr(ride, "vehicle_type", None) or "bike"
    data["passenger_count"] = getattr(ride, "passenger_count", 1) or 1
    data["driver_vehicle_type"] = driver_vehicle_type
    data["driver_passenger_capacity"] = driver_passenger_capacity
    data["pickup_otp"] = pickup_otp
    data["pickup_verified"] = bool(getattr(ride, "pickup_verified", False))
    data["notification_message"] = notification_message if is_customer else None

    try:
        live = redis_client.get(f"ride_location:{ride.id}")
    except Exception:
        live = None
    if live:
        try:
            loc = json.loads(live)
            data["driver_latitude"] = loc.get("latitude")
            data["driver_longitude"] = loc.get("longitude")
        except (json.JSONDecodeError, TypeError):
            pass

    return RideResponse(**data)
