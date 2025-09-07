from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from services.video_service import VideoService
from services.ball_tracking_service import BallTrackingService
from models.trajectory import Trajectory
from api.auth import get_current_user
from models.user import User
import uuid
import os
from pathlib import Path

router = APIRouter()

UPLOAD_DIR = Path("/Users/nirajkafle/Desktop/niraj/dev-projects/drs/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate file type
    if not file.filename.lower().endswith(('.mp4', '.mov', '.avi')):
        raise HTTPException(status_code=400, detail="Invalid file type")

    # Validate file size (max 500MB)
    file_size = 0
    content = await file.read()
    file_size = len(content)

    if file_size > 500 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")

    # Save file
    file_path = UPLOAD_DIR / f"{uuid.uuid4()}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(content)

    # Create video record
    video_service = VideoService(db)
    user_id = current_user.id

    video = video_service.create_video(
        user_id=user_id,
        filename=file.filename,
        file_path=str(file_path),
        file_size=file_size
    )

    return {
        "id": video.id,
        "status": video.status,
        "upload_date": video.upload_date
    }

@router.post("/{video_id}/track")
async def track_video(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    video_service = VideoService(db)
    video = video_service.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Check if video belongs to current user
    if video.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this video")

    if video.status == "processing":
        raise HTTPException(status_code=409, detail="Tracking already in progress")

    # Update status to processing
    video_service.update_video_status(video_id, "processing")

    # Start tracking (in real implementation, this would be async/background)
    tracking_service = BallTrackingService()
    trajectory_data = tracking_service.track_ball(video.file_path)

    # Save trajectory
    trajectory = Trajectory(
        video_id=video_id,
        points=trajectory_data["points"],
        timestamps=trajectory_data["timestamps"],
        confidence_score=trajectory_data["confidence_score"],
        ball_detected=trajectory_data["ball_detected"]
    )
    db.add(trajectory)
    db.commit()

    # Update video status
    video_service.update_video_status(video_id, "processed")

    return {
        "video_id": video_id,
        "status": "processing",
        "estimated_completion": "2025-09-07T12:00:00Z"  # Placeholder
    }

@router.get("/{video_id}/trajectory")
async def get_trajectory(
    video_id: str,
    db: Session = Depends(get_db)
):
    try:
        video_uuid = uuid.UUID(video_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid video ID")

    trajectory = db.query(Trajectory).filter(Trajectory.video_id == video_uuid).first()
    if not trajectory:
        raise HTTPException(status_code=404, detail="Trajectory not available")

    return {
        "video_id": video_id,
        "points": trajectory.points,
        "timestamps": trajectory.timestamps,
        "confidence_score": trajectory.confidence_score
    }
