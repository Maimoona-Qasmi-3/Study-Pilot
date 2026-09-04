import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from playwright.sync_api import sync_playwright
from ..config import STORAGE_STATE_FILE, MOODLE_AUTH_DIR

logger = logging.getLogger("studypilot.moodle.auth")

def is_session_saved() -> bool:
    """Checks whether an authenticated session file exists."""
    return STORAGE_STATE_FILE.exists()

def launch_interactive_login(moodle_url: str, timeout_seconds: int = 300) -> Dict[str, Any]:
    """
    Launches a real headed browser window so the user can authenticate
    using their university's real login system (SSO, Microsoft 365, Google, 2FA).
    Once the user successfully reaches an authenticated page (such as /my/),
    or once the user finishes and closes, the session state is preserved.
    """
    MOODLE_AUTH_DIR.mkdir(parents=True, exist_ok=True)

    if not moodle_url:
        return {"success": False, "message": "Moodle URL is not configured"}

    logger.info(f"Launching interactive login browser for: {moodle_url}")

    with sync_playwright() as p:
        # Launch headed browser
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto(moodle_url, timeout=60000)

            # Wait for user to navigate to an authenticated dashboard
            # Moodle typically lands on /my/, /my/courses.php, or has a user menu
            logger.info("Awaiting user login in the opened browser window...")

            # Wait up to timeout_seconds for typical Moodle post-login indicators
            try:
                page.wait_for_url("**/my/**", timeout=timeout_seconds * 1000)
                logger.info("Successfully detected authenticated Moodle dashboard (/my/)!")
            except Exception:
                # If university dashboard URL doesn't contain /my/, wait for page load / user interaction
                logger.info("Timeout or custom URL detected; capturing current session state...")

            # Ensure page is stable
            page.wait_for_timeout(3000)

            # Save authenticated state (cookies, localStorage)
            context.storage_state(path=str(STORAGE_STATE_FILE))
            logger.info(f"Session saved successfully to {STORAGE_STATE_FILE}")

            return {
                "success": True,
                "message": "Moodle session captured successfully!",
                "storage_state_path": str(STORAGE_STATE_FILE)
            }

        except Exception as e:
            logger.error(f"Interactive login failed: {e}")
            return {"success": False, "message": str(e)}
        finally:
            browser.close()

def verify_session(moodle_url: str) -> Dict[str, Any]:
    """
    Tests whether the saved storage_state.json is still valid
    without opening a visual browser.
    """
    if not is_session_saved():
        return {"valid": False, "message": "No saved session found. Please log in first."}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context(storage_state=str(STORAGE_STATE_FILE))
            page = context.new_page()
            target_url = moodle_url.rstrip("/") + "/my/"
            response = page.goto(target_url, timeout=30000)

            # Check if redirected back to login page
            current_url = page.url.lower()
            is_login_page = "login" in current_url

            if response and response.ok and not is_login_page:
                return {"valid": True, "message": "Session is active and valid"}
            else:
                return {"valid": False, "message": "Session expired or redirected to login"}
        except Exception as e:
            return {"valid": False, "message": f"Verification error: {str(e)}"}
        finally:
            browser.close()
