import time
import logging
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Optional
from playwright.sync_api import sync_playwright, Error as PlaywrightError
from ..config import STORAGE_STATE_FILE, BROWSER_PROFILE_DIR, MOODLE_AUTH_DIR

logger = logging.getLogger("studypilot.moodle.auth")

# Module state for interactive login tracking
_login_progress: Dict[str, Any] = {
    "is_logging_in": False,
    "status": "idle",  # idle, in_progress, success, failed
    "message": "Ready",
    "last_updated": 0,
}

def get_login_progress() -> Dict[str, Any]:
    """Returns the current state of the interactive login for frontend polling."""
    return dict(_login_progress)

def is_session_saved() -> bool:
    """Checks whether an authenticated session file exists."""
    return STORAGE_STATE_FILE.exists()

def _check_if_moodle_authenticated(page, moodle_base_url: str) -> bool:
    """
    Determines if the current page has successfully authenticated back into Moodle.
    Verifies:
      1. Not on Microsoft login domain (login.microsoftonline.com, live.com)
      2. Back on university Moodle domain
      3. Not on the login page (/login/index.php)
      4. Contains Moodle dashboard indicators or user menu
    """
    try:
        current_url = page.url.lower()

        # If still on Microsoft SSO domains, user is still authenticating or completing MFA
        if any(ms_domain in current_url for ms_domain in ["microsoft", "live.com", "msft", "windows"]):
            return False

        # If on the initial Moodle login page, authentication has not yet occurred
        if "/login/" in current_url and "/my" not in current_url:
            return False

        # Check domain match
        parsed_base = urllib.parse.urlparse(moodle_base_url)
        base_host = parsed_base.netloc.lower()

        if base_host in current_url:
            # Check for post-login indicators:
            # /my/, /my/courses.php, or Moodle user menu/profile elements
            if "/my" in current_url or "/course/" in current_url:
                return True

            # Check DOM for authenticated elements
            user_elem = page.query_selector(
                '.usermenu, .userbutton, [data-region="usermenu"], a[href*="logout.php"], a[href*="/user/profile.php"]'
            )
            if user_elem:
                return True

        return False
    except Exception as e:
        logger.debug(f"Error checking authentication state: {e}")
        return False

