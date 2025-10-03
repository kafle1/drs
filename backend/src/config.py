"""
Configuration management for DRS Backend
"""
import os
from pathlib import Path
from typing import List

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./src/drs.db")

# Upload Configuration
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR.parent / "uploads")))
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "500"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# Allowed video formats
ALLOWED_VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi', '.mkv', '.webm']

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# CORS Configuration
CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "http://localhost:3000")
CORS_ORIGINS: List[str] = [origin.strip() for origin in CORS_ORIGINS_STR.split(",")]

# Video Processing Configuration
MAX_PROCESSING_FRAMES = int(os.getenv("MAX_PROCESSING_FRAMES", "300"))
VIDEO_FPS_LIMIT = int(os.getenv("VIDEO_FPS_LIMIT", "60"))

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = Path(os.getenv("LOG_FILE", str(BASE_DIR / "logs" / "app.log")))
LOG_FILE.parent.mkdir(exist_ok=True, parents=True)

# Ball Tracking Configuration
BALL_TRACKING = {
    "min_radius": 3,
    "max_radius": 15,
    "min_confidence": 0.3,
    "max_velocity_px_per_sec": 200,
    "prediction_tolerance_px": 50,
}

# Pitch Configuration (meters)
PITCH_CONFIG = {
    "length_m": 22.0,  # 22 yards
    "width_m": 3.05,   # 10 feet
    "camera_height_m": 1.5,
    "camera_angle_deg": 15,
    "focal_length_px": 1000,
}

# Stump Detection Configuration
STUMP_CONFIG = {
    "min_area": 50,
    "max_area": 5000,
    "distance_threshold": 50,
}
