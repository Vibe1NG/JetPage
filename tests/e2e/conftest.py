"""Session-scoped fixtures that start the JetPage app and wire up pytest-playwright.

Key constraint: Flet/Flutter CanvasKit renderer does NOT respond to direct hash-URL
navigation in Playwright (all routes render the home page). The only reliable way to
navigate is by clicking the flt-semantics buttons exposed in the Flutter accessibility
tree after calling `_enable_accessibility()`.
"""

import os
import socket
import subprocess
import time

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Time for Flutter to initialise and render the first frame
FLUTTER_INIT_MS = 6_000
# Time for a route change to settle after a nav button click
NAV_SETTLE_MS = 3_000


def _free_port() -> int:
    """Return an available TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_port(port: int, timeout: float = 30.0) -> None:
    """Block until the given port accepts connections, or raise TimeoutError."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return
        except OSError:
            time.sleep(0.5)
    raise TimeoutError(f"JetPage did not start on port {port} within {timeout}s")


@pytest.fixture(scope="session")
def app_port() -> int:
    return _free_port()


@pytest.fixture(scope="session")
def app_server(app_port: int):
    """Launch the JetPage web server for the test session and shut it down afterwards."""
    env = {
        **os.environ,
        "PORT": str(app_port),
        "HOST": "127.0.0.1",
        "CONTENT_DIR": os.path.join(PROJECT_ROOT, "content"),
    }
    proc = subprocess.Popen(
        ["uv", "run", "python", "-m", "jetpage.main"],
        cwd=PROJECT_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        _wait_for_port(app_port)
    except TimeoutError:
        proc.terminate()
        raise
    yield proc
    proc.terminate()
    proc.wait(timeout=10)


@pytest.fixture(scope="session")
def base_url(app_server, app_port: int) -> str:
    """Override pytest-playwright's base_url with the live server address."""
    return f"http://127.0.0.1:{app_port}"


def enable_accessibility(page) -> None:
    """Click the Flutter semantics placeholder to activate the flt-semantics overlay.

    Flutter web (CanvasKit) renders all visuals to a <canvas>.  Text is not in the
    normal DOM.  Clicking the hidden flt-semantics-placeholder button tells Flutter
    to build an invisible accessibility tree (flt-semantics nodes) that Playwright
    can query for labels and click interactions.
    """
    page.evaluate("document.querySelector('flt-semantics-placeholder')?.click()")
    page.wait_for_timeout(1_000)


@pytest.fixture(scope="session")
def app_page(browser, base_url):
    """A single Playwright page shared across the whole test session.

    Flet's web server is single-user and crashes if multiple browser connections
    are opened in rapid succession.  One long-lived page avoids that problem.

    Navigation tests that change the page state should navigate back to home
    using the helper `go_home(page)` before taking their baseline screenshot.
    """
    context = browser.new_context(viewport={"width": 1280, "height": 720})
    page = context.new_page()
    page.goto(base_url + "/", wait_until="domcontentloaded")
    page.wait_for_timeout(FLUTTER_INIT_MS)
    enable_accessibility(page)
    yield page
    context.close()


def go_home(page) -> None:
    """Switch to the User Guide document and navigate to the Home page.

    Always call this at the start of any test that needs User Guide sidebar state.
    The session-scoped page may be on any document/page from a previous test.
    """
    # Ensure User Guide document is active (sidebar shows User Guide pages)
    page.locator("flt-semantics[flt-tappable]").filter(has_text="User Guide").first.click(force=True)
    page.wait_for_timeout(1_000)
    # Navigate to Home
    page.locator("flt-semantics[flt-tappable]").filter(has_text="Home").first.click(force=True)
    page.wait_for_timeout(NAV_SETTLE_MS)
