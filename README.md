# Study Pilot 🧭

**Study Pilot** is a personal academic workflow assistant that connects to Moodle and monitors university courses, assignments, deadlines, workflows, documents, and approval processes.

Running **100% locally** on Windows with **zero recurring infrastructure or API costs**.

---

## Architecture Overview

```
Study Pilot/
├── backend/                  # FastAPI & Python backend
│   ├── app/
│   │   ├── main.py           # FastAPI app entry point (port 8000)
│   │   ├── config.py         # Local paths & environment configuration
│   │   ├── database.py       # SQLite engine (SQLModel)
│   │   ├── models/           # Course, MoodleActivity, SyncRun, AgentActivityLog, SystemSetting
│   │   ├── api/              # REST routers: dashboard, courses, activities, moodle, logs, settings
│   │   ├── moodle/           # Playwright scraper & unified sync engine
│   │   └── cli.py            # CLI entrypoint for Windows Task Scheduler
│   ├── tests/                # Pytest test suite
│   ├── run_sync.py           # Standalone sync executable
│   └── requirements.txt
├── frontend/                 # Next.js 15 App Router frontend (port 3000)
│   ├── src/
│   │   ├── app/              # Dashboard, Courses, Activities, Calendar, Activity Log, Settings
│   │   ├── components/       # Layout, badges, buttons, live sync polling
│   │   └── lib/api.ts        # Zero-overhead typed fetch client
│   └── package.json
├── data/                     # Local data (gitignored)
│   ├── studypilot.db         # SQLite database
│   ├── moodle_auth/          # storage_state.json (browser session cookies)
│   └── logs/                 # Diagnostic DOM snapshots and sync logs
└── setup_windows_scheduler.ps1 # One-click Windows Task Scheduler registration
```

---

## Core Features (Phase 1 Foundation)

1. **Deterministic Moodle Monitoring**:
   - Discovers active semester courses automatically.
   - Extracts assignments, quizzes, files, forums, and course materials into `MoodleActivity`.
   - Strict deadline distinction: only assignments with verified due dates appear in the global calendar; no-deadline items remain in course archives.
2. **Zero-Credential-Leak Authentication**:
   - Launches a real headed browser window (`headless=False`) for one-time login.
   - Supports any university login mechanism: Microsoft 365, Google Workspace, Shibboleth, SAML, Duo, or 2FA.
   - Saves authenticated browser state to `data/moodle_auth/storage_state.json` without ever storing passwords.
3. **Dual Execution Architecture**:
   - **Manual Sync**: Click **[Check Moodle Now]** on the dashboard to trigger an immediate check with live status polling.
   - **Automatic Daily Sync**: Uses **Windows Task Scheduler** as the primary 24-hour scheduler, running `backend/run_sync.py` independently of whether the web server or browser is open.
4. **Complete Audit Trail**:
   - Every sync records a `SyncRun` table entry (`courses_found`, `activities_found`, `new_items_found`, `status`, `trigger`).
   - Granular event logs in `AgentActivityLog`.

---

## Quick Start

### 1. Run the Backend (FastAPI)
```powershell
cd backend
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
```
API Documentation will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 2. Run the Frontend (Next.js)
```powershell
cd frontend
npm run dev
```
Dashboard will be available at [http://localhost:3000](http://localhost:3000).

---

## Connecting Your Moodle Account

1. Open the dashboard at [http://localhost:3000](http://localhost:3000) and navigate to **Settings**.
2. Enter your university Moodle base URL (e.g. `https://moodle.your-university.edu`) and click **Save URL**.
3. Click **Open Login Browser**.
4. In the dedicated browser window that appears, log into your university account normally (including 2FA/SSO).
5. Once you reach your Moodle dashboard, close the browser or let Study Pilot automatically capture the session state.
6. Return to the dashboard and click **Check Moodle Now** to run your first synchronization.

---

## Setting Up Automatic 24-Hour Sync (Windows Task Scheduler)

To register the daily automatic check in Windows:
```powershell
powershell -ExecutionPolicy Bypass -File .\setup_windows_scheduler.ps1
```
This registers a daily task named `StudyPilot_Moodle_DailySync` that executes at 04:00 AM every day using your local virtual environment.

---

## Running Backend Tests

```powershell
.\backend\.venv\Scripts\pytest
```
All models, endpoint functions, and deadline classification logic are verified by the automated test suite.
