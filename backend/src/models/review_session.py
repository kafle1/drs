from sqlalchemy import Column, Text, ForeignKey, DateTime, String, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from database import Base

class ReviewSession(Base):
    __tablename__ = "review_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id = Column(String, ForeignKey("videos.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    decisions = Column(JSON)  # Array of decisions
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ReviewSession(id={self.id}, video_id={self.video_id})>"
