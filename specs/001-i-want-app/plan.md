# Implementation Plan: Ball Tracking DRS Web App

**Branch**: `001-i-want-app` | **Date**: September 7, 2025 | **Spec**: /Users/nirajkafle/Desktop/niraj/dev-projects/drs/specs/001-i-want-app/spec.md
**Input**: Feature specification from /Users/nirajkafle/Desktop/niraj/dev-projects/drs/specs/001-i-want-app/spec.md

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → SUCCESS: Spec loaded from /Users/nirajkafle/Desktop/niraj/dev-projects/drs/specs/001-i-want-app/spec.md
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Project Type: web (frontend + backend detected)
   → Structure Decision: Option 2 (web application)
3. Evaluate Constitution Check section below
   → No violations detected
   → Update Progress Tracking: Initial Constitution Check PASS
4. Execute Phase 0 → research.md
   → NEEDS CLARIFICATION resolved via research
5. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file
6. Re-evaluate Constitution Check section
   → No new violations
   → Update Progress Tracking: Post-Design Constitution Check PASS
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
8. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Primary requirement: Build a powerful web-based DRS system for ball tracking using phone videos, with clean modern UI and robust 3D rendering capabilities. Technical approach: Python backend with FastAPI, React frontend, OpenCV for tracking, Three.js for 3D visualization, PostgreSQL for data storage.

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI (backend), React (frontend), OpenCV (ball tracking), Three.js (3D rendering), PostgreSQL (storage)  
**Storage**: PostgreSQL for metadata, file system for video storage  
**Testing**: pytest for backend, Jest for frontend  
**Target Platform**: Web browsers (Chrome, Firefox, Safari)  
**Project Type**: web (frontend + backend)  
**Performance Goals**: Real-time ball tracking (<100ms latency), smooth 3D rendering (60fps), handle videos up to 4K resolution  
**Constraints**: Robust video processing, clean minimal modern UI, powerful core engine, handle edge cases like low-quality videos  
**Scale/Scope**: 10k concurrent users, 1M videos stored, 100GB storage

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 2 (backend, frontend)
- Using framework directly? Yes (FastAPI, React)
- Single data model? Yes (shared schemas)
- Avoiding patterns? Yes (no unnecessary abstractions)

**Architecture**:
- EVERY feature as library? Yes (ball_tracking, drs_engine, ui_components)
- Libraries listed: ball_tracking (video analysis), drs_engine (decision logic), ui_components (React components)
- CLI per library: Yes (command-line tools for each library)
- Library docs: llms.txt format planned

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? Yes
- Git commits show tests before implementation? Yes
- Order: Contract→Integration→E2E→Unit strictly followed? Yes
- Real dependencies used? Yes (actual video processing, not mocks)
- Integration tests for: new libraries, contract changes, shared schemas? Yes

**Observability**:
- Structured logging included? Yes
- Frontend logs → backend? Yes (unified logging stream)
- Error context sufficient? Yes

**Versioning**:
- Version number assigned? Yes (1.0.0)
- BUILD increments on every change? Yes
- Breaking changes handled? Yes (migration plan)

## Project Structure

### Documentation (this feature)
```
specs/001-i-want-app/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/
```

**Structure Decision**: Option 2 (web application) - Separate backend and frontend for scalability and modern UI.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context**:
   - Specific features from fulltrack.ai → research ball tracking best practices
   - Pricing model → research competitive pricing
   - User authentication method → research OAuth vs email/password
   - Data retention policies → research compliance requirements
   - Performance benchmarks for 3D rendering → research WebGL optimizations

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for ball tracking DRS web app"
   For each technology choice:
     Task: "Find best practices for {tech} in sports analytics domain"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Video: id, filename, upload_date, user_id, duration, resolution
   - Trajectory: id, video_id, points (JSON), timestamps
   - ReviewSession: id, video_id, user_id, decisions (JSON), created_at

2. **Generate API contracts** from functional requirements:
   - POST /api/videos/upload → upload video
   - POST /api/videos/{id}/track → initiate tracking
   - GET /api/videos/{id}/trajectory → get trajectory data
   - POST /api/reviews → create review session
   - Use OpenAPI 3.0 schema in /contracts/

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Upload video → integration test
   - Track ball → integration test
   - Review decision → integration test

5. **Update agent file incrementally**:
   - Run `/scripts/update-agent-context.sh copilot` for GitHub Copilot
   - Add new tech: OpenCV, Three.js, FastAPI
   - Preserve manual additions
   - Update recent changes
   - Keep under 150 lines
   - Output to .github/copilot-instructions.md

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, .github/copilot-instructions.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each contract → contract test task [P]
- Each entity → model creation task [P] 
- Each user story → integration test task
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Tests before implementation 
- Dependency order: Models before services before UI
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 25-30 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*No violations - design adheres to simplicity principles*

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [ ] Complexity deviations documented

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*