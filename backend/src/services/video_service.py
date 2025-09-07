from sqlalchemy.orm import Session
from models.video import Video
from models.user import User
import uuid
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class VideoService:
    def __init__(self, db: Session):
        self.db = db

    def create_video(self, user_id: str, filename: str, file_path: str,
                    duration: Optional[float] = None, resolution: Optional[str] = None,
                    file_size: Optional[int] = None) -> Video:
        logger.info(f"Creating video for user {user_id}: {filename}")
        video = Video(
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            duration=duration,
            resolution=resolution,
            file_size=file_size
        )
        self.db.add(video)
        self.db.commit()
        self.db.refresh(video)
        logger.info(f"Video created with ID: {video.id}")
        return video

    def get_video(self, video_id: str) -> Optional[Video]:
        logger.debug(f"Retrieving video: {video_id}")
        return self.db.query(Video).filter(Video.id == video_id).first()

    def update_video_status(self, video_id: str, status: str):
        logger.info(f"Updating video {video_id} status to: {status}")
        video = self.get_video(video_id)
        if video:
            video.status = status
            if status == "processing":
                from datetime import datetime
                video.processing_started_at = datetime.utcnow()
            elif status == "processed":
                video.processing_completed_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"Video {video_id} status updated successfully")
        else:
            logger.warning(f"Video {video_id} not found for status update")

    def get_user_videos(self, user_id: uuid.UUID):
        return self.db.query(Video).filter(Video.user_id == user_id).all()
