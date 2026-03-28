"""Phase 1 routing tests.

Constraints discovered during implementation:
- Flet/Flutter CanvasKit renderer ignores direct hash-URL navigation (all pages
  render home content when loaded via goto("#/slug")).
- Navigation only works through clicks on flt-semantics button nodes.
- Screenshots are the reliable way to verify content changes after navigation.
- Flet's web server is single-user; multiple rapid page.goto() calls crash it.
  All tests share one session-scoped page (see conftest.app_page).
- pytest interleaves parametrized tests, so tests that depend on a specific
  document/page state must call go_home() at the start to restore known state.

Test strategy:
1. Verify the Flutter app shell renders (canvas + flt-glass-pane present).
2. Verify all expected nav items are present in a single pass (one go_home call).
3. Verify that clicking each nav item changes the rendered content (screenshot diff).
"""

import pytest
from playwright.sync_api import Page

from tests.e2e.conftest import NAV_SETTLE_MS, go_home

# Document tabs always visible in the top bar regardless of active document
DOCUMENT_TABS = ["User Guide", "Reference Library"]

# (button_text, description) — each click must produce a screenshot different from home
NAVIGABLE_PAGES = [
    ("Installation", "getting-started/installation"),
    ("Configuration", "getting-started/configuration"),
    ("Content Authoring", "guides/content-authoring"),
    ("BDD with Gherkin", "guides/gherkin-example"),
    ("Reference Library", "reference-library-dropdown"),
]


# (button_text, description) — each click must produce a screenshot different from home
NAVIGABLE_PAGES = [
    ("Installation", "getting-started/installation"),
    ("Configuration", "getting-started/configuration"),
    ("Content Authoring", "guides/content-authoring"),
    ("BDD with Gherkin", "guides/gherkin-example"),
]


def _sem(page: Page):
    return page.locator("flt-semantics")


def _tappable(page: Page):
    return page.locator("flt-semantics[flt-tappable]")


# ---------------------------------------------------------------------------
# Shell integrity  (no navigation — inspects the initial home-page state)
# ---------------------------------------------------------------------------


def test_app_shell_renders(app_page: Page) -> None:
    """Flutter must have rendered a canvas and the glass-pane host element."""
    assert app_page.locator("flt-glass-pane").count() > 0, "flt-glass-pane missing — Flutter did not boot"
    assert app_page.locator("canvas").count() > 0, "No canvas element — CanvasKit did not render"


def test_flutter_accessibility_overlay(app_page: Page) -> None:
    """After enabling accessibility, at least one flt-semantics node must exist."""
    assert _sem(app_page).count() > 0, "No flt-semantics nodes — accessibility overlay absent"


# ---------------------------------------------------------------------------
# Navigation items  (one go_home call — checks all items in a single pass)
# ---------------------------------------------------------------------------


def test_all_document_tabs_present(app_page: Page) -> None:
    """All three document tabs must appear as tappable nodes in the top bar."""
    for label in DOCUMENT_TABS:
        count = _tappable(app_page).filter(has_text=label).count()
        assert count > 0, f"Document tab {label!r} not found in flt-semantics"


def test_all_sidebar_items_present(app_page: Page) -> None:
    """All User Guide sidebar items must be in the accessibility tree."""
    go_home(app_page)
    for label in SIDEBAR_ITEMS:
        count = _sem(app_page).filter(has_text=label).count()
        assert count > 0, f"Sidebar item {label!r} not found in flt-semantics"


# ---------------------------------------------------------------------------
# Navigation changes content
# Each test calls go_home() first so it starts from a known baseline.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("button_text,description", NAVIGABLE_PAGES)
def test_navigation_changes_content(app_page: Page, button_text: str, description: str) -> None:
    """Clicking a nav item must change the rendered page (screenshot differs from home)."""
    go_home(app_page)
    before = app_page.screenshot()

    _tappable(app_page).filter(has_text=button_text).first.click(force=True)
    app_page.wait_for_timeout(NAV_SETTLE_MS)

    after = app_page.screenshot()
    assert before != after, f"Page did not change after clicking {button_text!r} ({description})"


def test_library_navigation_works(app_page: Page) -> None:
    """Clicking a library dropdown and then a document link within it must navigate."""
    go_home(app_page)
    before = app_page.screenshot()

    # 1. Click the library button to open the dropdown
    _tappable(app_page).filter(has_text="Reference Library").first.click(force=True)
    app_page.wait_for_timeout(NAV_SETTLE_MS)

    # 2. Click the "Reference" link within the dropdown (it's now in the semantics tree)
    _tappable(app_page).filter(has_text="Reference").first.click(force=True)
    app_page.wait_for_timeout(NAV_SETTLE_MS)

    after = app_page.screenshot()
    assert before != after, "Navigating through library dropdown did not change the page"
