# Changelog

All notable changes to **Study Pilot** are documented in this file.
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and [Conventional Commits](https://www.conventionalcommits.org/).

---

## [0.3.0] - 2026-09-05

### Added
- **Academic Workspace Engine**: Idempotent directory generator creating `data/workspaces/{course}/{activity}/` with `src/`, `evidence/`, `output/`, and `workspace.json`.
- **Workflow Profile System**: Modular workflow profiles for `cpp_coding`, `python_scripting`, `digital_logic`, `academic_writing`, `linear_algebra`, and `generic_lab` with course heuristic bindings.
- **Isolated Native Windows Launchers**: Secure, validated process launchers for VS Code (`code <path>`), Windows File Explorer, and Windows Terminal (`wt.exe` / PowerShell).
- **Deterministic DOCX Report Generator**: University report compiler using `python-docx` that embeds raw Moodle instructions, monospaced code listings, and evidence screenshots without external AI dependencies.
- **Workspace REST APIs**: Full backend suite under `/api/workspaces/*` for initialization, inspection, OS launching, report compilation, and downloads.
- **Frontend Workspace Integration**: Full workspace controls on the Next.js Activities page with initialization modal, workflow picker, and one-click tool launchers.
- **SSO Expiration Guard**: Added graceful authentication expiration detection for Windows Task Scheduler background runs.
- **Phase 3 Specification**: Comprehensive architecture document for zero-cost local AI assistance via Ollama (`docs/phase3-architecture.md`).

---

## [0.2.0] - 2026-09-04

### Added
- **Real LMS Parser**: Reverse-engineered SHU-LMS DOM with automatic semester code detection (`2601` Spring 2026 vs `2503` Fall 2025).
- **Deadline Extraction**: Accurate parsing of `.submissionstatustable` for due dates, cutoff dates, and current submission states.
- **Native Microsoft Edge SSO**: Support for Windows Single Sign-On and Multi-Factor Authentication without saving passwords.
- **Live Sync Engine**: Discovered and indexed 12 courses and 141 activities with 55 strict deadlines.
- **Audit Logging**: Recorded all crawler actions in `SyncRun` and `AgentActivityLog`.

### Changed
- Refactored Moodle crawler to use Microsoft Edge channel with Windows Credential Manager integration.
- Switched sync scheduler to Windows Task Scheduler for autonomous 24-hour background execution.

---

## [0.1.0] - 2026-09-03

### Added
- **Project Foundation**: Initialized Next.js 15 App Router frontend and FastAPI backend.
- **Data Models**: Defined `Course`, `MoodleActivity`, `SyncRun`, and `SystemSetting` using SQLModel.
- **REST APIs**: Implemented dashboard statistics, course filtering, activity views, and calendar feeds.
- **Automated Tests**: Pytest test suite covering database models and API endpoints.
