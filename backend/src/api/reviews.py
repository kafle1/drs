from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from services.review_service import ReviewService
from api.auth import get_current_user_optional
from models.user import User
from pydantic import BaseModel
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)
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
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Create a new review for a video"""
    review_service = ReviewService(db)
    user_id = current_user.id if current_user else "anonymous"

    try:
        review = review_service.create_review(
            video_id=request.video_id,
            user_id=user_id,
            decisions=[decision.dict() for decision in request.decisions],
            notes=request.notes
        )

        logger.info(f"Review created: {review.id} for video: {request.video_id}")

        return {
            "id": review.id,
            "video_id": review.video_id,
            "created_at": review.created_at.isoformat() if review.created_at else None
        }
    except Exception as e:
        logger.error(f"Failed to create review: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create review: {str(e)}")

@router.get("/{review_id}")
async def get_review(
    review_id: str,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get a review by ID"""
    review_service = ReviewService(db)
    review = review_service.get_review(review_id)

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    return {
        "id": review.id,
        "video_id": review.video_id,
        "decisions": review.decisions,
        "notes": review.notes,
        "created_at": review.created_at.isoformat() if review.created_at else None
    }
