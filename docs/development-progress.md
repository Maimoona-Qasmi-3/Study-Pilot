# Development Progress & Engineering Milestones

This log tracks the chronological development milestones, verified capabilities, and technical evolution of **Study Pilot**.

---

## Current Status: Phase 1 Complete (Live & Verified)

- **Total Courses Tracked**: 12 (6 Active Spring 2026 courses + 6 Archived Fall 2025 courses)
- **Total Activities Indexed**: 141 activities
- **Deadlines Monitored**: 55 activities with verified due dates
- **Test Suite Status**: 9/9 Pytest unit & integration tests passing (100%)
- **Frontend Build Status**: Zero TypeScript or linting errors (`npm run build` passing)

---

## Phase 1: Local Foundation & Moodle Synchronization (Completed)

### Milestone 1.1 — Environment & Project Scaffold
- [x] Initialized Git repository with strict `.gitignore` excluding runtime databases, secrets, and auth directories.
- [x] Configured Python 3.14 virtual environment with dependencies: `fastapi`, `uvicorn[standard]`, `sqlmodel`, `playwright`, `pytest`.
- [x] Scaffolded Next.js 15 App Router frontend with TypeScript, Tailwind CSS, and Lucide React icons.
- [x] Created `run_dev.ps1` orchestration script with explicit directory resolution for Windows paths containing spaces.

### Milestone 1.2 — Data Architecture & SQLite Models
- [x] Implemented `Course` model with active status toggling and default workflow bindings.
- [x] Implemented `MoodleActivity` generalized model covering assignments, quizzes, files, forums, and attendance.
- [x] Implemented `SyncRun` audit logging model recording execution duration, item counts, and status codes.
- [x] Implemented `AgentActivityLog` and `SystemSetting` key-value configuration models.
- [x] Configured SQLModel database engine with connection pooling and `expire_on_commit=False` for thread safety.

### Milestone 1.3 — FastAPI REST Services
- [x] Built `/api/dashboard` returning aggregated counts, active course tallies, and upcoming deadline metrics.
- [x] Built `/api/courses` with search, active/archived filtering, and workflow patch endpoints.
- [x] Built `/api/activities` supporting multi-faceted filtering (by course, type, deadline presence, and status).
- [x] Built `/api/activities/calendar/events` delivering time-sorted strict deadline events.
- [x] Built `/api/moodle/sync` and `/api/moodle/sync/status` for interactive manual synchronization.

### Milestone 1.4 — Microsoft SSO Authentication Engine
- [x] Built headed Playwright launcher using native Microsoft Edge channel (`msedge`).
- [x] Integrated Windows SSO feature flags enabling automatic single-sign-on without password prompts.
- [x] Solved Chromium file lock error 32 by utilizing an isolated persistent browser profile under `data/moodle_auth/edge_profile/`.
- [x] Implemented session health verification (`/api/moodle/auth/verify`) and automated session persistence to `storage_state.json`.

### Milestone 1.5 — University LMS Parser & Heuristics
- [x] Reverse-engineered Salim Habib University Moodle 4 DOM structure (`lms.shu.edu.pk`).
- [x] Targeted `/my/courses.php` to bypass personalized dashboard layout differences.
- [x] Built semester classification heuristic: parsed term codes (e.g., `2601-...` for Spring 2026 vs `2503-...` for Fall 2025) to automatically separate active from archived courses.
- [x] Parsed Moodle `.submissionstatustable` elements to reliably extract submission deadlines and submission states (`"Submitted for grading"` vs `"No attempt"`).

### Milestone 1.6 — Windows Native Automation
- [x] Created standalone CLI runner `backend/run_sync.py` and `backend/app/cli.py`.
- [x] Created PowerShell installer `setup_windows_scheduler.ps1` registering a daily 04:00 AM Task Scheduler job.

---

## Phase 2: Academic Workflow Engine & Document Generation (In Progress)

- [x] Architectural plan drafted and verified (`implementation_plan.md`).
- [ ] Implement `data/workspaces/{course_code}/{activity_slug}/` workspace directory generator.
- [ ] Add native Windows integration: "Open in VS Code" (`code <path>`) and "Open in File Explorer" (`explorer.exe <path>`).
- [ ] Build university lab manual and assignment report generator using `python-docx` (Cover page, code listings, evidence screenshots).
- [ ] Course-specific workflow bindings:
  - `CSC-103 (Object Oriented Programming)` -> Coding/C++ workspace
  - `ELE-205 (Digital Logic Design)` -> Circuit simulation workspace
  - `ENG-102 (Expository Writing)` -> Academic report workspace

---

## Phase 3: AI-Assisted Academic Workflow & Verification (Planned)

- [ ] Local zero-cost LLM integration (Ollama / local model) for code analysis and proofreading.
- [ ] Assignment rubric and instruction breakdown.
- [ ] Code syntax verification and test case generation.

---

## Phase 4: Approval & Staging Pipeline (Planned)

- [ ] Staging and review dashboard: inspect generated deliverables before submission.
- [ ] Safe submission verification: multi-factor human approval before any Moodle file upload.
