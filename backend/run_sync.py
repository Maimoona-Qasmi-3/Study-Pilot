import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.cli import main

if __name__ == "__main__":
    # Default to sync command if no argument given
    if len(sys.argv) == 1:
        sys.argv.extend(["sync", "--trigger", "scheduled"])
    main()
