from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.user import UserCreate, OTPRequest, OTPVerify, TokenResponse, UserResponse
from app.services.sms import send_otp, verify_otp
from app.utils.phone import normalize_phone

router = APIRouter()


@router.post("/send-otp")
async def request_otp(request: OTPRequest):
    """Send OTP to phone number"""
    phone = normalize_phone(request.phone_number)
    otp = await send_otp(phone)

    return {
        "message": "OTP sent successfully",
        "phone_number": phone,
        "otp": otp,
        "dev_hint": "Use OTP 123456 in development" if otp == "123456" else None,
    }


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp_and_login(
    request: OTPVerify,
    db: Session = Depends(get_db)
):
    """Verify OTP and login/register user"""
    phone = normalize_phone(request.phone_number)
    otp = request.otp.strip()

    if not verify_otp(phone, otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP. In dev mode use 123456 after Send OTP."
        )

    user = db.query(User).filter(User.phone_number == phone).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Please register first."
        )
    
    user.is_verified = True
    db.commit()
    
    access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    existing_user = db.query(User).filter(User.phone_number == normalize_phone(user_data.phone_number)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )

    phone = normalize_phone(user_data.phone_number)
    user = User(
        phone_number=phone,
        full_name=user_data.full_name,
        email=user_data.email,
        role=user_data.role
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    wallet = Wallet(user_id=user.id, balance=0.0)
    db.add(wallet)
    db.commit()
    
    return UserResponse.model_validate(user)
