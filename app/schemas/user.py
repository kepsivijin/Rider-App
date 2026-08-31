from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.models.user import UserRole


class UserCreate(BaseModel):
    phone_number: str = Field(..., min_length=10, max_length=15)
    full_name: str = Field(..., min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    role: UserRole = UserRole.CUSTOMER


class UserLogin(BaseModel):
    phone_number: str = Field(..., min_length=10, max_length=15)
    otp: str = Field(..., min_length=4, max_length=6)


class UserResponse(BaseModel):
    id: UUID
    phone_number: str
    email: Optional[str]
    full_name: str
    role: UserRole
    profile_photo_url: Optional[str]
    is_verified: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class OTPRequest(BaseModel):
    phone_number: str = Field(..., min_length=10, max_length=15)


class OTPVerify(BaseModel):
    phone_number: str
    otp: str