def launch_interactive_login(moodle_url: str, timeout_seconds: int = 300) -> Dict[str, Any]:
    """
    Launches a real headed Playwright browser session for Microsoft SSO authentication.
    
    Flow:
      1. Opens Moodle in a persistent browser profile.
      2. If on the login page, automatically detects and clicks 'Sign in with Microsoft'.
      3. User completes Microsoft credentials and MFA manually if prompted,
         or Microsoft automatically authenticates the user via cached session.
      4. Playwright detects when Microsoft redirects back to an authenticated Moodle page.
      5. Saves storage_state.json locally under data/moodle_auth/.
      6. Closes the browser window and reports success.
    """
    global _login_progress

    MOODLE_AUTH_DIR.mkdir(parents=True, exist_ok=True)
    BROWSER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    if not moodle_url:
        _login_progress = {
            "is_logging_in": False,
            "status": "failed",
            "message": "Moodle URL is not configured. Please set it in Settings.",
            "last_updated": time.time(),
        }
        return {"success": False, "message": "Moodle URL is not configured."}

    _login_progress = {
        "is_logging_in": True,
        "status": "in_progress",
        "message": "Launching browser window for Microsoft SSO...",
        "last_updated": time.time(),
    }
    logger.info(f"Starting Microsoft SSO interactive login for: {moodle_url}")

    with sync_playwright() as p:
        # Launch persistent browser context using Microsoft Edge with Windows SSO flags
        edge_args = [
            "--enable-features=msSingleSignOnOSForPrimaryAccountIsShared,msImplicitSignIn",
            "--auth-server-allowlist=*.microsoftonline.com,*.live.com,*.office.com",
            "--no-first-run",
            "--no-default-browser-check",
            "--start-maximized",
        ]

        try:
            logger.info("Launching real Microsoft Edge (channel='msedge')...")
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(BROWSER_PROFILE_DIR),
                channel="msedge",
                headless=False,
                no_viewport=True,
                args=edge_args,
            )
        except Exception as edge_err:
            logger.warning(f"Could not launch Edge ({edge_err}), falling back to Chromium...")
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(BROWSER_PROFILE_DIR),
                headless=False,
                no_viewport=True,
                args=["--start-maximized"],
            )

        try:
            page = context.pages[0] if context.pages else context.new_page()

            _login_progress["message"] = "Opening university Moodle login page..."
            _login_progress["last_updated"] = time.time()
            logger.info("Navigating to Moodle login page...")

            # Navigate to Moodle (try /login/index.php or base URL)
            login_url = moodle_url.rstrip("/") + "/login/index.php"
            try:
                page.goto(login_url, timeout=45000, wait_until="domcontentloaded")
            except Exception:
                # Fallback to root URL if /login/index.php redirects
                page.goto(moodle_url, timeout=45000, wait_until="domcontentloaded")

            # Check if user is already logged in (from persistent browser profile)
            if _check_if_moodle_authenticated(page, moodle_url):
                logger.info("Existing session is already authenticated in browser profile!")
                page.wait_for_timeout(2000)
                context.storage_state(path=str(STORAGE_STATE_FILE))
                _login_progress = {
                    "is_logging_in": False,
                    "status": "success",
                    "message": "Already authenticated! Moodle session updated.",
                    "last_updated": time.time(),
                }
                return {"success": True, "message": "Already authenticated! Session saved."}

            # If on login page, detect 'Sign in with Microsoft' button and click it
            _login_progress["message"] = "Detecting 'Sign in with Microsoft' option..."
            _login_progress["last_updated"] = time.time()
            page.wait_for_timeout(1500)

            # Common selectors for Microsoft SSO buttons in Moodle
            ms_selectors = [
                'a:has-text("Sign in with Microsoft")',
                'button:has-text("Sign in with Microsoft")',
                'a:has-text("Microsoft 365")',
                'button:has-text("Microsoft 365")',
                'a:has-text("Microsoft")',
                'button:has-text("Microsoft")',
                'a[href*="auth/oidc"]',
                'a[href*="auth/oauth2"]',
                'a[href*="microsoft"]',
                'a[title*="Microsoft"]',
                '.potentialidplist a',
            ]

            clicked_ms = False
            for sel in ms_selectors:
                try:
                    btn = page.query_selector(sel)
                    if btn and btn.is_visible():
                        logger.info(f"Found Microsoft login button ({sel}), clicking...")
                        _login_progress["message"] = "Clicking 'Sign in with Microsoft'..."
                        _login_progress["last_updated"] = time.time()
                        btn.click()
                        clicked_ms = True
                        break
                except Exception:
                    continue

            if not clicked_ms:
                logger.info("Microsoft button not clicked automatically; waiting for user to click it or continue...")
                _login_progress["message"] = "Please click 'Sign in with Microsoft' in the browser window..."
            else:
                _login_progress["message"] = "Waiting for Microsoft authentication & MFA in the browser window..."

            _login_progress["last_updated"] = time.time()

            # Poll until authentication completes and user lands back on Moodle
            start_time = time.time()
            authenticated = False

            while time.time() - start_time < timeout_seconds:
                try:
                    # Give time between checks
                    page.wait_for_timeout(1000)

                    # Check current state
                    if _check_if_moodle_authenticated(page, moodle_url):
                        authenticated = True
                        break

                    # Update progress message if on Microsoft login
                    current_url = page.url.lower()
                    if "microsoft" in current_url or "live.com" in current_url:
                        _login_progress["message"] = "Microsoft authentication / MFA in progress..."
                        _login_progress["last_updated"] = time.time()
                    elif "/login/" in current_url:
                        _login_progress["message"] = "On login page. Please click 'Sign in with Microsoft'..."
                        _login_progress["last_updated"] = time.time()

                except PlaywrightError:
                    logger.warning("Browser window was closed by the user.")
                    break
                except Exception as poll_err:
                    logger.debug(f"Polling loop check: {poll_err}")
                    continue

            if authenticated:
                logger.info("Successfully detected authenticated Moodle session!")
                _login_progress["message"] = "Authentication confirmed! Saving session..."
                _login_progress["last_updated"] = time.time()

                # Allow 2 seconds for session cookies to settle
                page.wait_for_timeout(2000)

                # Save authenticated storage state
                context.storage_state(path=str(STORAGE_STATE_FILE))
                logger.info(f"Session saved to {STORAGE_STATE_FILE}")

                _login_progress = {
                    "is_logging_in": False,
                    "status": "success",
                    "message": "Microsoft SSO login completed successfully! Moodle session saved.",
                    "last_updated": time.time(),
                }
                return {
                    "success": True,
                    "message": "Microsoft SSO authentication completed successfully! Moodle session saved.",
                    "storage_state_path": str(STORAGE_STATE_FILE),
                }
            else:
                _login_progress = {
                    "is_logging_in": False,
                    "status": "failed",
                    "message": "Login was not completed within the allowed time or browser was closed.",
                    "last_updated": time.time(),
                }
                return {
                    "success": False,
                    "message": "Authentication was not completed within the time limit or the browser window was closed.",
                }

        except Exception as e:
            logger.error(f"Microsoft SSO login failed: {e}", exc_info=True)
            _login_progress = {
                "is_logging_in": False,
                "status": "failed",
                "message": f"Login error: {str(e)}",
                "last_updated": time.time(),
            }
            return {"success": False, "message": str(e)}

        finally:
            try:
                context.close()
            except Exception:
                pass

def verify_session(moodle_url: str) -> Dict[str, Any]:
    """
    Tests whether the saved Moodle storage_state.json is still valid
    using a headless browser check.
    
    Returns:
      - valid: bool
      - expired: bool
      - message: str
    """
    if not is_session_saved():
        return {
            "valid": False,
            "expired": False,
            "message": "No saved session found. Please click 'Sign in with Microsoft' to connect."
        }

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="msedge", headless=True)
        except Exception:
            browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context(storage_state=str(STORAGE_STATE_FILE))
            page = context.new_page()
            target_url = moodle_url.rstrip("/") + "/my/"
            response = page.goto(target_url, timeout=30000, wait_until="domcontentloaded")

            current_url = page.url.lower()

            # Check if redirected to Microsoft SSO login or Moodle login page
            is_microsoft_login = any(ms in current_url for ms in ["microsoft", "live.com", "msft"])
            is_moodle_login = "/login/" in current_url and "/my" not in current_url

            if is_microsoft_login or is_moodle_login:
                return {
                    "valid": False,
                    "expired": True,
                    "message": "Moodle session expired — Sign in again"
                }

            # Check if page is authenticated back into Moodle
            if _check_if_moodle_authenticated(page, moodle_url):
                return {
                    "valid": True,
                    "expired": False,
                    "message": "Moodle session is active and valid"
                }

            # If response is not OK or redirected elsewhere
            return {
                "valid": False,
                "expired": True,
                "message": "Moodle session expired — Sign in again"
            }

        except Exception as e:
            return {
                "valid": False,
                "expired": True,
                "message": f"Verification error: {str(e)}"
            }
        finally:
            browser.close()
