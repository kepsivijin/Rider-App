from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    DRIVER = "driver"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String(15), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.CUSTOMER)
    password_hash = Column(String(255), nullable=True)
    profile_photo_url = Column(String(500), nullable=True)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    fcm_token = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    driver_profile = relationship("Driver", back_populates="user", uselist=False)
    customer_rides = relationship("Ride", foreign_keys="Ride.customer_id", back_populates="customer")
    wallet = relationship("Wallet", back_populates="user", uselist=False)
    ratings_given = relationship("Rating", foreign_keys="Rating.from_user_id", back_populates="from_user")
    ratings_received = relationship("Rating", foreign_keys="Rating.to_user_id", back_populates="to_user")
