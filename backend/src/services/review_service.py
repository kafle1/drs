from sqlalchemy.orm import Session
from models.review_session import ReviewSession
from models.video import Video
import uuid
from typing import Optional, List, Dict

class ReviewService:
    def __init__(self, db: Session):
        self.db = db

    def create_review(self, video_id: str, user_id: str,
                     decisions: List[Dict], notes: Optional[str] = None) -> ReviewSession:
        review = ReviewSession(
            video_id=video_id,
            user_id=user_id,
            decisions=decisions,
            notes=notes
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review

    def get_review(self, review_id: str) -> Optional[ReviewSession]:
        return self.db.query(ReviewSession).filter(ReviewSession.id == review_id).first()

    def get_video_reviews(self, video_id: str) -> List[ReviewSession]:
        return self.db.query(ReviewSession).filter(ReviewSession.video_id == video_id).all()

    def update_review(self, review_id: str, decisions: List[Dict], notes: Optional[str] = None):
        review = self.get_review(review_id)
        if review:
            review.decisions = decisions
            if notes is not None:
                review.notes = notes
            self.db.commit()
