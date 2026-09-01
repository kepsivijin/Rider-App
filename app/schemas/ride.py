from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.models.ride import RideStatus, PaymentMethod, PaymentStatus
from app.models.driver import VehicleType


class RideCreate(BaseModel):
    pickup_latitude: float = Field(..., ge=-90, le=90)
    pickup_longitude: float = Field(..., ge=-180, le=180)
    pickup_address: str = Field(..., min_length=3, max_length=500)
    dropoff_latitude: float = Field(..., ge=-90, le=90)
    dropoff_longitude: float = Field(..., ge=-180, le=180)
    dropoff_address: str = Field(..., min_length=3, max_length=500)
    payment_method: PaymentMethod = PaymentMethod.CASH
    vehicle_type: VehicleType = VehicleType.BIKE
    passenger_count: int = Field(1, ge=1, le=8)
    scheduled_at: Optional[datetime] = None


class RideUpdate(BaseModel):
    status: Optional[RideStatus] = None
    actual_fare: Optional[float] = None
    payment_status: Optional[PaymentStatus] = None
    payment_transaction_id: Optional[str] = None


class PickupOtpVerify(BaseModel):
    pickup_otp: str = Field(..., min_length=4, max_length=6)


class RideResponse(BaseModel):
    id: UUID
    customer_id: UUID
    driver_id: Optional[UUID]
    pickup_latitude: float
    pickup_longitude: float
    pickup_address: str
    dropoff_latitude: float
    dropoff_longitude: float
    dropoff_address: str
    status: RideStatus
    estimated_fare: float
    actual_fare: Optional[float]
    distance_km: float
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    payment_transaction_id: Optional[str]
    requested_at: datetime
    accepted_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    scheduled_at: Optional[datetime] = None
    created_at: datetime
    driver_name: Optional[str] = None
    driver_vehicle: Optional[str] = None
    driver_user_id: Optional[UUID] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    vehicle_type: Optional[str] = None
    passenger_count: int = 1
    driver_vehicle_type: Optional[str] = None
    driver_passenger_capacity: Optional[int] = None
    pickup_otp: Optional[str] = None
    pickup_verified: bool = False
    notification_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class NearbyDriverResponse(BaseModel):
    driver_id: UUID
    user_id: UUID
    full_name: str
    vehicle_type: str
    vehicle_number: str
    rating: float
    total_rides: int
    latitude: float
    longitude: float
    distance_km: float
