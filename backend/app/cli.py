import sys
import argparse
import logging
from .database import init_db
from .moodle.sync_service import run_moodle_sync

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("studypilot.cli")

def main():
    parser = argparse.ArgumentParser(description="Study Pilot CLI Runner")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    sync_parser = subparsers.add_parser("sync", help="Run Moodle synchronization")
    sync_parser.add_argument(
        "--trigger",
        choices=["scheduled", "manual"],
        default="scheduled",
        help="Trigger source for this sync run (default: scheduled)"
    )

    args = parser.parse_args()

    if args.command == "sync":
        logger.info(f"Executing Moodle synchronization (trigger={args.trigger})...")
        init_db()
        try:
            sync_run = run_moodle_sync(trigger=args.trigger)
            if sync_run.status == "completed":
                logger.info(
                    f"Sync completed successfully. Courses found: {sync_run.courses_found}, "
                    f"Activities found: {sync_run.activities_found}, New: {sync_run.new_items_found}"
                )
                sys.exit(0)
            else:
                is_auth_error = any(
                    k in (sync_run.error_message or "").lower()
                    for k in ["expired", "not found", "permission", "login"]
                )
                if is_auth_error:
                    logger.warning(
                        f"Authentication required: {sync_run.error_message}. "
                        "Background check paused safely. Please sign in via Study Pilot Settings."
                    )
                    # Exit cleanly for scheduled OS task so it doesn't trigger OS error alerts
                    sys.exit(0 if args.trigger == "scheduled" else 1)
                else:
                    logger.error(f"Sync ended with status: {sync_run.status}. Error: {sync_run.error_message}")
                    sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to execute sync: {e}", exc_info=True)
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
