# GitHub Copilot Instructions for DRS Project

## Project Overview
Web-based Decision Review System (DRS) for ball tracking in sports. Upload videos, process with computer vision, visualize 3D trajectories, and conduct review sessions.

## Architecture
- **Backend**: FastAPI with service layer pattern (`api/` routes → `services/` business logic → `models/` data)
- **Frontend**: React with component-based architecture using Material-UI
- **Data Flow**: Video Upload → Ball Tracking (OpenCV) → Trajectory Storage → 3D Visualization (Three.js)
- **Database**: SQLAlchemy ORM, SQLite for development, PostgreSQL for production

## Technology Stack
- **Backend**: Python 3.11, FastAPI, OpenCV, SQLAlchemy, PostgreSQL
- **Frontend**: React 18, Three.js, Material-UI, Axios
- **Infrastructure**: Docker, Redis (caching), Nginx (production proxy)

## Critical Development Workflows

### Getting Started
```bash
make setup              # Install deps, build containers, start services
make dev                # Run backend (port 8000) + frontend (port 3000)
make docker-up          # Start full containerized environment
```

### Testing & Quality
```bash
make test               # Run all tests (backend + frontend)
make test-backend       # Python tests with coverage
make test-frontend      # React tests
make lint               # Code formatting (black, isort, eslint)
```

### File Upload Pattern
- Videos stored in `uploads/` with UUID prefix: `{uuid}_{original_filename}`
- Validate file types: `.mp4`, `.mov`, `.avi` (max 500MB)
- Mount uploads volume in Docker for persistence

## Key Code Patterns

### Backend Service Layer
```python
# api/videos.py - Route handlers
@router.post("/upload")
async def upload_video(file: UploadFile = File(...), db: Session = Depends(get_db)):
    video_service = VideoService(db)
    video = video_service.create_video(user_id, filename, file_path, file_size)

# services/video_service.py - Business logic
class VideoService:
    def create_video(self, user_id, filename, file_path, file_size):
        # Validation, database operations, file handling
```

### Ball Tracking Implementation
```python
# services/ball_tracking_service.py
class BallTrackingService:
    def track_ball(self, video_path: str) -> Dict[str, Any]:
        # OpenCV video processing with Kalman filtering
        # Returns trajectory points with timestamps and 3D coordinates
```

### React Component Structure
```javascript
// App.js - Main orchestration
function App() {
  const [uploadedVideo, setUploadedVideo] = useState(null);
  const [trajectoryData, setTrajectoryData] = useState(null);
  // API calls, state management, component coordination
}
```

### Database Configuration
```python
# database.py
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./drs.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
```

## Project-Specific Conventions

### File Organization
- Feature branches use `specs/{branch-name}/` for documentation
- Backend: `src/{api,models,services}/` with `main.py` entry point
- Frontend: Standard `src/components/` structure
- Scripts in `scripts/` for automation (setup, feature management)

### API Patterns
- RESTful endpoints with `/videos`, `/reviews`, `/auth` prefixes
- File uploads use `UploadFile` with validation
- JWT auth middleware (currently optional in development)
- CORS configured for React dev server (`http://localhost:3000`)

### Error Handling
- HTTPException for API errors with descriptive messages
- File validation (type, size) before processing
- Database connection error handling in services

### Testing Approach
- Backend: pytest with async support and coverage reporting
- Frontend: React Testing Library
- Integration tests for API endpoints
- E2E tests with Cypress (planned)

## Integration Points

### Video Processing Pipeline
1. Upload video file with UUID naming
2. Extract frames using OpenCV
3. Apply ball detection algorithms (color thresholding, contour detection)
4. Kalman filtering for trajectory smoothing
5. Store trajectory data as JSON with timestamps and 3D coordinates

### 3D Visualization
- Three.js scene with trajectory points
- Interactive camera controls
- Real-time rendering of ball path
- Integration with video playback timing

### Database Models
- `Video`: File metadata, user association, processing status
- `Trajectory`: Ball position data with frame timestamps
- `ReviewSession`: Decision review workflow
- `User`: Authentication and permissions

## Performance Considerations
- Video processing is CPU-intensive; consider async processing
- Large video files (500MB limit) require efficient streaming
- Trajectory data cached in Redis for quick access
- 3D rendering optimized for smooth interaction

## Security Patterns
- File upload validation (type, size, content)
- JWT tokens for API authentication
- CORS properly configured for frontend origin
- Input sanitization in API endpoints

## Deployment Architecture
- Docker multi-stage builds (separate for backend/frontend)
- Nginx reverse proxy for production
- PostgreSQL with health checks
- Redis for caching layer
- Volume mounts for uploads and logs persistence

## Manual Additions
<!-- Add any project-specific instructions below this marker -->
<!-- Preserve this section between updates -->
