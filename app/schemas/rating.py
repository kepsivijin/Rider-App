from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class RatingCreate(BaseModel):
    ride_id: UUID
    to_user_id: UUID
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)


class RatingResponse(BaseModel):
    id: UUID
    ride_id: UUID
    from_user_id: UUID
    to_user_id: UUID
    rating: int
    comment: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
