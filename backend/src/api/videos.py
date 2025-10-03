from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from services.video_service import VideoService
from services.ball_tracking_service import BallTrackingService
from models.trajectory import Trajectory
from api.auth import get_current_user_optional
from models.user import User
from config import UPLOAD_DIR, MAX_UPLOAD_SIZE_BYTES, ALLOWED_VIDEO_EXTENSIONS
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Upload a video file for ball tracking analysis"""
    # Validate file type
    file_ext = file.filename.lower()[file.filename.rfind('.'):] if '.' in file.filename else ''
    if file_ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"
        )

    # Read and validate file size
    content = await file.read()
    file_size = len(content)

    if file_size > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_UPLOAD_SIZE_BYTES / (1024*1024):.0f}MB"
        )

    # Save file with unique ID
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"

    try:
        with open(file_path, "wb") as f:
            f.write(content)
        logger.info(f"Video uploaded: {file_path}")
    except Exception as e:
        logger.error(f"Failed to save video file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save video file")

    # Create video record
    video_service = VideoService(db)
    user_id = current_user.id if current_user else "anonymous"

    video = video_service.create_video(
        user_id=user_id,
        filename=file.filename,
        file_path=str(file_path),
        file_size=file_size
    )

    return {
        "id": video.id,
        "filename": file_path.name,  # Return stored filename with UUID
        "original_filename": video.filename,
        "file_path": video.file_path,
        "status": video.status,
        "upload_date": video.upload_date.isoformat() if video.upload_date else None,
        "file_size": video.file_size
    }

@router.post("/{video_id}/track")
async def track_video(
    video_id: str,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Start ball tracking analysis on a video"""
    video_service = VideoService(db)
    video = video_service.get_video(video_id)

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Check if tracking is already in progress
    if video.status == "processing":
        raise HTTPException(status_code=409, detail="Tracking already in progress")

    # Check if already processed
    if video.status == "processed":
        return {
            "video_id": video_id,
            "status": "processed",
            "message": "Video already processed. Retrieve trajectory using /trajectory endpoint"
        }

    # Update status to processing
    video_service.update_video_status(video_id, "processing")
    logger.info(f"Starting ball tracking for video: {video_id}")

    try:
        # Start tracking
        tracking_service = BallTrackingService()
        trajectory_data = tracking_service.track_ball(video.file_path)

        # Save trajectory
        additional_data = {
            "stumps_position": trajectory_data.get("stumps_position"),
            "bowler_position": trajectory_data.get("bowler_position"),
            "batter_position": trajectory_data.get("batter_position"),
            "lbw_analysis": trajectory_data.get("lbw_analysis", []),
            "debug_info": trajectory_data.get("debug_info", {}),
            "pitch_info": trajectory_data.get("pitch_info")
        }

        trajectory = Trajectory(
            video_id=video_id,
            points=trajectory_data["points"],
            timestamps=trajectory_data["timestamps"],
            confidence_score=trajectory_data["confidence_score"],
            ball_detected=trajectory_data["ball_detected"],
            additional_data=additional_data
        )
        db.add(trajectory)
        db.commit()

        # Update video status
        video_service.update_video_status(video_id, "processed")
        logger.info(f"Ball tracking completed for video: {video_id}")

        return {
            "video_id": video_id,
            "status": "processed",
            "ball_detected": trajectory_data["ball_detected"],
            "confidence_score": trajectory_data["confidence_score"],
            "processing_time": trajectory_data.get("processing_time", 0)
        }

    except Exception as e:
        logger.error(f"Ball tracking failed for video {video_id}: {e}")
        video_service.update_video_status(video_id, "failed")
        raise HTTPException(status_code=500, detail=f"Tracking failed: {str(e)}")

@router.get("/{video_id}/trajectory")
async def get_trajectory(
    video_id: str,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get trajectory data for a processed video"""
    trajectory = db.query(Trajectory).filter(Trajectory.video_id == video_id).first()

    if not trajectory:
        raise HTTPException(
            status_code=404,
            detail="Trajectory not found. Video may not be processed yet."
        )

    # Parse additional data
    additional_data = {}
    if hasattr(trajectory, 'additional_data') and trajectory.additional_data:
        try:
            additional_data = trajectory.additional_data if isinstance(trajectory.additional_data, dict) else {}
        except Exception as e:
            logger.warning(f"Failed to parse additional_data: {e}")
            additional_data = {}

    return {
        "video_id": video_id,
        "points": trajectory.points,
        "timestamps": trajectory.timestamps,
        "confidence_score": trajectory.confidence_score,
        "ball_detected": trajectory.ball_detected,
        # Additional DRS data
        "stumps_position": additional_data.get("stumps_position"),
        "bowler_position": additional_data.get("bowler_position"),
        "batter_position": additional_data.get("batter_position"),
        "lbw_analysis": additional_data.get("lbw_analysis", []),
        "pitch_info": additional_data.get("pitch_info")
    }
