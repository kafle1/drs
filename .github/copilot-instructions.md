# GitHub Copilot Instructions for DRS Project

## Project Overview
This is a web-based Decision Review System (DRS) for ball tracking in sports, built with Python backend and React frontend.

## Technology Stack
- **Backend**: Python 3.11, FastAPI, PostgreSQL, OpenCV
- **Frontend**: React, Three.js, Material-UI
- **Infrastructure**: Docker, AWS S3, Redis

## Key Libraries and Frameworks
- **FastAPI**: For REST API development
- **OpenCV**: Computer vision for ball tracking
- **Three.js**: 3D visualization of trajectories
- **PostgreSQL**: Data persistence
- **React**: Frontend framework
- **Material-UI**: UI component library

## Development Principles
- Test-First Development (TDD)
- Library-First Architecture
- Clean, minimal, modern UI
- Robust core engine
- Cross-platform compatibility

## Recent Changes
- Added ball tracking with OpenCV
- Implemented 3D trajectory visualization with Three.js
- Created FastAPI backend structure
- Set up PostgreSQL data models

## Coding Standards
- Use type hints in Python
- Follow REST API conventions
- Implement proper error handling
- Write comprehensive tests
- Maintain clean, readable code

## Common Patterns
- Async/await for I/O operations
- Dependency injection in FastAPI
- Component-based React architecture
- JSON schemas for API contracts

## Performance Considerations
- Optimize video processing algorithms
- Implement caching for trajectory data
- Use lazy loading for large datasets
- Ensure responsive 3D rendering

## Security Best Practices
- Input validation and sanitization
- JWT authentication
- CORS configuration
- Secure file upload handling

## Testing Strategy
- Unit tests for individual functions
- Integration tests for API endpoints
- End-to-end tests for user workflows
- Performance tests for video processing

## Deployment
- Docker containerization
- CI/CD with GitHub Actions
- Cloud deployment on AWS/GCP
- Monitoring with Prometheus

## Manual Additions
<!-- Add any project-specific instructions below this marker -->
<!-- Preserve this section between updates -->
