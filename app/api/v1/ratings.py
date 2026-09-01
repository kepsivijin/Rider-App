from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.rating import Rating
from app.models.ride import Ride, RideStatus
from app.models.driver import Driver
from app.schemas.rating import RatingCreate, RatingResponse

router = APIRouter()


@router.post("", response_model=RatingResponse)
@router.post("/", response_model=RatingResponse)
async def create_rating(
    rating_data: RatingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a rating for a completed ride"""
    ride = db.query(Ride).filter(Ride.id == rating_data.ride_id).first()
    if not ride:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride not found"
        )

    if ride.status != RideStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can only rate completed rides"
        )
    
    if ride.customer_id != current_user.id:
        driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
        if not driver or ride.driver_id != driver.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to rate this ride"
            )

    if not ride.driver_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No driver assigned to this ride"
        )

    driver = db.query(Driver).filter(Driver.id == ride.driver_id).first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Driver not found")

    expected_driver_user_id = driver.user_id
    if rating_data.to_user_id != expected_driver_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid driver to rate for this ride"
        )
    
    existing_rating = db.query(Rating).filter(
        Rating.ride_id == rating_data.ride_id,
        Rating.from_user_id == current_user.id
    ).first()
    
    if existing_rating:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already rated this ride"
        )
    
    rating = Rating(
        ride_id=rating_data.ride_id,
        from_user_id=current_user.id,
        to_user_id=rating_data.to_user_id,
        rating=rating_data.rating,
        comment=rating_data.comment
    )
    
    db.add(rating)
    db.flush()
    
    to_user_ratings = db.query(Rating).filter(Rating.to_user_id == rating_data.to_user_id).all()
    avg_rating = sum(r.rating for r in to_user_ratings) / len(to_user_ratings)
    
    driver_profile = db.query(Driver).filter(Driver.user_id == rating_data.to_user_id).first()
    if driver_profile:
        driver_profile.rating = round(avg_rating, 2)
    
    db.commit()
    db.refresh(rating)
    
    return RatingResponse.model_validate(rating)


@router.get("/user/{user_id}", response_model=List[RatingResponse])
async def get_user_ratings(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ratings received by a user"""
    ratings = db.query(Rating).filter(Rating.to_user_id == user_id).order_by(Rating.created_at.desc()).all()
    return [RatingResponse.model_validate(rating) for rating in ratings]


@router.get("/ride/{ride_id}", response_model=List[RatingResponse])
async def get_ride_ratings(
    ride_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ratings for a specific ride"""
    ratings = db.query(Rating).filter(Rating.ride_id == ride_id).all()
    return [RatingResponse.model_validate(rating) for rating in ratings]
