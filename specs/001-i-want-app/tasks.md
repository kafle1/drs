# Tasks: Ball Tracking DRS Web App

**Input**: Design documents from `/specs/001-i-want-app/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → SUCCESS: Plan loaded from /Users/nirajkafle/Desktop/niraj/dev-projects/drs/specs/001-i-want-app/plan.md
   → Extract: Python 3.11, FastAPI, React, OpenCV, Three.js, PostgreSQL, web structure
2. Load optional design documents:
   → data-model.md: Extract entities User, Video, Trajectory, ReviewSession → model tasks
   → contracts/: api.yaml → contract test tasks
   → research.md: Extract decisions → setup tasks
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests
   → Core: models, services, endpoints
   → Integration: DB, middleware, logging
   → Polish: unit tests, performance, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All contracts have tests? Yes
   → All entities have models? Yes
   → All endpoints implemented? Planned
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Web app**: `backend/src/`, `frontend/src/`
- Backend: Python/FastAPI
- Frontend: React/Three.js

## Phase 3.1: Setup
- [ ] T001 Create backend project structure in backend/ per implementation plan
- [ ] T002 Create frontend project structure in frontend/ per implementation plan
- [ ] T003 Initialize Python backend with FastAPI, OpenCV, PostgreSQL dependencies
- [ ] T004 Initialize React frontend with Three.js, Material-UI dependencies
- [ ] T005 [P] Configure linting and formatting tools (black, eslint)

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [ ] T006 [P] Contract test POST /videos/upload in backend/tests/contract/test_videos_upload.py
- [ ] T007 [P] Contract test POST /videos/{id}/track in backend/tests/contract/test_videos_track.py
- [ ] T008 [P] Contract test GET /videos/{id}/trajectory in backend/tests/contract/test_videos_trajectory.py
- [ ] T009 [P] Contract test POST /reviews in backend/tests/contract/test_reviews_post.py
- [ ] T010 [P] Contract test GET /reviews/{id} in backend/tests/contract/test_reviews_get.py
- [ ] T011 [P] Integration test video upload and tracking in backend/tests/integration/test_video_workflow.py
- [ ] T012 [P] Integration test review creation in backend/tests/integration/test_review_workflow.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [ ] T013 [P] User model in backend/src/models/user.py
- [ ] T014 [P] Video model in backend/src/models/video.py
- [ ] T015 [P] Trajectory model in backend/src/models/trajectory.py
- [ ] T016 [P] ReviewSession model in backend/src/models/review_session.py
- [ ] T017 [P] VideoService in backend/src/services/video_service.py
- [ ] T018 [P] BallTrackingService in backend/src/services/ball_tracking_service.py
- [ ] T019 [P] ReviewService in backend/src/services/review_service.py
- [ ] T020 POST /videos/upload endpoint in backend/src/api/videos.py
- [ ] T021 POST /videos/{id}/track endpoint in backend/src/api/videos.py
- [ ] T022 GET /videos/{id}/trajectory endpoint in backend/src/api/videos.py
- [ ] T023 POST /reviews endpoint in backend/src/api/reviews.py
- [ ] T024 GET /reviews/{id} endpoint in backend/src/api/reviews.py
- [ ] T025 Video upload component in frontend/src/components/VideoUpload.js
- [ ] T026 Trajectory viewer component in frontend/src/components/TrajectoryViewer.js
- [ ] T027 Review interface component in frontend/src/components/ReviewInterface.js

## Phase 3.4: Integration
- [ ] T028 Connect models to PostgreSQL database
- [ ] T029 Auth middleware for JWT authentication
- [ ] T030 Request/response logging
- [ ] T031 CORS and security headers
- [ ] T032 File storage integration (AWS S3 or local)
- [ ] T033 Frontend API client integration

## Phase 3.5: Polish
- [ ] T034 [P] Unit tests for ball tracking in backend/tests/unit/test_ball_tracking.py
- [ ] T035 [P] Unit tests for trajectory calculation in backend/tests/unit/test_trajectory.py
- [ ] T036 Performance tests for video processing (<60s)
- [ ] T037 [P] Update API documentation
- [ ] T038 [P] Frontend unit tests
- [ ] T039 End-to-end test following quickstart.md
- [ ] T040 Docker containerization for deployment

## Dependencies
- Tests (T006-T012) before implementation (T013-T027)
- Models (T013-T016) before services (T017-T019)
- Services before endpoints (T020-T024)
- Backend before frontend integration (T028-T033)
- Implementation before polish (T034-T040)

## Parallel Example
```
# Launch T006-T012 together:
Task: "Contract test POST /videos/upload in backend/tests/contract/test_videos_upload.py"
Task: "Contract test POST /videos/{id}/track in backend/tests/contract/test_videos_track.py"
Task: "Contract test GET /videos/{id}/trajectory in backend/tests/contract/test_videos_trajectory.py"
Task: "Contract test POST /reviews in backend/tests/contract/test_reviews_post.py"
Task: "Contract test GET /reviews/{id} in backend/tests/contract/test_reviews_get.py"
Task: "Integration test video upload and tracking in backend/tests/integration/test_video_workflow.py"
Task: "Integration test review creation in backend/tests/integration/test_review_workflow.py"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Commit after each task
- Focus on MVP: video upload, ball tracking, trajectory view, basic review
- Avoid: vague tasks, same file conflicts

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
   - Each contract file → contract test task [P]
   - Each endpoint → implementation task

2. **From Data Model**:
   - Each entity → model creation task [P]
   - Relationships → service layer tasks

3. **From User Stories**:
   - Each story → integration test [P]
   - Quickstart scenarios → validation tasks

4. **Ordering**:
   - Setup → Tests → Models → Services → Endpoints → Polish
   - Dependencies block parallel execution

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All contracts have corresponding tests
- [x] All entities have model tasks
- [x] All tests come before implementation
- [x] Parallel tasks truly independent
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
