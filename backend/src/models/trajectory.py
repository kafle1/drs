from sqlalchemy import Column, Float, Boolean, ForeignKey, Text, DateTime, String, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from database import Base

class Trajectory(Base):
    __tablename__ = "trajectories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id = Column(String, ForeignKey("videos.id"), unique=True, nullable=False)
    points = Column(JSON)  # Array of {x, y, z, t}
    timestamps = Column(JSON)  # Array of timestamps
    confidence_score = Column(Float)
    ball_detected = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Trajectory(id={self.id}, video_id={self.video_id}, confidence={self.confidence_score})>"
