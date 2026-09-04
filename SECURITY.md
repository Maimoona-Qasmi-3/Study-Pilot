# Security Policy

## Reporting Security Vulnerabilities

Study Pilot takes the security and privacy of academic credentials and personal student data seriously. If you discover a security vulnerability or potential risk in this repository, please report it responsibly.

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please send a detailed report via email to:
- **Email**: `maimoonaqasmi4@gmail.com`
- **Subject**: `[SECURITY] Study Pilot Vulnerability Report`

### What to Include in Your Report
- A description of the vulnerability and its potential impact.
- Step-by-step instructions to reproduce the issue.
- Proof-of-concept code or network payloads, if available.
- Any suggested mitigations.

You will receive an acknowledgment within 48 hours, followed by an assessment and timeline for resolution.

---

## Security & Privacy Architecture

Study Pilot is designed with strict local-first privacy guarantees:

1. **Zero Password Storage**:
   - The application **never** prompts for, receives, or stores user passwords.
   - Authentication is performed directly by the user inside a native Microsoft Edge browser window via university Single Sign-On (SSO) and Multi-Factor Authentication (MFA).

2. **Isolated Local Session State**:
   - Browser cookies and local session storage are written to `data/moodle_auth/storage_state.json`.
   - The entire `data/` directory and all database files (`*.db`, `*.sqlite`) are strictly excluded from source control via `.gitignore`.
   - No telemetry, analytics, or session cookies are ever transmitted to external servers.

3. **Local Network Boundary**:
   - The FastAPI backend binds strictly to `127.0.0.1` (localhost).
   - Cross-Origin Resource Sharing (CORS) is configured explicitly for local frontend dev origins (`http://localhost:3000`, `http://127.0.0.1:3000`).
