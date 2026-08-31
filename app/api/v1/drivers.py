from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.api.dependencies import get_current_user, get_current_driver
from app.models.user import User
from app.models.driver import Driver
from app.schemas.driver import DriverCreate, DriverResponse, DriverUpdate, DriverLocationUpdate

router = APIRouter()


@router.post("/register", response_model=DriverResponse)
async def register_driver(
    driver_data: DriverCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register as a driver"""
    existing_driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
    if existing_driver:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already registered as a driver"
        )
    
    driver = Driver(
        user_id=current_user.id,
        vehicle_type=driver_data.vehicle_type,
        vehicle_number=driver_data.vehicle_number,
        license_number=driver_data.license_number,
        license_expiry=driver_data.license_expiry,
        vehicle_photo_url=driver_data.vehicle_photo_url,
        license_photo_url=driver_data.license_photo_url,
        passenger_capacity=driver_data.passenger_capacity or 1,
        is_approved=False
    )
    
    db.add(driver)
    db.commit()
    db.refresh(driver)
    
    return DriverResponse.model_validate(driver)


@router.get("/me", response_model=DriverResponse)
async def get_my_driver_profile(
    current_user: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """Get current driver's profile"""
    driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver profile not found"
        )
    
    return DriverResponse.model_validate(driver)


@router.patch("/me", response_model=DriverResponse)
async def update_driver_profile(
    driver_data: DriverUpdate,
    current_user: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """Update driver profile"""
    driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver profile not found"
        )
    
    for key, value in driver_data.model_dump(exclude_unset=True).items():
        setattr(driver, key, value)
    
    db.commit()
    db.refresh(driver)
    
    return DriverResponse.model_validate(driver)


@router.post("/location", response_model=dict)
async def update_location(
    location: DriverLocationUpdate,
    current_user: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """Update driver's current location"""
    driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver profile not found"
        )
    
    driver.current_latitude = location.latitude
    driver.current_longitude = location.longitude
    
    db.commit()
    
    return {
        "message": "Location updated successfully",
        "latitude": location.latitude,
        "longitude": location.longitude
    }


@router.post("/toggle-online", response_model=dict)
async def toggle_online_status(
    is_online: bool,
    current_user: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """Toggle driver online/offline status"""
    driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver profile not found"
        )
    
    if not driver.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Driver profile is not approved yet"
        )
    
    driver.is_online = is_online
    db.commit()
    
    return {
        "message": f"Driver is now {'online' if is_online else 'offline'}",
        "is_online": is_online
    }


@router.get("/{driver_id}", response_model=DriverResponse)
async def get_driver_by_id(
    driver_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get driver details by ID"""
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    
    return DriverResponse.model_validate(driver)
