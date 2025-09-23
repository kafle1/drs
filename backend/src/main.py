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
import os

# Setup logging
logger = setup_logging()

# Create database tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.warning(f"Database table creation failed (might already exist): {e}")

app = FastAPI(title="DRS Ball Tracking API", version="1.0.0")

# Mount static files
uploads_path = os.path.join(os.path.dirname(__file__), "../../uploads")
if os.path.exists(uploads_path):
    app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")
else:
    logger.warning(f"Uploads directory not found at: {uploads_path}")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
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
    return {"message": "DRS Ball Tracking API"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting DRS Ball Tracking API server")
    uvicorn.run(app, host="0.0.0.0", port=8000)
