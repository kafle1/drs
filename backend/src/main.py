from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.videos import router as videos_router
from api.reviews import router as reviews_router
from api.auth import router as auth_router
from database import engine, Base
from models.user import User
from models.video import Video
from models.trajectory import Trajectory
from models.review_session import ReviewSession
from logging_config import setup_logging
from config import CORS_ORIGINS, UPLOAD_DIR, HOST, PORT

# Setup logging
logger = setup_logging()

# Create database tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Database table creation failed: {e}")

app = FastAPI(
    title="DRS Ball Tracking API",
    version="1.0.0",
    description="Cricket Decision Review System with Ball Tracking"
)

# Mount static files for video uploads
if UPLOAD_DIR.exists():
    app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
    logger.info(f"Mounted uploads directory: {UPLOAD_DIR}")
else:
    logger.warning(f"Uploads directory not found: {UPLOAD_DIR}")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(videos_router, prefix="/videos", tags=["videos"])
app.include_router(reviews_router, prefix="/reviews", tags=["reviews"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {
        "message": "DRS Ball Tracking API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting DRS Ball Tracking API server on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
