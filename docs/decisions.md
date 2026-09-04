# Architectural Decision Records (ADR)

This document records the critical architectural and engineering decisions made during the design and development of **Study Pilot**.

---

## ADR 01: Windows Task Scheduler as Primary Daily Scheduler vs In-Process APScheduler

### Problem
Study Pilot must reliably inspect university Moodle courses and check for upcoming deadlines once every 24 hours. However, as a local desktop-oriented assistant, the FastAPI web server and Next.js frontend are not guaranteed to remain running 24/7 on the user's personal Windows machine.

### Options Considered
1. **In-Process Python Scheduler (e.g. APScheduler / Celery / schedule)**: Run a background thread inside the FastAPI server process.
2. **OS-Native Scheduler (Windows Task Scheduler)**: Schedule a standalone Python CLI script (`run_sync.py`) via the Windows Task Scheduler service.
3. **Continuous Background Daemon / Windows Service**: Run a continuous Windows background service or system tray agent.

### Decision
Implement an OS-native **Windows Task Scheduler** task as the primary automated daily sync mechanism, triggering a standalone Python entrypoint (`run_sync.py sync --trigger scheduled`).

### Why
- Windows Task Scheduler is an OS-level subsystem that wakes or runs independently of whether any application server or browser is open.
- In-process schedulers like APScheduler immediately cease functioning the moment the user closes their terminal or shuts down the web server.
- Writing a custom Windows background service adds unnecessary complexity and requires elevated administrative daemon management, whereas Task Scheduler tasks can run seamlessly in user context.

### Trade-offs
- **Gained**: Complete reliability across server reboots and application closures; zero idle memory consumption between daily runs.
- **Sacrificed**: Platform specificity (tailored to Windows Task Scheduler via PowerShell script `setup_windows_scheduler.ps1`; will require `cron` or `systemd` if ported to Linux/macOS).

---

## ADR 02: Playwright with Microsoft Edge Channel & Windows SSO Flags vs Standard Chromium

### Problem
The university LMS (Salim Habib University - `lms.shu.edu.pk`) uses Microsoft 365 Single Sign-On (SSO) with Multi-Factor Authentication (MFA). Standard automated Chromium browsers lack access to the operating system's credential store, frequently getting rejected or trapped in complex verification screens. Furthermore, attempting to attach to the user's running Edge profile directory causes Windows file-lock errors (`ProcessSingleton lock error 32`).

### Options Considered
1. **Direct Credential Automation**: Request student username and password, then attempt to fill in Microsoft login forms via automation.
2. **Standard Headless Chromium**: Open Chromium and rely on standard cookie storage.
3. **Microsoft Edge (`channel="msedge"`) with Dedicated Profile & SSO Flags**: Launch Playwright using the native Microsoft Edge binary with Windows Single Sign-On flags and an isolated persistent profile directory (`data/moodle_auth/edge_profile/`).

### Decision
Adopt **Microsoft Edge (`channel="msedge"`)** with dedicated persistent profile storage and explicit SSO flags:
`--enable-features=msSingleSignOnOSForPrimaryAccountIsShared,msImplicitSignIn`

### Why
- Never handling user passwords eliminates critical security vulnerabilities and guarantees compliance with university IT policies.
- Native Edge utilizes the Windows Web Account Manager (WAM) and Windows Credential Manager, allowing automatic one-click Microsoft SSO authentication without MFA re-prompts.
- Using an isolated profile directory (`data/moodle_auth/edge_profile/`) eliminates the fatal `ProcessSingleton` lock conflict that occurs if the user already has Edge open for daily work.

### Trade-offs
- **Gained**: Seamless one-click SSO login; device trust and session tokens persist reliably; zero password handling.
- **Sacrificed**: Requires Microsoft Edge to be installed on the host operating system (standard on Windows 10/11).

---

## ADR 03: Unified Sync Engine Decoupled from Presentation Layer

### Problem
Synchronization can be invoked in two completely different contexts:
1. Interactively via the Web UI ("Check Moodle Now" button on the Next.js dashboard).
2. Headlessly via the Windows Task Scheduler background CLI command.
Duplicating scraping or parsing logic across these two entry points would lead to synchronization discrepancies, maintenance overhead, and brittle error handling.

