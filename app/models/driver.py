from sqlalchemy import Column, String, Boolean, DateTime, Float, Integer, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class VehicleType(str, enum.Enum):
    BIKE = "bike"
    AUTO = "auto"
    CAR = "car"


class Driver(Base):
    __tablename__ = "drivers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    vehicle_type = Column(Enum(VehicleType), nullable=False, default=VehicleType.BIKE)
    passenger_capacity = Column(Integer, nullable=False, default=1)
    vehicle_number = Column(String(50), nullable=False)
    license_number = Column(String(50), nullable=False)
    license_expiry = Column(DateTime, nullable=False)
    vehicle_photo_url = Column(String(500), nullable=True)
    license_photo_url = Column(String(500), nullable=True)
    is_approved = Column(Boolean, default=False)
    is_online = Column(Boolean, default=False)
    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)
    rating = Column(Float, default=5.0)
    total_rides = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="driver_profile")
    rides = relationship("Ride", foreign_keys="Ride.driver_id", back_populates="driver")
