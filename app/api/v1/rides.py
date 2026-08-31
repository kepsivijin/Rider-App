from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.api.dependencies import get_current_user, get_current_driver
from app.models.user import User
from app.models.ride import Ride, RideStatus, PaymentStatus
from app.models.driver import Driver, VehicleType
from app.schemas.ride import RideCreate, RideResponse, RideUpdate, NearbyDriverResponse
from app.services.fare_calculator import estimate_fare
from app.services.ride_matching import find_nearby_drivers, haversine_distance
from app.services.geofence import validate_ride_locations
from app.services.notification import notify_driver_ride_request, notify_customer_ride_accepted
from app.services.geocoding import resolve_address
from app.services.ride_serializer import serialize_ride

router = APIRouter()


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
    
    estimated_fare = estimate_fare(distance_km, ride_data.vehicle_type)

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
        status=RideStatus.REQUESTED
    )
    
    db.add(ride)
    db.commit()
    db.refresh(ride)
    
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
    
    return serialize_ride(ride, db)


@router.get("/pending", response_model=List[RideResponse])
async def get_pending_rides(
    current_user: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """Get all requested rides waiting for a driver"""
    rides = (
        db.query(Ride)
        .filter(Ride.status == RideStatus.REQUESTED)
        .order_by(Ride.requested_at.desc())
        .limit(20)
        .all()
    )
    return [serialize_ride(ride, db) for ride in rides]


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
    return serialize_ride(ride, db)


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
    
    ride.driver_id = driver.id
    ride.status = RideStatus.ACCEPTED
    ride.accepted_at = datetime.utcnow()
    
    db.commit()
    db.refresh(ride)
    
    customer = db.query(User).filter(User.id == ride.customer_id).first()
    if customer and customer.fcm_token:
        await notify_customer_ride_accepted(
            customer.fcm_token,
            str(ride.id),
            current_user.full_name,
            driver.vehicle_number
        )
    
    return serialize_ride(ride, db)


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
    
    ride.status = RideStatus.STARTED
    ride.started_at = datetime.utcnow()
    
    db.commit()
    db.refresh(ride)
    
    return serialize_ride(ride, db)


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
    
    return serialize_ride(ride, db)


@router.get("/my-rides", response_model=List[RideResponse])
async def get_my_rides(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get rides for current user"""
    rides = db.query(Ride).filter(Ride.customer_id == current_user.id).order_by(Ride.created_at.desc()).all()
    return [serialize_ride(ride, db) for ride in rides]


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
    return [serialize_ride(ride, db) for ride in rides]


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
    
    return serialize_ride(ride, db)
