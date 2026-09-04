import os
from pathlib import Path

# Base Paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
MOODLE_AUTH_DIR = DATA_DIR / "moodle_auth"
STORAGE_STATE_FILE = MOODLE_AUTH_DIR / "storage_state.json"
EDGE_PROFILE_DIR = MOODLE_AUTH_DIR / "edge_profile"
BROWSER_PROFILE_DIR = EDGE_PROFILE_DIR
WORKSPACES_DIR = DATA_DIR / "workspaces"
LOGS_DIR = DATA_DIR / "logs"
DATABASE_FILE = DATA_DIR / "studypilot.db"

# Ensure runtime directories exist
for directory in [DATA_DIR, MOODLE_AUTH_DIR, EDGE_PROFILE_DIR, WORKSPACES_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_FILE}")

# App defaults
DEFAULT_SYNC_INTERVAL_HOURS = int(os.getenv("DEFAULT_SYNC_INTERVAL_HOURS", "24"))
