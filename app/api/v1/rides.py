from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _to_naive_utc(value: datetime) -> datetime:
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value

from app.core.database import get_db
from app.api.dependencies import get_current_user, get_current_driver
from app.models.user import User
from app.models.ride import Ride, RideStatus, PaymentStatus
from app.models.driver import Driver, VehicleType
from app.schemas.ride import RideCreate, RideResponse, RideUpdate, NearbyDriverResponse, PickupOtpVerify
from app.services.fare_calculator import estimate_fare
from app.services.ride_matching import find_nearby_drivers, haversine_distance
from app.services.geofence import validate_ride_locations
from app.services.notification import notify_driver_ride_request, notify_customer_ride_accepted
from app.services.geocoding import resolve_address
from app.services.ride_serializer import serialize_ride
from app.services.pickup_otp import generate_pickup_otp
from app.services.ride_rejections import get_rejected_ride_ids, record_driver_rejection

router = APIRouter()


def _serialize(ride: Ride, db: Session, viewer: Optional[User] = None) -> RideResponse:
    return serialize_ride(ride, db, viewer)


@router.post("/request", response_model=RideResponse)
async def request_ride(
    ride_data: RideCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new ride request"""
    is_valid, error_msg = validate_ride_locations(
        ride_data.pickup_latitude,
        ride_data.pickup_longitude,
        ride_data.dropoff_latitude,
        ride_data.dropoff_longitude
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    distance_km = haversine_distance(
        ride_data.pickup_latitude,
        ride_data.pickup_longitude,
        ride_data.dropoff_latitude,
        ride_data.dropoff_longitude
    )
    
    estimated_fare = estimate_fare(distance_km, ride_data.vehicle_type, ride_data.passenger_count)

    pickup_address = resolve_address(
        ride_data.pickup_address,
        ride_data.pickup_latitude,
        ride_data.pickup_longitude,
    )
    dropoff_address = resolve_address(
        ride_data.dropoff_address,
        ride_data.dropoff_latitude,
        ride_data.dropoff_longitude,
    )
    
    ride = Ride(
        customer_id=current_user.id,
        pickup_latitude=ride_data.pickup_latitude,
        pickup_longitude=ride_data.pickup_longitude,
        pickup_address=pickup_address,
        dropoff_latitude=ride_data.dropoff_latitude,
        dropoff_longitude=ride_data.dropoff_longitude,
        dropoff_address=dropoff_address,
        estimated_fare=estimated_fare,
        distance_km=distance_km,
        payment_method=ride_data.payment_method,
        vehicle_type=ride_data.vehicle_type.value,
        passenger_count=ride_data.passenger_count,
        scheduled_at=_to_naive_utc(ride_data.scheduled_at) if ride_data.scheduled_at else None,
        status=RideStatus.REQUESTED
    )
    
    db.add(ride)
    db.commit()
    db.refresh(ride)
    
    is_scheduled_later = ride_data.scheduled_at and _to_naive_utc(ride_data.scheduled_at) > _utc_now()
    
    if not is_scheduled_later:
        nearby_drivers = find_nearby_drivers(
            db,
            ride_data.pickup_latitude,
            ride_data.pickup_longitude,
            radius_km=5.0
        )
        
        for driver, user, distance in nearby_drivers:
            if user.fcm_token:
                await notify_driver_ride_request(
                    user.fcm_token,
                    str(ride.id),
                    pickup_address,
                    estimated_fare
                )
    
    return _serialize(ride, db, current_user)


@router.get("/pending", response_model=List[RideResponse])
async def get_pending_rides(
    current_user: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """Get all requested rides waiting for a driver (immediate + due scheduled)"""
    now = _utc_now()
    driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver profile not found")

    rides = (
        db.query(Ride)
        .filter(
            Ride.status == RideStatus.REQUESTED,
            or_(Ride.scheduled_at.is_(None), Ride.scheduled_at <= now),
        )
        .order_by(Ride.requested_at.desc())
        .limit(20)
        .all()
    )
    visible = [ride for ride in rides if str(ride.id) not in get_rejected_ride_ids(driver.id)]
    return [_serialize(ride, db, current_user) for ride in visible]


@router.get("/driver/active", response_model=Optional[RideResponse])
async def get_driver_active_ride(
    current_user: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """Get driver's current active ride (accepted or started)"""
    driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver profile not found")

    ride = (
        db.query(Ride)
        .filter(
            Ride.driver_id == driver.id,
            Ride.status.in_([RideStatus.ACCEPTED, RideStatus.STARTED])
        )
        .order_by(Ride.accepted_at.desc())
        .first()
    )
    if not ride:
        return None
    return _serialize(ride, db, current_user)


@router.get("/nearby-drivers", response_model=List[NearbyDriverResponse])
async def get_nearby_drivers(
    latitude: float,
    longitude: float,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Find nearby available drivers"""
    nearby = find_nearby_drivers(db, latitude, longitude, radius_km=5.0)
    
    return [
        NearbyDriverResponse(
            driver_id=driver.id,
            user_id=user.id,
            full_name=user.full_name,
            vehicle_type=driver.vehicle_type.value,
            vehicle_number=driver.vehicle_number,
            rating=driver.rating,
            total_rides=driver.total_rides,
            latitude=driver.current_latitude,
            longitude=driver.current_longitude,
            distance_km=round(distance, 2)
        )
        for driver, user, distance in nearby
    ]


@router.post("/{ride_id}/accept", response_model=RideResponse)
async def accept_ride(
    ride_id: UUID,
    current_user: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """Driver accepts a ride request"""
    ride = db.query(Ride).filter(Ride.id == ride_id).first()
    if not ride:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride not found"
        )
    
    if ride.status != RideStatus.REQUESTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ride is not available"
        )
    
    driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
    if not driver or not driver.is_approved or not driver.is_online:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Driver not eligible to accept rides"
        )
    
    pickup_otp = generate_pickup_otp()
    ride.driver_id = driver.id
    ride.status = RideStatus.ACCEPTED
    ride.accepted_at = datetime.utcnow()
    ride.pickup_otp = pickup_otp
    ride.pickup_verified = False
    
    db.commit()
    db.refresh(ride)
    
    customer = db.query(User).filter(User.id == ride.customer_id).first()
    await notify_customer_ride_accepted(
        customer.fcm_token if customer else None,
        str(ride.id),
        current_user.full_name,
        driver.vehicle_number,
        pickup_otp,
    )
    
    return _serialize(ride, db, current_user)


@router.post("/{ride_id}/reject", response_model=dict)
async def reject_ride(
    ride_id: UUID,
    current_user: User = Depends(get_current_driver),
    db: Session = Depends(get_db),
):
    """Driver declines a ride request — hidden for this driver, still available to others."""
    ride = db.query(Ride).filter(Ride.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")

    if ride.status != RideStatus.REQUESTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ride is not available")

    driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
    if not driver or not driver.is_approved or not driver.is_online:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Driver not eligible")

    record_driver_rejection(driver.id, ride.id)
    return {"message": "Ride rejected", "ride_id": str(ride_id)}


@router.post("/{ride_id}/verify-pickup", response_model=RideResponse)
async def verify_pickup_otp(
    ride_id: UUID,
    body: PickupOtpVerify,
    current_user: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """Driver verifies customer pickup OTP before starting the ride"""
    ride = db.query(Ride).filter(Ride.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")

    driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
    if not driver or ride.driver_id != driver.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    if ride.status != RideStatus.ACCEPTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ride is not awaiting pickup verification")

    if not ride.pickup_otp or body.pickup_otp.strip() != ride.pickup_otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid pickup OTP. Ask customer for the code shown in their app.")

    ride.pickup_verified = True
    db.commit()
    db.refresh(ride)
    return _serialize(ride, db, current_user)


@router.post("/{ride_id}/start", response_model=RideResponse)
async def start_ride(
    ride_id: UUID,
    current_user: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """Driver starts the ride"""
    ride = db.query(Ride).filter(Ride.id == ride_id).first()
    if not ride:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride not found"
        )
    
    driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
    if ride.driver_id != driver.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    if ride.status != RideStatus.ACCEPTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ride cannot be started"
        )

    if not ride.pickup_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verify customer pickup OTP before starting the ride"
        )
    
    ride.status = RideStatus.STARTED
    ride.started_at = datetime.utcnow()
    
    db.commit()
    db.refresh(ride)
    
    return _serialize(ride, db, current_user)


@router.post("/{ride_id}/complete", response_model=RideResponse)
async def complete_ride(
    ride_id: UUID,
    current_user: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """Driver completes the ride"""
    ride = db.query(Ride).filter(Ride.id == ride_id).first()
    if not ride:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride not found"
        )
    
    driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
    if ride.driver_id != driver.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    if ride.status != RideStatus.STARTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ride is not in progress"
        )
    
    ride.status = RideStatus.COMPLETED
    ride.completed_at = datetime.utcnow()
    ride.actual_fare = ride.estimated_fare
    
    if ride.payment_method.value == "cash":
        ride.payment_status = PaymentStatus.COMPLETED
    
    driver.total_rides += 1
    
    db.commit()
    db.refresh(ride)
    
    return _serialize(ride, db, current_user)


@router.get("/my-rides", response_model=List[RideResponse])
async def get_my_rides(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get rides for current user"""
    rides = db.query(Ride).filter(Ride.customer_id == current_user.id).order_by(Ride.created_at.desc()).all()
    return [_serialize(ride, db, current_user) for ride in rides]


@router.get("/driver/history", response_model=List[RideResponse])
async def get_driver_ride_history(
    current_user: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """Get completed and past rides for the current driver"""
    driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver profile not found")

    rides = (
        db.query(Ride)
        .filter(Ride.driver_id == driver.id)
        .order_by(Ride.created_at.desc())
        .limit(50)
        .all()
    )
    return [_serialize(ride, db, current_user) for ride in rides]


@router.get("/{ride_id}", response_model=RideResponse)
async def get_ride(
    ride_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ride details"""
    ride = db.query(Ride).filter(Ride.id == ride_id).first()
    if not ride:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride not found"
        )
    
    return _serialize(ride, db, current_user)