### Options Considered
1. **API-Only Trigger**: Have the CLI make an HTTP POST request to the local FastAPI server.
2. **Duplicated Scripts**: One script for the CLI and one endpoint function inside FastAPI.
3. **Unified Service Class (`MoodleSyncService`)**: A pure Python service class in `backend/app/moodle/sync_service.py` that receives a database session and a trigger tag (`"manual"` or `"scheduled"`).

### Decision
Build a single, decoupled **`MoodleSyncService`** class that is invoked identically by the FastAPI endpoint (`backend/app/api/moodle.py`) and the CLI script (`backend/app/cli.py` / `run_sync.py`).

### Why
- An API-only trigger would fail if the web server was closed during the scheduled 04:00 AM check.
- Duplicating logic violates DRY principles and creates high risk of parser divergence.
- The unified service receives a SQLModel session directly, performs the full crawl, updates the database, writes audit logs (`SyncRun`), and returns structured stats regardless of caller.

### Trade-offs
- **Gained**: 100% logic parity between manual clicks and automated background checks; testable independently in Pytest without starting a web server.
- **Sacrificed**: Background execution inside FastAPI requires careful thread management (`asyncio.create_task` or FastAPI `BackgroundTasks`) and database session isolation.

---

## ADR 04: Generalized `MoodleActivity` Schema with Strict Deadline Segregation

### Problem
Universities host diverse content types on Moodle courses: assignments, quizzes, syllabus files, slide decks, discussion forums, and attendance trackers. Treating every item as an "Assignment" creates confusion, while creating separate tables for each activity type causes schema bloat. Furthermore, displaying items without due dates on the calendar clutters scheduling.

### Options Considered
1. **Narrow "Assignment" Table**: Only record items that accept file submissions.
2. **Polymorphic Table Hierarchy**: Separate tables for `Assignment`, `Quiz`, `Resource`, `Forum`, etc.
3. **Single Generalized `MoodleActivity` Table with Strict Deadline Tagging**: One unified table with an `activity_type` enum (`assignment`, `quiz`, `resource`, `file`, `forum`, `attendance`, `other`) and explicit `has_deadline: bool` and `due_date: Optional[datetime]` columns.

### Decision
Implement the unified **`MoodleActivity`** schema, indexing `has_deadline` and `due_date`.

### Why
- Accommodates all Moodle activity types discovered across 12 university courses under a unified query model.
- Allows the UI to cleanly separate the **Global Calendar** (strictly items where `has_deadline == True`) from general course resources and reference files.
- Simplifies filter queries in the UI (by course, type, deadline status, or completion state).

### Trade-offs
- **Gained**: Flexible, future-proof schema; single table for full course indexing; high query performance on indexed date fields.
- **Sacrificed**: Activity-specific metadata (e.g. quiz time limits vs assignment file submission formats) must be stored in generalized columns or structured JSON fields.

---

## ADR 05: Local-First Zero-Cost Architecture (SQLite + SQLModel + Next.js)

### Problem
Academic workflow management is inherently personal. Introducing cloud infrastructure (AWS/GCP, managed PostgreSQL, Redis, Docker containers, paid scraping APIs) would impose recurring subscription costs on a student project and expose private academic data to third-party servers.

### Options Considered
1. **Cloud-Hosted SaaS**: Next.js on Vercel, Supabase PostgreSQL, Redis queue, cloud Playwright instances.
2. **Local Docker Compose**: Containerized PostgreSQL, Redis, FastAPI, and Next.js.
3. **Native Local-First Architecture**: Standalone Python virtual environment with embedded SQLite (SQLModel) and Next.js running directly on the host Windows machine.

### Decision
Build a completely native **local-first architecture** using embedded SQLite and direct local process orchestration (`run_dev.ps1`).

### Why
- **Zero Recurring Cost**: Exactly \$0/month infrastructure, database, and API expenses.
- **Data Privacy**: Academic records, assignment briefs, and session cookies stay strictly on the local machine.
- **Simplicity**: No Docker daemon overhead, container networking latency, or database port collisions.
- **Portability**: The entire state resides in the `data/` folder, easily backed up or migrated.

### Trade-offs
- **Gained**: Zero cost, zero privacy risk, instant startup, lightweight resource footprint (<200MB RAM).
- **Sacrificed**: Cannot be accessed remotely from a mobile phone without a tunnel (e.g. Tailscale or ngrok).
