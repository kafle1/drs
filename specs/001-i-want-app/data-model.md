# Data Model: Ball Tracking DRS Web App

**Date**: September 7, 2025  
**Feature**: 001-i-want-app  

## Entities

### User
- **id**: UUID (primary key)
- **email**: String (unique, required)
- **name**: String (required)
- **created_at**: DateTime (auto)
- **subscription_tier**: Enum (free, pro, enterprise)
- **oauth_provider**: String (optional)

**Relationships**: One-to-many with Video, ReviewSession

### Video
- **id**: UUID (primary key)
- **user_id**: UUID (foreign key to User)
- **filename**: String (required)
- **file_path**: String (required)
- **upload_date**: DateTime (auto)
- **duration**: Float (seconds)
- **resolution**: String (e.g., "1920x1080")
- **file_size**: Integer (bytes)
- **status**: Enum (uploaded, processing, processed, failed)
- **processing_started_at**: DateTime (optional)
- **processing_completed_at**: DateTime (optional)

**Relationships**: One-to-one with Trajectory, One-to-many with ReviewSession

**Validation Rules**:
- file_size <= 500MB
- duration <= 300 seconds
- resolution in ["720p", "1080p", "4K"]

### Trajectory
- **id**: UUID (primary key)
- **video_id**: UUID (foreign key to Video, unique)
- **points**: JSON (array of {x: float, y: float, z: float, t: float})
- **timestamps**: JSON (array of timestamps)
- **confidence_score**: Float (0-1)
- **ball_detected**: Boolean
- **created_at**: DateTime (auto)

**Relationships**: One-to-one with Video

**Validation Rules**:
- confidence_score >= 0.5 for valid trajectories
- points array length matches timestamps

### ReviewSession
- **id**: UUID (primary key)
- **video_id**: UUID (foreign key to Video)
- **user_id**: UUID (foreign key to User)
- **decisions**: JSON (array of {type: string, outcome: string, timestamp: float, confidence: float})
- **notes**: Text (optional)
- **created_at**: DateTime (auto)
- **updated_at**: DateTime (auto)

**Relationships**: Many-to-one with Video, Many-to-one with User

**Validation Rules**:
- decisions array not empty
- decision types in ["lbw", "run_out", "caught", "other"]

## State Transitions

### Video Status
- uploaded → processing (on upload complete)
- processing → processed (on tracking success)
- processing → failed (on tracking error)
- processed → processing (on re-analysis request)

### Review Session
- created → in_progress (on first decision)
- in_progress → completed (on final decision)
- completed → revised (on edit)

## Database Schema
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    subscription_tier VARCHAR(20) DEFAULT 'free',
    oauth_provider VARCHAR(50)
);

CREATE TABLE videos (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration FLOAT,
    resolution VARCHAR(20),
    file_size BIGINT,
    status VARCHAR(20) DEFAULT 'uploaded',
    processing_started_at TIMESTAMP,
    processing_completed_at TIMESTAMP
);

CREATE TABLE trajectories (
    id UUID PRIMARY KEY,
    video_id UUID REFERENCES videos(id) UNIQUE,
    points JSONB,
    timestamps JSONB,
    confidence_score FLOAT,
    ball_detected BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE review_sessions (
    id UUID PRIMARY KEY,
    video_id UUID REFERENCES videos(id),
    user_id UUID REFERENCES users(id),
    decisions JSONB,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Indexes
- videos(user_id, upload_date DESC)
- trajectories(video_id)
- review_sessions(video_id, created_at DESC)
- review_sessions(user_id, created_at DESC)
