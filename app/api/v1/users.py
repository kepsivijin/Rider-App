from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user's profile"""
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    full_name: str = None,
    email: str = None,
    profile_photo_url: str = None,
    fcm_token: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    if full_name:
        current_user.full_name = full_name
    if email:
        current_user.email = email
    if profile_photo_url:
        current_user.profile_photo_url = profile_photo_url
    if fcm_token:
        current_user.fcm_token = fcm_token
    
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)
