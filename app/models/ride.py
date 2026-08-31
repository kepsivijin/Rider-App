from sqlalchemy import Column, String, Float, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class RideStatus(str, enum.Enum):
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    STARTED = "started"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    ONLINE = "online"
    WALLET = "wallet"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    REFUNDED = "refunded"


class Ride(Base):
    __tablename__ = "rides"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=True)
    
    pickup_latitude = Column(Float, nullable=False)
    pickup_longitude = Column(Float, nullable=False)
    pickup_address = Column(String(500), nullable=False)
    
    dropoff_latitude = Column(Float, nullable=False)
    dropoff_longitude = Column(Float, nullable=False)
    dropoff_address = Column(String(500), nullable=False)
    
    status = Column(Enum(RideStatus), nullable=False, default=RideStatus.REQUESTED)
    estimated_fare = Column(Float, nullable=False)
    actual_fare = Column(Float, nullable=True)
    distance_km = Column(Float, nullable=False)
    vehicle_type = Column(String(20), nullable=False, default="bike")
    passenger_count = Column(Integer, nullable=False, default=1)
    
    payment_method = Column(Enum(PaymentMethod), nullable=False, default=PaymentMethod.CASH)
    payment_status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    payment_transaction_id = Column(String(255), nullable=True)
    
    requested_at = Column(DateTime, default=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    customer = relationship("User", foreign_keys=[customer_id], back_populates="customer_rides")
    driver = relationship("Driver", foreign_keys=[driver_id], back_populates="rides")
    rating = relationship("Rating", back_populates="ride", uselist=False)
