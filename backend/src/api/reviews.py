from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from services.review_service import ReviewService
from api.auth import get_current_user
from models.user import User
from pydantic import BaseModel
from typing import List, Optional
import uuid

router = APIRouter()

class DecisionModel(BaseModel):
    type: str
    outcome: str
    timestamp: float
    confidence: float

class CreateReviewRequest(BaseModel):
    video_id: str
    decisions: List[DecisionModel]
    notes: Optional[str] = None

@router.post("/")
async def create_review(
    request: CreateReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    review_service = ReviewService(db)
    user_id = current_user.id

    review = review_service.create_review(
        video_id=request.video_id,
        user_id=user_id,
        decisions=[decision.dict() for decision in request.decisions],
        notes=request.notes
    )

    return {
        "id": review.id,
        "video_id": str(review.video_id),
        "created_at": review.created_at
    }

@router.get("/{review_id}")
async def get_review(
    review_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    review_service = ReviewService(db)
    review = review_service.get_review(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # Check if review belongs to current user
    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this review")

    return {
        "id": str(review.id),
        "video_id": str(review.video_id),
        "decisions": review.decisions,
        "notes": review.notes,
        "created_at": review.created_at
    }
