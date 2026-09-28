"""Exercise the real homepage layout and disclosure controls in Chromium."""

from collections.abc import Iterator
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest
from playwright.sync_api import Page, sync_playwright


@pytest.fixture
def homepage() -> Iterator[Page]:
    """Serve repository assets and yield a real browser page.

    Yields:
        Page: Chromium page connected to the local static site.
    """
    root = Path(__file__).resolve().parents[1]
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(root)))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            page.goto(f"http://127.0.0.1:{server.server_port}/preview/")
            yield page
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize("width", [320, 390, 768, 1440])
def test_homepage_readable_without_overflow(homepage: Page, width: int) -> None:
    """Keep every card readable at phone, tablet, and desktop widths.

    Args:
        homepage (Page): Browser page serving the actual repository.
        width (int): Viewport width in CSS pixels.
    """
    homepage.set_viewport_size({"width": width, "height": 900})
    assert homepage.locator('meta[name="viewport"]').get_attribute("content") == (
        "width=device-width, initial-scale=1"
    )
    assert homepage.locator(".dashboards > li").count() == 6
    assert homepage.locator(".dashboards a").first.get_attribute("href") == "https://search.austinwagner.org"
    assert homepage.locator("details").count() == 5
    assert homepage.locator("details[open]").count() == 0
    assert homepage.locator("details a").count() == 14
    for summary in homepage.locator("details > summary").all():
        summary.focus()
        homepage.keyboard.press("Enter")
    assert homepage.locator("details[open]").count() == 5
    scroll_width: int = homepage.evaluate("document.documentElement.scrollWidth")
    assert scroll_width == width
    for panel in homepage.locator(".panel").all():
        bounds = panel.bounding_box()
        assert bounds is not None
        assert bounds["x"] >= 0
        assert bounds["x"] + bounds["width"] <= width
        background: str = panel.evaluate("(element) => getComputedStyle(element).backgroundColor")
        assert background == "rgb(255, 255, 255)"
        font_size: str = panel.locator("p").evaluate("(element) => getComputedStyle(element).fontSize")
        assert font_size == "18px"
    upper = homepage.locator(".upper").bounding_box()
    forest = homepage.locator("#backdrop").bounding_box()
    assert upper is not None
    assert forest is not None
    assert forest["y"] >= upper["y"] + upper["height"]
    cards = homepage.locator(".dashboards a")
    first = cards.nth(0).bounding_box()
    second = cards.nth(1).bounding_box()
    assert first is not None
    assert second is not None
    if width <= 700:
        assert second["y"] >= first["y"] + first["height"]
    else:
        assert first["y"] == second["y"]
        assert second["x"] >= first["x"] + first["width"]
