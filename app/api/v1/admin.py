from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.api.dependencies import get_current_admin
from app.models.user import User
from app.models.driver import Driver
from app.models.ride import Ride
from app.schemas.driver import DriverResponse, AdminDriverResponse, AdminCreateDriver
from app.schemas.ride import RideResponse
from app.schemas.user import UserResponse
from app.services.ride_serializer import serialize_ride

router = APIRouter()


def _serialize_admin_driver(driver: Driver, db: Session) -> AdminDriverResponse:
    user = db.query(User).filter(User.id == driver.user_id).first()
    data = DriverResponse.model_validate(driver).model_dump()
    data["full_name"] = user.full_name if user else None
    data["phone_number"] = user.phone_number if user else None
    data["email"] = user.email if user else None
    return AdminDriverResponse(**data)


@router.get("/drivers", response_model=List[AdminDriverResponse])
async def get_all_drivers(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all drivers with user details for admin"""
    drivers = db.query(Driver).order_by(Driver.created_at.desc()).all()
    return [_serialize_admin_driver(driver, db) for driver in drivers]


@router.get("/drivers/pending", response_model=List[AdminDriverResponse])
async def get_pending_drivers(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all pending driver applications"""
    drivers = db.query(Driver).filter(Driver.is_approved == False).all()
    return [_serialize_admin_driver(driver, db) for driver in drivers]


@router.post("/drivers", response_model=AdminDriverResponse)
async def create_driver(
    data: AdminCreateDriver,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin creates a driver with vehicle type and passenger capacity"""
    from datetime import datetime, timedelta
    from app.models.user import UserRole
    from app.models.wallet import Wallet
    from app.utils.phone import normalize_phone

    phone = normalize_phone(data.phone_number)
    existing = db.query(User).filter(User.phone_number == phone).first()
    if existing:
        driver = db.query(Driver).filter(Driver.user_id == existing.id).first()
        if driver:
            raise HTTPException(status_code=400, detail="This phone already has a driver profile")
        user = existing
        user.role = UserRole.DRIVER
        user.full_name = data.full_name
        user.is_verified = True
        user.is_active = True
    else:
        user = User(
            phone_number=phone,
            full_name=data.full_name,
            role=UserRole.DRIVER,
            is_verified=True,
            is_active=True,
        )
        db.add(user)
        db.flush()
        db.add(Wallet(user_id=user.id, balance=0.0))

    default_capacity = {"bike": 1, "auto": 3, "car": 4}
    capacity = data.passenger_capacity or default_capacity.get(data.vehicle_type.value, 1)

    driver = Driver(
        user_id=user.id,
        vehicle_type=data.vehicle_type,
        passenger_capacity=capacity,
        vehicle_number=data.vehicle_number.upper(),
        license_number=f"ADMIN-{phone[-6:]}",
        license_expiry=datetime.utcnow() + timedelta(days=365 * 3),
        is_approved=True,
        is_online=False,
        current_latitude=8.264,
        current_longitude=77.138,
    )
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return _serialize_admin_driver(driver, db)


@router.post("/drivers/{driver_id}/approve", response_model=DriverResponse)
async def approve_driver(
    driver_id: UUID,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Approve a driver application"""
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    
    driver.is_approved = True
    db.commit()
    db.refresh(driver)
    
    return DriverResponse.model_validate(driver)


@router.post("/drivers/{driver_id}/reject", response_model=dict)
async def reject_driver(
    driver_id: UUID,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Reject a driver application"""
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    
    db.delete(driver)
    db.commit()
    
    return {"message": "Driver application rejected"}


@router.get("/rides", response_model=List[RideResponse])
async def get_all_rides(
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all rides for admin view"""
    rides = db.query(Ride).order_by(Ride.created_at.desc()).limit(limit).offset(offset).all()
    return [serialize_ride(ride, db) for ride in rides]


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all users for admin view"""
    users = db.query(User).order_by(User.created_at.desc()).limit(limit).offset(offset).all()
    return [UserResponse.model_validate(user) for user in users]


@router.get("/recent-activity", response_model=List[dict])
async def get_recent_activity(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get recent rides and user registrations for admin dashboard"""
    from datetime import datetime

    activities = []

    recent_rides = db.query(Ride).order_by(Ride.created_at.desc()).limit(10).all()
    for ride in recent_rides:
        customer = db.query(User).filter(User.id == ride.customer_id).first()
        serialized = serialize_ride(ride, db)
        activities.append({
            "type": "ride",
            "title": f"Ride {ride.status.value}",
            "detail": f"{serialized.pickup_address} → {serialized.dropoff_address}",
            "timestamp": (ride.completed_at or ride.created_at).isoformat(),
            "status": ride.status.value,
            "fare": ride.actual_fare or ride.estimated_fare,
            "customer_name": customer.full_name if customer else "Unknown",
        })

    recent_users = db.query(User).order_by(User.created_at.desc()).limit(5).all()
    for user in recent_users:
        activities.append({
            "type": "user",
            "title": f"New {user.role.value} registered",
            "detail": user.full_name,
            "timestamp": user.created_at.isoformat(),
        })

    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    return activities[:15]


@router.get("/stats", response_model=dict)
async def get_admin_stats(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics"""
    total_users = db.query(User).count()
    total_drivers = db.query(Driver).count()
    approved_drivers = db.query(Driver).filter(Driver.is_approved == True).count()
    online_drivers = db.query(Driver).filter(Driver.is_online == True).count()
    total_rides = db.query(Ride).count()
    completed_rides = db.query(Ride).filter(Ride.status == "completed").count()
    from sqlalchemy import func
    from app.models.ride import RideStatus, PaymentStatus

    cash_total = (
        db.query(func.coalesce(func.sum(Ride.actual_fare), 0.0))
        .filter(Ride.status == RideStatus.COMPLETED)
        .scalar()
        or 0.0
    )
    
    return {
        "total_users": total_users,
        "total_drivers": total_drivers,
        "approved_drivers": approved_drivers,
        "online_drivers": online_drivers,
        "total_rides": total_rides,
        "completed_rides": completed_rides,
        "cash_collected": round(float(cash_total), 2),
    }


@router.get("/cash", response_model=dict)
async def get_cash_collection(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Monitor cash collected from completed rides (no payment gateway)"""
    from sqlalchemy import func
    from datetime import datetime, timedelta
    from app.models.ride import RideStatus

    completed = (
        db.query(Ride)
        .filter(Ride.status == RideStatus.COMPLETED)
        .order_by(Ride.completed_at.desc())
        .limit(100)
        .all()
    )
    total = sum((r.actual_fare or r.estimated_fare or 0) for r in completed)
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today = [r for r in completed if r.completed_at and r.completed_at >= today_start]
    today_total = sum((r.actual_fare or r.estimated_fare or 0) for r in today)

    return {
        "total_cash_collected": round(total, 2),
        "today_cash_collected": round(today_total, 2),
        "completed_rides": len(completed),
        "today_rides": len(today),
        "rides": [
            {
                "id": str(r.id),
                "pickup": r.pickup_address,
                "dropoff": r.dropoff_address,
                "amount": r.actual_fare or r.estimated_fare,
                "payment": "cash",
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in completed[:50]
        ],
    }
