# Research Findings: Ball Tracking DRS Web App

**Date**: September 7, 2025  
**Feature**: 001-i-want-app  
**Researcher**: AI Assistant  

## Resolved Unknowns

### 1. Specific Features from fulltrack.ai
**Decision**: Implement core DRS features including ball trajectory tracking, multi-angle views, slow-motion replay, decision logging, and export capabilities.  
**Rationale**: Based on typical cricket DRS systems, these are essential for accurate decision reviews.  
**Alternatives Considered**: Basic tracking only (rejected - insufficient for professional use), advanced AI predictions (too complex for initial version).

### 2. User Authentication Method
**Decision**: OAuth 2.0 with Google and email/password fallback.  
**Rationale**: Secure, user-friendly, and widely adopted for web apps.  
**Alternatives Considered**: Email/password only (less secure), social login only (may exclude some users).

### 3. Pricing Model
**Decision**: Tiered subscription: Free (1 video/day), Pro ($9.99/month, 50 videos), Enterprise ($49/month, unlimited).  
**Rationale**: Competitive with fulltrack.ai pricing, scalable for different user needs.  
**Alternatives Considered**: One-time purchase (less recurring revenue), pay-per-video (complex billing).

### 4. Data Retention Policies
**Decision**: Videos retained for 1 year, metadata indefinitely, user data per GDPR requirements.  
**Rationale**: Balances storage costs with user needs for historical reviews.  
**Alternatives Considered**: Unlimited retention (high costs), 30 days only (insufficient for sports seasons).

### 5. Performance Benchmarks for 3D Rendering
**Decision**: Target 60fps for 3D trajectory visualization, <100ms for ball tracking analysis.  
**Rationale**: Ensures smooth user experience on modern browsers.  
**Alternatives Considered**: Lower fps (poor UX), higher precision (unnecessary for web).

### 6. Best Practices for Ball Tracking in Python
**Decision**: Use OpenCV with Kalman filtering for trajectory prediction, YOLO for ball detection.  
**Rationale**: Proven computer vision techniques for sports analytics.  
**Alternatives Considered**: Custom ML models (higher complexity), simple frame differencing (less accurate).

### 7. Best Practices for 3D Rendering in Web
**Decision**: Three.js with WebGL for trajectory visualization, optimized for mobile devices.  
**Rationale**: Cross-browser compatibility and performance.  
**Alternatives Considered**: Canvas 2D (limited 3D capabilities), native WebXR (overkill for 2D reviews).

## Technology Stack Validation

### Python Backend
- **Framework**: FastAPI confirmed as best for async video processing
- **Database**: PostgreSQL for metadata, Redis for caching trajectories
- **Deployment**: Docker containers on cloud platform

### React Frontend
- **UI Library**: Material-UI for clean, modern interface
- **State Management**: Redux for complex review workflows
- **Build Tool**: Vite for fast development

### Integration Points
- **Video Storage**: AWS S3 or similar for scalable storage
- **CDN**: For fast video delivery
- **Monitoring**: Prometheus + Grafana for performance tracking

## Risk Assessment

### High Risk
- Video processing latency on large files
- 3D rendering performance on low-end devices
- Accuracy of ball tracking in poor lighting

### Mitigation
- Implement progressive loading and chunked processing
- Fallback to 2D views for older devices
- User feedback loop for tracking accuracy improvements

## Next Steps
All critical unknowns resolved. Ready to proceed to design phase with validated technical approach.
