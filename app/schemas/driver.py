from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.models.driver import VehicleType


class DriverCreate(BaseModel):
    vehicle_type: VehicleType
    vehicle_number: str = Field(..., min_length=3, max_length=50)
    license_number: str = Field(..., min_length=3, max_length=50)
    license_expiry: datetime
    vehicle_photo_url: Optional[str] = None
    license_photo_url: Optional[str] = None
    passenger_capacity: int = Field(1, ge=1, le=8)


class AdminCreateDriver(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    phone_number: str = Field(..., min_length=10, max_length=15)
    vehicle_type: VehicleType
    passenger_capacity: int = Field(..., ge=1, le=8)
    vehicle_number: str = Field(..., min_length=3, max_length=50)


class DriverUpdate(BaseModel):
    vehicle_number: Optional[str] = None
    vehicle_photo_url: Optional[str] = None
    license_photo_url: Optional[str] = None
    is_online: Optional[bool] = None
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None


class DriverResponse(BaseModel):
    id: UUID
    user_id: UUID
    vehicle_type: VehicleType
    passenger_capacity: int = 1
    vehicle_number: str
    license_number: str
    license_expiry: datetime
    vehicle_photo_url: Optional[str]
    license_photo_url: Optional[str]
    is_approved: bool
    is_online: bool
    current_latitude: Optional[float]
    current_longitude: Optional[float]
    rating: float
    total_rides: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class AdminDriverResponse(DriverResponse):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None


class DriverLocationUpdate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
